#!/usr/bin/env python3
"""
Netflix Password Reset Script
Automatically logs into Netflix and changes password
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# ============================================================================
# CONFIGURATION - Set your credentials here
# ============================================================================
OLD_EMAIL = "csayrcsin@gmail.com"
OLD_PASSWORD = "Popo-3355"
NEW_PASSWORD = "Crush-7788"
# ============================================================================

def wait_for_page_load(driver, timeout=10):
    """Wait for page to load completely"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(0.3)
    except Exception as e:
        print(f"Page load timeout: {e}")

def netflix_password_reset():
    """Main function to reset Netflix password"""

    print(f"\n{'='*60}")
    print("Netflix Password Reset")
    print(f"{'='*60}")
    print(f"Email: {OLD_EMAIL}")
    print(f"{'='*60}\n")

    # Setup Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Uncomment for headless mode
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Initialize Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    # Get screen dimensions and set window to 1/3 width and full height
    screen_width = driver.execute_script("return window.screen.width;")
    screen_height = driver.execute_script("return window.screen.height;")
    window_width = screen_width // 3
    window_height = screen_height

    driver.set_window_size(window_width, window_height)
    driver.set_window_position(0, 0)
    print(f"Browser window set to {window_width}x{window_height}")

    try:
        # Step 1: Navigate to Netflix login page
        print("\nStep 1: Navigating to Netflix login page...")
        driver.get("https://www.netflix.com/th/login")
        wait_for_page_load(driver)
        print("✓ Loaded Netflix login page")
        time.sleep(1)

        # Step 2: Enter email
        print("\nStep 2: Entering email...")
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
                        print(f"Found email input using: {selector}")
                        break
                except:
                    continue

            if email_input:
                email_input.clear()
                email_input.send_keys(OLD_EMAIL)
                print(f"✓ Entered email: {OLD_EMAIL}")
                time.sleep(0.5)
            else:
                print("✗ Could not find email input field")
                return False

        except Exception as e:
            print(f"Error entering email: {e}")
            return False

        # Step 3: Enter password
        print("\nStep 3: Entering password...")
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
                        print(f"Found password input using: {selector}")
                        break
                except:
                    continue

            if password_input:
                password_input.clear()
                password_input.send_keys(OLD_PASSWORD)
                print("✓ Entered password")
                time.sleep(0.5)
            else:
                print("✗ Could not find password input field")
                return False

        except Exception as e:
            print(f"Error entering password: {e}")
            return False

        # Step 4: Click sign-in button
        print("\nStep 4: Clicking sign-in button...")
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
                        print(f"Found sign-in button using: {selector}")
                        break
                except:
                    continue

            if signin_button:
                signin_button.click()
                print("✓ Clicked sign-in button")
                time.sleep(3)
            else:
                print("✗ Could not find sign-in button")
                return False

        except Exception as e:
            print(f"Error clicking sign-in button: {e}")
            return False

        # Step 5: Wait for login to complete
        print("\nStep 5: Waiting for login to complete...")
        time.sleep(3)

        # Check if login was successful
        current_url = driver.current_url
        if "login" in current_url.lower():
            print("⚠ Still on login page - checking for errors...")
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, "[data-uia*='error']")
                for error in error_elements:
                    if error.is_displayed():
                        print(f"✗ Login error: {error.text}")
                        return False
            except:
                pass
        else:
            print("✓ Login successful!")

        # Step 6: Navigate to manage account access page
        print("\nStep 6: Navigating to manage account access...")
        driver.get("https://www.netflix.com/manageaccountaccess")
        wait_for_page_load(driver)
        print("✓ Loaded manage account access page")
        time.sleep(2)

        # Step 7: Click "Sign out of all devices" button
        print("\nStep 7: Clicking 'Sign out of all devices' button...")
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
                        print(f"Found sign out button using: {selector}")
                        break
                except:
                    continue

            if signout_button:
                signout_button.click()
                print("✓ Clicked 'Sign out of all devices' button")
                time.sleep(2)
            else:
                print("⚠ Could not find sign out button, continuing...")

        except Exception as e:
            print(f"⚠ Error clicking sign out button: {e}")

        # Step 8: Navigate to password change page
        print("\nStep 8: Navigating to password change page...")
        driver.get("https://www.netflix.com/password")
        wait_for_page_load(driver)
        print("✓ Loaded password change page")
        time.sleep(2)

        # Step 9: Enter current password
        print("\nStep 9: Entering current password...")
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
                        print(f"Found current password input using: {selector}")
                        break
                except:
                    continue

            if current_pwd_input:
                current_pwd_input.clear()
                current_pwd_input.send_keys(OLD_PASSWORD)
                print("✓ Entered current password")
                time.sleep(0.5)
            else:
                print("✗ Could not find current password input")
                return False

        except Exception as e:
            print(f"Error entering current password: {e}")
            return False

        # Step 10: Enter new password
        print("\nStep 10: Entering new password...")
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
                        print(f"Found new password input using: {selector}")
                        break
                except:
                    continue

            if new_pwd_input:
                new_pwd_input.clear()
                new_pwd_input.send_keys(NEW_PASSWORD)
                print("✓ Entered new password")
                time.sleep(0.5)
            else:
                print("✗ Could not find new password input")
                return False

        except Exception as e:
            print(f"Error entering new password: {e}")
            return False

        # Step 11: Re-enter new password
        print("\nStep 11: Re-entering new password...")
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
                        print(f"Found confirm password input using: {selector}")
                        break
                except:
                    continue

            if confirm_pwd_input:
                confirm_pwd_input.clear()
                confirm_pwd_input.send_keys(NEW_PASSWORD)
                print("✓ Re-entered new password")
                time.sleep(0.5)
            else:
                print("✗ Could not find confirm password input")
                return False

        except Exception as e:
            print(f"Error re-entering new password: {e}")
            return False

        # Step 12: Click save/submit button
        print("\nStep 12: Looking for Save button...")
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
                        print(f"Found save button using: {selector}")
                        break
                except:
                    continue

            if save_button:
                save_button.click()
                print("✓ Clicked save button")
                time.sleep(3)
            else:
                print("✗ Could not find save button")
                print("⚠ Please manually click the save button")

        except Exception as e:
            print(f"Error clicking save button: {e}")

        # Step 13: Verify password change
        print("\nStep 13: Verifying password change...")
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
                print("\n✓ Password change successful!")
                print(f"✓ New password: {NEW_PASSWORD}")
            else:
                print("\n⚠ Password change status unclear")
                print("⚠ Please verify manually")

        except Exception as e:
            print(f"Error verifying password change: {e}")

        # Step 14: Navigate to device management and remove all devices
        print("\nStep 14: Navigating to device management...")
        driver.get("https://www.netflix.com/deviceManagement")
        wait_for_page_load(driver)
        print("✓ Loaded device management page")
        time.sleep(2)

        # Step 15: Remove all devices
        print("\nStep 15: Removing all devices...")
        try:
            # Find all "Remove device" buttons
            remove_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-uia='dm-remove-device']")

            if remove_buttons:
                print(f"Found {len(remove_buttons)} device(s) to remove")

                # Click each remove button
                devices_removed = 0
                for i in range(len(remove_buttons)):
                    try:
                        # Re-find buttons each time as the page updates after removal
                        current_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-uia='dm-remove-device']")

                        if current_buttons:
                            # Always click the first button since the list updates after each removal
                            current_buttons[0].click()
                            devices_removed += 1
                            print(f"✓ Removed device {devices_removed}")
                            time.sleep(1)
                        else:
                            break

                    except Exception as e:
                        print(f"⚠ Error removing device {i+1}: {e}")
                        continue

                print(f"\n✓ Removed {devices_removed} device(s) successfully!")

            else:
                print("⚠ No devices found to remove")

        except Exception as e:
            print(f"⚠ Error during device removal: {e}")

        # Step 16: Navigate to profiles page and remove extra profiles
        print("\nStep 16: Navigating to profiles page...")
        driver.get("https://www.netflix.com/account/profiles")
        wait_for_page_load(driver)
        print("✓ Loaded profiles page")
        time.sleep(2)

        # Step 17: Remove extra profiles (keep only 1 profile)
        print("\nStep 17: Removing extra profiles...")
        try:
            profiles_deleted = 0

            while True:
                # Find all profile buttons
                profile_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-cl-view='accountProfileSettings']")
                total_profiles = len(profile_buttons)

                print(f"Found {total_profiles} profile(s)")

                if total_profiles <= 1:
                    print("✓ Only 1 profile remaining (main profile)")
                    break

                # Click on the second profile (index 1) - never delete the first profile
                try:
                    profile_buttons[1].click()
                    print(f"Clicked on profile #{profiles_deleted + 2}")
                    time.sleep(2)

                    # Click delete profile button
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
                            print("✓ Clicked 'Delete Profile' button")
                            delete_clicked = True
                            time.sleep(1)
                            break
                        except:
                            continue

                    if not delete_clicked:
                        print("⚠ Could not find delete profile button")
                        break

                    # Confirm deletion
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
                            print("✓ Confirmed profile deletion")
                            confirm_clicked = True
                            profiles_deleted += 1
                            time.sleep(2)
                            break
                        except:
                            continue

                    if not confirm_clicked:
                        print("⚠ Could not find confirm deletion button")
                        break

                    # Go back to profiles page
                    driver.get("https://www.netflix.com/account/profiles")
                    wait_for_page_load(driver)
                    time.sleep(2)

                except Exception as e:
                    print(f"⚠ Error deleting profile: {e}")
                    break

            if profiles_deleted > 0:
                print(f"\n✓ Deleted {profiles_deleted} extra profile(s) successfully!")
            else:
                print("✓ No extra profiles to delete")

        except Exception as e:
            print(f"⚠ Error during profile deletion: {e}")

        # Step 18: Add profiles 2-5
        print("\nStep 18: Adding profiles 2-5...")
        try:
            profiles_created = 0

            for profile_number in range(2, 6):  # Create profiles 2, 3, 4, 5
                try:
                    # Go back to profiles page
                    driver.get("https://www.netflix.com/account/profiles")
                    wait_for_page_load(driver)
                    time.sleep(1)

                    # Click "Add Profile" button
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
                            print(f"✓ Clicked 'Add Profile' button for profile {profile_number}")
                            add_clicked = True
                            time.sleep(1)
                            break
                        except:
                            continue

                    if not add_clicked:
                        print(f"⚠ Could not find 'Add Profile' button")
                        break

                    # Enter profile name
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
                            print(f"✓ Entered profile name: {profile_number}")
                            name_entered = True
                            time.sleep(0.5)
                            break
                        except:
                            continue

                    if not name_entered:
                        print(f"⚠ Could not find name input field")
                        break

                    # Click save button
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
                            print(f"✓ Saved profile {profile_number}")
                            save_clicked = True
                            profiles_created += 1
                            time.sleep(2)
                            break
                        except:
                            continue

                    if not save_clicked:
                        print(f"⚠ Could not find save button")
                        break

                except Exception as e:
                    print(f"⚠ Error creating profile {profile_number}: {e}")
                    continue

            print(f"\n✓ Created {profiles_created} new profile(s) successfully!")

        except Exception as e:
            print(f"⚠ Error during profile creation: {e}")

        print(f"\n{'='*60}")
        print("Process completed!")
        print(f"{'='*60}\n")

        # Keep browser open for verification
        print("Browser will remain open for 30 seconds for verification...")
        time.sleep(30)

        return True

    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        return False

    finally:
        # Close the browser
        try:
            driver.quit()
            print("✓ Browser closed")
        except:
            pass

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Netflix Password Reset Script")
    print("="*60)
    print(f"\nOld Email: {OLD_EMAIL}")
    print(f"Old Password: {'*' * len(OLD_PASSWORD)}")
    print(f"New Password: {'*' * len(NEW_PASSWORD)}")
    print("\nMake sure to update the configuration at the top of this file!")
    print("="*60 + "\n")

    input("Press Enter to start the password reset process...")

    success = netflix_password_reset()

    if success:
        print("\n✓ Password reset completed successfully!")
    else:
        print("\n✗ Password reset failed. Please try again or reset manually.")
