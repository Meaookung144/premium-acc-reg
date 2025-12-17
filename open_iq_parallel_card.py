#!/Users/meaookung144/Documents/GitHub/premium-acc-reg/venv/bin/python3
"""
Selenium macro to open iq.com with Chromium browser - PARALLEL VERSION (CARD PAYMENT)
Runs 2 browsers simultaneously to process 2 accounts at once
Uses CREDIT CARD payment instead of Rabbit Line Pay
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import random
import requests
from datetime import datetime
import threading
from queue import Queue
import imaplib
import email as email_module
import socket
import re
import os
import zipfile

# Configuration
PASSWORD = "schema94"  # Set your password here
EMAILS_FILE = "emails.txt"  # File containing emails (one per line)
NUM_PARALLEL_BROWSERS = 2  # Number of browsers to run in parallel
AUTO_OTP = True  # Set to True for automatic OTP fetching, False for manual entry

# ============================================================================
# SUBSCRIPTION PACKAGE CONFIGURATION
# ============================================================================
SUBSCRIPTION_MONTHS = 1  # Options: 1, 3, or 12
# - 1 month:  ฿119 (Monthly Subscription) - rseat='0:0'
# - 3 months: ฿339 (Quarterly Subscription) - rseat='0:1'
# - 12 months: ฿1200 (Annual Subscription) - rseat='0:2'

# ============================================================================
# WEBMAIL CONFIGURATION
# ============================================================================
WEBMAIL_TYPE = "pranakorn"  # Options: "pranakorn" or "hotmail"
# - "pranakorn": Uses coaco.space IMAP (format: email|password)
# - "hotmail": Uses read-mail.me API (format: email|password|refresh_token|client_id)

# ============================================================================
# PROXY CONFIGURATION
# ============================================================================
USE_PROXY = False  # Set to True to enable proxy support
PROXY_FILE = "proxy.txt"  # File containing proxies (format: ip:port or user:pass@ip:port)
PROXY_TYPE = "http"  # Options: "http", "https", "socks5"

# ============================================================================
# CARD PAYMENT CONFIGURATION
# ============================================================================
# Credit card details for automatic payment
# The card will be split into 4 groups of 4 digits for the input fields
CARD_NUMBER = "55010"  # Card number (16 digits, no spaces)
CARD_EXPIRY_MONTH = "12"  # Expiry month (MM format, e.g., "12")
CARD_EXPIRY_YEAR = "2025"  # Expiry year (YYYY format, e.g., "2025")
CARD_CVV = "123"  # CVV code (3-4 digits)

# IMAP Configuration for pranakorn emails
IMAP_SERVER = "mail.coaco.space"
OTP_POLL_INTERVAL = 0.5  # Poll every 500ms for pranakorn

# Month names
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

# Proxy queue for thread-safe proxy rotation
proxy_queue = Queue()
proxy_lock = threading.Lock()


def load_proxies(filename):
    """Load proxies from file"""
    proxies = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        print(f"✓ Loaded {len(proxies)} proxy/proxies from {filename}")
    except FileNotFoundError:
        print(f"⚠ Proxy file not found: {filename}")
    return proxies


def create_proxy_extension(proxy_host, proxy_port, proxy_user=None, proxy_pass=None):
    """Create a Chrome extension for authenticated proxy"""
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    if proxy_user and proxy_pass:
        # Authenticated proxy
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy_host, proxy_port, proxy_user, proxy_pass)
    else:
        # Non-authenticated proxy
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        """ % (proxy_host, proxy_port)

    plugin_file = f'proxy_auth_plugin_{proxy_host}_{proxy_port}.zip'

    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_file


