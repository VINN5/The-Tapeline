from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConnectionConfigViewSet, ExtractionJobViewSet

router = DefaultRouter()
router.register(r'connections', ConnectionConfigViewSet)
router.register(r'jobs', ExtractionJobViewSet)

urlpatterns = [
    path('', include(router.urls)),
]