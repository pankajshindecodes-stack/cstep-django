from rest_framework import viewsets,status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsModerator
from .models import Registration, RegistrationStatus
from .serializers import (
    RegistrationSerializer,
    BulkStatusUpdateSerializer,
    LobbyRegistrationSerializer,
)
from django.utils import timezone


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.select_related("user", "event").prefetch_related("participation_dates")

    def get_serializer_class(self):
        if self.action in ["update_status", "update_travel_status", "update_translation_status"]:
            return BulkStatusUpdateSerializer
        elif self.action in ["registered", "proposed"]:
            return LobbyRegistrationSerializer

        return RegistrationSerializer

    def get_permissions(self):
        if self.action in ["create", "my_registrations"]:
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

    def perform_create(self, serializer):
        serializer.save()

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
        return self._bulk_update_registration(
            request,
            field_name="status",
        )

    @action(detail=False, methods=["patch"], permission_classes=[IsModerator], url_path="bulk-travel-status")
    def bulk_update_travel_status(self, request):
        return self._bulk_update_registration(
            request,
            field_name="travel_status",
        )

    @action( detail=False, methods=["patch"], permission_classes=[IsModerator], url_path="bulk-translation-status")
    def bulk_update_translation_status(self, request):
        return self._bulk_update_registration(
            request,
            field_name="translation_status",
        )
    
    def _bulk_update_registration(self, request, field_name):
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data["ids"]
        value = serializer.validated_data["status"]

        updated = Registration.objects.filter(
            id__in=ids
        ).update(
            **{
                field_name: value,
                "updated_at": timezone.now(),
            }
        )

        return Response(
            {
                "message": f"{updated} registrations updated successfully.",
                "updated_count": updated,
            },
            status=status.HTTP_200_OK,
        )

    def _lobby_queryset(self, event_id, **filters):
        return (
            Registration.objects
            .select_related("user")
            .prefetch_related("participation_dates")
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