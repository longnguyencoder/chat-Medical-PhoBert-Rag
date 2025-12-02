"""
Test Verify với OTP từ log
===========================
"""

import requests

BASE_URL = "http://localhost:5000/api/auth"

email = "test_user_9348@example.com"
otp_code = "780811"

print(f"\nVerifying OTP:")
print(f"Email: {email}")
print(f"OTP: {otp_code}")

resp = requests.post(
    f"{BASE_URL}/verify-otp",
    json={
        "email": email,
        "otp_code": otp_code,
        "purpose": "register"
    }
)

print(f"\nStatus: {resp.status_code}")
print(f"Response: {resp.json()}")
