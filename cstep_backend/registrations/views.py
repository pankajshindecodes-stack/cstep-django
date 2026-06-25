from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from accounts.permissions import IsModerator
from .models import (
    Registration, RegistrationStatus,
    TravelAssistance, MedicalAssistance, TranslationAssistance, AccommodationAssistance

)
from .serializers import (
    RegistrationSerializer,
    BulkStatusUpdateSerializer,
    LobbyRegistrationSerializer,
    TravelAssistanceSerializer,
    MedicalAssistanceSerializer,
    TranslationAssistanceSerializer,
    AccommodationAssistanceSerializer,
)

class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = (
        Registration.objects
        .select_related("user", "event", "medical_assistance", "translation_assistance", "accommodation_assistance")
        .prefetch_related("participation_dates", "travel_assistance")
    )

    def get_serializer_class(self):
        if self.action in [
            "bulk_update_status", "bulk_update_travel_status",
            "bulk_update_medical_status", "bulk_update_translation_status",
            "bulk_update_accommodation_status",
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
        if self.action == "request_accommodation":
            return AccommodationAssistanceSerializer
        return RegistrationSerializer

    def get_permissions(self):
        if self.action in [
            "create",
            "my_registrations",
            "request_travel",
            "request_medical",
            "request_translation",
            "request_accommodation",
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

    # ------------------------------------------------------------------ #
    #  Assistance request endpoints                                        #
    # ------------------------------------------------------------------ #

    def _create_assistance(self, request, duplicate_attr=None, duplicate_msg=None):
        """
        Generic assistance creator. Delegates event_id + user resolution
        entirely to the serializer's validate(). Optionally guards OneToOne
        duplicates before hitting the DB.

        Args:
            duplicate_attr:  related_name to check on registration (e.g. "medical_assistance").
                             Pass None for FK-based assistance (TravelAssistance).
            duplicate_msg:   Error message returned on duplicate.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # validated_data already has `registration` resolved by the serializer
        if duplicate_attr:
            registration = serializer.validated_data["registration"]
            if hasattr(registration, duplicate_attr):
                return Response(
                    {"detail": duplicate_msg},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="request-travel")
    def request_travel(self, request):
        """TravelAssistance is FK — multiple legs per registration allowed."""
        return self._create_assistance(request)

    @action(detail=False, methods=["post"], url_path="request-medical")
    def request_medical(self, request):
        """MedicalAssistance is OneToOne — guard duplicates."""
        return self._create_assistance(
            request,
            duplicate_attr="medical_assistance",
            duplicate_msg="Medical assistance has already been requested for this registration.",
        )

    @action(detail=False, methods=["post"], url_path="request-translation")
    def request_translation(self, request):
        """TranslationAssistance is OneToOne — guard duplicates."""
        return self._create_assistance(
            request,
            duplicate_attr="translation_assistance",
            duplicate_msg="Translation assistance has already been requested for this registration.",
        )

    @action(detail=False, methods=["post"], url_path="request-accommodation")
    def request_accommodation(self, request):
        """AccommodationAssistance is OneToOne — guard duplicates."""
        return self._create_assistance(
            request,
            duplicate_attr="accommodation_assistance",
            duplicate_msg="Accommodation assistance has already been requested for this registration.",
        )

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

    def _bulk_update(self, request, model, *, field_name="status", filter_field="id__in"):
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids    = serializer.validated_data["ids"]
        value  = serializer.validated_data["status"]
        now    = timezone.now()

        updated = model.objects.filter(**{filter_field: ids}).update(
            **{field_name: value, "updated_at": now}
        )

        return Response(
            {"message": f"{updated} records updated successfully.", "updated_count": updated},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["patch"], url_path="bulk-status")
    def bulk_update_status(self, request):
        return self._bulk_update(request, Registration)

    @action(detail=False, methods=["patch"], url_path="bulk-travel-status")
    def bulk_update_travel_status(self, request):
        return self._bulk_update(request, TravelAssistance)

    @action(detail=False, methods=["patch"], url_path="bulk-medical-status")
    def bulk_update_medical_status(self, request):
        return self._bulk_update(request, MedicalAssistance)

    @action(detail=False, methods=["patch"], url_path="bulk-translation-status")
    def bulk_update_translation_status(self, request):
        return self._bulk_update(request, TranslationAssistance)

    @action(detail=False, methods=["patch"], url_path="bulk-accommodation-status")
    def bulk_update_accommodation_status(self, request):
        return self._bulk_update(request, AccommodationAssistance)

    # ------------------------------------------------------------------ #
    #  Lobby endpoints                                                     #
    # ------------------------------------------------------------------ #

    def _lobby_queryset(self, event_id, **filters):
        return (
            Registration.objects
            .select_related("user", "medical_assistance", "translation_assistance", "accommodation_assistance")
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