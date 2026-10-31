from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status, serializers
from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework_simplejwt.views import TokenObtainPairView

from drf_spectacular.utils import extend_schema, inline_serializer

from .models import EmailOTP, UserProfile
from .serializers import (
    UserRegistrationSerializer,
    EmailOTPVerificationSerializer,
    SendPhoneOTPSerializer,
    VerifyPhoneOTPSerializer,
    CustomTokenObtainPairSerializer,
)
from .services import (
    generate_email_otp,
    send_phone_otp,
    verify_phone_otp,
)

import logging

logger = logging.getLogger(__name__)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        try:
            generate_email_otp(user)
            phone_status = send_phone_otp(user.profile.phone_number)

        except Exception:
            logger.exception("Registration OTP sending failed")

            user.delete()

            return Response(
                {
                    "detail": (
                        "Registration verification could not be started. "
                        "Please check the server logs."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "detail": (
                    "Registration successful. Verify your email "
                    "and mobile number to complete registration."
                ),
                "email_verification_required": True,
                "phone_verification_status": phone_status,
            },
            status=status.HTTP_201_CREATED,
        )


class SendEmailOTPView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="send_email_otp",
        summary="Send email OTP",
        description="Sends an email verification OTP to the authenticated user.",
        request=None,
        responses={
            200: inline_serializer(
                name="SendEmailOTPResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request):
        if request.user.profile.email_verified:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        generate_email_otp(request.user)

        return Response(
            {"detail": "Verification OTP sent to your email."},
            status=status.HTTP_200_OK,
        )


class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="verify_email_otp",
        summary="Verify email OTP",
        description="Verifies a user's email address using the OTP.",
        request=EmailOTPVerificationSerializer,
        responses={
            200: inline_serializer(
                name="VerifyEmailOTPResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = EmailOTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp_code = serializer.validated_data["otp"]

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            return Response(
                {"detail": "Invalid email or OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = EmailOTP.objects.filter(
            user=user,
            code=otp_code,
        ).order_by("-created_at").first()

        if otp is None:
            return Response(
                {"detail": "Invalid email or OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() >= otp.expires_at:
            otp.delete()
            return Response(
                {"detail": "OTP has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = user.profile
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])

        EmailOTP.objects.filter(user=user).delete()

        return Response(
            {"detail": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )


class SendPhoneOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="send_phone_otp",
        summary="Send phone OTP",
        description="Sends a phone verification OTP to the registered number.",
        request=SendPhoneOTPSerializer,
        responses={
            200: inline_serializer(
                name="SendPhoneOTPResponse",
                fields={
                    "detail": serializers.CharField(),
                    "status": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = SendPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            return Response(
                {"detail": "Invalid email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = user.profile

        if profile.phone_verified:
            return Response(
                {"detail": "Phone number is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not profile.phone_number:
            return Response(
                {"detail": "No phone number is registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_status = send_phone_otp(profile.phone_number)

        return Response(
            {
                "detail": "Phone OTP sent successfully.",
                "status": otp_status,
            },
            status=status.HTTP_200_OK,
        )


class VerifyPhoneOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="verify_phone_otp",
        summary="Verify phone OTP",
        description="Verifies the user's phone number using the OTP.",
        request=VerifyPhoneOTPSerializer,
        responses={
            200: inline_serializer(
                name="VerifyPhoneOTPResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = VerifyPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            return Response(
                {"detail": "Invalid email or OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = user.profile

        if profile.phone_verified:
            return Response(
                {"detail": "Phone number is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not profile.phone_number:
            return Response(
                {"detail": "No phone number is registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification_status = verify_phone_otp(
            profile.phone_number,
            code,
        )

        if verification_status == "approved":
            profile.phone_verified = True
            profile.save(update_fields=["phone_verified"])

            return Response(
                {"detail": "Phone number verified successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Invalid or expired OTP."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

