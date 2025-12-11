# Open IQ Parallel - Proxy & Webmail Configuration Guide

## New Features Added

### 1. Webmail Type Configuration
Choose between two email services for OTP verification:

**Configuration:**
```python
WEBMAIL_TYPE = "hotmail"  # or "pranakorn"
```

**Options:**
- `"pranakorn"` - Uses coaco.space IMAP server
  - Email format: `email|password`
  - Direct IMAP access to mail.coaco.space
  - Faster OTP polling (500ms intervals)
  
- `"hotmail"` - Uses read-mail.me API
  - Email format: `email|password|refresh_token|client_id`
  - API-based OTP fetching
  - 6-second polling intervals

### 2. Proxy Support
Run browsers through proxy servers with automatic rotation.

**Configuration:**
```python
USE_PROXY = True  # Enable proxy support
PROXY_FILE = "proxy.txt"  # Proxy list file
PROXY_TYPE = "http"  # Options: "http", "https", "socks5"
```

**Proxy Formats in proxy.txt:**
```
# Simple proxy (no authentication)
123.45.67.89:8080

# Authenticated proxy
username:password@123.45.67.89:8080
```

**Features:**
- Automatic proxy rotation across browsers
- Support for authenticated and non-authenticated proxies
- Thread-safe proxy queue management
- Chrome extension for authenticated proxy support

## File Formats

### emails.txt (Pranakorn Mode)
```
email@coaco.space|password123
another@coaco.space|password456
```

### emails.txt (Hotmail Mode)
```
user@hotmail.com|pass123|refresh_token_here|client_id_here
another@hotmail.com|pass456|refresh_token2|client_id2
```

### proxy.txt
```
# One proxy per line
123.45.67.89:8080
user:pass@45.67.89.123:3128
socks5://192.168.1.100:1080
```

## Example Configurations

### Configuration 1: Pranakorn emails with proxy
```python
WEBMAIL_TYPE = "pranakorn"
USE_PROXY = True
PROXY_FILE = "proxy.txt"
PROXY_TYPE = "http"
```

### Configuration 2: Hotmail emails without proxy
```python
WEBMAIL_TYPE = "hotmail"
USE_PROXY = False
```

### Configuration 3: Pranakorn with SOCKS5 proxy
```python
WEBMAIL_TYPE = "pranakorn"
USE_PROXY = True
PROXY_TYPE = "socks5"
```

## How It Works

1. **Webmail Selection:**
   - Script automatically uses correct OTP method based on WEBMAIL_TYPE
   - Pranakorn: IMAP-based (faster, direct access)
   - Hotmail: API-based (read-mail.me)

2. **Proxy Rotation:**
   - Each browser thread gets a proxy from the rotation queue
   - After use, proxy is returned to queue for next browser
   - Supports both simple and authenticated proxies

3. **Thread Safety:**
   - Proxy queue uses locks to prevent race conditions
   - Each thread independently manages its Chrome options
   - Clean separation between browser instances

## Troubleshooting

**Issue:** "No proxies loaded"
- Check proxy.txt exists in the same directory
- Verify file is not empty
- Check file format (ip:port or user:pass@ip:port)

**Issue:** Proxy connection fails
- Verify proxy is online and accessible
- Check proxy credentials if using authenticated proxy
- Try different PROXY_TYPE (http/https/socks5)

**Issue:** OTP not received (Pranakorn)
- Verify IMAP_SERVER is correct (mail.coaco.space)
- Check email password is correct
- Ensure IMAP ports (993/143) are not blocked

**Issue:** OTP not received (Hotmail)
- Verify refresh_token and client_id are valid
- Check read-mail.me API is accessible
- Ensure API credentials are current
