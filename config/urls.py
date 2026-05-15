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


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', health_check),
    path('api/v1/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
