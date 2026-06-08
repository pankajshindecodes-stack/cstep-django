from rest_framework import serializers
from .models import Registration


class RegistrationSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Registration
        fields = [
            "id",
            "user",
            "event",
            "participation_date",
            "participation_time",
            "food_preference",

            # Travel
            "travel_arrangement",
            "travel_status",

            # Medical
            "medical_support",

            # Translation
            "translation_language",
            "translation_status",

            # Registration
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "travel_status",
            "translation_status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        """
        Automatically set statuses when requests are submitted.
        """

        if attrs.get("travel_arrangement"):
            attrs.setdefault(
                "travel_status",
                Registration.ApprovalStatus.PENDING
                if hasattr(Registration, "ApprovalStatus")
                else "PENDING"
            )

        if attrs.get("translation_language"):
            attrs.setdefault(
                "translation_status",
                Registration.ApprovalStatus.PENDING
                if hasattr(Registration, "ApprovalStatus")
                else "PENDING"
            )

        return attrs

class RegistrationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ["status"]


class TravelStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ["travel_status"]


class TranslationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ["translation_status"]

class LobbyRegistrationSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )
    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = Registration
        fields = [
            "id",
            "user_id",
            "user_name",
            "phone_number",
            "email",

            "participation_date",
            "participation_time",
            "food_preference",

            "travel_arrangement",
            "travel_status",

            "medical_support",

            "translation_language",
            "translation_status",

            "status",
        ]

    def get_user_name(self, obj):
        return (
            f"{obj.user.first_name} {obj.user.last_name}"
        ).strip()