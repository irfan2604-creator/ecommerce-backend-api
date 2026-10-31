from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import UserProfile

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    phone_number = serializers.CharField(max_length=16, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_phone_number(self, value):
        if not value.startswith("+"):
            raise serializers.ValidationError(
                "Enter the phone number with its country code, e.g. +919876543210."
            )

        if UserProfile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "An account with this phone number already exists."
            )
        return value

    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number")
        print("Serializer received phone:", repr(phone_number))
        user = User.objects.create_user(**validated_data)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = phone_number
        profile.email_verified = False
        profile.phone_verified = False
        profile.save()
        profile.refresh_from_db()
        print("Database saved phone:", repr(profile.phone_number))

        return user


class EmailOTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain exactly 6 digits."
            )
        return value
class SendPhoneOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyPhoneOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10, min_length=4)
    
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        profile = self.user.profile

        if not profile.email_verified:
            raise AuthenticationFailed("Please verify your email before logging in.")

        if not profile.phone_verified:
            raise AuthenticationFailed("Please verify your phone number before logging in.")

        return data