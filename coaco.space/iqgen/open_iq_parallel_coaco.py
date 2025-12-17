#!/usr/bin/env python3
"""
Selenium macro to open iq.com with Chromium browser - COACO.SPACE VERSION
Uses coaco.space email accounts with integrated OTP reading via IMAP
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import random
import os
import sys
import threading
from queue import Queue

# Add parent directory to path for otpread import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import OTP reading functionality
import imaplib
import email as email_module
import socket
import re

# Configuration
PASSWORD = "status93"  # Set your password here
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EMAILS_FILE = os.path.join(SCRIPT_DIR, "emails.txt")  # File containing emails (one per line)
SUCCESS_FILE = os.path.join(SCRIPT_DIR, "success.txt")  # File for successful accounts
NUM_PARALLEL_BROWSERS = 3  # Number of browsers to run in parallel
IMAP_SERVER = "mail.coaco.space"
OTP_POLL_INTERVAL = 0.5  # Poll every 500ms (reduced from 6 seconds)

# ============================================================================
# SUBSCRIPTION PACKAGE CONFIGURATION
# ============================================================================
SUBSCRIPTION_MONTHS = 1  # Options: 1, 3, or 12
# - 1 month:  ฿119 (Monthly Subscription) - rseat='0:0'
# - 3 months: ฿339 (Quarterly Subscription) - rseat='0:1'
# - 12 months: ฿1200 (Annual Subscription) - rseat='0:2'

# Month names
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

def wait_for_page_load(driver, timeout=10):
    """Wait for page to complete loading"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

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


