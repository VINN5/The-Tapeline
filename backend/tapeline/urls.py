from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Old apps
from connectors.views import DatabaseConnectionViewSet
from data_manager.views import ExtractionJobViewSet, StoredFileViewSet

# New core app
from core.views import (
    ConnectionConfigViewSet,
    ExtractionJobViewSet as CoreExtractionJobViewSet,
    FileStorageViewSet,
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

    # API routes
    path('api/', include(router.urls)),
    path('api/', include(core_router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    path('api/accounts/', include('accounts.urls')),

    # Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)