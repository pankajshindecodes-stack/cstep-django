from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import (
    Registration, ParticipationDate,
    TravelAssistance, MedicalAssistance, TranslationAssistance,
)

class ParticipationDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipationDate
        fields = ["id", "date"]


class TravelAssistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelAssistance
        fields = [
            "id",
            "transport_mode",
            "source_location",
            "destination_location",
            "travel_date",
            "status",
        ]
        read_only_fields = ["id", "status"]


class MedicalAssistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalAssistance
        fields = ["id", "medical_needs", "date", "status"]
        read_only_fields = ["id", "status"]


class TranslationAssistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationAssistance
        fields = ["id", "language", "date", "status"]
        read_only_fields = ["id", "status"]
        
class RegistrationSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    participation_dates = ParticipationDateSerializer(many=True)
    travel_assistance = TravelAssistanceSerializer(many=True, read_only=True)
    medical_assistance = MedicalAssistanceSerializer(read_only=True)
    translation_assistance = TranslationAssistanceSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = [
            "id",
            "user",
            "event",
            "participation_dates",
            "participation_time",
            "attendance_mode",
            "food_preference",
            "travel_assistance",
            "medical_assistance",
            "translation_assistance",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]
        validators = [
            UniqueTogetherValidator(
                queryset=Registration.objects.all(),
                fields=["user", "event"],
                message="You have already registered for this event.",
            )
        ]

    def validate_participation_dates(self, value):
        if not value:
            raise serializers.ValidationError("At least one participation date is required.")
        return value

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
    
class BulkStatusUpdateSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    status = serializers.CharField()


class LobbyRegistrationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    participation_dates = ParticipationDateSerializer(many=True, read_only=True)
    travel_assistance = TravelAssistanceSerializer(many=True, read_only=True)
    medical_assistance = MedicalAssistanceSerializer(read_only=True)
    translation_assistance = TranslationAssistanceSerializer(read_only=True)

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
            "attendance_mode",
            "food_preference",
            "travel_assistance",
            "medical_assistance",
            "translation_assistance",
            "status",
        ]