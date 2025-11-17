from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.schemas import get_schema_view

schema_view = get_schema_view(
    title="DFitness API",
    description="Default DRF generated OpenAPI schema",
    version="1.0.0",
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('fitproject.api.urls')),
    # path('api-auth/', include('rest_framework.urls'))
    path('api/schema/', schema_view, name='openapi-schema'),  # raw JSON (add ?format=openapi)

    
    
    # # YOUR PATTERNS
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # # Optional UI:
    # path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
