from rest_framework import serializers
from .models import Registration, ParticipationDate, ApprovalStatus
from rest_framework.validators import UniqueTogetherValidator


class ParticipationDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipationDate
        fields = ["id", "date"]


class RegistrationSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    participation_dates = ParticipationDateSerializer(many=True)

    class Meta:
        model = Registration
        fields = [
            "id",
            "user",
            "event",
            "participation_dates",
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
        validators = [
            UniqueTogetherValidator(
                queryset=Registration.objects.all(),
                fields=["user", "event"],
                message="You have already registered for this event."
            )
        ]

    def validate_participation_dates(self, value):
        if not value:
            raise serializers.ValidationError("At least one participation date is required.")
        return value

    def validate(self, attrs):
        if attrs.get("travel_arrangement"):
            attrs["travel_status"] = ApprovalStatus.PENDING

        if attrs.get("translation_language"):
            attrs["translation_status"] = ApprovalStatus.PENDING

        return attrs

    def create(self, validated_data):
        dates_data = validated_data.pop("participation_dates")
        registration = Registration.objects.create(**validated_data)
        ParticipationDate.objects.bulk_create([
            ParticipationDate(registration=registration, **d) for d in dates_data
        ])
        return registration

    def update(self, instance, validated_data):
        dates_data = validated_data.pop("participation_dates", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if dates_data is not None:
            instance.participation_dates.all().delete()
            ParticipationDate.objects.bulk_create([
                ParticipationDate(registration=instance, **d) for d in dates_data
            ])

        return instance


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
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    participation_dates = ParticipationDateSerializer(many=True, read_only=True)

    class Meta:
        model = Registration
        fields = [
            "id",
            "user_id",
            "user_name",
            "phone_number",
            "email",

            "participation_dates",
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
        return f"{obj.user.first_name} {obj.user.last_name}".strip()