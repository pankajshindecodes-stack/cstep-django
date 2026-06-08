from django.db import models
from django.conf import settings
from events.models import Event

class FoodPreference(models.TextChoices):
    VEG = "VEG", "Veg"
    JAIN = "JAIN", "Jain"
    VEGAN = "VEGAN", "Vegan"
    PESCETARIAN = "PESCETARIAN", "Pescetarian"
    NON_VEG_CHICKEN = "NON_VEG_CHICKEN", "Non Veg (Chicken only)"
    NON_VEG_ANY = "NON_VEG_ANY", "Non Veg (Any)"
    NO_PREFERENCE = "NO_PREFERENCE", "No Preference"

class TravelArrangement(models.TextChoices):
    FLIGHT_TAXI_HOTEL = "FLIGHT_TAXI_HOTEL", "Flight + Taxi + Hotel"
    TAXI_HOTEL = "TAXI_HOTEL", "Taxi + Hotel"
    HOTEL_ONLY = "HOTEL_ONLY", "Hotel Only"
    TAXI_ONLY = "TAXI_ONLY", "Taxi Only"
    FLIGHT_ONLY = "FLIGHT_ONLY", "Flight Only"
    TRAIN_ONLY = "TRAIN_ONLY", "Train Only"
    SELF_ARRANGED = "SELF_ARRANGED", "Self Arranged"

class MedicalSupport(models.TextChoices):
    WHEEL_CHAIR = "WHEEL_CHAIR", "Wheel Chair"
    ATTENDER = "ATTENDER", "Attender"
    BLIND_COMPANION = "BLIND_COMPANION", "Blind Companion"
    SIGN_LANGUAGE_INTERPRETER = "SIGN_LANGUAGE_INTERPRETER", "Sign Language Interpreter"
    HEARING_ASSISTANCE = "HEARING_ASSISTANCE", "Hearing Assistance"
    OTHER = "OTHER", "Other"

class TranslationLanguage(models.TextChoices):
    HINDI = "HINDI", "Hindi"
    ENGLISH = "ENGLISH", "English"
    KANNADA = "KANNADA", "Kannada"
    TAMIL = "TAMIL", "Tamil"
    TELUGU = "TELUGU", "Telugu"
    MALAYALAM = "MALAYALAM", "Malayalam"
    PUNJABI = "PUNJABI", "Punjabi"
    MARATHI = "MARATHI", "Marathi"
    GUJARATI = "GUJARATI", "Gujarati"
    BENGALI = "BENGALI", "Bengali"
    ODIA = "ODIA", "Odia"
    ASSAMESE = "ASSAMESE", "Assamese"

class ParticipationTime(models.TextChoices):
    HALF_DAY = "HALF_DAY", "Half Day"
    FULL_DAY = "FULL_DAY", "Full Day"
    MULTIPLE_DAYS = "MULTIPLE_DAYS", "Multiple Days"

class RegistrationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    HELD = "HELD", "Held"
    REJECTED = "REJECTED", "Rejected"


class ApprovalStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"

class Registration(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )

    participation_date = models.DateField()
    participation_time = models.CharField(
        max_length=20,
        choices=ParticipationTime.choices,
        null=True,
        blank=True,
    )

    food_preference = models.CharField(
        max_length=20,
        choices=FoodPreference.choices,
        null=True,
        blank=True,
    )

    # Travel
    travel_arrangement = models.CharField(
        max_length=20,
        choices=TravelArrangement.choices,
        null=True,
        blank=True,
    )
    travel_status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
        null=True,
        blank=True,
    )

    # Medical
    medical_support = models.CharField(
        max_length=50,
        choices=MedicalSupport.choices,
        null=True,
        blank=True,
    )

    # Translation
    translation_language = models.CharField(
        max_length=20,
        choices=TranslationLanguage.choices,
        null=True,
        blank=True,
    )
    translation_status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=10,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"],
                name="unique_user_event_registration",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.event} [{self.status}]"