def extract_otp(text):
    """Extract OTP code from text (typically 4-8 digits)"""
    if not text:
        return None

    # Look for patterns like "220446 is your", "code: 123456", "OTP: 123456", etc.
    patterns = [
        r'\b(\d{4,8})\s+is\s+your',  # "220446 is your dynamic security verification code"
        r'code[:\s]+(\d{4,8})',       # "code: 123456" or "code 123456"
        r'otp[:\s]+(\d{4,8})',        # "OTP: 123456" or "OTP 123456"
        r'verification[:\s]+(\d{4,8})', # "verification: 123456"
        r'\b(\d{6})\b',               # Any standalone 6-digit number
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def get_otp_pranakorn(email_address, email_password, max_retries=40):
    """
    Fetch OTP code from pranakorn/coaco.space email via IMAP
    Polls every 500ms for up to 40 attempts (20 seconds total)
    """
    print(f"\n{'='*60}")
    print(f"Fetching OTP code for {email_address} via IMAP")
    print(f"Will poll every {OTP_POLL_INTERVAL}s up to {max_retries} times")
    print(f"{'='*60}")

    for attempt in range(max_retries):
        try:
            print(f"\n[Attempt {attempt + 1}/{max_retries}] Connecting to IMAP...")

            # Try SSL connection
            try:
                sock = socket.create_connection((IMAP_SERVER, 993), timeout=5)
                sock.close()
                mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
            except:
                # Fallback to STARTTLS
                try:
                    mail = imaplib.IMAP4(IMAP_SERVER, 143)
                    mail.starttls()
                except Exception as e:
                    print(f"✗ Connection failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(OTP_POLL_INTERVAL)
                    continue

            # Login
            try:
                mail.login(email_address, email_password)
                print(f"✓ Logged in to {IMAP_SERVER}")
            except Exception as e:
                print(f"✗ Login failed: {e}")
                try:
                    mail.logout()
                except:
                    pass
                if attempt < max_retries - 1:
                    time.sleep(OTP_POLL_INTERVAL)
                continue

            # Select inbox
            mail.select("INBOX")

            # Search for all emails
            status, messages = mail.search(None, "ALL")
            if status != "OK":
                print(f"✗ Failed to search emails")
                mail.logout()
                if attempt < max_retries - 1:
                    time.sleep(OTP_POLL_INTERVAL)
                continue

            # Get the latest email
            email_ids = messages[0].split()
            if not email_ids:
                print(f"✗ No emails found in inbox")
                mail.logout()
                if attempt < max_retries - 1:
                    time.sleep(OTP_POLL_INTERVAL)
                continue

            latest_email_id = email_ids[-1]

            # Fetch the email
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            if status != "OK":
                print(f"✗ Failed to fetch email")
                mail.logout()
                if attempt < max_retries - 1:
                    time.sleep(OTP_POLL_INTERVAL)
                continue

            # Parse email
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email_module.message_from_bytes(response_part[1])

                    # Get subject
                    subject = msg.get("Subject", "")
                    from_addr = msg.get("From", "")

                    print(f"✓ Latest email from: {from_addr}")
                    print(f"  Subject: {subject}")

                    # Check if from iQIYI
                    if "iq.com" not in from_addr.lower() and "iqiyi" not in from_addr.lower():
                        print(f"✗ Email not from iQIYI, waiting for new email...")
                        mail.logout()
                        if attempt < max_retries - 1:
                            time.sleep(OTP_POLL_INTERVAL)
                        continue

                    # Try to extract OTP from subject first
                    otp_code = extract_otp(subject)

                    # If not in subject, check body
                    if not otp_code and msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    otp_code = extract_otp(body)
                                    if otp_code:
                                        break
                                except:
                                    pass
                    elif not otp_code:
                        try:
                            body = msg.get_payload(decode=True).decode()
                            otp_code = extract_otp(body)
                        except:
                            pass

                    if otp_code:
                        print(f"✓ Found OTP code: {otp_code}")
                        mail.logout()
                        return otp_code
                    else:
                        print(f"✗ No OTP found in email")

            mail.logout()

            if attempt < max_retries - 1:
                time.sleep(OTP_POLL_INTERVAL)

        except Exception as e:
            print(f"✗ Error reading email: {e}")
            if attempt < max_retries - 1:
                time.sleep(OTP_POLL_INTERVAL)

    print(f"\n✗ Failed to get OTP after {max_retries} attempts")
    return None


def wait_for_page_load(driver, timeout=10):
    """Wait for page to complete loading"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def read_emails(filename):
    """Read emails from text file
    Format depends on WEBMAIL_TYPE:
    - pranakorn: email|password
    - hotmail: email|password|refresh_token|client_id
    """
    try:
        with open(filename, 'r') as f:
            email_data = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Split by | and extract all parts
                    parts = line.split('|')

                    if WEBMAIL_TYPE == "pranakorn":
                        # Format: email|password
                        if len(parts) >= 2:
                            email_info = {
                                'email': parts[0].strip(),
                                'password': parts[1].strip(),
                                'refresh_token': None,
                                'client_id': None
                            }
                            email_data.append(email_info)
                    else:  # hotmail
                        # Format: email|password|refresh_token|client_id
                        if len(parts) >= 4:
                            email_info = {
                                'email': parts[0].strip(),
                                'password': parts[1].strip(),
                                'refresh_token': parts[2].strip(),
                                'client_id': parts[3].strip()
                            }
                            email_data.append(email_info)
        return email_data
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []

def get_otp_code(email, refresh_token, client_id, max_retries=8):
    """Fetch OTP code from read-mail.me with retry logic"""
    url = "https://read-mail.me/get_data.php"
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://read-mail.me",
        "Referer": "https://read-mail.me/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

    payload = {
        "email": email,
        "refresh_token": refresh_token,
        "client_id": client_id
    }

    print(f"\n{'='*60}")
    print(f"Fetching OTP code for {email}")
    print(f"Will retry up to {max_retries} times (waiting 6 seconds between attempts)")
    print(f"{'='*60}")

    for attempt in range(max_retries):
        try:
            print(f"\n[Attempt {attempt + 1}/{max_retries}] Sending request to read OTP...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                print(f"✓ API request successful (status: 200)")

                if 'messages' in data and len(data['messages']) > 0:
                    print(f"✓ Found {len(data['messages'])} message(s) in mailbox")

                    expired_codes_count = 0

                    for message in data['messages']:
                        # Check if message is from iQIYI
                        if 'from' in message and len(message['from']) > 0:
                            from_address = message['from'][0].get('address', '')
                            from_name = message['from'][0].get('name', '')

                            if 'iq.com' in from_address.lower():
                                # Extract code
                                code = message.get('code', '')
                                date_str = message.get('date', '')

                                if code:
                                    print(f"✓ Found message from {from_name} ({from_address})")

                                    # Check if code is less than 5 minutes old
                                    try:
                                        msg_time = datetime.fromisoformat(date_str.replace('+08:00', ''))
                                        current_time = datetime.now()
                                        time_diff = (current_time - msg_time).total_seconds() / 60

                                        if time_diff < 5:
                                            print(f"✓ OTP code is VALID: {code} (received {time_diff:.1f} min ago)")
                                            print(f"{'='*60}")
                                            return code
                                        else:
                                            expired_codes_count += 1
                                            print(f"✗ OTP code {code} is EXPIRED ({time_diff:.1f} min old, max 5 min)")
                                            print(f"  Continuing to check other messages...")
                                            continue  # Check next message
                                    except Exception as parse_error:
                                        # If time parsing fails, skip this code for safety
                                        print(f"⚠ Could not verify time for code {code}: {parse_error}")
                                        print(f"  Skipping unverifiable code, checking next message...")
                                        continue  # Check next message

                    # If we got here, no valid code was found
                    if expired_codes_count > 0:
                        print(f"\n⚠ Found {expired_codes_count} expired OTP code(s)")
                        print(f"  Will retry API call to get fresh code...")
                    else:
                        print(f"✗ No valid OTP codes found in messages")
                else:
                    print(f"✗ No messages found in mailbox yet")
            else:
                print(f"✗ API request failed (status: {response.status_code})")

            # Wait before retry
            if attempt < max_retries - 1:
                print(f"Waiting 6 seconds before next attempt...")
                time.sleep(6)

        except requests.exceptions.Timeout:
            print(f"✗ Timeout on attempt {attempt + 1}: API took too long to respond (>30s)")
            if attempt < max_retries - 1:
                print(f"Waiting 6 seconds before next attempt...")
                time.sleep(6)
        except Exception as e:
            print(f"✗ Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Waiting 6 seconds before next attempt...")
                time.sleep(6)

    print(f"\n{'='*60}")
    print(f"✗ Failed to retrieve OTP code after {max_retries} attempts")
    print(f"{'='*60}")
    return None

def save_success(email_data):
    """Save successful email to success.txt"""
    try:
        with open('success.txt', 'a') as f:
            line = f"{email_data['email']}|{email_data['password']}|{email_data['refresh_token']}|{email_data['client_id']}\n"
            f.write(line)
        print(f"✓ Saved {email_data['email']} to success.txt")
    except Exception as e:
        print(f"Error saving to success.txt: {e}")

def remove_from_emails_file(email_to_remove, filename):
    """Remove processed email from emails.txt"""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()

        with open(filename, 'w') as f:
            for line in lines:
                if not line.startswith(email_to_remove):
                    f.write(line)
        print(f"✓ Removed {email_to_remove} from {filename}")
    except Exception as e:
        print(f"Error removing from {filename}: {e}")

def process_single_email(driver, wait, current_email_data, url):
    """Process a single email through the entire registration flow
    Returns:
        True - Success
        False - Permanent failure
        'retry' - Connection not secure, should retry entire process
    """
    global SUBSCRIPTION_MONTHS

    print(f"\n{'='*60}")
    print(f"Processing email: {current_email_data['email']}")
    print(f"{'='*60}")

    # Navigate to iq.com
    driver.get(url)
    wait_for_page_load(driver)
    print(f"Successfully opened {url}")
    time.sleep(0.5)

    # Step 1: Click the Login button
    try:
        print("\nStep 1: Looking for Login button...")
        login_button = None
        login_selectors = [
            (By.CSS_SELECTOR, "div.userImg-wrap[role='button']"),
            (By.CSS_SELECTOR, "div.userImg-wrap"),
            (By.XPATH, "//div[@class='userImg-wrap' and @role='button']"),
            (By.XPATH, "//div[contains(@class, 'login-button')]")
        ]

        for by, selector in login_selectors:
            try:
                login_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if login_button:
                    print(f"Found login button using: {selector}")
                    break
            except:
                continue

        if login_button:
            login_button.click()
            print("✓ Clicked Login button successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find Login button")
            raise Exception("Login button not found")

    except Exception as e:
        print(f"Error clicking login button: {e}")
        raise

    # Step 2: Click the Sign Up link
    try:
        print("\nStep 2: Looking for Sign Up link...")
        signup_link = None
        signup_selectors = [
            (By.XPATH, "//span[contains(@class, 'passport-login-tip__link') and contains(text(), 'Sign Up')]"),
            (By.CSS_SELECTOR, "span.passport-login-tip__link"),
            (By.XPATH, "//span[contains(text(), 'Sign Up')]")
        ]

        for by, selector in signup_selectors:
            try:
                signup_link = wait.until(EC.element_to_be_clickable((by, selector)))
                if signup_link:
                    print(f"Found Sign Up link using: {selector}")
                    break
            except:
                continue

        if signup_link:
            signup_link.click()
            print("✓ Clicked Sign Up link successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find Sign Up link")
            raise Exception("Sign Up link not found")

    except Exception as e:
        print(f"Error clicking Sign Up link: {e}")
        raise

    # Step 3: Click the "Sign up with Email" button
    try:
        print("\nStep 3: Looking for 'Sign up with Email' button...")
        email_signup_button = None
        email_signup_selectors = [
            (By.XPATH, "//div[contains(@class, 'passport-btn-login')]//span[contains(text(), 'Sign up with Email')]"),
            (By.CSS_SELECTOR, "div.passport-btn-login"),
            (By.XPATH, "//div[contains(@class, 'passport-btn')]//span[contains(text(), 'Email')]")
        ]

        for by, selector in email_signup_selectors:
            try:
                email_signup_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if email_signup_button:
                    print(f"Found 'Sign up with Email' button using: {selector}")
                    break
            except:
                continue

        if email_signup_button:
            email_signup_button.click()
            print("✓ Clicked 'Sign up with Email' button successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find 'Sign up with Email' button")

    except Exception as e:
        print(f"Error clicking 'Sign up with Email' button: {e}")

    # Step 4: Fill in the email field
    try:
        print("\nStep 4: Filling in email...")
        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='text'].passport-input__input")
        ))
        email_input.clear()
        email_input.send_keys(current_email_data['email'])
        print(f"✓ Entered email: {current_email_data['email']}")
        time.sleep(0.3)
    except Exception as e:
        print(f"Error entering email: {e}")

    # Step 5: Fill in the password field
    try:
        print("\nStep 5: Filling in password...")
        password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password'].passport-input__input")
        if len(password_inputs) >= 1:
            password_inputs[0].clear()
            password_inputs[0].send_keys(PASSWORD)
            print(f"✓ Entered password")
            time.sleep(0.3)
    except Exception as e:
        print(f"Error entering password: {e}")

    # Step 6: Fill in the re-password field
    try:
        print("\nStep 6: Filling in re-password...")
        password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password'].passport-input__input")
        if len(password_inputs) >= 2:
            password_inputs[1].clear()
            password_inputs[1].send_keys(PASSWORD)
            print(f"✓ Re-entered password")
            time.sleep(0.3)
    except Exception as e:
        print(f"Error entering re-password: {e}")

    # Step 7: Select the year (2000)
    try:
        print("\nStep 7: Selecting birth year (2000)...")
        # Click on the year picker wrapper to open dropdown
        year_wrapper = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.pikcer-wrapper.year-pikcer-wrapper")
        ))
        year_wrapper.click()
        print("✓ Opened year dropdown")
        time.sleep(0.5)

        # Click on the year 2000 from the list
        year_item_selectors = [
            (By.XPATH, "//li[@class='date-item' and contains(text(), '2000')]"),
            (By.XPATH, "//li[contains(@class, 'date-item') and normalize-space()='2000']"),
            (By.XPATH, "//li[contains(text(), '2000')]")
        ]

        year_found = False
        for by, selector in year_item_selectors:
            try:
                year_item = wait.until(EC.element_to_be_clickable((by, selector)))
                if year_item:
                    year_item.click()
                    print(f"✓ Selected year: 2000")
                    year_found = True
                    break
            except:
                continue

        if not year_found:
            print("✗ Could not find year 2000 in list")

        time.sleep(0.3)
    except Exception as e:
        print(f"Error selecting year: {e}")

    # Step 8: Select random month
    try:
        print("\nStep 8: Selecting random month...")
        # Click on the month picker wrapper to open dropdown
        month_wrapper = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.pikcer-wrapper.month-pikcer-wrapper")
        ))
        month_wrapper.click()
        print("✓ Opened month dropdown")
        time.sleep(0.5)

        # Generate random month name
        random_month_index = random.randint(0, 11)
        month_name = MONTHS[random_month_index]

        # Click on the month from the list
        month_item_selectors = [
            (By.XPATH, f"//li[@class='date-item' and contains(text(), '{month_name}')]"),
            (By.XPATH, f"//li[contains(@class, 'date-item') and normalize-space()='{month_name}']"),
            (By.XPATH, f"//li[contains(text(), '{month_name}')]")
        ]

        month_found = False
        for by, selector in month_item_selectors:
            try:
                month_item = wait.until(EC.element_to_be_clickable((by, selector)))
                if month_item:
                    month_item.click()
                    print(f"✓ Selected month: {month_name}")
                    month_found = True
                    break
            except:
                continue

        if not month_found:
            print(f"✗ Could not find month {month_name} in list")

        time.sleep(0.3)
    except Exception as e:
        print(f"Error selecting month: {e}")

    # Step 9: Select random day (1-9)
    try:
        print("\nStep 9: Selecting random day (1-9)...")
        # Click on the day picker wrapper to open dropdown
        day_wrapper = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.pikcer-wrapper.day-pikcer-wrapper")
        ))
        day_wrapper.click()
        print("✓ Opened day dropdown")
        time.sleep(0.5)

        # Generate random day (1-9 without leading zero for single digits)
        random_day = random.randint(1, 9)
        day_str = str(random_day)  # Use without zero padding for better compatibility

        # Click on the day from the list
        day_item_selectors = [
            (By.XPATH, f"//li[@class='date-item' and normalize-space()='{day_str}']"),
            (By.XPATH, f"//li[contains(@class, 'date-item') and normalize-space()='{day_str}']"),
            (By.XPATH, f"//li[contains(@class, 'date-item') and normalize-space()='{random_day}']"),
            (By.XPATH, f"//li[contains(text(), '{day_str}')]")
        ]

        day_found = False
        for by, selector in day_item_selectors:
            try:
                day_item = wait.until(EC.element_to_be_clickable((by, selector)))
                if day_item:
                    day_item.click()
                    print(f"✓ Selected day: {day_str}")
                    day_found = True
                    break
            except:
                continue

        if not day_found:
            print(f"✗ Could not find day {day_str} in list")

        time.sleep(0.3)
    except Exception as e:
        print(f"Error selecting day: {e}")

    # Step 10: Click the Sign Up submit button
    try:
        print("\nStep 10: Clicking Sign Up button...")
        signup_submit_button = None
        signup_submit_selectors = [
            (By.XPATH, "//div[contains(@class, 'passport-btn-primary') and contains(text(), 'Sign Up')]"),
            (By.CSS_SELECTOR, "div.passport-btn.passport-btn-primary"),
            (By.XPATH, "//div[contains(@class, 'passport-btn') and contains(@class, 'passport-btn-primary')]")
        ]

        for by, selector in signup_submit_selectors:
            try:
                signup_submit_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if signup_submit_button:
                    print(f"Found Sign Up submit button using: {selector}")
                    break
            except:
                continue

        if signup_submit_button:
            signup_submit_button.click()
            print("✓ Clicked Sign Up submit button successfully!")
            time.sleep(2)  # Wait for potential error toast

            # Check for "Connection is not secure" error
            try:
                error_toast = driver.find_element(By.CSS_SELECTOR, "p.passport-toast-txt")
                error_text = error_toast.text.strip()
                if "Connection is not secure" in error_text or "not secure" in error_text.lower():
                    print(f"\n{'='*60}")
                    print("⚠ ERROR: Connection is not secure")
                    print(f"⚠ Message: {error_text}")
                    print("⚠ Will restart registration process for this account")
                    print(f"{'='*60}")
                    return 'retry'  # Signal to restart the entire registration process
            except:
                pass  # No error toast found, continue normally
        else:
            print("✗ Could not find Sign Up submit button")

    except Exception as e:
        print(f"Error clicking Sign Up submit button: {e}")

    print("\n✓ Form filled and submitted successfully!")

    # Step 11: OTP verification with retry logic
    max_otp_retries = 10  # Increased retry limit
    otp_verified = False
    otp_start_time = time.time()
    last_otp_code = None

    if AUTO_OTP:
        # Automatic OTP mode - fetch OTP from read-mail.me API
        print(f"\n{'='*60}")
        print("AUTO OTP MODE: ENABLED")
        print("Automatically fetching OTP codes from OTP API")
        print(f"{'='*60}")

        for otp_attempt in range(max_otp_retries):
            print(f"\n{'='*60}")
            print(f"OTP ATTEMPT {otp_attempt + 1}/{max_otp_retries}")
            print(f"{'='*60}")

            # Check if we need to click resend OTP (after 70 seconds)
            elapsed_time = time.time() - otp_start_time
            if elapsed_time > 70:
                print(f"\n⚠ More than 70 seconds elapsed ({elapsed_time:.1f}s), clicking resend OTP...")
                try:
                    resend_selectors = [
                        (By.XPATH, "//span[contains(text(), 'Resend')]"),
                        (By.XPATH, "//span[contains(text(), 'resend')]"),
                        (By.XPATH, "//a[contains(text(), 'Resend')]"),
                        (By.CSS_SELECTOR, "span.resend-link"),
                        (By.XPATH, "//div[contains(@class, 'resend')]")
                    ]

                    resend_clicked = False
                    for by, selector in resend_selectors:
                        try:
                            resend_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            resend_button.click()
                            print("✓ Clicked resend OTP button")
                            resend_clicked = True
                            otp_start_time = time.time()  # Reset timer
                            time.sleep(2)
                            break
                        except:
                            continue

                    if not resend_clicked:
                        print("⚠ Could not find resend OTP button")
                except Exception as e:
                    print(f"⚠ Error clicking resend OTP: {e}")

            # Fetch OTP code based on webmail type
            if WEBMAIL_TYPE == "pranakorn":
                # Use IMAP for pranakorn/coaco.space emails
                otp_code = get_otp_pranakorn(
                    current_email_data['email'],
                    current_email_data['password']
                )
            else:
                # Use read-mail.me API for hotmail
                otp_code = get_otp_code(
                    current_email_data['email'],
                    current_email_data['refresh_token'],
                    current_email_data['client_id']
            )

            if not otp_code:
                print("✗ Failed to get OTP code.")
                if otp_attempt < max_otp_retries - 1:
                    print("Waiting 5 seconds before retrying OTP fetch...")
                    time.sleep(5)
                    continue
                else:
                    print("✗ Failed to get OTP code after all attempts. Cannot proceed with verification.")
                    return False

            # Check if this is a new OTP code (different from last attempt)
            if last_otp_code and otp_code == last_otp_code:
                print(f"⚠ Got same OTP code as before ({otp_code}), waiting for new code...")
                time.sleep(5)
                continue

            last_otp_code = otp_code

            # Step 12: Enter OTP code
            try:
                print("\nStep 11: Entering OTP code...")
                otp_input = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[type='text'][maxlength='6'].passport-input__input")
                ))
                otp_input.clear()
                otp_input.send_keys(otp_code)
                print(f"✓ Entered OTP code: {otp_code}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error entering OTP code: {e}")
                if otp_attempt < max_otp_retries - 1:
                    continue

            # Step 13: Click Verify button
            try:
                print("\nStep 12: Clicking Verify button...")
                verify_button = None
                verify_selectors = [
                    (By.XPATH, "//div[contains(@class, 'passport-btn-primary') and contains(text(), 'Verify')]"),
                    (By.CSS_SELECTOR, "div.passport-btn.passport-btn-primary"),
                    (By.XPATH, "//div[contains(@class, 'passport-btn') and contains(text(), 'Verify')]")
                ]

                for by, selector in verify_selectors:
                    try:
                        verify_button = wait.until(EC.element_to_be_clickable((by, selector)))
                        if verify_button:
                            print(f"Found Verify button using: {selector}")
                            break
                    except:
                        continue

                if verify_button:
                    verify_button.click()
                    print("✓ Clicked Verify button successfully!")
                    time.sleep(2)

                    # Check for "Connection is not secure" error
                    try:
                        error_toast = driver.find_element(By.CSS_SELECTOR, "p.passport-toast-txt")
                        error_text = error_toast.text.strip()
                        if "Connection is not secure" in error_text or "not secure" in error_text.lower():
                            print(f"\n{'='*60}")
                            print("⚠ ERROR: Connection is not secure")
                            print(f"⚠ Message: {error_text}")
                            print("⚠ Will restart registration process for this account")
                            print(f"{'='*60}")
                            return 'retry'  # Signal to restart the entire registration process
                    except:
                        pass  # No error toast found, continue normally
                else:
                    print("✗ Could not find Verify button")

            except Exception as e:
                print(f"Error clicking Verify button: {e}")

            # Step 13.5: Check for "Invalid verification code" error
            try:
                print("\nChecking for verification errors...")
                error_element = driver.find_element(By.CSS_SELECTOR, "p.passport-input__error")
                error_text = error_element.text.strip()

                if "Invalid verification code" in error_text or "invalid" in error_text.lower():
                    print(f"\n{'='*60}")
                    print(f"✗ INVALID OTP CODE DETECTED")
                    print(f"✗ Error message: {error_text}")
                    print(f"✓ Will re-read OTP from {'IMAP server' if WEBMAIL_TYPE == 'pranakorn' else 'API'} and retry...")
                    print(f"✓ Attempt {otp_attempt + 1}/{max_otp_retries}")
                    print(f"{'='*60}")
                    time.sleep(3)
                    continue  # Loop back to fetch fresh OTP
                else:
                    print(f"⚠ Found error message but not about invalid code: {error_text}")
                    otp_verified = True
                    break

            except Exception as e:
                # No error found - verification successful
                print("✓ No error message found - OTP verification successful!")
                otp_verified = True
                break

        if not otp_verified:
            print("✗ OTP verification failed after all attempts")
            return False

        print("✓ Proceeding to next step...")
        time.sleep(3)

    else:
        # Manual OTP mode - user enters code themselves
        print(f"\n{'='*60}")
        print("AUTO OTP MODE: DISABLED")
        print("Please manually enter the OTP code in the browser")
        print("The script will wait for you to complete verification")
        print(f"{'='*60}")

        # Wait for OTP input field to appear
        try:
            print("\nStep 11: Waiting for OTP input field...")
            otp_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='text'][maxlength='6'].passport-input__input")
            ))
            print("✓ OTP input field is ready")
            print("\n" + "="*60)
            print("MANUAL OTP ENTRY REQUIRED")
            print("="*60)
            print(f"Email: {current_email_data['email']}")
            print("Please:")
            print("  1. Check your email for the OTP code")
            print("  2. Enter the code in the browser")
            print("  3. Click the Verify button")
            print("\nWaiting for verification to complete...")
            print("="*60)
        except Exception as e:
            print(f"Error finding OTP input field: {e}")
            return False

        # Wait for verification to complete (check if we move past OTP page)
        # Monitor for successful navigation or error messages
        verification_timeout = 300  # 5 minutes for manual entry
        start_time = time.time()

        while time.time() - start_time < verification_timeout:
            try:
                # Check if verification error appears
                try:
                    error_element = driver.find_element(By.CSS_SELECTOR, "p.passport-input__error")
                    error_text = error_element.text.strip()
                    if error_text and "invalid" in error_text.lower():
                        print(f"\n⚠ Verification error detected: {error_text}")
                        print("Please try entering the OTP code again...")
                        time.sleep(2)
                        continue
                except:
                    pass

                # Check if we've moved past the OTP page (successful verification)
                # Try to find the next step elements
                try:
                    # If we can't find the OTP input anymore, verification likely succeeded
                    driver.find_element(By.CSS_SELECTOR, "input[type='text'][maxlength='6'].passport-input__input")
                    # Still on OTP page, keep waiting
                    time.sleep(2)
                except:
                    # OTP input not found - likely moved to next page
                    print("\n✓ OTP verification appears to be complete!")
                    otp_verified = True
                    break

            except Exception as e:
                # If we get any unexpected state, assume verification completed
                print(f"\n✓ OTP page state changed - verification likely complete")
                otp_verified = True
                break

        if not otp_verified:
            print(f"\n⚠ Manual OTP verification timeout after {verification_timeout}s")
            print("Please ensure OTP was entered correctly")
            return False

        print("✓ Proceeding to next step...")
        time.sleep(3)

    print("\n✓ Registration completed successfully!")

    # Step 14: Click VIP button
    try:
        print("\nStep 13: Clicking VIP button...")
        time.sleep(3)  # Wait for page to settle after verification

        vip_button = None
        vip_selectors = [
            (By.CSS_SELECTOR, "a.user-level-tag[alt='joinVIP']"),
            (By.XPATH, "//a[@class='user-level-tag' and @alt='joinVIP']"),
            (By.XPATH, "//a[@alt='joinVIP']"),
            (By.CSS_SELECTOR, "a[alt='joinVIP']")
        ]

        print("Searching for VIP button...")
        for by, selector in vip_selectors:
            try:
                print(f"  Trying selector: {selector}")
                vip_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if vip_button:
                    print(f"✓ Found VIP button using: {selector}")
                    break
            except Exception as e:
                print(f"  ✗ Not found with this selector: {str(e)[:50]}")
                continue

        if vip_button:
            vip_button.click()
            print("✓ Clicked VIP button successfully!")
            time.sleep(1)
        else:
            print("✗ Could not find VIP button with any selector")
            print(f"Current URL: {driver.current_url}")

    except Exception as e:
        print(f"Error clicking VIP button: {e}")

    # Step 15: Close popup if present
    try:
        print("\nStep 14: Closing popup...")
        close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "p.pop-close[rseat='close']")))
        close_button.click()
        print("✓ Closed popup successfully!")
        time.sleep(0.5)
    except Exception as e:
        print(f"Note: No popup to close or error: {e}")

    # Step 16: Select Subscription package based on configuration
    try:
        # Determine package details based on SUBSCRIPTION_MONTHS
        package_config = {
            1: {
                'rseat': '0:0',
                'name': 'Monthly Subscription',
                'price': '฿49',
                'description': '1 Month'
            },
            3: {
                'rseat': '0:1',
                'name': 'Quarterly Subscription',
                'price': '฿339',
                'description': '3 Months'
            },
            12: {
                'rseat': '0:2',
                'name': 'Annual Subscription',
                'price': '฿1200',
                'description': '12 Months'
            }
        }

        if SUBSCRIPTION_MONTHS not in package_config:
            print(f"⚠ Invalid SUBSCRIPTION_MONTHS: {SUBSCRIPTION_MONTHS}, defaulting to 1 month")
            SUBSCRIPTION_MONTHS = 1

        package = package_config[SUBSCRIPTION_MONTHS]

        print(f"\nStep 15: Selecting {package['description']} Subscription ({package['price']})...")
        print(f"Target rseat: {package['rseat']}")
        print(f"Package name: {package['name']}")

        subscription_plan = None
        plan_selectors = [
            (By.XPATH, f"//div[contains(@class, 'goods-item-wrapper')]//p[contains(text(), '{package['name']}')]"),
            (By.CSS_SELECTOR, "div.goods-item-wrapper"),
            (By.XPATH, f"//div[contains(@class, 'goods-item-wrapper') and contains(@rseat, '{package['rseat']}')]")
        ]

        for by, selector in plan_selectors:
            try:
                subscription_plan = wait.until(EC.element_to_be_clickable((by, selector)))
                if subscription_plan:
                    break
            except:
                continue

        if subscription_plan:
            subscription_plan.click()
            print(f"✓ Selected {package['description']} Subscription ({package['price']}) successfully!")
            time.sleep(0.5)
        else:
            print(f"✗ Could not find {package['description']} Subscription plan")

    except Exception as e:
        print(f"Error selecting subscription plan: {e}")

    # Step 17: Select Credit Card Payment
    try:
        print("\nStep 16: Selecting Credit Card payment...")
        payment_method = None
        payment_selectors = [
            (By.XPATH, "//li[contains(@class, 'pay-list-item')]//p[contains(text(), 'บัตรเครดิต')]"),
            (By.CSS_SELECTOR, "li.pay-list-item[rseat='2:2']"),
            (By.XPATH, "//li[@rseat='2:2']")
        ]

        for by, selector in payment_selectors:
            try:
                payment_method = wait.until(EC.element_to_be_clickable((by, selector)))
                if payment_method:
                    print(f"Found Credit Card payment using: {selector}")
                    break
            except:
                continue

        if payment_method:
            payment_method.click()
            print("✓ Selected Credit Card payment successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find Credit Card payment")

    except Exception as e:
        print(f"Error selecting payment method: {e}")

    # Step 17.5: Fill in card details
    try:
        print("\nStep 16.5: Filling in card details...")

        # Split card number into 4 groups of 4 digits
        card_groups = [CARD_NUMBER[i:i+4] for i in range(0, 16, 4)]

        # Find all card number input fields
        card_inputs = driver.find_elements(By.CSS_SELECTOR, "input.banknumber-input-input[type='type']")

        if len(card_inputs) >= 6:
            # Fill card number (4 inputs)
            print(f"  Filling card number...")
            for i in range(4):
                card_inputs[i].clear()
                card_inputs[i].send_keys(card_groups[i])
                time.sleep(0.1)
            print(f"  ✓ Card number entered: {CARD_NUMBER}")

            # Fill expiry date (month and year in one input, usually MM/YY format)
            print(f"  Filling expiry date...")
            card_inputs[4].clear()
            card_inputs[4].send_keys(CARD_EXPIRY_MONTH)
            time.sleep(0.1)
            card_inputs[4].send_keys(CARD_EXPIRY_YEAR[-2:])  # Last 2 digits of year
            print(f"  ✓ Expiry date entered: {CARD_EXPIRY_MONTH}/{CARD_EXPIRY_YEAR[-2:]}")

            # Fill CVV
            print(f"  Filling CVV...")
            card_inputs[5].clear()
            card_inputs[5].send_keys(CARD_CVV)
            print(f"  ✓ CVV entered")

            print("✓ Card details filled successfully!")
            time.sleep(0.5)
        else:
            print(f"⚠ Found {len(card_inputs)} input fields, expected at least 6")

    except Exception as e:
        print(f"Error filling card details: {e}")

    # Step 18: Click Join VIP button
    try:
        print("\nStep 17: Clicking Join VIP button...")

        # Store original window handle
        original_window = driver.current_window_handle
        print(f"✓ Original window handle stored: {original_window}")

        join_vip_button = None
        join_vip_selectors = [
            (By.XPATH, "//div[@class='buy-btn']//p[contains(text(), 'Join VIP')]"),
            (By.CSS_SELECTOR, "div.buy-btn"),
            (By.XPATH, "//div[contains(@class, 'buy-btn')]")
        ]

        for by, selector in join_vip_selectors:
            try:
                join_vip_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if join_vip_button:
                    print(f"Found Join VIP button using: {selector}")
                    break
            except:
                continue

        if join_vip_button:
            join_vip_button.click()
            print("✓ Clicked Join VIP button successfully!")
            time.sleep(3)
        else:
            print("✗ Could not find Join VIP button")

    except Exception as e:
        print(f"Error clicking Join VIP button: {e}")

    # Step 19: Wait for payment tab and monitor for redirect
    print("\n" + "="*60)
    print("✓ Payment tab should open now!")
    print("Please complete the payment in the new tab...")
    print("Waiting for redirect to payResult page...")
    print("="*60)

    # Monitor for new window/tab and wait for redirect
    start_time = time.time()
    max_wait = 600  # 10 minutes max wait
    payment_tab = None
    payment_completed = False

    while True:
        try:
            # Get all window handles
            all_windows = driver.window_handles

            # Check if there's a new window/tab
            if len(all_windows) > 1:
                # Find the new tab (not the original)
                for window in all_windows:
                    if window != original_window:
                        payment_tab = window
                        break

                if payment_tab:
                    # Switch to payment tab to check URL
                    driver.switch_to.window(payment_tab)
                    current_url = driver.current_url

                    # Check if redirected to payResult page
                    if 'iq.com/vip/payResult' in current_url:
                        print(f"\n✓ Payment completed! Detected redirect to: {current_url}")
                        print("✓ Staying in payment result tab to continue cancellation...")
                        payment_completed = True
                        break

                    # Show current payment URL
                    if 'payment-service-th.line-apps.com' in current_url or 'line-apps.com' in current_url:
                        elapsed = time.time() - start_time
                        if int(elapsed) % 10 == 0:  # Print every 10 seconds
                            print(f"⏳ Payment in progress... ({int(elapsed)}s elapsed)")
            else:
                # No second tab yet, check main window
                current_url = driver.current_url
                if 'iq.com/vip/payResult' in current_url:
                    print(f"\n✓ Payment completed in main tab! Redirected to: {current_url}")
                    payment_completed = True
                    break

            # Check elapsed time
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                print(f"\n⚠ Maximum wait time ({max_wait}s) reached")
                break

            time.sleep(2)

        except Exception as e:
            print(f"⚠ Error monitoring payment: {e}")
            time.sleep(2)

    if not payment_completed:
        print("\n⚠ Payment monitoring timed out or failed")
        return False

    # Step 20: Navigate to autorenew page and cancel subscription
    try:
        print("\nStep 18: Navigating to autorenew management page...")
        driver.get("https://www.iq.com/vip/autorenew")
        wait_for_page_load(driver)
        print("✓ Loaded autorenew page")
        time.sleep(0.3)

    except Exception as e:
        print(f"Error navigating to autorenew page: {e}")

    # Step 21: Click Cancel Subscription button
    try:
        print("\nStep 19: Clicking Cancel Subscription button...")
        cancel_button = None
        cancel_selectors = [
            (By.XPATH, "//button[@type='button' and @rseat='cancel']//p[contains(text(), 'Cancel Subscription')]"),
            (By.CSS_SELECTOR, "button.item-button[rseat='cancel']"),
            (By.XPATH, "//button[@rseat='cancel']")
        ]

        for by, selector in cancel_selectors:
            try:
                cancel_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if cancel_button:
                    print(f"Found Cancel Subscription button using: {selector}")
                    break
            except:
                continue

        if cancel_button:
            cancel_button.click()
            print("✓ Clicked Cancel Subscription button successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find Cancel Subscription button")

    except Exception as e:
        print(f"Error clicking Cancel Subscription button: {e}")

    # Step 22: Click "Cancel, I don't want the benefits"
    try:
        print("\nStep 20: Clicking 'Cancel, I don't want the benefits'...")
        confirm_cancel = None
        confirm_selectors = [
            (By.XPATH, "//a[@rseat='1' and contains(text(), 'Cancel, I don\\'t want the benefits')]"),
            (By.CSS_SELECTOR, "a.btn-text[rseat='1']"),
            (By.XPATH, "//a[@rseat='1']")
        ]

        for by, selector in confirm_selectors:
            try:
                confirm_cancel = wait.until(EC.element_to_be_clickable((by, selector)))
                if confirm_cancel:
                    print(f"Found confirm cancel link using: {selector}")
                    break
            except:
                continue

        if confirm_cancel:
            confirm_cancel.click()
            print("✓ Confirmed cancellation successfully!")
            time.sleep(1)
        else:
            print("✗ Could not find confirm cancel link")

    except Exception as e:
        print(f"Error confirming cancellation: {e}")

    print("\n✓ Subscription cancelled successfully!")
    return True


def worker_thread(thread_id, email_queue, results_queue, url):
    """Worker thread that processes emails from the queue"""
    window_width = 780
    window_height = 600
    x_position = thread_id * window_width
    y_position = 0

    # Process emails from the queue
    while True:
        driver = None
        current_proxy = None
        try:
            # Get next email from queue (non-blocking with timeout)
            try:
                current_email_data = email_queue.get(timeout=1)
            except:
                continue

            if current_email_data is None:  # Sentinel value to stop thread
                email_queue.task_done()
                break

            print(f"\n[Thread {thread_id}] {'='*60}")
            print(f"[Thread {thread_id}] Opening new browser for: {current_email_data['email']}")
            print(f"[Thread {thread_id}] {'='*60}\n")

            # Create Chrome options for this browser instance
            chrome_options = Options()

            # Add proxy if enabled
            if USE_PROXY:
                try:
                    with proxy_lock:
                        if not proxy_queue.empty():
                            current_proxy = proxy_queue.get()
                            proxy_queue.put(current_proxy)  # Put it back for rotation

                    if current_proxy:
                        print(f"[Thread {thread_id}] Using proxy: {current_proxy}")

                        # Parse proxy format: ip:port or user:pass@ip:port
                        if '@' in current_proxy:
                            # Authenticated proxy
                            auth_part, server_part = current_proxy.split('@')
                            proxy_user, proxy_pass = auth_part.split(':')
                            proxy_host, proxy_port = server_part.split(':')

                            # Create proxy extension
                            proxy_extension = create_proxy_extension(
                                proxy_host, proxy_port, proxy_user, proxy_pass
                            )
                            chrome_options.add_extension(proxy_extension)
                        else:
                            # Simple proxy without auth
                            chrome_options.add_argument(f'--proxy-server={PROXY_TYPE}://{current_proxy}')
                    else:
                        print(f"[Thread {thread_id}] ⚠ No proxy available, running without proxy")
                except Exception as e:
                    print(f"[Thread {thread_id}] ⚠ Error setting up proxy: {e}")

            # Initialize a fresh Chrome driver for this email
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 20)

            # Position the browser window
            driver.set_window_size(window_width, window_height)
            driver.set_window_position(x_position, y_position)
            print(f"[Thread {thread_id}] Browser window set to {window_width}x{window_height} at position ({x_position}, {y_position})")

            # Process the email with retry logic for "Connection not secure" errors
            max_retries = 5
            success = False

            for retry_attempt in range(max_retries):
                if retry_attempt > 0:
                    print(f"\n[Thread {thread_id}] {'='*60}")
                    print(f"[Thread {thread_id}] RETRY ATTEMPT {retry_attempt}/{max_retries - 1}")
                    print(f"[Thread {thread_id}] Restarting registration process...")
                    print(f"[Thread {thread_id}] {'='*60}\n")
                    # Navigate back to start fresh
                    driver.get(url)
                    wait_for_page_load(driver)
                    time.sleep(2)

                result = process_single_email(driver, wait, current_email_data, url)

                if result == 'retry':
                    # Connection not secure - retry the entire process
                    if retry_attempt < max_retries - 1:
                        print(f"[Thread {thread_id}] Waiting 5 seconds before retry...")
                        time.sleep(5)
                        continue
                    else:
                        print(f"[Thread {thread_id}] ✗ Max retries reached, giving up on this account")
                        success = False
                        break
                elif result == True:
                    # Success!
                    success = True

                    # Immediately save to success.txt
                    print(f"\n[Thread {thread_id}] ✓ Account completed successfully!")
                    save_success(current_email_data)
                    remove_from_emails_file(current_email_data['email'], EMAILS_FILE)
                    break
                else:
                    # Permanent failure
                    success = False
                    break

            if success:
                results_queue.put({
                    'success': True,
                    'email_data': current_email_data,
                    'thread_id': thread_id
                })
            else:
                results_queue.put({
                    'success': False,
                    'email_data': current_email_data,
                    'thread_id': thread_id
                })

            email_queue.task_done()

            # Wait for user input before closing browser
            print(f"\n[Thread {thread_id}] " + "="*60)
            print(f"[Thread {thread_id}] Processing complete for {current_email_data['email']}")
            print(f"[Thread {thread_id}] Browser will remain open for inspection")
            print(f"[Thread {thread_id}] Press 'd' and Enter to close browser and continue...")
            print(f"[Thread {thread_id}] " + "="*60)

            while True:
                user_input = input(f"[Thread {thread_id}] ").strip().lower()
                if user_input == 'd':
                    print(f"[Thread {thread_id}] ✓ Closing browser...")
                    break
                else:
                    print(f"[Thread {thread_id}] Invalid input. Press 'd' and Enter to continue...")

            # Close browser after processing this email
            if driver:
                try:
                    print(f"\n[Thread {thread_id}] Closing browser for {current_email_data['email']}...")
                    driver.quit()
                    print(f"[Thread {thread_id}] Browser closed. Ready for next email.\n")
                    driver = None
                except Exception as close_error:
                    print(f"[Thread {thread_id}] Error closing browser: {close_error}")

            # Small delay before opening next browser
            time.sleep(2)

        except Exception as e:
            print(f"[Thread {thread_id}] Error: {str(e)}")
            if driver:
                try:
                    # Wait for user input before closing browser (even on error)
                    print(f"\n[Thread {thread_id}] " + "="*60)
                    print(f"[Thread {thread_id}] Error occurred - Browser will remain open for inspection")
                    print(f"[Thread {thread_id}] Press 'd' and Enter to close browser and continue...")
                    print(f"[Thread {thread_id}] " + "="*60)

                    while True:
                        user_input = input(f"[Thread {thread_id}] ").strip().lower()
                        if user_input == 'd':
                            print(f"[Thread {thread_id}] ✓ Closing browser...")
                            break
                        else:
                            print(f"[Thread {thread_id}] Invalid input. Press 'd' and Enter to continue...")

                    driver.quit()
                except:
                    pass
            continue

    print(f"[Thread {thread_id}] Worker thread finished.")


def main():
    """Main function to process all emails in parallel"""
    url = "https://iq.com"

    # Read emails from file
    email_data_list = read_emails(EMAILS_FILE)
    if not email_data_list:
        print("No emails found. Please create emails.txt with one email per line.")
        return

    print(f"\n{'='*60}")
    print(f"STARTING PARALLEL BATCH PROCESSING")
    print(f"{'='*60}")
    print(f"Total emails to process: {len(email_data_list)}")
    print(f"Number of parallel browsers: {NUM_PARALLEL_BROWSERS}")
    print(f"Using password: {PASSWORD}")
    print(f"Webmail type: {WEBMAIL_TYPE}")
    print(f"Proxy enabled: {USE_PROXY}")
    print(f"{'='*60}\n")

    # Load proxies if enabled
    if USE_PROXY:
        proxies = load_proxies(PROXY_FILE)
        if proxies:
            for proxy in proxies:
                proxy_queue.put(proxy)
            print(f"✓ Proxy rotation enabled with {len(proxies)} proxy/proxies\n")
        else:
            print("⚠ USE_PROXY is True but no proxies loaded. Running without proxy.\n")

    # Create queues for coordinating work
    email_queue = Queue()
    results_queue = Queue()

    # Add all emails to the queue
    for email_data in email_data_list:
        email_queue.put(email_data)

    # Add sentinel values to stop threads
    for _ in range(NUM_PARALLEL_BROWSERS):
        email_queue.put(None)

    # Start worker threads
    threads = []
    for i in range(NUM_PARALLEL_BROWSERS):
        thread = threading.Thread(
            target=worker_thread,
            args=(i, email_queue, results_queue, url)
        )
        thread.start()
        threads.append(thread)
        time.sleep(2)  # Small delay to stagger browser startups

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Process results
    processed_count = 0
    failed_count = 0

    while not results_queue.empty():
        result = results_queue.get()
        if result['success']:
            # Save to success.txt
            save_success(result['email_data'])
            # Remove from emails.txt
            remove_from_emails_file(result['email_data']['email'], EMAILS_FILE)
            processed_count += 1
            print(f"\n✓ COMPLETED: {result['email_data']['email']} (Thread {result['thread_id']})")
        else:
            failed_count += 1
            print(f"\n✗ FAILED: {result['email_data']['email']} (Thread {result['thread_id']})")

    # Final summary
    print(f"\n{'='*60}")
    print(f"PARALLEL BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total processed: {processed_count}")
    print(f"Total failed: {failed_count}")
    print(f"Total emails: {len(email_data_list)}")
    print(f"{'='*60}\n")

    print("\n✓ All done! Press Enter to exit...")
    input()


if __name__ == "__main__":
    main()