def get_otp_from_email(email_address, email_password, max_retries=40):
    """
    Fetch OTP code from coaco.space email via IMAP
    Polls every 500ms for up to 40 attempts (20 seconds total)
    """
    print(f"\n{'='*60}")
    print(f"Fetching OTP code for {email_address}")
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
            mail.login(email_address, email_password)
            mail.select("INBOX")

            # Read latest email
            status, messages = mail.search(None, "ALL")
            mail_ids = messages[0].split()

            if not mail_ids:
                print(f"✗ No emails found in mailbox yet")
                mail.close()
                mail.logout()
                if attempt < max_retries - 1:
                    time.sleep(OTP_POLL_INTERVAL)
                continue

            last_email = mail_ids[-1]
            status, msg_data = mail.fetch(last_email, "(RFC822)")
            msg = email_module.message_from_bytes(msg_data[0][1])

            # Extract OTP from subject first
            subject = msg["Subject"] or ""
            from_addr = msg["From"] or ""
            otp_code = extract_otp(subject)

            # If not found in subject, try body
            if not otp_code:
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        otp_code = extract_otp(body)
                        if otp_code:
                            break

            mail.close()
            mail.logout()

            if otp_code:
                # Verify it's from iQIYI
                if 'iq.com' in from_addr.lower() or 'iqiyi' in from_addr.lower():
                    print(f"✓ Found OTP code: {otp_code}")
                    print(f"✓ From: {from_addr}")
                    print(f"✓ Subject: {subject}")
                    print(f"{'='*60}")
                    return otp_code
                else:
                    print(f"⚠ Found OTP but not from iQIYI (from: {from_addr})")
            else:
                print(f"✗ No OTP code found in email")

            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(OTP_POLL_INTERVAL)

        except Exception as e:
            print(f"✗ Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(OTP_POLL_INTERVAL)

    print(f"\n{'='*60}")
    print(f"✗ Failed to retrieve OTP code after {max_retries} attempts")
    print(f"{'='*60}")
    return None


def read_emails(filename):
    """Read emails from text file (format: email|password)"""
    try:
        with open(filename, 'r') as f:
            email_data = []
            for line in f:
                line = line.strip()
                if line:
                    # Split by | and extract email and password
                    parts = line.split('|')
                    if len(parts) >= 2:
                        email_info = {
                            'email': parts[0].strip(),
                            'password': parts[1].strip()
                        }
                        email_data.append(email_info)
        return email_data
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []

def save_success(email_data):
    """Save successful email to success.txt"""
    try:
        with open(SUCCESS_FILE, 'a') as f:
            line = f"{email_data['email']}|{email_data['password']}\n"
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

    # Navigate to iq.com/login
    driver.get("https://www.iq.com/login")
    wait_for_page_load(driver)
    print(f"Successfully opened iq.com/login")
    time.sleep(0.5)

    # Step 1: Click the Register link
    try:
        print("\nStep 1: Looking for Register link...")
        register_link = None
        register_selectors = [
            (By.XPATH, "//span[contains(@class, 'passport-login-tip__link') and contains(text(), 'Sign Up')]"),
            (By.CSS_SELECTOR, "span.passport-login-tip__link"),
            (By.XPATH, "//span[contains(text(), 'Sign Up')]"),
            (By.XPATH, "//a[contains(text(), 'Register')]")
        ]

        for by, selector in register_selectors:
            try:
                register_link = wait.until(EC.element_to_be_clickable((by, selector)))
                if register_link:
                    print(f"Found Register link using: {selector}")
                    break
            except:
                continue

        if register_link:
            register_link.click()
            print("✓ Clicked Register link successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find Register link")
            raise Exception("Register link not found")

    except Exception as e:
        print(f"Error clicking Register link: {e}")
        raise

    # Step 2: Click the "Sign up with Email" button
    try:
        print("\nStep 2: Looking for 'Sign up with Email' button...")
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

    # Step 3: Fill in the email field
    try:
        print("\nStep 3: Filling in email...")
        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='text'].passport-input__input")
        ))
        email_input.clear()
        email_input.send_keys(current_email_data['email'])
        print(f"✓ Entered email: {current_email_data['email']}")
        time.sleep(0.3)
    except Exception as e:
        print(f"Error entering email: {e}")

    # Step 4: Fill in the password field
    try:
        print("\nStep 4: Filling in password...")
        password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password'].passport-input__input")
        if len(password_inputs) >= 1:
            password_inputs[0].clear()
            password_inputs[0].send_keys(PASSWORD)
            print(f"✓ Entered password")
            time.sleep(0.3)
    except Exception as e:
        print(f"Error entering password: {e}")

    # Step 5: Fill in the re-password field
    try:
        print("\nStep 5: Filling in re-password...")
        password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password'].passport-input__input")
        if len(password_inputs) >= 2:
            password_inputs[1].clear()
            password_inputs[1].send_keys(PASSWORD)
            print(f"✓ Re-entered password")
            time.sleep(0.3)
    except Exception as e:
        print(f"Error entering re-password: {e}")

    # Step 6: Select the year (2000)
    try:
        print("\nStep 6: Selecting birth year (2000)...")
        year_wrapper = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.pikcer-wrapper.year-pikcer-wrapper")
        ))
        year_wrapper.click()
        print("✓ Opened year dropdown")
        time.sleep(0.5)

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

    # Step 7: Select random month
    try:
        print("\nStep 7: Selecting random month...")
        month_wrapper = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.pikcer-wrapper.month-pikcer-wrapper")
        ))
        month_wrapper.click()
        print("✓ Opened month dropdown")
        time.sleep(0.5)

        random_month_index = random.randint(0, 11)
        month_name = MONTHS[random_month_index]

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

    # Step 8: Select random day (1-9)
    try:
        print("\nStep 8: Selecting random day (1-9)...")
        day_wrapper = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.pikcer-wrapper.day-pikcer-wrapper")
        ))
        day_wrapper.click()
        print("✓ Opened day dropdown")
        time.sleep(0.5)

        random_day = random.randint(1, 9)
        day_str = str(random_day)

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

    # Step 9: Click the Sign Up submit button
    try:
        print("\nStep 9: Clicking Sign Up button...")
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

    # Step 10: OTP verification with retry logic
    max_otp_retries = 10
    otp_verified = False
    otp_start_time = time.time()
    last_otp_code = None

    print(f"\n{'='*60}")
    print("AUTO OTP MODE: ENABLED (COACO.SPACE EMAIL)")
    print("Automatically fetching OTP codes via IMAP")
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
                        otp_start_time = time.time()
                        time.sleep(2)
                        break
                    except:
                        continue

                if not resend_clicked:
                    print("⚠ Could not find resend OTP button")
            except Exception as e:
                print(f"⚠ Error clicking resend OTP: {e}")

        # Fetch OTP code from email via IMAP
        otp_code = get_otp_from_email(
            current_email_data['email'],
            current_email_data['password']
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

        # Step 11: Enter OTP code
        try:
            print("\nStep 10: Entering OTP code...")
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

        # Step 12: Click Verify button
        try:
            print("\nStep 11: Clicking Verify button...")
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

        # Step 12.5: Check for "Invalid verification code" error
        try:
            print("\nChecking for verification errors...")
            error_element = driver.find_element(By.CSS_SELECTOR, "p.passport-input__error")
            error_text = error_element.text.strip()

            if "Invalid verification code" in error_text or "invalid" in error_text.lower():
                print(f"\n{'='*60}")
                print(f"✗ INVALID OTP CODE DETECTED")
                print(f"✗ Error message: {error_text}")
                print(f"✓ Will re-read OTP from IMAP server and retry...")
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

    print("\n✓ Registration completed successfully!")

    # Step 13: Click VIP button
    try:
        print("\nStep 12: Clicking VIP button...")
        time.sleep(3)

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

    # Step 14: Close popup if present
    try:
        print("\nStep 13: Closing popup...")
        close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "p.pop-close[rseat='close']")))
        close_button.click()
        print("✓ Closed popup successfully!")
        time.sleep(0.5)
    except Exception as e:
        print(f"Note: No popup to close or error: {e}")

    # Step 15: Select Subscription package based on configuration
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

        print(f"\nStep 14: Selecting {package['description']} Subscription ({package['price']})...")
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

    # Step 16: Select Rabbit Line Pay
    try:
        print("\nStep 15: Selecting Rabbit Line Pay...")
        payment_method = None
        payment_selectors = [
            (By.XPATH, "//li[contains(@class, 'pay-list-item')]//p[contains(text(), 'Rabbit Line Pay')]"),
            (By.CSS_SELECTOR, "li.pay-list-item[rseat='2:1']"),
            (By.XPATH, "//li[@rseat='2:1']")
        ]

        for by, selector in payment_selectors:
            try:
                payment_method = wait.until(EC.element_to_be_clickable((by, selector)))
                if payment_method:
                    print(f"Found Rabbit Line Pay using: {selector}")
                    break
            except:
                continue

        if payment_method:
            payment_method.click()
            print("✓ Selected Rabbit Line Pay successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find Rabbit Line Pay")

    except Exception as e:
        print(f"Error selecting payment method: {e}")

    # Step 17: Click Join VIP button
    try:
        print("\nStep 16: Clicking Join VIP button...")

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

    # Step 18: Wait for payment tab and monitor for redirect
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

    # Step 19: Navigate to autorenew page and cancel subscription (QUICK)
    try:
        print("\nStep 17: Navigating to autorenew management page...")
        driver.get("https://www.iq.com/vip/autorenew")
        wait_for_page_load(driver)
        print("✓ Loaded autorenew page")
        time.sleep(0.1)  # Reduced from 0.3 to 0.1 for quicker action

    except Exception as e:
        print(f"Error navigating to autorenew page: {e}")

    # Step 20: Click Cancel Subscription button (QUICK)
    try:
        print("\nStep 18: Clicking Cancel Subscription button...")
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
            time.sleep(0.3)  # Reduced from 0.5
        else:
            print("✗ Could not find Cancel Subscription button")

    except Exception as e:
        print(f"Error clicking Cancel Subscription button: {e}")

    # Step 21: Click "Cancel, I don't want the benefits" (QUICK)
    try:
        print("\nStep 19: Clicking 'Cancel, I don't want the benefits'...")
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
            time.sleep(0.5)  # Reduced from 1
        else:
            print("✗ Could not find confirm cancel link")

    except Exception as e:
        print(f"Error confirming cancellation: {e}")

    print("\n✓ Subscription cancelled successfully!")
    return True


