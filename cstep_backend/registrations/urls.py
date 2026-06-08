from rest_framework.routers import DefaultRouter
from .views import RegistrationViewSet

router = DefaultRouter()
router.register(
    r"",
    RegistrationViewSet,
    basename="registration",
)

urlpatterns = router.urls
