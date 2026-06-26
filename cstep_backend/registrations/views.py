from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from accounts.permissions import IsModerator
from accounts.models import UserRole, User
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

    filterset_fields = {
        "status":           ["exact", "in"],
        "attendance_mode":  ["exact"],
        "food_preference":  ["exact"],
        "participation_time": ["exact"],
        "event":            ["exact"],           # filter by event id
        "event__title":     ["exact", "icontains"],
        "user":             ["exact"],
        "created_at":       ["date", "gte", "lte"],
    }

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "event__title",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "status",
        "event__title",
        "user__email",
    ]
    ordering = ["-created_at"]   # default

    # ---------------------------------

    def get_serializer_class(self):
        if self.action == "bulk_update_status":
            return BulkStatusUpdateSerializer
        return RegistrationSerializer

    def get_permissions(self):
        if self.action in ["create", "my_registrations"]:
            return [IsAuthenticated()]
        return [IsModerator()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "my_registrations":
            return queryset.filter(user=self.request.user)
        return queryset

    @action(detail=False, methods=["get"], url_path="my")
    def my_registrations(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class TravelAssistanceViewSet(viewsets.ModelViewSet):
    serializer_class = TravelAssistanceSerializer
    queryset = (
        TravelAssistance.objects
        .select_related("registration__user", "registration__event")
    )

    filterset_fields = {
        "status":                       ["exact", "in"],
        "transport_mode":               ["exact", "in"],
        "travel_date":                  ["exact", "gte", "lte"],
        "registration":                 ["exact"],
        "registration__event":          ["exact"],
        "registration__status":         ["exact"],
    }

    search_fields = [
        "source_location",
        "destination_location",
        "registration__user__email",
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__event__title",
    ]

    ordering_fields = [
        "travel_date",
        "status",
        "transport_mode",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    # ---------------------------------
    def get_permissions(self):
        if self.action in ["create"]: # "update", "partial_update", "destroy"
            return [IsAuthenticated()]
        return [IsModerator()]
        
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == UserRole.BASE_USER and self.action == "list":
            raise PermissionDenied("You do not have permission to access this API.")
        return queryset

    @action(detail=False, methods=["patch"], url_path="bulk-status", permission_classes=[IsModerator])
    def bulk_update_status(self, request):
        """Bulk update the status of multiple TravelAssistance records."""
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = (
            self.get_queryset()
            .filter(id__in=serializer.validated_data["ids"])
            .update(status=serializer.validated_data["status"], updated_at=timezone.now())
        )
        return Response({"message": f"{updated} records updated.", "updated_count": updated})


class MedicalAssistanceViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalAssistanceSerializer
    queryset = (
        MedicalAssistance.objects
        .select_related("registration__user", "registration__event")
    )

    filterset_fields = {
        "status":                   ["exact", "in"],
        "date":                     ["exact", "gte", "lte"],
        "registration":             ["exact"],
        "registration__event":      ["exact"],
        "registration__status":     ["exact"],
    }

    search_fields = [
        "medical_needs",
        "registration__user__email",
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__event__title",
    ]

    ordering_fields = [
        "date",
        "status",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    # ---------------------------------

    def get_permissions(self):
        if self.action in ["bulk_update_status"]:
            return [IsModerator()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == UserRole.BASE_USER and self.action == "list":
            raise PermissionDenied("You do not have permission to access this API.")
        return queryset

    @action(detail=False, methods=["patch"], url_path="bulk-status", permission_classes=[IsModerator])
    def bulk_update_status(self, request):
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = (
            self.get_queryset()
            .filter(id__in=serializer.validated_data["ids"])
            .update(status=serializer.validated_data["status"], updated_at=timezone.now())
        )
        return Response({"message": f"{updated} records updated.", "updated_count": updated})


class TranslationAssistanceViewSet(viewsets.ModelViewSet):
    serializer_class = TranslationAssistanceSerializer
    queryset = (
        TranslationAssistance.objects
        .select_related("registration__user", "registration__event")
    )

    filterset_fields = {
        "status":                   ["exact", "in"],
        "language":                 ["exact", "in"],
        "date":                     ["exact", "gte", "lte"],
        "registration":             ["exact"],
        "registration__event":      ["exact"],
        "registration__status":     ["exact"],
    }

    search_fields = [
        "language",
        "registration__user__email",
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__event__title",
    ]

    ordering_fields = [
        "date",
        "language",
        "status",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    # ---------------------------------

    def get_permissions(self):
        if self.action in ["bulk_update_status"]:
            return [IsModerator()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == UserRole.BASE_USER and self.action == "list":
            raise PermissionDenied("You do not have permission to access this API.")
        return queryset

    @action(detail=False, methods=["patch"], url_path="bulk-status", permission_classes=[IsModerator])
    def bulk_update_status(self, request):
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = (
            self.get_queryset()
            .filter(id__in=serializer.validated_data["ids"])
            .update(status=serializer.validated_data["status"], updated_at=timezone.now())
        )
        return Response({"message": f"{updated} records updated.", "updated_count": updated})


class AccommodationAssistanceViewSet(viewsets.ModelViewSet):
    serializer_class = AccommodationAssistanceSerializer
    queryset = (
        AccommodationAssistance.objects
        .select_related("registration__user", "registration__event")
    )

    filterset_fields = {
        "status":                   ["exact", "in"],
        "from_date":                ["exact", "gte", "lte"],
        "to_date":                  ["exact", "gte", "lte"],
        "registration":             ["exact"],
        "registration__event":      ["exact"],
        "registration__status":     ["exact"],
    }

    search_fields = [
        "hotel_name",
        "address",
        "room_no",
        "registration__user__email",
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__event__title",
    ]

    ordering_fields = [
        "from_date",
        "to_date",
        "status",
        "hotel_name",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    # ---------------------------------

    def get_permissions(self):
        if self.action in ["bulk_update_status"]:
            return [IsModerator()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == UserRole.BASE_USER and self.action == "list":
            raise PermissionDenied("You do not have permission to access this API.")
        return queryset

    @action(detail=False, methods=["patch"], url_path="bulk-status", permission_classes=[IsModerator])
    def bulk_update_status(self, request):
        serializer = BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = (
            self.get_queryset()
            .filter(id__in=serializer.validated_data["ids"])
            .update(status=serializer.validated_data["status"], updated_at=timezone.now())
        )
        return Response({"message": f"{updated} records updated.", "updated_count": updated})