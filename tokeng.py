#!/usr/bin/env python3
"""
Script to log into existing Outlook accounts and stay in mailbox
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

# Configuration
INPUT_FILE = "untokenmail.txt"  # File containing email:password pairs

def wait_for_page_load(driver, timeout=10):
    """Wait for page to complete loading"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def read_accounts(filename):
    """Read email:password pairs from file"""
    try:
        with open(filename, 'r') as f:
            accounts = []
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        email, password = parts
                        accounts.append({
                            'email': email.strip(),
                            'password': password.strip()
                        })
            return accounts
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return []

def login_to_outlook(driver, wait, account_data):
    """Log into Outlook account and stay in mailbox"""
    print(f"\n{'='*60}")
    print(f"Processing: {account_data['email']}")
    print(f"{'='*60}")

    # Step 1: Navigate to Microsoft Outlook sign-in page
    try:
        start_url = "https://go.microsoft.com/fwlink/p/?LinkID=2125442&deeplink=mail%2F0%2F%3Fnlp%3D0"
        driver.get(start_url)
        wait_for_page_load(driver)
        print(f"✓ Opened Microsoft Outlook sign-in page")
        time.sleep(1)
    except Exception as e:
        print(f"Error opening Microsoft Outlook page: {e}")
        return False

    # Step 2: Enter email address
    try:
        print("\nStep 1: Entering email address...")

        # Find email input field
        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email'][name='loginfmt']")
        ))
        email_input.clear()
        email_input.send_keys(account_data['email'])
        print(f"✓ Entered email: {account_data['email']}")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error entering email: {e}")
        return False

    # Step 3: Click Next button after email
    try:
        print("\nStep 2: Clicking Next button...")

        # Find and click Next button
        next_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input[type='submit'][value='Next']")
        ))
        next_button.click()
        print("✓ Clicked Next button")
        time.sleep(1.5)
    except Exception as e:
        print(f"Error clicking Next: {e}")
        return False

    # Step 4: Enter password and press Enter
    try:
        print("\nStep 3: Entering password...")

        # Find password input field
        password_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password'][name='passwd']")
        ))
        password_input.clear()
        password_input.send_keys(account_data['password'])
        print(f"✓ Entered password")
        time.sleep(0.5)

        # Press Enter to submit
        print("\nStep 4: Pressing Enter to sign in...")
        password_input.send_keys(Keys.RETURN)
        print("✓ Pressed Enter")
        time.sleep(2)
    except Exception as e:
        print(f"Error entering password or pressing Enter: {e}")
        return False

    # Step 5.5: Handle "Skip for now (x days until this is required)" link
    try:
        print("\nStep 4.5: Checking for 'Skip for now' link...")

        # Try to find by text content first
        try:
            skip_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Skip for now')]")
            skip_link.click()
            print("✓ Clicked 'Skip for now' link (found by text)")
            time.sleep(2)
        except:
            # Try by ID as fallback
            try:
                skip_link = driver.find_element(By.CSS_SELECTOR, "a#iShowSkip")
                skip_link.click()
                print("✓ Clicked 'Skip for now' link (found by ID)")
                time.sleep(2)
            except:
                print("Note: No 'Skip for now' link found")
    except Exception as e:
        print(f"Note: Skip for now handling: {e}")

    # Step 6: Handle "Skip for now" button (if present)
    try:
        print("\nStep 5: Checking for 'Skip for now' button...")
        skip_button = driver.find_element(By.CSS_SELECTOR, "button[type='button'][data-testid='secondaryButton']")
        if skip_button and 'skip' in skip_button.text.lower():
            skip_button.click()
            print("✓ Clicked 'Skip for now' button")
            time.sleep(2)
    except Exception as e:
        print("Note: No 'Skip for now' button found")

    # Step 7: Handle "No" button for "Stay signed in?" prompt
    try:
        print("\nStep 6: Handling 'Stay signed in?' prompt...")

        # Try to find the new "No" button with data-testid
        try:
            no_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'][data-testid='secondaryButton']")
            if no_button and 'no' in no_button.text.lower():
                no_button.click()
                print("✓ Clicked 'No' button")
                time.sleep(2)
        except:
            # Try old style "No" button
            try:
                no_button = driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='No']")
                no_button.click()
                print("✓ Clicked 'No' on stay signed in prompt")
                time.sleep(2)
            except:
                # Try "Yes" button if "No" not found
                try:
                    yes_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Yes']")
                    yes_button.click()
                    print("✓ Clicked 'Yes' on stay signed in prompt")
                    time.sleep(2)
                except:
                    print("Note: No 'Stay signed in?' prompt found")
    except Exception as e:
        print(f"Note: Stay signed in handling: {e}")

    # Step 7.5: Handle OAuth consent screen - look for "No" or "Cancel" buttons
    try:
        print("\nStep 6.5: Checking for consent/permission prompts...")
        time.sleep(2)

        # Try to find "No" or "Cancel" button by text
        try:
            no_cancel_button = driver.find_element(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'no') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cancel')]")
            no_cancel_button.click()
            print("✓ Clicked 'No' or 'Cancel' button on consent screen")
            time.sleep(2)
        except:
            # Try input type buttons
            try:
                no_cancel_button = driver.find_element(By.XPATH, "//input[@type='button' or @type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'no') or contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cancel')]")
                no_cancel_button.click()
                print("✓ Clicked 'No' or 'Cancel' input button")
                time.sleep(2)
            except:
                # Try "Accept" button if no No/Cancel found (for OAuth consent)
                try:
                    accept_button = driver.find_element(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'yes')]")
                    accept_button.click()
                    print("✓ Clicked 'Accept' or 'Yes' button on consent screen")
                    time.sleep(2)
                except:
                    print("Note: No consent prompt buttons found")
    except Exception as e:
        print(f"Note: Consent handling: {e}")

    # Step 8: Monitor for successful login to Outlook mailbox
    print("\n✓ Login in progress...")
    print("Waiting for redirect to Outlook mailbox...")
    print("Target: https://outlook.live.com/mail/0/")

    # Wait and check URL for redirect
    start_time = time.time()
    max_wait = 180  # 3 minutes
    login_successful = False

    while time.time() - start_time < max_wait:
        try:
            current_url = driver.current_url
            elapsed = time.time() - start_time

            # Print progress every 10 seconds
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"⏳ Waiting for redirect... ({int(elapsed)}s elapsed)")
                print(f"   Current URL: {current_url[:80]}...")

            # Check if redirected to Outlook mail (login complete)
            if 'outlook.live.com/mail' in current_url:
                print(f"\n✓ Redirected to Outlook mailbox!")
                print(f"✓ Login successful!")
                print(f"✓ Email: {account_data['email']}")
                print(f"✓ You are now logged into the Outlook mailbox")
                print(f"Final URL: {current_url}")

                login_successful = True
                break

            time.sleep(2)

        except Exception as e:
            print(f"⚠ Error monitoring: {e}")
            time.sleep(2)

    if login_successful:
        print("\n✓ Account logged in successfully!")
        return True
    else:
        print(f"\n⚠ Timeout waiting for redirect after {max_wait}s")
        print(f"Last URL: {driver.current_url}")
        return False