def worker_thread(thread_id, email_queue, results_queue, chrome_options, url):
    """Worker thread that processes emails from the queue"""
    window_width = 780
    window_height = 600
    x_position = thread_id * window_width
    y_position = 0

    # Process emails from the queue
    while True:
        driver = None
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

                    # Immediately save to success.txt and remove from emails.txt
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
                print(f"\n[Thread {thread_id}] ✗ Account processing failed")
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
        print(f"No emails found. Please create {EMAILS_FILE} with email|password format (one per line).")
        return

    print(f"\n{'='*60}")
    print(f"STARTING PARALLEL BATCH PROCESSING")
    print(f"COACO.SPACE VERSION - Using IMAP for OTP")
    print(f"{'='*60}")
    print(f"Total emails to process: {len(email_data_list)}")
    print(f"Number of parallel browsers: {NUM_PARALLEL_BROWSERS}")
    print(f"Using password: {PASSWORD}")
    print(f"OTP Poll interval: {OTP_POLL_INTERVAL}s")
    print(f"{'='*60}\n")

    # Set up Chrome/Chromium options
    chrome_options = Options()

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
            args=(i, email_queue, results_queue, chrome_options, url)
        )
        thread.start()
        threads.append(thread)
        time.sleep(2)  # Small delay to stagger browser startups

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Process results (already saved/removed in worker threads)
    processed_count = 0
    failed_count = 0

    while not results_queue.empty():
        result = results_queue.get()
        if result['success']:
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
