#!/usr/bin/env python3
"""
Netflix Password Reset Script - Parallel Version
Reads credentials from netflix.txt and processes multiple accounts in parallel
Format: email:password (current password)
All accounts will be reset to NEW_PASSWORD
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import threading
from queue import Queue

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NETFLIX_FILE = os.path.join(SCRIPT_DIR, "netflix.txt")  # File containing credentials
SUCCESS_FILE = os.path.join(SCRIPT_DIR, "netflix_success.txt")  # File for successful resets
NUM_PARALLEL_BROWSERS = 2  # Number of browsers to run in parallel
NEW_PASSWORD = "Crush-7788"  # New password for all accounts

# Lock for file operations
file_lock = threading.Lock()


def wait_for_page_load(driver, timeout=10):
    """Wait for page to load completely"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(0.3)
    except Exception as e:
        print(f"Page load timeout: {e}")


def load_accounts(filename):
    """Load accounts from file"""
    accounts = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Support both : and | separators
                    if ':' in line:
                        parts = line.split(':', 1)
                    elif '|' in line:
                        parts = line.split('|', 1)
                    else:
                        continue

                    if len(parts) >= 2:
                        accounts.append({
                            'email': parts[0].strip(),
                            'old_password': parts[1].strip(),
                            'new_password': NEW_PASSWORD
                        })
        print(f"✓ Loaded {len(accounts)} account(s) from {filename}")
    except FileNotFoundError:
        print(f"✗ File not found: {filename}")
        print(f"Please create {filename} with format: email:password")
    except Exception as e:
        print(f"✗ Error loading accounts: {e}")

    return accounts


def save_success(account):
    """Save successful account to success file"""
    with file_lock:
        try:
            with open(SUCCESS_FILE, 'a') as f:
                f.write(f"{account['email']}|{account['new_password']}\n")
            print(f"✓ Saved to success file: {account['email']}")
        except Exception as e:
            print(f"✗ Error saving to success file: {e}")


def remove_from_netflix_file(email, filename):
    """Remove processed email from netflix.txt"""
    with file_lock:
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()

            with open(filename, 'w') as f:
                for line in lines:
                    if not line.strip().startswith(email):
                        f.write(line)

            print(f"✓ Removed {email} from {filename}")
        except Exception as e:
            print(f"✗ Error removing from file: {e}")


