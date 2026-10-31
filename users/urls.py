from django.urls import path
from .views import (
    UserRegistrationView,
    SendEmailOTPView,
    VerifyEmailOTPView,
    SendPhoneOTPView,
    VerifyPhoneOTPView,
)

urlpatterns = [
    path("users/register/", UserRegistrationView.as_view(), name="register"),
    path("users/email-otp/send/", SendEmailOTPView.as_view(), name="send-email-otp"),
    path("users/email-otp/verify/", VerifyEmailOTPView.as_view(), name="verify-email-otp"),
    path(
    "users/phone-otp/send/",
    SendPhoneOTPView.as_view(),
    name="send-phone-otp",
),
    path(
    "users/phone-otp/verify/",
    VerifyPhoneOTPView.as_view(),
    name="verify-phone-otp",
),
]