#!/usr/bin/env python3
"""
OTP Email Reader - Continuous Loop Version
Reads emails continuously and extracts OTP codes every 500ms
Press Ctrl+C to exit
"""

import imaplib
import email as email_module
import socket
import re
import time

IMAP_SERVER = "mail.coaco.space"
EMAIL = ""
PASSWORD = ""
# Alternative: Set credential string in format "email|password" or "email:password"
CREDENTIAL_STRING = "testuser3@coaco.space|alonso370"
POLL_INTERVAL = 0.5  # 500ms

# Parse credentials if EMAIL and PASSWORD are blank
if not EMAIL or not PASSWORD:
    if CREDENTIAL_STRING:
        # Try pipe separator first
        if "|" in CREDENTIAL_STRING:
            EMAIL, PASSWORD = CREDENTIAL_STRING.split("|", 1)
        # Try colon separator
        elif ":" in CREDENTIAL_STRING:
            EMAIL, PASSWORD = CREDENTIAL_STRING.split(":", 1)
        else:
            print("✗ Invalid credential format. Use 'email|password' or 'email:password'")
            exit(1)

        EMAIL = EMAIL.strip()
        PASSWORD = PASSWORD.strip()
        print(f"Parsed credentials: {EMAIL}")
    else:
        print("✗ No credentials provided. Set EMAIL/PASSWORD or CREDENTIAL_STRING")
        exit(1)


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
        r'\b(\d{5})\b',               # Any standalone 5-digit number
        r'\b(\d{4})\b',               # Any standalone 4-digit number
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def read_otp():
    """Read OTP from latest email"""
    try:
        # Try SSL connection
        try:
            sock = socket.create_connection((IMAP_SERVER, 993), timeout=5)
            sock.close()
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        except:
            # Fallback to STARTTLS
            mail = imaplib.IMAP4(IMAP_SERVER, 143)
            mail.starttls()

        # Login
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")

        # Read latest email
        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()

        if not mail_ids:
            return None, None, None, None

        last_email = mail_ids[-1]
        status, msg_data = mail.fetch(last_email, "(RFC822)")
        msg = email_module.message_from_bytes(msg_data[0][1])

        # Extract OTP from subject first
        subject = msg["Subject"] or ""
        from_addr = msg["From"] or ""
        date = msg["Date"] or ""
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

        return otp_code, from_addr, subject, date

    except Exception as e:
        return None, None, None, str(e)


print(f"\n{'='*60}")
print(f"OTP READER - CONTINUOUS MODE")
print(f"{'='*60}")
print(f"Email: {EMAIL}")
print(f"Poll interval: {POLL_INTERVAL}s (500ms)")
print(f"Press Ctrl+C to exit")
print(f"{'='*60}\n")

last_otp = None
attempt = 0

try:
    while True:
        attempt += 1
        otp_code, from_addr, subject, date = read_otp()

        if otp_code:
            # Only display if it's a new OTP (different from last one)
            if otp_code != last_otp:
                print(f"\n[Attempt {attempt}] ✓ NEW OTP FOUND!")
                print("="*60)
                print(f"OTP: {otp_code}")
                print(f"From: {from_addr}")
                print(f"Subject: {subject}")
                print(f"Date: {date}")
                print("="*60)
                last_otp = otp_code
            else:
                # Same OTP as before
                print(f"[Attempt {attempt}] Same OTP: {otp_code}", end="\r")
        else:
            # No OTP found
            print(f"[Attempt {attempt}] No OTP found...", end="\r")

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print(f"\n\n{'='*60}")
    print("Stopped by user (Ctrl+C)")
    print(f"{'='*60}")
    if last_otp:
        print(f"Last OTP found: {last_otp}")
    print("Exiting...")
