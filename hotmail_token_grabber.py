#!/Users/meaookung144/Documents/GitHub/premium-acc-reg/venv/bin/python3
"""
Selenium script to create Hotmail accounts and grab client_id and access tokens
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import random
import re
import json
from urllib.parse import parse_qs, urlparse, unquote

# Configuration
GENMAIL_FILE = "genmail.txt"  # File containing email:password pairs
OUTPUT_FILE = "successhotmail.txt"  # Output file for successful accounts with tokens

def wait_for_page_load(driver, timeout=10):
    """Wait for page to complete loading"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def read_genmail(filename):
    """Read email:password pairs from genmail.txt"""
    try:
        with open(filename, 'r') as f:
            accounts = []
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    email, password = line.split(':', 1)
                    accounts.append({
                        'email': email.strip(),
                        'password': password.strip()
                    })
        return accounts
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []

def save_account_tokens(email, password, client_id, access_token, refresh_token):
    """Save account with tokens to output file"""
    try:
        with open(OUTPUT_FILE, 'a') as f:
            line = f"{email}|{password}|{refresh_token}|{client_id}\n"
            f.write(line)
        print(f"✓ Saved {email} with tokens to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving to {OUTPUT_FILE}: {e}")

def extract_tokens_from_url(url):
    """Extract tokens from redirect URL"""
    tokens = {}
    try:
        # Parse fragment (after #)
        if '#' in url:
            fragment = url.split('#')[1]
            params = parse_qs(fragment)

            if 'access_token' in params:
                tokens['access_token'] = params['access_token'][0]
            if 'refresh_token' in params:
                tokens['refresh_token'] = params['refresh_token'][0]
            if 'id_token' in params:
                tokens['id_token'] = params['id_token'][0]

        # Parse query string (after ?)
        if '?' in url:
            query = url.split('?')[1].split('#')[0]  # Get query before fragment
            params = parse_qs(query)

            if 'code' in params:
                tokens['code'] = params['code'][0]

    except Exception as e:
        print(f"Error extracting tokens: {e}")

    return tokens

def extract_client_id_from_url(url):
    """Extract client_id from URL"""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'client_id' in params:
            return params['client_id'][0]
    except:
        pass
    return None

