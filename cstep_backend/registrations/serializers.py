from rest_framework import serializers
from .models import Registration, ParticipationDate, RegistrationDetails, ApprovalStatus
from rest_framework.validators import UniqueTogetherValidator


class ParticipationDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipationDate
        fields = ["id", "date"]


class RegistrationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationDetails
        fields = [
            "food_preference",
            "food_preference_status",
            "travel_arrangement",
            "travel_status",
            "medical_support",
            "medical_support_status",
            "translation_language",
            "translation_status"
        ]
        read_only_fields = [
            "food_preference_status",
            "travel_status",
            "medical_support_status",
            "translation_status"
        ]
    def validate(self, attrs):
        status_fields = {
            "food_preference"      : "food_preference_status",
            "travel_arrangement"   : "travel_status",
            "medical_support"      : "medical_support_status",
            "translation_language" : "translation_status"
        }
        attrs.update({
            status_field: ApprovalStatus.PENDING
            for field, status_field in status_fields.items()
            if attrs.get(field)
        })
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    participation_dates = ParticipationDateSerializer(many=True)
    details = RegistrationDetailsSerializer(required=False)

    class Meta:
        model = Registration
        fields = [
            "id",
            "user",
            "event",
            "participation_dates",
            "participation_time",
            "details",

            # Attendance
            "attendance_mode",

            # Registration
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
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
        details = attrs.get("details")
        if details:
            if details.get("travel_arrangement"):
                details["travel_status"] = ApprovalStatus.PENDING
            if details.get("translation_language"):
                details["translation_status"] = ApprovalStatus.PENDING
        return attrs

    def create(self, validated_data):
        dates_data = validated_data.pop("participation_dates")
        details_data = validated_data.pop("details", None)

        registration = Registration.objects.create(**validated_data)

        ParticipationDate.objects.bulk_create([
            ParticipationDate(registration=registration, **d) for d in dates_data
        ])

        if details_data:
            RegistrationDetails.objects.create(registration=registration, **details_data)

        return registration

    def update(self, instance, validated_data):
        dates_data = validated_data.pop("participation_dates", None)
        details_data = validated_data.pop("details", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if dates_data is not None:
            instance.participation_dates.all().delete()
            ParticipationDate.objects.bulk_create([
                ParticipationDate(registration=instance, **d) for d in dates_data
            ])

        if details_data is not None:
            details, _ = RegistrationDetails.objects.get_or_create(registration=instance)
            for attr, value in details_data.items():
                setattr(details, attr, value)
            details.save()

        return instance


class BulkStatusUpdateSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    status = serializers.CharField()


class LobbyRegistrationSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    participation_dates = ParticipationDateSerializer(many=True, read_only=True)
    details = serializers.SerializerMethodField()

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
            "details",

            "attendance_mode",

            "status",
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def get_details(self, obj):
        details = getattr(obj, "details", None)
        if details is None:
            return None
        return RegistrationDetailsSerializer(details).data