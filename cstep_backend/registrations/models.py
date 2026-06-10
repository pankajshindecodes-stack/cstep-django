from django.db import models
from django.conf import settings
from events.models import Event

class FoodPreference(models.TextChoices):
    VEG = "VEG", "Vegetarian"
    JAIN = "JAIN", "Jain"
    VEGAN = "VEGAN", "Vegan"
    SATVIK = "SATVIK", "Satvik"
    EGG_VEG = "EGG_VEG", "Egg Vegetarian"
    PESCETARIAN = "PESCETARIAN", "Pescetarian"
    GLUTEN_FREE = "GLUTEN_FREE", "Gluten Free"
    LACTOSE_FREE = "LACTOSE_FREE", "Lactose Free"
    DIABETIC_FRIENDLY = "DIABETIC_FRIENDLY", "Diabetic Friendly"
    NUT_ALLERGY = "NUT_ALLERGY", "Nut Allergy"
    HALAL = "HALAL", "Halal"
    NON_VEG_CHICKEN = "NON_VEG_CHICKEN", "Non Veg (Chicken Only)"
    NON_VEG_ANY = "NON_VEG_ANY", "Non Veg (Any)"

class TravelArrangement(models.TextChoices):
    FLIGHT_TAXI_HOTEL = "FLIGHT_TAXI_HOTEL", "Flight + Taxi + Hotel"
    TAXI_HOTEL = "TAXI_HOTEL", "Taxi + Hotel"
    HOTEL_ONLY = "HOTEL_ONLY", "Hotel Only"
    TAXI_ONLY = "TAXI_ONLY", "Taxi Only"
    FLIGHT_ONLY = "FLIGHT_ONLY", "Flight Only"
    TRAIN_ONLY = "TRAIN_ONLY", "Train Only"
    SELF_ARRANGED = "SELF_ARRANGED", "Self Arranged"

class MedicalSupport(models.TextChoices):
    WHEEL_CHAIR = "WHEEL_CHAIR", "Wheelchair Access"
    MOBILITY_ASSISTANCE = "MOBILITY_ASSISTANCE", "Mobility Assistance"
    ATTENDER = "ATTENDER", "Personal Attender"
    BLIND_COMPANION = "BLIND_COMPANION", "Blind Companion / Guide"
    HEARING_IMPAIRED = "HEARING_IMPAIRED", "Hearing Impaired Support"
    SIGN_LANGUAGE_INTERPRETER = "SIGN_LANGUAGE_INTERPRETER", "Sign Language Interpreter"
    OXYGEN_SUPPORT = "OXYGEN_SUPPORT", "Oxygen Support"
    GUIDE_DOG = "GUIDE_DOG", "Guide Dog Accommodation"
    RESERVED_SEATING = "RESERVED_SEATING", "Reserved Seating (Medical)"
    OTHER_MEDICAL = "OTHER_MEDICAL", "Other Medical Requirement"

class TranslationLanguage(models.TextChoices):
    HINDI = "HINDI", "Hindi"
    ENGLISH = "ENGLISH", "English"
    KANNADA = "KANNADA", "Kannada"
    TAMIL = "TAMIL", "Tamil"
    TELUGU = "TELUGU", "Telugu"
    MALAYALAM = "MALAYALAM", "Malayalam"
    PUNJABI = "PUNJABI", "Punjabi"
    BENGALI = "BENGALI", "Bengali"
    MARATHI = "MARATHI", "Marathi"
    GUJARATI = "GUJARATI", "Gujarati"
    ODIA = "ODIA", "Odia"
    ASSAMESE = "ASSAMESE", "Assamese"
    URDU = "URDU", "Urdu"

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

class AttendanceMode(models.TextChoices):
    PHYSICAL = "PHYSICAL", "Physical (On-site)"
    VIRTUAL = "VIRTUAL", "Virtual (Online)"
    HYBRID = "HYBRID", "Hybrid"
    RECORDED = "RECORDED", "Recorded Session Only"
    UNDECIDED = "UNDECIDED", "Not Decided Yet"

class ParticipationDate(models.Model):
    registration = models.ForeignKey(
        "Registration",
        on_delete=models.CASCADE,
        related_name="participation_dates",
    )
    date = models.DateField()
    

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["registration", "date"],
                name="unique_registration_date",
            )
        ]
        ordering = ["date"]

    def __str__(self):
        return f"{self.registration} → {self.date}"


class Registration(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    participation_time = models.CharField(
        max_length=20,
        choices=ParticipationTime.choices,
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )

    food_preference = models.CharField(
        max_length=20,
        choices=FoodPreference.choices,
        null=True,
        blank=True,
    )

    attendance_mode = models.CharField(
        max_length=10,
        choices=AttendanceMode.choices,
        default=AttendanceMode.UNDECIDED,
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