def create_hotmail_account(driver, wait, account_data):
    """Create a Hotmail account and grab tokens"""
    print(f"\n{'='*60}")
    print(f"Processing: {account_data['email']}")
    print(f"{'='*60}")

    # Store captured tokens from network
    captured_tokens = {
        'access_token': None,
        'refresh_token': None,
        'id_token': None,
        'code': None
    }

    # Enable Chrome DevTools Protocol to capture network requests
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        print("✓ Network monitoring enabled")
    except Exception as e:
        print(f"Note: Could not enable network monitoring: {e}")

    # Step 1: Navigate to Microsoft account creation page
    try:
        start_url = "https://go.microsoft.com/fwlink/p/?LinkID=2125442&deeplink=mail%2F0%2F"
        driver.get(start_url)
        wait_for_page_load(driver)
        print(f"✓ Opened Microsoft account page")
        time.sleep(2)
    except Exception as e:
        print(f"Error loading page: {e}")
        return False

    # Step 2: Click "Create one!" link
    try:
        print("\nStep 1: Looking for 'Create one!' link...")
        create_link = wait.until(EC.element_to_be_clickable((By.ID, "signup")))

        # Extract client_id from the href
        href = create_link.get_attribute('href')
        client_id = extract_client_id_from_url(href)
        if client_id:
            print(f"✓ Extracted client_id: {client_id}")

        create_link.click()
        print("✓ Clicked 'Create one!' link")
        time.sleep(2)
    except Exception as e:
        print(f"Error clicking 'Create one!' link: {e}")
        return False

    # Step 3: Click domain dropdown to ensure @hotmail.com is selected
    try:
        print("\nStep 2: Clicking domain dropdown...")
        dropdown_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[name='domainDropdownName']")
        ))
        dropdown_button.click()
        print("✓ Clicked domain dropdown")
        time.sleep(1)

        # Click @hotmail.com option if visible
        try:
            hotmail_option = driver.find_element(By.XPATH, "//div[@role='option']//span[contains(text(), 'hotmail.com')]")
            hotmail_option.click()
            print("✓ Selected @hotmail.com")
        except:
            print("✓ @hotmail.com already selected")

        time.sleep(1)
    except Exception as e:
        print(f"Note: Domain dropdown handling: {e}")

    # Step 4: Enter email
    try:
        print("\nStep 3: Entering email...")
        # Extract username from email (before @)
        username = account_data['email'].split('@')[0]

        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email'][name='New email']")
        ))
        email_input.clear()
        email_input.send_keys(username)
        print(f"✓ Entered username: {username}")
        time.sleep(1)
    except Exception as e:
        print(f"Error entering email: {e}")
        return False

    # Step 5: Click Next button
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            print(f"\nStep 4 (Attempt {attempt + 1}): Clicking Next button...")
            next_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[type='submit'][data-testid='primaryButton']")
            ))
            next_button.click()
            print("✓ Clicked Next button")
            time.sleep(3)

            # Check for "username already taken" error
            try:
                error_element = driver.find_element(By.CSS_SELECTOR, "div.fui-Field__validationMessage[role='alert']")
                error_text = error_element.text

                if "already taken" in error_text.lower():
                    print(f"✗ Username already taken: {username}")

                    if attempt < max_attempts - 1:
                        # Try adding random numbers
                        username = f"{username}{random.randint(100, 999)}"
                        print(f"Trying new username: {username}")

                        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email'][name='New email']")
                        email_input.clear()
                        email_input.send_keys(username)
                        time.sleep(1)
                        continue
                    else:
                        print("✗ Failed after all attempts")
                        return False
            except:
                # No error, proceed
                print("✓ Username accepted!")
                account_data['final_email'] = f"{username}@hotmail.com"
                break

        except Exception as e:
            print(f"Error clicking Next: {e}")
            if attempt < max_attempts - 1:
                continue
            return False

    # Step 6: Enter password
    try:
        print("\nStep 5: Entering password...")
        password_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password'][autocomplete='new-password']")
        ))
        password_input.clear()
        password_input.send_keys(account_data['password'])
        print(f"✓ Entered password")
        time.sleep(1)
    except Exception as e:
        print(f"Error entering password: {e}")
        return False

    # Step 7: Click Next button
    try:
        print("\nStep 6: Clicking Next button...")
        next_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[type='submit'][data-testid='primaryButton']")
        ))
        next_button.click()
        print("✓ Clicked Next button")
        time.sleep(2)
    except Exception as e:
        print(f"Error clicking Next: {e}")
        return False

    # Step 8: Select birth month
    try:
        print("\nStep 7: Selecting birth month...")

        # Find and click element containing "Month"
        month_element = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Month')]")
        ))
        month_element.click()
        print("✓ Clicked 'Month' element")
        time.sleep(1)

        # Find and click "May"
        may_element = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[text()='May']")
        ))
        may_element.click()
        print("✓ Selected month: May")
        time.sleep(1)
    except Exception as e:
        print(f"Error selecting month: {e}")

    # Step 9: Select birth day
    try:
        print("\nStep 8: Selecting birth day...")

        # Find and click element containing "Day"
        day_element = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Day')]")
        ))
        day_element.click()
        print("✓ Clicked 'Day' element")
        time.sleep(1)

        # Find and click "5"
        day_5_element = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[text()='5']")
        ))
        day_5_element.click()
        print("✓ Selected day: 5")
        time.sleep(1)
    except Exception as e:
        print(f"Error selecting day: {e}")

    # Step 10: Enter birth year (2000)
    try:
        print("\nStep 9: Entering birth year (2000)...")
        year_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='number'][name='BirthYear']")
        ))
        year_input.clear()
        year_input.send_keys("2000")
        print(f"✓ Entered birth year: 2000")
        time.sleep(1)
    except Exception as e:
        print(f"Error entering year: {e}")

    # Step 11: Click Next button
    try:
        print("\nStep 10: Clicking Next button...")
        next_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[type='submit'][data-testid='primaryButton']")
        ))
        next_button.click()
        print("✓ Clicked Next button")
        time.sleep(3)
    except Exception as e:
        print(f"Error clicking Next: {e}")
        return False

    # Step 12: Enter First Name and Last Name (if prompted)
    try:
        print("\nStep 11: Checking for name fields...")

        # Get the final email username
        final_email = account_data.get('final_email', account_data['email'])
        username = final_email.split('@')[0]

        # Calculate first name (first 5 letters) and last name (last 6 letters)
        first_name = username[:5] if len(username) >= 5 else username
        last_name = username[-6:] if len(username) >= 6 else username

        name_fields_found = False

        # Try to find and fill first name
        try:
            first_name_input = driver.find_element(By.CSS_SELECTOR, "input[id='firstNameInput']")
            first_name_input.clear()
            first_name_input.send_keys(first_name.capitalize())
            print(f"✓ Entered first name: {first_name.capitalize()}")
            name_fields_found = True
            time.sleep(0.5)
        except:
            print("Note: First name field not found (may not be required)")

        # Try to find and fill last name
        try:
            last_name_input = driver.find_element(By.CSS_SELECTOR, "input[id='lastNameInput']")
            last_name_input.clear()
            last_name_input.send_keys(last_name.capitalize())
            print(f"✓ Entered last name: {last_name.capitalize()}")
            name_fields_found = True
            time.sleep(0.5)
        except:
            print("Note: Last name field not found (may not be required)")

        # Click Next button after entering names
        if name_fields_found:
            try:
                print("\nStep 12: Finding and clicking Next button...")
                next_button = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[type='submit'][data-testid='primaryButton']")
                ))
                next_button.click()
                print("✓ Clicked Next button after entering names")
                time.sleep(3)
            except Exception as e:
                print(f"⚠ Could not click Next after names: {e}")

    except Exception as e:
        print(f"Note: Name fields handling: {e}")

    # Step 13: Monitor for redirect to Outlook mail and capture tokens
    print("\n✓ Account creation in progress...")
    print("Waiting for redirect to Outlook mail...")
    print("Monitoring network traffic for tokens...")
    print("Target: https://outlook.live.com/mail/0/")

    # Wait and check URL for redirect
    start_time = time.time()
    max_wait = 180  # 3 minutes
    account_created = False

    while time.time() - start_time < max_wait:
        try:
            current_url = driver.current_url
            elapsed = time.time() - start_time

            # Print progress every 10 seconds
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"⏳ Waiting for redirect... ({int(elapsed)}s elapsed)")
                print(f"   Current URL: {current_url[:80]}...")

            # Try to capture tokens from localStorage/sessionStorage
            try:
                # Check localStorage
                local_storage = driver.execute_script("return window.localStorage;")
                for key, value in local_storage.items():
                    if 'token' in key.lower() or 'refresh' in key.lower():
                        try:
                            token_data = json.loads(value)
                            if isinstance(token_data, dict):
                                if 'refresh_token' in token_data and not captured_tokens['refresh_token']:
                                    captured_tokens['refresh_token'] = token_data['refresh_token']
                                    print(f"✓ Found refresh_token in localStorage")
                                if 'access_token' in token_data and not captured_tokens['access_token']:
                                    captured_tokens['access_token'] = token_data['access_token']
                                    print(f"✓ Found access_token in localStorage")
                        except:
                            pass

                # Check sessionStorage
                session_storage = driver.execute_script("return window.sessionStorage;")
                for key, value in session_storage.items():
                    if 'token' in key.lower() or 'refresh' in key.lower():
                        try:
                            token_data = json.loads(value)
                            if isinstance(token_data, dict):
                                if 'refresh_token' in token_data and not captured_tokens['refresh_token']:
                                    captured_tokens['refresh_token'] = token_data['refresh_token']
                                    print(f"✓ Found refresh_token in sessionStorage")
                                if 'access_token' in token_data and not captured_tokens['access_token']:
                                    captured_tokens['access_token'] = token_data['access_token']
                                    print(f"✓ Found access_token in sessionStorage")
                        except:
                            pass
            except Exception as e:
                pass

            # Check if redirected to Outlook mail (account creation complete)
            if 'outlook.live.com/mail' in current_url:
                print(f"\n✓ Redirected to Outlook mail!")
                print(f"✓ Account created successfully!")
                print(f"Final URL: {current_url}")

                # Check for tokens in URL
                url_tokens = extract_tokens_from_url(current_url)
                if url_tokens:
                    print(f"✓ Tokens found in URL: {url_tokens}")
                    for key, value in url_tokens.items():
                        if value and not captured_tokens.get(key):
                            captured_tokens[key] = value

                # Try to get tokens from cookies
                try:
                    cookies = driver.get_cookies()
                    for cookie in cookies:
                        cookie_name = cookie.get('name', '').lower()
                        if 'token' in cookie_name or 'refresh' in cookie_name:
                            print(f"✓ Found token in cookie: {cookie['name']}")
                except:
                    pass

                # Save account with tokens and client_id
                if client_id:
                    access_token = captured_tokens.get('access_token', '') or captured_tokens.get('code', '')
                    refresh_token = captured_tokens.get('refresh_token', '')

                    print(f"\nCapturing tokens:")
                    print(f"  Client ID: {client_id}")
                    print(f"  Access Token: {'✓' if access_token else '✗'}")
                    print(f"  Refresh Token: {'✓' if refresh_token else '✗'}")

                    save_account_tokens(
                        account_data.get('final_email', account_data['email']),
                        account_data['password'],
                        client_id,
                        access_token,
                        refresh_token
                    )
                    account_created = True
                    break
                else:
                    print("⚠ No client_id found")

            # Also check for tokens in URL even before full redirect
            if 'access_token' in current_url or 'code=' in current_url or '#' in current_url:
                url_tokens = extract_tokens_from_url(current_url)
                if url_tokens:
                    print(f"\n✓ Tokens found in URL!")
                    for key, value in url_tokens.items():
                        if value and not captured_tokens.get(key):
                            captured_tokens[key] = value
                            print(f"✓ Captured {key}")

                    # If we have enough tokens and we're close to outlook, save
                    if 'outlook' in current_url.lower() or 'login.live.com' in current_url:
                        if client_id and captured_tokens.get('access_token'):
                            access_token = captured_tokens.get('access_token', '') or captured_tokens.get('code', '')
                            refresh_token = captured_tokens.get('refresh_token', '')

                            save_account_tokens(
                                account_data.get('final_email', account_data['email']),
                                account_data['password'],
                                client_id,
                                access_token,
                                refresh_token
                            )
                            account_created = True
                            # Continue monitoring for complete redirect

            time.sleep(2)

        except Exception as e:
            print(f"⚠ Error monitoring: {e}")
            time.sleep(2)

    if account_created:
        print("\n✓ Account created and saved successfully!")
        return True
    else:
        print(f"\n⚠ Timeout waiting for redirect after {max_wait}s")
        print(f"Last URL: {driver.current_url}")

        # Last attempt: save what we have
        if client_id and (captured_tokens.get('access_token') or captured_tokens.get('code')):
            print("Attempting to save partial data...")
            save_account_tokens(
                account_data.get('final_email', account_data['email']),
                account_data['password'],
                client_id,
                captured_tokens.get('access_token', '') or captured_tokens.get('code', ''),
                captured_tokens.get('refresh_token', '')
            )
            return True

        return False

