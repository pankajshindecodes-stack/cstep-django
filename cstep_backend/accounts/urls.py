from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import AuthViewSet, UserViewSet

router = DefaultRouter()

router.register("", AuthViewSet, basename="auth")
router.register("users", UserViewSet, basename="users")

me_view = UserViewSet.as_view({"get": "me", "patch": "me"})

urlpatterns = [
    *router.urls,
    path("me/", me_view, name="auth-me"),
]
