from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User,UserRole

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "salutation", "first_name", "middle_name", "last_name",
            "phone_number", "email", "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["is_active"] = True  
        validated_data["role"] = UserRole.BASE_USER  
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs["username"]
        password = attrs["password"]

        user = (
            User.objects.filter(email=username).first()
            or User.objects.filter(phone_number=username).first()
        )

        if not user or not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid credentials"
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "User account is inactive"
            )

        if not user.email_verified and not user.phone_verified:
            raise serializers.ValidationError(
                "Please verify your email or phone number first."
            )

        attrs["user"] = user
        return attrs
    
class OTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        phone = attrs.get("phone_number")
        email = attrs.get("email")

        if not phone and not email:
            raise serializers.ValidationError(
                "Provide either phone_number or email."
            )

        if phone and email:
            raise serializers.ValidationError(
                "Provide only one of phone_number or email."
            )

        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "salutation", "first_name", "middle_name", "last_name",
            "phone_number", "email", "role", "phone_verified", "email_verified",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "phone_verified", "email_verified", "created_at"]

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role"]

class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    @classmethod
    def get_tokens(cls, user):
        refresh = RefreshToken.for_user(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}