def process_single_account(driver, wait, account, thread_id):
    """Process a single Netflix account"""
    email = account['email']
    old_password = account['old_password']
    new_password = account['new_password']

    print(f"\n[Thread {thread_id}] {'='*60}")
    print(f"[Thread {thread_id}] Processing: {email}")
    print(f"[Thread {thread_id}] {'='*60}")

    try:
        # Step 1: Navigate to Netflix login page
        print(f"[Thread {thread_id}] Step 1: Navigating to Netflix login page...")
        driver.get("https://www.netflix.com/th/login")
        wait_for_page_load(driver)
        print(f"[Thread {thread_id}] ✓ Loaded Netflix login page")
        time.sleep(1)

        # Step 2: Enter email
        print(f"[Thread {thread_id}] Step 2: Entering email...")
        try:
            email_input = None
            email_selectors = [
                (By.CSS_SELECTOR, "input[data-uia='field-userLoginId']"),
                (By.CSS_SELECTOR, "input[name='userLoginId']"),
                (By.CSS_SELECTOR, "input[autocomplete='email']"),
                (By.ID, "userLoginId")
            ]

            for by, selector in email_selectors:
                try:
                    email_input = wait.until(EC.presence_of_element_located((by, selector)))
                    if email_input:
                        print(f"[Thread {thread_id}] Found email input using: {selector}")
                        break
                except:
                    continue

            if email_input:
                email_input.clear()
                email_input.send_keys(email)
                print(f"[Thread {thread_id}] ✓ Entered email: {email}")
                time.sleep(0.5)
            else:
                print(f"[Thread {thread_id}] ✗ Could not find email input field")
                return False

        except Exception as e:
            print(f"[Thread {thread_id}] Error entering email: {e}")
            return False

        # Step 3: Enter password
        print(f"[Thread {thread_id}] Step 3: Entering password...")
        try:
            password_input = None
            password_selectors = [
                (By.CSS_SELECTOR, "input[data-uia='field-password']"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.ID, "password")
            ]

            for by, selector in password_selectors:
                try:
                    password_input = wait.until(EC.presence_of_element_located((by, selector)))
                    if password_input:
                        print(f"[Thread {thread_id}] Found password input using: {selector}")
                        break
                except:
                    continue

            if password_input:
                password_input.clear()
                password_input.send_keys(old_password)
                print(f"[Thread {thread_id}] ✓ Entered password")
                time.sleep(2)
            else:
                print(f"[Thread {thread_id}] ✗ Could not find password input field")
                return False

        except Exception as e:
            print(f"[Thread {thread_id}] Error entering password: {e}")
            return False

        # Step 4: Click sign-in button
        print(f"[Thread {thread_id}] Step 4: Clicking sign-in button...")
        try:
            signin_button = None
            signin_selectors = [
                (By.CSS_SELECTOR, "button[data-uia='sign-in-button']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[@type='submit']")
            ]

            for by, selector in signin_selectors:
                try:
                    signin_button = wait.until(EC.element_to_be_clickable((by, selector)))
                    if signin_button:
                        print(f"[Thread {thread_id}] Found sign-in button using: {selector}")
                        break
                except:
                    continue

            if signin_button:
                signin_button.click()
                print(f"[Thread {thread_id}] ✓ Clicked sign-in button")
                time.sleep(3)
            else:
                print(f"[Thread {thread_id}] ✗ Could not find sign-in button")
                return False

        except Exception as e:
            print(f"[Thread {thread_id}] Error clicking sign-in button: {e}")
            return False

        # Step 5: Wait for login to complete
        print(f"[Thread {thread_id}] Step 5: Waiting for login to complete...")
        time.sleep(3)

        # Check if login was successful
        current_url = driver.current_url
        if "login" in current_url.lower():
            print(f"[Thread {thread_id}] ⚠ Still on login page - checking for errors...")
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, "[data-uia*='error']")
                for error in error_elements:
                    if error.is_displayed():
                        print(f"[Thread {thread_id}] ✗ Login error: {error.text}")
                        return False
            except:
                pass
        else:
            print(f"[Thread {thread_id}] ✓ Login successful!")

        # Step 6: Navigate to manage account access page
        print(f"[Thread {thread_id}] Step 6: Navigating to manage account access...")
        driver.get("https://www.netflix.com/manageaccountaccess")
        wait_for_page_load(driver)
        print(f"[Thread {thread_id}] ✓ Loaded manage account access page")
        time.sleep(2)

        # Step 7: Click "Sign out of all devices" button
        print(f"[Thread {thread_id}] Step 7: Clicking 'Sign out of all devices' button...")
        try:
            signout_button = None
            signout_selectors = [
                (By.CSS_SELECTOR, "button[data-uia='manage-account-access-page+soad-button']"),
                (By.CSS_SELECTOR, "button[data-cl-command='LogoutAllDevicesCommand']"),
                (By.XPATH, "//button[@type='button' and @data-uia='manage-account-access-page+soad-button']")
            ]

            for by, selector in signout_selectors:
                try:
                    signout_button = wait.until(EC.element_to_be_clickable((by, selector)))
                    if signout_button:
                        print(f"[Thread {thread_id}] Found sign out button using: {selector}")
                        break
                except:
                    continue

            if signout_button:
                signout_button.click()
                print(f"[Thread {thread_id}] ✓ Clicked 'Sign out of all devices' button")
                time.sleep(2)
            else:
                print(f"[Thread {thread_id}] ⚠ Could not find sign out button, continuing...")

        except Exception as e:
            print(f"[Thread {thread_id}] ⚠ Error clicking sign out button: {e}")

        # Step 8: Navigate to password change page
        print(f"[Thread {thread_id}] Step 8: Navigating to password change page...")
        driver.get("https://www.netflix.com/password")
        wait_for_page_load(driver)
        print(f"[Thread {thread_id}] ✓ Loaded password change page")
        time.sleep(2)

        # Step 9: Enter current password
        print(f"[Thread {thread_id}] Step 9: Entering current password...")
        try:
            current_pwd_input = None
            current_pwd_selectors = [
                (By.CSS_SELECTOR, "input[data-uia='change-password-form+current-password-input']"),
                (By.CSS_SELECTOR, "input[name='current-password']"),
                (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]

            for by, selector in current_pwd_selectors:
                try:
                    current_pwd_input = wait.until(EC.presence_of_element_located((by, selector)))
                    if current_pwd_input:
                        print(f"[Thread {thread_id}] Found current password input using: {selector}")
                        break
                except:
                    continue

            if current_pwd_input:
                current_pwd_input.clear()
                current_pwd_input.send_keys(old_password)
                print(f"[Thread {thread_id}] ✓ Entered current password")
                time.sleep(0.5)
            else:
                print(f"[Thread {thread_id}] ✗ Could not find current password input")
                return False

        except Exception as e:
            print(f"[Thread {thread_id}] Error entering current password: {e}")
            return False

        # Step 10: Enter new password
        print(f"[Thread {thread_id}] Step 10: Entering new password...")
        try:
            new_pwd_input = None
            new_pwd_selectors = [
                (By.CSS_SELECTOR, "input[data-uia='change-password-form+new-password-input']"),
                (By.CSS_SELECTOR, "input[name='new-password']"),
                (By.CSS_SELECTOR, "input[autocomplete='new-password']")
            ]

            for by, selector in new_pwd_selectors:
                try:
                    new_pwd_input = wait.until(EC.presence_of_element_located((by, selector)))
                    if new_pwd_input:
                        print(f"[Thread {thread_id}] Found new password input using: {selector}")
                        break
                except:
                    continue

            if new_pwd_input:
                new_pwd_input.clear()
                new_pwd_input.send_keys(new_password)
                print(f"[Thread {thread_id}] ✓ Entered new password")
                time.sleep(0.5)
            else:
                print(f"[Thread {thread_id}] ✗ Could not find new password input")
                return False

        except Exception as e:
            print(f"[Thread {thread_id}] Error entering new password: {e}")
            return False

        # Step 11: Re-enter new password
        print(f"[Thread {thread_id}] Step 11: Re-entering new password...")
        try:
            confirm_pwd_input = None
            confirm_pwd_selectors = [
                (By.CSS_SELECTOR, "input[data-uia='change-password-form+reeneter-new-password-input']"),
                (By.CSS_SELECTOR, "input[name='reeneter-new-password']")
            ]

            for by, selector in confirm_pwd_selectors:
                try:
                    confirm_pwd_input = wait.until(EC.presence_of_element_located((by, selector)))
                    if confirm_pwd_input:
                        print(f"[Thread {thread_id}] Found confirm password input using: {selector}")
                        break
                except:
                    continue

            if confirm_pwd_input:
                confirm_pwd_input.clear()
                confirm_pwd_input.send_keys(new_password)
                print(f"[Thread {thread_id}] ✓ Re-entered new password")
                time.sleep(0.5)
            else:
                print(f"[Thread {thread_id}] ✗ Could not find confirm password input")
                return False

        except Exception as e:
            print(f"[Thread {thread_id}] Error re-entering new password: {e}")
            return False

        # Step 12: Click save/submit button
        print(f"[Thread {thread_id}] Step 12: Looking for Save button...")
        try:
            save_button = None
            save_selectors = [
                (By.CSS_SELECTOR, "button[data-uia='change-password-form+save-button']"),
                (By.CSS_SELECTOR, "button[data-cl-command='SubmitCommand']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[@type='submit']")
            ]

            for by, selector in save_selectors:
                try:
                    save_button = wait.until(EC.element_to_be_clickable((by, selector)))
                    if save_button:
                        print(f"[Thread {thread_id}] Found save button using: {selector}")
                        break
                except:
                    continue

            if save_button:
                save_button.click()
                print(f"[Thread {thread_id}] ✓ Clicked save button")
                time.sleep(3)
            else:
                print(f"[Thread {thread_id}] ✗ Could not find save button")
                return False

        except Exception as e:
            print(f"[Thread {thread_id}] Error clicking save button: {e}")
            return False

        # Step 13: Verify password change
        print(f"[Thread {thread_id}] Step 13: Verifying password change...")
        time.sleep(2)

        try:
            # Look for success message
            success_indicators = [
                "password has been updated",
                "password changed",
                "successfully"
            ]

            page_text = driver.page_source.lower()
            success = any(indicator.lower() in page_text for indicator in success_indicators)

            if success:
                print(f"[Thread {thread_id}] ✓ Password change successful!")
                print(f"[Thread {thread_id}] ✓ New password: {new_password}")
            else:
                print(f"[Thread {thread_id}] ⚠ Password change status unclear")
                # Still continue with other steps

        except Exception as e:
            print(f"[Thread {thread_id}] Error verifying password change: {e}")

        # Step 14: Navigate to device management and remove all devices
        print(f"[Thread {thread_id}] Step 14: Navigating to device management...")
        driver.get("https://www.netflix.com/deviceManagement")
        wait_for_page_load(driver)
        print(f"[Thread {thread_id}] ✓ Loaded device management page")
        time.sleep(2)

        # Step 15: Remove all devices
        print(f"[Thread {thread_id}] Step 15: Removing all devices...")
        try:
            remove_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-uia='dm-remove-device']")

            if remove_buttons:
                print(f"[Thread {thread_id}] Found {len(remove_buttons)} device(s) to remove")

                devices_removed = 0
                for i in range(len(remove_buttons)):
                    try:
                        current_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-uia='dm-remove-device']")

                        if current_buttons:
                            current_buttons[0].click()
                            devices_removed += 1
                            print(f"[Thread {thread_id}] ✓ Removed device {devices_removed}")
                            time.sleep(1)
                        else:
                            break

                    except Exception as e:
                        print(f"[Thread {thread_id}] ⚠ Error removing device {i+1}: {e}")
                        continue

                print(f"[Thread {thread_id}] ✓ Removed {devices_removed} device(s) successfully!")

            else:
                print(f"[Thread {thread_id}] ⚠ No devices found to remove")

        except Exception as e:
            print(f"[Thread {thread_id}] ⚠ Error during device removal: {e}")

        # Step 16: Navigate to profiles page and remove extra profiles
        print(f"[Thread {thread_id}] Step 16: Navigating to profiles page...")
        driver.get("https://www.netflix.com/account/profiles")
        wait_for_page_load(driver)
        print(f"[Thread {thread_id}] ✓ Loaded profiles page")
        time.sleep(2)

        # Step 17: Remove extra profiles (keep only 1 profile)
        print(f"[Thread {thread_id}] Step 17: Removing extra profiles...")
        try:
            profiles_deleted = 0

            while True:
                profile_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-cl-view='accountProfileSettings']")
                total_profiles = len(profile_buttons)

                print(f"[Thread {thread_id}] Found {total_profiles} profile(s)")

                if total_profiles <= 1:
                    print(f"[Thread {thread_id}] ✓ Only 1 profile remaining (main profile)")
                    break

                try:
                    profile_buttons[1].click()
                    print(f"[Thread {thread_id}] Clicked on profile #{profiles_deleted + 2}")
                    time.sleep(2)

                    delete_button_selectors = [
                        (By.CSS_SELECTOR, "button[data-uia='profile-settings-page+delete-profile-button']"),
                        (By.XPATH, "//button[@data-uia='profile-settings-page+delete-profile-button']")
                    ]

                    delete_clicked = False
                    for by, selector in delete_button_selectors:
                        try:
                            delete_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            delete_button.click()
                            print(f"[Thread {thread_id}] ✓ Clicked 'Delete Profile' button")
                            delete_clicked = True
                            time.sleep(1)
                            break
                        except:
                            continue

                    if not delete_clicked:
                        print(f"[Thread {thread_id}] ⚠ Could not find delete profile button")
                        break

                    confirm_button_selectors = [
                        (By.CSS_SELECTOR, "button[data-uia='profile-settings-page+delete-profile+destructive-button']"),
                        (By.XPATH, "//button[@data-uia='profile-settings-page+delete-profile+destructive-button']")
                    ]

                    confirm_clicked = False
                    for by, selector in confirm_button_selectors:
                        try:
                            confirm_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            confirm_button.click()
                            print(f"[Thread {thread_id}] ✓ Confirmed profile deletion")
                            confirm_clicked = True
                            profiles_deleted += 1
                            time.sleep(2)
                            break
                        except:
                            continue

                    if not confirm_clicked:
                        print(f"[Thread {thread_id}] ⚠ Could not find confirm deletion button")
                        break

                    driver.get("https://www.netflix.com/account/profiles")
                    wait_for_page_load(driver)
                    time.sleep(2)

                except Exception as e:
                    print(f"[Thread {thread_id}] ⚠ Error deleting profile: {e}")
                    break

            if profiles_deleted > 0:
                print(f"[Thread {thread_id}] ✓ Deleted {profiles_deleted} extra profile(s) successfully!")
            else:
                print(f"[Thread {thread_id}] ✓ No extra profiles to delete")

        except Exception as e:
            print(f"[Thread {thread_id}] ⚠ Error during profile deletion: {e}")

        # Step 18: Add profiles 2-5
        print(f"[Thread {thread_id}] Step 18: Adding profiles 2-5...")
        try:
            profiles_created = 0

            for profile_number in range(2, 6):
                try:
                    driver.get("https://www.netflix.com/account/profiles")
                    wait_for_page_load(driver)
                    time.sleep(1)

                    add_profile_button_selectors = [
                        (By.CSS_SELECTOR, "button[data-uia='menu-card+button'][data-cl-view='addProfile']"),
                        (By.CSS_SELECTOR, "button[data-cl-view='addProfile']"),
                        (By.XPATH, "//button[@data-cl-view='addProfile']")
                    ]

                    add_clicked = False
                    for by, selector in add_profile_button_selectors:
                        try:
                            add_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            add_button.click()
                            print(f"[Thread {thread_id}] ✓ Clicked 'Add Profile' button for profile {profile_number}")
                            add_clicked = True
                            time.sleep(1)
                            break
                        except:
                            continue

                    if not add_clicked:
                        print(f"[Thread {thread_id}] ⚠ Could not find 'Add Profile' button")
                        break

                    name_input_selectors = [
                        (By.CSS_SELECTOR, "input[data-uia='account-profiles-page+add-profile+name-input']"),
                        (By.CSS_SELECTOR, "input[name='name']"),
                        (By.CSS_SELECTOR, "input[type='text']")
                    ]

                    name_entered = False
                    for by, selector in name_input_selectors:
                        try:
                            name_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((by, selector))
                            )
                            name_input.clear()
                            name_input.send_keys(str(profile_number))
                            print(f"[Thread {thread_id}] ✓ Entered profile name: {profile_number}")
                            name_entered = True
                            time.sleep(0.5)
                            break
                        except:
                            continue

                    if not name_entered:
                        print(f"[Thread {thread_id}] ⚠ Could not find name input field")
                        break

                    save_button_selectors = [
                        (By.CSS_SELECTOR, "button[data-uia='account-profiles-page+add-profile+primary-button']"),
                        (By.CSS_SELECTOR, "button[data-cl-command='SubmitCommand'][data-cl-view='addProfile']"),
                        (By.XPATH, "//button[@data-uia='account-profiles-page+add-profile+primary-button']")
                    ]

                    save_clicked = False
                    for by, selector in save_button_selectors:
                        try:
                            save_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            save_button.click()
                            print(f"[Thread {thread_id}] ✓ Saved profile {profile_number}")
                            save_clicked = True
                            profiles_created += 1
                            time.sleep(2)
                            break
                        except:
                            continue

                    if not save_clicked:
                        print(f"[Thread {thread_id}] ⚠ Could not find save button")
                        break

                except Exception as e:
                    print(f"[Thread {thread_id}] ⚠ Error creating profile {profile_number}: {e}")
                    continue

            print(f"[Thread {thread_id}] ✓ Created {profiles_created} new profile(s) successfully!")

        except Exception as e:
            print(f"[Thread {thread_id}] ⚠ Error during profile creation: {e}")

        print(f"\n[Thread {thread_id}] {'='*60}")
        print(f"[Thread {thread_id}] ✓ Account processing completed!")
        print(f"[Thread {thread_id}] {'='*60}")

        return True

    except Exception as e:
        print(f"[Thread {thread_id}] ✗ An error occurred: {e}")
        return False


