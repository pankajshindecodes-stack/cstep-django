from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("rest_framework.urls")),
    path("auth/", include("accounts.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("analytics/", include("analytics.urls")),
]
