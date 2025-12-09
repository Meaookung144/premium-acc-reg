#!/usr/bin/env python3
"""
Batch Email Creation Script
Reads usernames from inpmail.txt and creates email accounts
"""

import requests
import os

# ============================================================================
# CONFIGURATION
# ============================================================================
API_URL = "https://mail.coaco.space/api/v1/user"
API_KEY = "0CLB1PH5U0KE2BXDGYOY5A28VOTYAM7I"
DEFAULT_PASSWORD = "alonso370"
DOMAIN = "coaco.space"
QUOTA = 2048  # MB
# ============================================================================

headers_auth = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def read_usernames_from_file():
    """Read usernames from inpmail.txt"""
    file_path = os.path.join(os.path.dirname(__file__) or ".", "inpmail.txt")

    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return []

    with open(file_path, 'r') as f:
        usernames = [line.strip() for line in f if line.strip()]

    return usernames


def move_to_success(username, password):
    """Move successful email to success.txt and remove from inpmail.txt"""
    base_path = os.path.dirname(__file__) or "."
    inpmail_path = os.path.join(base_path, "inpmail.txt")
    success_path = os.path.join(base_path, "success.txt")

    # Read all usernames from inpmail.txt
    if os.path.exists(inpmail_path):
        with open(inpmail_path, 'r') as f:
            usernames = [line.strip() for line in f if line.strip()]

        # Remove the successful username
        usernames = [u for u in usernames if u != username]

        # Write back to inpmail.txt
        with open(inpmail_path, 'w') as f:
            for u in usernames:
                f.write(f"{u}\n")

    # Append to success.txt
    with open(success_path, 'a') as f:
        f.write(f"{username}@{DOMAIN}|{password}\n")


def create_email(username, password):
    """Create a single email account"""
    data = {
        "email": f"{username}@{DOMAIN}",
        "raw_password": password,
        "quota": QUOTA
    }

    try:
        r = requests.post(API_URL, json=data, headers=headers_auth)

        if r.status_code == 200:
            return True, "Success"
        else:
            return False, r.text
    except Exception as e:
        return False, str(e)


def main():
    """Main function to create batch emails"""
    print("="*60)
    print("Batch Email Creation Script")
    print("="*60)

    # Read usernames from file
    usernames = read_usernames_from_file()

    if not usernames:
        print("✗ No usernames found in inpmail.txt")
        print("\nPlease add usernames (one per line) to inpmail.txt")
        return

    print(f"\nFound {len(usernames)} username(s) to process")
    print(f"Domain: {DOMAIN}")
    print(f"Password: {DEFAULT_PASSWORD}")
    print("="*60)

    successful = 0
    failed = 0

    for i, username in enumerate(usernames, 1):
        print(f"\n[{i}/{len(usernames)}] Processing: {username}")

        success, message = create_email(username, DEFAULT_PASSWORD)

        if success:
            print(f"    ✓ Created: {username}@{DOMAIN}")
            move_to_success(username, DEFAULT_PASSWORD)
            successful += 1
        else:
            print(f"    ✗ Failed: {username}@{DOMAIN}")
            print(f"    Error: {message}")
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Total processed: {len(usernames)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print("="*60)

    if successful > 0:
        print(f"\n✓ Successfully created emails saved to success.txt")
        print(f"✓ Remaining usernames in inpmail.txt: {len(usernames) - successful}")


if __name__ == "__main__":
    main()
