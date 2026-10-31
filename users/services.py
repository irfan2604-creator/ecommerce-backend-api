import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP

import os
from twilio.rest import Client
from django.conf import settings


def generate_email_otp(user):
    # Invalidate previous OTPs for this user.
    EmailOTP.objects.filter(user=user).delete()

    # Generate a secure six-digit OTP.
    code = f"{secrets.randbelow(1_000_000):06d}"

    # Set the expiry time to five minutes.
    expires_at = timezone.now() + timedelta(minutes=5)

    otp = EmailOTP.objects.create(
        user=user,
        code=code,
        expires_at=expires_at,
    )

    send_mail(
        subject="Your Email Verification OTP",
        message=(
            f"Your verification OTP is {code}.\n"
            "It expires in 5 minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return otp
def send_phone_otp(phone_number):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )

    verification = client.verify.v2.services(
        settings.TWILIO_VERIFY_SERVICE_SID
    ).verifications.create(
        to=phone_number,
        channel="sms",
    )

    return verification.status

def verify_phone_otp(phone_number, code):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )

    verification_check = client.verify.v2.services(
        settings.TWILIO_VERIFY_SERVICE_SID
    ).verification_checks.create(
        to=phone_number,
        code=code,
    )

    return verification_check.status