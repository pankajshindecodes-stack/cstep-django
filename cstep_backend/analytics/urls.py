from django.urls import path
from . import views

urlpatterns = [
    path("user-summary/", views.UserSummaryView.as_view(), name="user_summary"),
    path("<int:event_id>/participation/", views.ParticipationSummaryView.as_view(), name="participation_summary"),
]
