# views.py

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    OTPVerifySerializer,
    UserSerializer,
    UserRoleUpdateSerializer,
    LoginSerializer
)
from .models import User
from .permissions import IsModerator, IsSuperAdmin
from .utils import (
    generate_otp,
    set_otp,
    get_otp,
    delete_otp,
    phone_otp_key,
    email_otp_key,
)

class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]

    
    @action(
        detail=False,
        methods=["post"],
        serializer_class=LoginSerializer,
    )
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
        )
    @action(
        detail=False,
        methods=["post"],
        serializer_class=RegisterSerializer,
    )
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        phone_otp = "000000"
        email_otp = "000000"

        set_otp(phone_otp_key(user.phone_number), phone_otp)
        set_otp(email_otp_key(user.email), email_otp)

        return Response(
            {
                "message": "Registration successful. OTP sent.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["post"],
        serializer_class=OTPVerifySerializer,
        url_path="verify-otp",
    )
    def verify_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if data.get("phone_number"):
            key = phone_otp_key(data["phone_number"])
            user = User.objects.filter(
                phone_number=data["phone_number"]
            ).first()
            verify_field = "phone_verified"

        else:
            key = email_otp_key(data["email"])
            user = User.objects.filter(
                email=data["email"]
            ).first()
            verify_field = "email_verified"

        if not user:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        saved_otp = get_otp(key)

        if saved_otp != data["otp"]:
            return Response(
                {"message": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        setattr(user, verify_field, True)
        user.save(update_fields=[verify_field])

        delete_otp(key)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": f"{verify_field} verified successfully",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="resend-otp",
    )
    def resend_otp(self, request):
        phone = request.data.get("phone_number")
        email = request.data.get("email")

        if not phone and not email:
            return Response(
                {"message": "phone_number or email required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if phone and email:
            return Response(
                {"message": "Provide only one field"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if phone:
            user = User.objects.filter(
                phone_number=phone
            ).first()

            if not user:
                return Response(
                    {"message": "User not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            otp = "000000"  # testing
            set_otp(phone_otp_key(phone), otp)

        else:
            user = User.objects.filter(
                email=email
            ).first()

            if not user:
                return Response(
                    {"message": "User not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            otp = "000000"  # testing
            set_otp(email_otp_key(email), otp)

        return Response(
            {
                "message": "OTP resent successfully",
            }
        )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == "me":
            return [IsAuthenticated()]

        if self.action in ["list", "retrieve"]:
            return [IsModerator()]

        if self.action in ["update_role", "deactivate"]:
            return [IsSuperAdmin()]

        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "update_role":
            return UserRoleUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        if request.method == "GET":
            return Response(UserSerializer(request.user).data)

        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="role")
    def update_role(self, request, pk=None):
        user = self.get_object()

        serializer = UserRoleUpdateSerializer(
            user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=["delete"])
    def deactivate(self, request, pk=None):
        user = self.get_object()

        user.is_active = False
        user.save(update_fields=["is_active"])

        return Response(
            {"message": "User deactivated successfully"}
        )