def main():
    """Main function"""
    # Read accounts from untokenmail.txt
    accounts = read_accounts(INPUT_FILE)
    if not accounts:
        print(f"No accounts found in {INPUT_FILE}")
        print(f"Format: email:password (one per line)")
        return

    print(f"Found {len(accounts)} accounts to process")

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Process each account
    success_count = 0
    fail_count = 0

    for i, account in enumerate(accounts, 1):
        print(f"\n{'#'*60}")
        print(f"Processing account {i}/{len(accounts)}")
        print(f"{'#'*60}")

        driver = None
        try:
            # Create new browser instance
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 20)

            # Set window size
            driver.set_window_size(1200, 900)

            # Login to Outlook
            success = login_to_outlook(driver, wait, account)

            if success:
                success_count += 1
            else:
                fail_count += 1

            # Wait for user input before closing browser
            print("\n" + "="*60)
            print("Browser will remain open for inspection")
            print("Press 'd' and Enter to close browser and continue...")
            print("="*60)

            while True:
                user_input = input().strip().lower()
                if user_input == 'd':
                    print("✓ Closing browser...")
                    break
                else:
                    print("Invalid input. Press 'd' and Enter to continue...")

            # Close browser
            driver.quit()
            driver = None

            # Small delay between accounts
            if i < len(accounts):
                print("\nWaiting 3 seconds before next account...")
                time.sleep(3)

        except Exception as e:
            print(f"Error processing account: {e}")
            fail_count += 1
            if driver:
                try:
                    # Wait for user input before closing browser (even on error)
                    print("\n" + "="*60)
                    print("Error occurred - Browser will remain open for inspection")
                    print("Press 'd' and Enter to close browser and continue...")
                    print("="*60)

                    while True:
                        user_input = input().strip().lower()
                        if user_input == 'd':
                            print("✓ Closing browser...")
                            break
                        else:
                            print("Invalid input. Press 'd' and Enter to continue...")

                    driver.quit()
                except:
                    pass

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total accounts: {len(accounts)}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