def worker_thread(thread_id, account_queue, results_queue, chrome_options):
    """Worker thread that processes accounts from the queue"""
    window_width = 780
    window_height = 600
    x_position = thread_id * window_width
    y_position = 0

    # Process accounts from the queue
    while True:
        driver = None
        try:
            # Get next account from queue (non-blocking with timeout)
            try:
                current_account = account_queue.get(timeout=1)
            except:
                # Queue is empty, exit thread
                break

            print(f"\n[Thread {thread_id}] {'='*60}")
            print(f"[Thread {thread_id}] Opening new browser for: {current_account['email']}")
            print(f"[Thread {thread_id}] {'='*60}\n")

            # Initialize a fresh Chrome driver for this account
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 20)

            # Position the browser window
            driver.set_window_size(window_width, window_height)
            driver.set_window_position(x_position, y_position)
            print(f"[Thread {thread_id}] Browser window set to {window_width}x{window_height} at position ({x_position}, {y_position})")

            # Process the account
            success = process_single_account(driver, wait, current_account, thread_id)

            if success:
                # Immediately save to success file and remove from netflix.txt
                print(f"\n[Thread {thread_id}] ✓ Account completed successfully!")
                save_success(current_account)
                remove_from_netflix_file(current_account['email'], NETFLIX_FILE)

                results_queue.put({
                    'success': True,
                    'account': current_account,
                    'thread_id': thread_id
                })
            else:
                print(f"\n[Thread {thread_id}] ✗ Account processing failed")
                results_queue.put({
                    'success': False,
                    'account': current_account,
                    'thread_id': thread_id
                })

            account_queue.task_done()

        except Exception as e:
            print(f"[Thread {thread_id}] ✗ Worker thread error: {e}")
            account_queue.task_done()

        finally:
            # Close the browser for this account
            if driver:
                try:
                    driver.quit()
                    print(f"[Thread {thread_id}] ✓ Browser closed for this account")
                except:
                    pass


