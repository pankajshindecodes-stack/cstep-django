from django.db.models import Count
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsModerator
from registrations.models import Registration, RegistrationStatus


class UserSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        regs = Registration.objects.all()
        return Response({
            "total_registered_users": User.objects.count(),
            "participants_registered": regs.count(),
            "participants_accepted": regs.filter(status=RegistrationStatus.ACCEPTED).count(),
            "participants_rejected": regs.filter(status=RegistrationStatus.REJECTED).count(),
            "participants_pending": regs.filter(status=RegistrationStatus.PENDING).count(),
            "participants_held": regs.filter(status=RegistrationStatus.HELD).count(),
        })


class ParticipationSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_id):
        qs = Registration.objects.filter(event_id=event_id)

        by_date = dict(
            qs.values("participation_date")
            .annotate(count=Count("id"))
            .values_list("participation_date", "count")
        )
        by_time = dict(
            qs.values("participation_time")
            .annotate(count=Count("id"))
            .values_list("participation_time", "count")
        )
        by_food = dict(
            qs.values("food_preference")
            .annotate(count=Count("id"))
            .values_list("food_preference", "count")
        )
        by_status = dict(
            qs.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        return Response({
            "by_date": by_date,
            "by_time": by_time,
            "by_food": by_food,
            "by_status": by_status,
        })