def main():
    """Main function"""
    # Read accounts from genmail.txt
    accounts = read_genmail(GENMAIL_FILE)
    if not accounts:
        print(f"No accounts found in {GENMAIL_FILE}")
        print(f"Please create {GENMAIL_FILE} with format: email:password (one per line)")
        return

    print(f"\n{'='*60}")
    print(f"HOTMAIL TOKEN GRABBER")
    print(f"{'='*60}")
    print(f"Total accounts to process: {len(accounts)}")
    print(f"{'='*60}\n")

    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Uncomment for headless mode

    # Set window size
    window_width = 780
    window_height = 700

    success_count = 0
    failed_count = 0

    for index, account_data in enumerate(accounts, 1):
        driver = None
        try:
            print(f"\n{'='*60}")
            print(f"PROCESSING ACCOUNT {index}/{len(accounts)}")
            print(f"{'='*60}\n")

            # Initialize browser
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 10)

            # Set window size and position
            driver.set_window_size(window_width, window_height)
            driver.set_window_position(0, 0)

            # Process account
            success = create_hotmail_account(driver, wait, account_data)

            if success:
                success_count += 1
                print(f"\n✓ SUCCESS: {account_data['email']}")
            else:
                failed_count += 1
                print(f"\n✗ FAILED: {account_data['email']}")

            # Close browser
            driver.quit()

            # Delay before next account
            if index < len(accounts):
                print(f"\nWaiting 3 seconds before next account...")
                time.sleep(3)

        except Exception as e:
            failed_count += 1
            print(f"\n✗ ERROR processing {account_data['email']}: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    # Final summary
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total accounts: {len(accounts)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
