"""Root URL configuration for ExpenseIQ Django backend."""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
import time

_start_time = time.time()


def health_check(request):
    """Health check endpoint matching Node.js format."""
    from datetime import datetime, timezone
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime': round(time.time() - _start_time, 2),
    })


from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('admin/', admin.site.urls),
    path('health', health_check),
    path('api/v1/', include('api.urls')),
    
    # Swagger docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