def main():
    """Main function to orchestrate parallel processing"""
    print(f"\n{'='*60}")
    print("Netflix Password Reset - Parallel Processing")
    print(f"{'='*60}")
    print(f"Parallel browsers: {NUM_PARALLEL_BROWSERS}")
    print(f"Input file: {NETFLIX_FILE}")
    print(f"Success file: {SUCCESS_FILE}")
    print(f"{'='*60}\n")

    # Load accounts from file
    accounts = load_accounts(NETFLIX_FILE)

    if not accounts:
        print("\n✗ No accounts to process. Exiting.")
        return

    print(f"\n✓ Found {len(accounts)} account(s) to process\n")

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Create queues
    account_queue = Queue()
    results_queue = Queue()

    # Fill the queue with accounts
    for account in accounts:
        account_queue.put(account)

    # Create and start worker threads
    threads = []
    for i in range(min(NUM_PARALLEL_BROWSERS, len(accounts))):
        thread = threading.Thread(
            target=worker_thread,
            args=(i, account_queue, results_queue, chrome_options)
        )
        thread.daemon = True
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
            processed_count += 1
            print(f"\n✓ COMPLETED: {result['account']['email']} (Thread {result['thread_id']})")
        else:
            failed_count += 1
            print(f"\n✗ FAILED: {result['account']['email']} (Thread {result['thread_id']})")

    # Final summary
    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total accounts: {len(accounts)}")
    print(f"Successful: {processed_count}")
    print(f"Failed: {failed_count}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
