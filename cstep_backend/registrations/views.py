from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from accounts.permissions import IsModerator
from .models import (
    Registration, RegistrationStatus,
    TravelAssistance, MedicalAssistance, TranslationAssistance,Event
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
        if self.action in ["bulk_update_status", "bulk_update_travel_status",
                        "bulk_update_medical_status", "bulk_update_translation_status"]:
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
    
    # Inside RegistrationViewSet
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="request-travel")
    def request_travel(self, request):
        registration = (
            Event.objects.get(id=request.data.get("event_id"))
            .registrations.filter(user=request.user).first()
        )
        serializer = TravelAssistanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(registration=registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="request-medical")
    def request_medical(self, request):
        registration = registration = (
            Event.objects.get(id=request.data.get("event_id"))
            .registrations.filter(user=request.user).first()
        )

        if hasattr(registration, "medical_assistance"):
            return Response(
                {"detail": "Medical assistance has already been requested for this registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MedicalAssistanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(registration=registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="request-translation")
    def request_translation(self, request):
        registration = registration = (
            Event.objects.get(id=request.data.get("event_id"))
            .registrations.filter(user=request.user).first()
        )

        if hasattr(registration, "translation_assistance"):
            return Response(
                {"detail": "Translation assistance has already been requested for this registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TranslationAssistanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(registration=registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="my")
    def my_registrations(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsModerator], url_path="all")
    def all_registrations(self, request):
        serializer = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], permission_classes=[IsModerator], url_path="bulk-status")
    def bulk_update_status(self, request):
        return self._bulk_update(request, Registration, "status")

    @action(detail=False, methods=["patch"], permission_classes=[IsModerator], url_path="bulk-travel-status")
    def bulk_update_travel_status(self, request):
        return self._bulk_update(request, TravelAssistance, "status", fk="registration_id")

    @action(detail=False, methods=["patch"], permission_classes=[IsModerator], url_path="bulk-medical-status")
    def bulk_update_medical_status(self, request):
        return self._bulk_update(request, MedicalAssistance, "status", fk="registration_id")

    @action(detail=False, methods=["patch"], permission_classes=[IsModerator], url_path="bulk-translation-status")
    def bulk_update_translation_status(self, request):
        return self._bulk_update(request, TranslationAssistance, "status", fk="registration_id")

    def _bulk_update(self, request, model, field_name, fk=None):
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data["ids"]
        value = serializer.validated_data["status"]
        now = timezone.now()

        filter_kwarg = {f"{fk}__in" if fk else "id__in": ids}
        updated = model.objects.filter(**filter_kwarg).update(
            **{field_name: value, "updated_at": now}
        )

        # Keep parent Registration timestamps in sync for assistance models
        if fk:
            Registration.objects.filter(id__in=ids).update(updated_at=now)

        return Response(
            {"message": f"{updated} records updated successfully.", "updated_count": updated},
            status=status.HTTP_200_OK,
        )

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