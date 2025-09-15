# AfroMessage Python SDK

A complete Python SDK for the AfroMessage SMS and OTP API.

## Installation

```bash
pip install afromessage
```

# Quick Start

```bash
from afromessage import AfroMessage

# Initialize with your API token
sdk = AfroMessage(token="your_api_token_here")

# Send an SMS
response = sdk.sms.send(
    to="+yourNumber",
    message="Hello from AfroMessage!",
    from_="your_sender_id",
    sender="YourBrand"
)

# Create OTP challenge
otp_response = sdk.challenge.challenge(
    to="+yourNumber", 
    pr="Your code is",
    len_=6
)

# Verify OTP
verify_response = sdk.challenge.verify(
    to="+yourNumber",
    code="123456"
)
```
Features
✅ Single SMS sending

✅ Bulk SMS campaigns

✅ OTP challenge generation

✅ OTP verification

✅ Comprehensive error handling

✅ Request/response logging