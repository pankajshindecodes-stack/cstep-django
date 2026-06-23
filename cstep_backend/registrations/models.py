from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from accounts.permissions import IsModerator
from .models import (
    Registration, RegistrationStatus,
    TravelAssistance, MedicalAssistance, TranslationAssistance, Event
)
from .serializers import (
    RegistrationSerializer,
    BulkStatusUpdateSerializer,
    LobbyRegistrationSerializer,
    TravelAssistanceSerializer,
    MedicalAssistanceSerializer,
    TranslationAssistanceSerializer,
)


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = (
        Registration.objects
        .select_related("user", "event", "medical_assistance", "translation_assistance")
        .prefetch_related("participation_dates", "travel_assistance")
    )

    def get_serializer_class(self):
        if self.action in [
            "bulk_update_status", "bulk_update_travel_status",
            "bulk_update_medical_status", "bulk_update_translation_status",
        ]:
            return BulkStatusUpdateSerializer
        if self.action in ["registered", "proposed"]:
            return LobbyRegistrationSerializer
        if self.action == "request_travel":
            return TravelAssistanceSerializer
        if self.action == "request_medical":
            return MedicalAssistanceSerializer
        if self.action == "request_translation":
            return TranslationAssistanceSerializer
        return RegistrationSerializer

    def get_permissions(self):
        if self.action in [
            "create",
            "my_registrations",
            "request_travel",
            "request_medical",
            "request_translation",
        ]:
            return [IsAuthenticated()]
        return [IsModerator()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "my_registrations":
            return queryset.filter(user=self.request.user)
        if self.action == "list":
            event_id = self.request.query_params.get("event_id")
            if event_id:
                queryset = queryset.filter(event_id=event_id)
        return queryset

    def _get_registration_for_user(self, request) -> Registration:
        """Resolve the user's Registration for the given event_id in request.data."""
        event = get_object_or_404(Event, id=request.data.get("event_id"))
        return get_object_or_404(Registration, event=event, user=request.user)

    # ------------------------------------------------------------------ #
    #  Assistance request endpoints                                        #
    # ------------------------------------------------------------------ #

    @action(detail=False, methods=["post"], url_path="request-travel")
    def request_travel(self, request):
        """
        TravelAssistance is a FK (multiple rows per registration allowed),
        so no duplicate guard here — each POST creates a new travel leg.
        """
        registration = self._get_registration_for_user(request)
        serializer = TravelAssistanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(registration=registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="request-medical")
    def request_medical(self, request):
        """MedicalAssistance is OneToOne — guard against duplicates."""
        registration = self._get_registration_for_user(request)
        if hasattr(registration, "medical_assistance"):
            return Response(
                {"detail": "Medical assistance has already been requested for this registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = MedicalAssistanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(registration=registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="request-translation")
    def request_translation(self, request):
        """TranslationAssistance is OneToOne — guard against duplicates."""
        registration = self._get_registration_for_user(request)
        if hasattr(registration, "translation_assistance"):
            return Response(
                {"detail": "Translation assistance has already been requested for this registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = TranslationAssistanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(registration=registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------ #
    #  Listing endpoints                                                   #
    # ------------------------------------------------------------------ #

    @action(detail=False, methods=["get"], url_path="my")
    def my_registrations(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsModerator], url_path="all")
    def all_registrations(self, request):
        serializer = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    #  Bulk status update endpoints                                        #
    # ------------------------------------------------------------------ #

    @action(detail=False, methods=["patch"], url_path="bulk-status")
    def bulk_update_status(self, request):
        """ids = Registration PKs."""
        return self._bulk_update(request, Registration, field_name="status")

    @action(detail=False, methods=["patch"], url_path="bulk-travel-status")
    def bulk_update_travel_status(self, request):
        """
        ids = Registration PKs.
        Updates ALL TravelAssistance rows belonging to those registrations.
        This is intentional: a single registration can have multiple travel
        legs (FK), and a moderator bulk-approving/rejecting acts on all of them.
        If you need per-row control, use the TravelAssistance detail endpoint instead.
        """
        return self._bulk_update(
            request, TravelAssistance,
            field_name="status",
            filter_field="registration_id__in",   # filter by parent registration PK
            sync_parent=True,
        )

    @action(detail=False, methods=["patch"], url_path="bulk-medical-status")
    def bulk_update_medical_status(self, request):
        """ids = Registration PKs (OneToOne → one row per registration)."""
        return self._bulk_update(
            request, MedicalAssistance,
            field_name="status",
            filter_field="registration_id__in",
            sync_parent=True,
        )

    @action(detail=False, methods=["patch"], url_path="bulk-translation-status")
    def bulk_update_translation_status(self, request):
        """ids = Registration PKs (OneToOne → one row per registration)."""
        return self._bulk_update(
            request, TranslationAssistance,
            field_name="status",
            filter_field="registration_id__in",
            sync_parent=True,
        )

    def _bulk_update(self, request, model, *, field_name, filter_field="id__in", sync_parent=False):
        """
        Generic bulk-status updater.

        Args:
            model:          The model class to update.
            field_name:     The field to set (always "status" for now).
            filter_field:   ORM lookup used to scope the queryset.
                            "id__in"             → ids are the model's own PKs  (Registration)
                            "registration_id__in" → ids are Registration PKs    (assistance models)
            sync_parent:    When True, also touch Registration.updated_at so
                            the parent row reflects the latest change.
        """
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data["ids"]
        value = serializer.validated_data["status"]
        now = timezone.now()

        updated = model.objects.filter(**{filter_field: ids}).update(
            **{field_name: value, "updated_at": now}
        )

        if sync_parent:
            # ids are Registration PKs for all assistance models
            Registration.objects.filter(id__in=ids).update(updated_at=now)

        return Response(
            {"message": f"{updated} records updated successfully.", "updated_count": updated},
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------ #
    #  Lobby endpoints                                                     #
    # ------------------------------------------------------------------ #

    def _lobby_queryset(self, event_id, **filters):
        return (
            Registration.objects
            .select_related("user", "medical_assistance", "translation_assistance")
            .prefetch_related("participation_dates", "travel_assistance")
            .filter(event_id=event_id, **filters)
        )

    @action(
        detail=False, methods=["get"], permission_classes=[IsModerator],
        url_path=r"lobby/(?P<event_id>[^/.]+)/registered",
    )
    def registered(self, request, event_id=None):
        serializer = LobbyRegistrationSerializer(self._lobby_queryset(event_id), many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["get"], permission_classes=[IsModerator],
        url_path=r"lobby/(?P<event_id>[^/.]+)/proposed",
    )
    def proposed(self, request, event_id=None):
        serializer = LobbyRegistrationSerializer(
            self._lobby_queryset(event_id, status=RegistrationStatus.PENDING), many=True
        )
        return Response(serializer.data)