from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsModerator
from .models import Registration, RegistrationStatus
from .serializers import (
    RegistrationSerializer,
    RegistrationStatusSerializer,
    TravelStatusSerializer,
    TranslationStatusSerializer,
    LobbyRegistrationSerializer,
)


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.select_related("user", "event")

    def get_serializer_class(self):
        if self.action == "update_status":
            return RegistrationStatusSerializer
        elif self.action == "update_travel_status":
            return TravelStatusSerializer
        elif self.action == "update_translation_status":
            return TranslationStatusSerializer
        elif self.action in ["registered", "proposed"]:
            return LobbyRegistrationSerializer

        return RegistrationSerializer

    def get_permissions(self):
        if self.action in [
            "create",
            "my_registrations",
        ]:
            return [IsAuthenticated()]

        return [IsModerator()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # User's registrations
        if self.action == "my_registrations":
            return queryset.filter(user=self.request.user)

        # Moderator registration listing
        if self.action == "list":
            event_id = self.request.query_params.get("event_id")
            if event_id:
                queryset = queryset.filter(event_id=event_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def my_registrations(self, request):
        queryset = self.get_queryset()

        serializer = self.get_serializer(
            queryset,
            many=True,
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsModerator],
    )
    def update_status(self, request, pk=None):
        registration = self.get_object()

        serializer = RegistrationStatusSerializer(
            registration,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsModerator],
    )
    def update_travel_status(self, request, pk=None):
        registration = self.get_object()

        serializer = TravelStatusSerializer(
            registration,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsModerator],
    )
    def update_translation_status(self, request, pk=None):
        registration = self.get_object()

        serializer = TranslationStatusSerializer(
            registration,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"lobby/(?P<event_id>[^/.]+)/registered",
        permission_classes=[IsModerator],
    )
    def registered(self, request, event_id=None):
        queryset = Registration.objects.select_related("user").filter(
            event_id=event_id
        )

        serializer = LobbyRegistrationSerializer(
            queryset,
            many=True,
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"lobby/(?P<event_id>[^/.]+)/proposed",
        permission_classes=[IsModerator],
    )
    def proposed(self, request, event_id=None):
        queryset = Registration.objects.select_related("user").filter(
            event_id=event_id,
            status=RegistrationStatus.PENDING,
        )

        serializer = LobbyRegistrationSerializer(
            queryset,
            many=True,
        )
        return Response(serializer.data)