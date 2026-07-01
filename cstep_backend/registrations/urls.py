from rest_framework.routers import DefaultRouter
from .views import MedicalAssistanceViewSet, RegistrationViewSet, TranslationAssistanceViewSet, TravelAssistanceViewSet, AccommodationAssistanceViewSet

router = DefaultRouter()
router.register("registration", RegistrationViewSet, basename="registration")
router.register("travel-assistance", TravelAssistanceViewSet)
router.register("medical-assistance", MedicalAssistanceViewSet)
router.register("translation-assistance", TranslationAssistanceViewSet)
router.register("accommodation-assistance", AccommodationAssistanceViewSet)
urlpatterns = router.urls
