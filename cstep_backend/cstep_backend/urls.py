from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("rest_framework.urls")),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/", include("accounts.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("analytics/", include("analytics.urls")),
]
