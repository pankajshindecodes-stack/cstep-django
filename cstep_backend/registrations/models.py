from django.db import models
from django.conf import settings
from events.models import Event
from .constants import (
    FoodPreference,
    TravelArrangement,
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
    
class RegistrationDetails(models.Model):
    registration = models.OneToOneField(
        "Registration",
        on_delete=models.CASCADE,
        related_name="details",
    )

    food_preference = models.CharField(
        max_length=20,
        choices=FoodPreference.choices,
        null=True,
        blank=True,
    )

    food_preference_status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
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
        choices=MedicalSupportType.choices,
        null=True,
        blank=True,
    )

    medical_support_status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Details for {self.registration}"