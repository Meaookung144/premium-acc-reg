import imaplib
import email
import socket

IMAP_SERVER = "mail.coaco.space"
EMAIL = ""
PASSWORD = ""
# Alternative: Set credential string in format "email|password" or "email:password"
CREDENTIAL_STRING = "welmon23@coaco.space|alonso370"

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

print(f"Attempting to connect to {IMAP_SERVER}:993...")

try:
    # Test basic connectivity first
    sock = socket.create_connection((IMAP_SERVER, 993), timeout=10)
    sock.close()
    print("✓ Basic connection successful")
except Exception as e:
    print(f"✗ Basic connection failed: {e}")
    print("\nTrying alternative ports and methods...")

    # Try port 143 with STARTTLS
    try:
        print(f"\nTrying IMAP on port 143 (STARTTLS)...")
        mail = imaplib.IMAP4(IMAP_SERVER, 143)
        mail.starttls()
        mail.login(EMAIL, PASSWORD)
        print("✓ Connected via port 143 with STARTTLS")
    except Exception as e2:
        print(f"✗ Port 143 failed: {e2}")
        print("\nPlease check:")
        print("1. Is the IMAP server address correct?")
        print("2. Is IMAP enabled on your email account?")
        print("3. Are you behind a firewall blocking IMAP ports?")
        exit(1)
else:
    # Original SSL connection
    try:
        print(f"Connecting to {IMAP_SERVER} via SSL...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(EMAIL, PASSWORD)
        print("✓ Login successful")
    except Exception as e:
        print(f"✗ SSL connection or login failed: {e}")
        exit(1)

try:
    mail.select("INBOX")
    print("✓ Selected INBOX")

    # Read latest email
    status, messages = mail.search(None, "ALL")
    mail_ids = messages[0].split()

    if not mail_ids:
        print("No emails found in inbox")
        exit(0)

    last_email = mail_ids[-1]
    status, msg_data = mail.fetch(last_email, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    print("\n" + "="*60)
    print("From:", msg["From"])
    print("Subject:", msg["Subject"])
    print("="*60)
    print("------ Body ------")
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            print(part.get_payload(decode=True).decode())
        elif part.get_content_type() == "text/html":
            print("[HTML content]")

    mail.close()
    mail.logout()
    print("\n✓ Done")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
