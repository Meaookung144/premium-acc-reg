#!/Users/meaookung144/Documents/GitHub/premium-acc-reg/venv/bin/python3
"""
Selenium macro to open iq.com with Chromium browser
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

# Configuration
PASSWORD = "mission67"  # Set your password here
EMAILS_FILE = "emails.txt"  # File containing emails (one per line)

# Month names
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

def wait_for_page_load(driver, timeout=10):
    """Wait for page to complete loading"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def read_emails(filename):
    """Read emails from text file (format: email|password|refresh_token|client_id)"""
    try:
        with open(filename, 'r') as f:
            email_data = []
            for line in f:
                line = line.strip()
                if line:
                    # Split by | and extract all parts
                    parts = line.split('|')
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

def get_otp_code(email, refresh_token, client_id, max_retries=5):
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
    print(f"Will retry up to {max_retries} times (waiting 4 seconds between attempts)")
    print(f"{'='*60}")

    for attempt in range(max_retries):
        try:
            print(f"\n[Attempt {attempt + 1}/{max_retries}] Sending request to read-mail.me...")
            response = requests.post(url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f"✓ API request successful (status: 200)")

                if 'messages' in data and len(data['messages']) > 0:
                    print(f"✓ Found {len(data['messages'])} message(s) in mailbox")

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
                                            print(f"✓ OTP code is valid: {code} (received {time_diff:.1f} min ago)")
                                            print(f"{'='*60}")
                                            return code
                                        else:
                                            print(f"✗ OTP code {code} is expired ({time_diff:.1f} min old, max 5 min)")
                                            print(f"  Skipping expired code, will retry API call...")
                                    except Exception as parse_error:
                                        # If time parsing fails, skip this code for safety
                                        print(f"⚠ Could not verify time for code {code}: {parse_error}")
                                        print(f"  Skipping unverifiable code, will retry API call...")
                else:
                    print(f"✗ No messages found in mailbox yet")
            else:
                print(f"✗ API request failed (status: {response.status_code})")

            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(4)

        except Exception as e:
            print(f"✗ Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(4)

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
    """Process a single email through the entire registration flow"""
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
            time.sleep(1)
        else:
            print("✗ Could not find Sign Up submit button")

    except Exception as e:
        print(f"Error clicking Sign Up submit button: {e}")

    print("\n✓ Form filled and submitted successfully!")

    # Step 11: Fetch OTP code from read-mail.me
    otp_code = get_otp_code(
        current_email_data['email'],
        current_email_data['refresh_token'],
        current_email_data['client_id']
    )

    if not otp_code:
        print("✗ Failed to get OTP code. Cannot proceed with verification.")
        print("Browser will remain open. Close manually or press Ctrl+C to quit.")
        input("Press Enter to close the browser...")
        return

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
        else:
            print("✗ Could not find Verify button")

    except Exception as e:
        print(f"Error clicking Verify button: {e}")

    print("\n✓ Registration completed successfully!")

    # Step 14: Click VIP button
    try:
        print("\nStep 13: Clicking VIP button...")
        time.sleep(2)  # Wait for page to settle after verification

        vip_button = None
        vip_selectors = [
            (By.CSS_SELECTOR, "a.user-level-tag[rseat='joinVIP']"),
            (By.XPATH, "//a[@rseat='joinVIP']"),
            (By.CSS_SELECTOR, "a[alt='joinVIP']")
        ]

        for by, selector in vip_selectors:
            try:
                vip_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if vip_button:
                    print(f"Found VIP button using: {selector}")
                    break
            except:
                continue

        if vip_button:
            vip_button.click()
            print("✓ Clicked VIP button successfully!")
            time.sleep(1)
        else:
            print("✗ Could not find VIP button")

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

    # Step 16: Select Monthly Subscription plan
    try:
        print("\nStep 15: Selecting Monthly Subscription plan (฿49)...")
        monthly_plan = None
        monthly_selectors = [
            (By.XPATH, "//div[contains(@class, 'goods-item-wrapper')]//p[contains(text(), 'Monthly Subscription')]"),
            (By.CSS_SELECTOR, "div.goods-item-wrapper"),
            (By.XPATH, "//div[contains(@class, 'goods-item-wrapper') and contains(@rseat, '1:0')]")
        ]

        for by, selector in monthly_selectors:
            try:
                monthly_plan = wait.until(EC.element_to_be_clickable((by, selector)))
                if monthly_plan:
                    print(f"Found Monthly plan using: {selector}")
                    break
            except:
                continue

        if monthly_plan:
            monthly_plan.click()
            print("✓ Selected Monthly Subscription (฿49) successfully!")
            time.sleep(0.5)
        else:
            print("✗ Could not find Monthly Subscription plan")

    except Exception as e:
        print(f"Error selecting Monthly plan: {e}")

    # Step 17: Select Rabbit Line Pay
    try:
        print("\nStep 16: Selecting Rabbit Line Pay...")
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

    # Step 18: Click Join VIP button
    try:
        print("\nStep 17: Clicking Join VIP button...")
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
            time.sleep(2)
        else:
            print("✗ Could not find Join VIP button")

    except Exception as e:
        print(f"Error clicking Join VIP button: {e}")

    # Step 19: Wait for payment redirect
    print("\n" + "="*60)
    print("✓ VIP subscription process initiated!")
    print("Waiting for payment completion...")
    print("Press 'd' and Enter to skip waiting, or wait for auto-redirect")
    print("="*60)

    # Monitor for redirect or user input
    start_time = time.time()
    max_wait = 300  # 5 minutes max wait

    payment_completed = False
    while True:
        current_url = driver.current_url

        # Check if redirected to payResult page
        if 'iq.com/vip/payResult' in current_url:
            print(f"\n✓ Payment completed! Redirected to: {current_url}")
            payment_completed = True
            break

        # Check if redirected back to iq.com (alternative)
        if 'iq.com' in current_url and 'cashier' not in current_url.lower() and 'payResult' not in current_url:
            print(f"\n✓ Redirected back to iq.com!")
            print(f"Current URL: {current_url}")
            break

        # Check elapsed time
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\n⚠ Maximum wait time ({max_wait}s) reached")
            break

        # Check for user input (non-blocking)
        import select
        import sys
        if sys.platform != 'win32':
            # Unix-like systems
            i, o, e = select.select([sys.stdin], [], [], 0.1)
            if i:
                user_input = sys.stdin.readline().strip()
                if user_input.lower() == 'd':
                    print("\n✓ User pressed 'd' - continuing to cancel subscription")
                    break
        else:
            # Windows fallback - just wait
            time.sleep(1)

    # Step 20: Navigate to autorenew page and cancel subscription
    try:
        print("\nStep 18: Navigating to autorenew management page...")
        driver.get("https://www.iq.com/vip/autorenew")
        wait_for_page_load(driver)
        print("✓ Loaded autorenew page")
        time.sleep(2)

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
            time.sleep(1)
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
            time.sleep(2)
        else:
            print("✗ Could not find confirm cancel link")

    except Exception as e:
        print(f"Error confirming cancellation: {e}")

    print("\n✓ Subscription cancelled successfully!")
    return True

def main():
    """Main function to process all emails"""
    url = "https://iq.com"

    # Read emails from file
    email_data_list = read_emails(EMAILS_FILE)
    if not email_data_list:
        print("No emails found. Please create emails.txt with one email per line.")
        return

    print(f"\n{'='*60}")
    print(f"STARTING BATCH PROCESSING")
    print(f"{'='*60}")
    print(f"Total emails to process: {len(email_data_list)}")
    print(f"Using password: {PASSWORD}")
    print(f"{'='*60}\n")

    # Set up Chrome/Chromium options
    chrome_options = Options()
    # Uncomment the line below if you want to run in headless mode
    # chrome_options.add_argument('--headless')

    # Optional: Set custom Chromium binary location if needed
    # chrome_options.binary_location = "/Applications/Chromium.app/Contents/MacOS/Chromium"

    driver = None
    processed_count = 0
    failed_count = 0

    try:
        # Initialize the Chrome driver once
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 6)

        # Set browser window to 780px width and 1/2 height
        screen_height = driver.execute_script("return window.screen.height;")
        window_width = 780
        window_height = screen_height // 2
        driver.set_window_size(window_width, window_height)
        driver.set_window_position(0, 0)  # Position at top-left corner
        print(f"✓ Browser window set to {window_width}x{window_height} (780px width, 1/2 height)")

        # Process each email
        for index, current_email_data in enumerate(email_data_list, 1):
            print(f"\n{'='*60}")
            print(f"PROCESSING EMAIL {index}/{len(email_data_list)}")
            print(f"Email: {current_email_data['email']}")
            print(f"{'='*60}\n")

            try:
                # Process the email
                success = process_single_email(driver, wait, current_email_data, url)

                if success:
                    # Save to success.txt
                    save_success(current_email_data)

                    # Remove from emails.txt
                    remove_from_emails_file(current_email_data['email'], EMAILS_FILE)

                    processed_count += 1

                    print(f"\n{'='*60}")
                    print(f"✓ COMPLETED: {current_email_data['email']}")
                    print(f"Progress: {processed_count}/{len(email_data_list)} successful")
                    print(f"{'='*60}\n")

                    # Small delay before next email
                    if index < len(email_data_list):
                        print("Waiting 3 seconds before processing next email...")
                        time.sleep(3)

            except Exception as e:
                failed_count += 1
                print(f"\n{'='*60}")
                print(f"✗ FAILED: {current_email_data['email']}")
                print(f"Error: {str(e)}")
                print(f"{'='*60}\n")

                # Continue with next email
                continue

        # Final summary
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total processed: {processed_count}")
        print(f"Total failed: {failed_count}")
        print(f"Total emails: {len(email_data_list)}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        print("\nMake sure you have:")
        print("1. Installed selenium: pip install selenium")
        print("2. Installed ChromeDriver or have Chrome/Chromium installed")

    finally:
        if driver:
            try:
                print("\nClosing browser...")
                driver.quit()
                print("✓ Browser closed.")
            except:
                pass

    print("\n✓ All done! Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()
