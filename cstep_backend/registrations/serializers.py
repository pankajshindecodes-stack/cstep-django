from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from accounts.models import User
from accounts.permissions import IsModerator 
from .models import (
    AccommodationAssistance, Registration, ParticipationDate,
    TravelAssistance, MedicalAssistance, TranslationAssistance,Event
)
class EventDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title"]

class AssistanceBaseSerializer(serializers.ModelSerializer):
    one_to_one_models = (MedicalAssistance, TranslationAssistance, AccommodationAssistance)
    event_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    event_name = serializers.CharField(source="registration.event.title", read_only=True)
    user_name = serializers.CharField(source="registration.user.full_name", read_only=True)
    user_phone = serializers.CharField(source="registration.user.phone_number", read_only=True)
    user_email = serializers.CharField(source="registration.user.email", read_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        model = self.Meta.model
        
        if not self.instance:
            event_id = attrs.pop("event_id", None)
            user_id = attrs.pop("user_id", None) or (request.user.id if request else None)

            if not event_id:
                raise serializers.ValidationError({"event_id": "This field is required for creation."})

            try:
                registration = Registration.objects.get(event_id=event_id, user_id=user_id)
            except Registration.DoesNotExist:
                raise serializers.ValidationError(
                    "No registration found for this user and event."
                )

            # Prevent duplicate creation for one-to-one models
            if model in self.one_to_one_models:
                if model.objects.filter(registration=registration).exists():
                    raise serializers.ValidationError(
                        f"{model.__name__} already requested for this registration."
                    )
            
            attrs["registration"] = registration
        return attrs


class AccommodationAssistanceSerializer(AssistanceBaseSerializer):
    class Meta:
        model  = AccommodationAssistance
        fields = [
            "id", "event_id", "user_id",
            "event_name", "user_name",
            "user_email", "user_phone",
            "hotel_name", "address", "room_no",
            "from_date", "to_date", "status",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

class TravelAssistanceSerializer(AssistanceBaseSerializer):
    class Meta:
        model  = TravelAssistance
        fields = [
            "id", "event_id", "user_id",
            "event_name","user_name",
            "user_email", "user_phone",
            "transport_mode", "source_location",
            "destination_location", "travel_date",
            "status"
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

class MedicalAssistanceSerializer(AssistanceBaseSerializer):
    class Meta:
        model  = MedicalAssistance
        fields = [
            "id", "event_id", "user_id",
            "event_name", "user_name",
            "user_email", "user_phone",
            "medical_needs", "date", "status",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

class TranslationAssistanceSerializer(AssistanceBaseSerializer):
    class Meta:
        model  = TranslationAssistance
        fields = [
            "id", "event_id", "user_id",
            "event_name", "user_name",
            "user_email", "user_phone",
            "language", "date", "status",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

class RegistrationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, is_superuser=False),
        default=serializers.CurrentUserDefault()
    )
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    participation_dates = serializers.ListField(child=serializers.DateField(),write_only=True)
    travel_assistance = TravelAssistanceSerializer(many=True, read_only=True)
    medical_assistance = MedicalAssistanceSerializer(read_only=True)
    translation_assistance = TranslationAssistanceSerializer(read_only=True)
    accommodation_assistance = AccommodationAssistanceSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = [
            "id",
            "user",
            "user_name",
            "phone_number",
            "email",
            "event",
            "participation_dates",
            "participation_time",
            "attendance_mode",
            "food_preference",
            "travel_assistance",
            "medical_assistance",
            "translation_assistance",
            "accommodation_assistance",
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

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["participation_dates"] = list(
            instance.participation_dates.values_list("date", flat=True)
        )
        return rep

    def validate_participation_dates(self, value):
        if not value:
            raise serializers.ValidationError("At least one participation date is required.")
        return value
    
    def create(self, validated_data):
        dates = validated_data.pop("participation_dates", [])
        registration = Registration.objects.create(**validated_data)
        ParticipationDate.objects.bulk_create([
            ParticipationDate(registration=registration, date=d) for d in dates
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
