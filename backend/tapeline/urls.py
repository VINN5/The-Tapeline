from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Old apps
from connectors.views import DatabaseConnectionViewSet
from data_manager.views import ExtractionJobViewSet, StoredFileViewSet

# New core app
from core.views import (
    ConnectionConfigViewSet,
    ExtractionJobViewSet as CoreExtractionJobViewSet,
    FileStorageViewSet
)

# Old router
router = DefaultRouter()
router.register(r'connections', DatabaseConnectionViewSet, basename='connections')
router.register(r'jobs', ExtractionJobViewSet, basename='jobs')
router.register(r'files', StoredFileViewSet, basename='files')

# New core router
core_router = DefaultRouter()
core_router.register(r'core/connections', ConnectionConfigViewSet, basename='core-connections')
core_router.register(r'core/jobs', CoreExtractionJobViewSet, basename='core-jobs')
core_router.register(r'core/files', FileStorageViewSet, basename='core-files')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),      # Old endpoints
    path('api/', include(core_router.urls)), # New core endpoints
    path('api/auth/', include('rest_framework.urls')),
    path('api/accounts/', include('accounts.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)