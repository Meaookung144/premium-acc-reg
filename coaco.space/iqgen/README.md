# iQiyi Registration Bot - Coaco.space Version

This version is specifically designed to work with **coaco.space** email accounts and integrates IMAP-based OTP reading.

## Key Differences from Original

### 1. **Email Format**
- **Original**: `email|password|refresh_token|client_id`
- **This version**: `email|password`

Simply put your coaco.space email credentials in `emails.txt`.

### 2. **OTP Method**
- **Original**: Uses read-mail.me API with refresh tokens
- **This version**: Connects directly to `mail.coaco.space` via IMAP to read OTP emails

### 3. **OTP Polling Speed**
- **Original**: Polls every 6 seconds
- **This version**: Polls every **500ms** (0.5 seconds) for faster OTP detection

### 4. **Navigation**
- **Original**: Goes to iq.com → clicks login → clicks sign up
- **This version**: Goes directly to `iq.com/login` → clicks register

### 5. **Subscription Cancellation Speed**
- **Original**: Waits 1 second after loading autorenew page
- **This version**: Waits only **0.1 seconds** for quicker cancellation

### 6. **Window Sizing**
- **Both versions**: Fixed 780x600 pixels per browser window
- Positioned side-by-side for parallel processing

### 7. **File Management**
- Automatically moves completed accounts from `emails.txt` to `success.txt`
- Uses local files in this directory (not root directory)

## Setup

1. Create email accounts using `../generatemail.py`
2. Add credentials to `emails.txt` in format: `email|password`

Example `emails.txt`:
```
testuser1@coaco.space|alonso370
testuser2@coaco.space|alonso370
testuser3@coaco.space|alonso370
```

## Usage

```bash
cd /Users/meaookung144/Documents/GitHub/premium-acc-reg/coaco.space/iqgen
python3 open_iq_parallel_coaco.py
```

## How It Works

1. **Read Emails**: Loads all email/password pairs from `emails.txt`
2. **Parallel Processing**: Opens 2 browsers simultaneously
3. **Registration**:
   - Goes to iq.com/login → Register
   - Fills in email, password, birthdate
   - Submits form
4. **OTP Verification**:
   - Connects to `mail.coaco.space` via IMAP
   - Polls every 500ms for new OTP email
   - Extracts OTP code from subject/body
   - Auto-enters and verifies
5. **VIP Subscription**:
   - Selects Monthly plan (฿49)
   - Chooses Rabbit Line Pay
   - Opens payment tab (manual payment required)
6. **Auto-Cancel**:
   - After payment, navigates to autorenew page
   - Cancels subscription immediately
7. **Save Success**:
   - Moves completed email to `success.txt`
   - Removes from `emails.txt`

## Window Sizing

- Each browser window is **780x600** pixels
- Positioned side-by-side (Thread 0 at x=0, Thread 1 at x=780)
- Same sizing as original version for consistency

## Configuration

Edit these variables in the script:

```python
PASSWORD = "alonso370"  # iQiyi account password
NUM_PARALLEL_BROWSERS = 2  # Number of parallel browsers
IMAP_SERVER = "mail.coaco.space"
OTP_POLL_INTERVAL = 0.5  # Poll every 500ms
```

## Troubleshooting

### OTP Not Found
- Check that email is actually created in coaco.space
- Verify IMAP access works: `python3 ../otpread.py`
- Check email password is correct

### IMAP Connection Failed
- Ensure `mail.coaco.space` port 993 (SSL) or 143 (STARTTLS) is accessible
- Check firewall settings

### Payment Issues
- Payment tab opens automatically - complete it manually
- Script waits for redirect to `iq.com/vip/payResult`
- Max wait time: 10 minutes

## Files

- `open_iq_parallel_coaco.py` - Main script
- `emails.txt` - Input file (email|password format)
- `success.txt` - Completed accounts
- `README.md` - This file
