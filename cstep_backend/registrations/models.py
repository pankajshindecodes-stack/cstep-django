from django.db import models
from django.conf import settings
from events.models import Event
from .constants import (
    FoodPreference,
    TransportMode,
    MedicalSupportType,
    TranslationLanguage,
    ParticipationTime,
    RegistrationStatus,
    ApprovalStatus,
    AttendanceMode
)

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
    attendance_mode = models.CharField(
        max_length=10,
        choices=AttendanceMode.choices,
        default=AttendanceMode.UNDECIDED,
    )
    food_preference = models.CharField(
        max_length=20,
        choices=FoodPreference.choices,
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

class TravelAssistance(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="travel_assistance",
    )
    transport_mode = models.CharField(max_length=20, choices=TransportMode.choices)

    # Flight / Train / Taxi
    source_location = models.CharField(max_length=255, blank=True, default="")
    destination_location = models.CharField(max_length=255, blank=True, default="")
    travel_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Travel ({self.transport_mode}) - {self.registration}"

class MedicalAssistance(models.Model):
    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name="medical_assistance",
    )
    medical_needs = models.TextField(
        help_text="e.g. wheelchair accessibility, medications, emergency contact"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Medical - {self.registration}"

class TranslationAssistance(models.Model):
    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name="translation_assistance",
    )
    language = models.CharField(max_length=20, choices=TranslationLanguage.choices)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Translation ({self.language}) - {self.registration}"