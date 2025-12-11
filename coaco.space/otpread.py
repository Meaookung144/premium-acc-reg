#!/usr/bin/env python3
"""
OTP Email Reader
Reads the latest email and extracts OTP code from subject or body
"""

import imaplib
import email
import socket
import re

IMAP_SERVER = "mail.coaco.space"
EMAIL = ""
PASSWORD = ""
# Alternative: Set credential string in format "email|password" or "email:password"
CREDENTIAL_STRING = "xarvin24@coaco.space|alonso370"

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


try:
    # Test basic connectivity first
    sock = socket.create_connection((IMAP_SERVER, 993), timeout=10)
    sock.close()
except Exception as e:
    # Try port 143 with STARTTLS
    try:
        mail = imaplib.IMAP4(IMAP_SERVER, 143)
        mail.starttls()
        mail.login(EMAIL, PASSWORD)
    except Exception as e2:
        print(f"✗ Connection failed: {e2}")
        exit(1)
else:
    # Original SSL connection
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(EMAIL, PASSWORD)
    except Exception as e:
        print(f"✗ SSL connection or login failed: {e}")
        exit(1)

try:
    mail.select("INBOX")

    # Read latest email
    status, messages = mail.search(None, "ALL")
    mail_ids = messages[0].split()

    if not mail_ids:
        print("No emails found in inbox")
        exit(0)

    last_email = mail_ids[-1]
    status, msg_data = mail.fetch(last_email, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

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

    # Print OTP on first line
    if otp_code:
        print(otp_code)
    else:
        print("NO_OTP_FOUND")

    # Print email details
    print("=" * 60)
    print("From:", from_addr)
    print("Subject:", subject)
    print("Date:", date)
    print("=" * 60)
    print("------ Body ------")
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            print(part.get_payload(decode=True).decode())
        elif part.get_content_type() == "text/html":
            print("[HTML content]")

    mail.close()
    mail.logout()

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
