import random

def generate_otp() -> str:
    # Hardcoded OTP for UI testing
    return "123456"

def send_otp(destination: str, otp: str):
    """
    Mock sending OTP. In production, connect to Twilio or SendGrid based on destination.
    """
    print(f"\n{'='*50}")
    print(f"== MOCK OTP DELIVERED TO: {destination} ==")
    print(f"== OTP CODE: {otp} ==")
    print(f"{'='*50}\n")
