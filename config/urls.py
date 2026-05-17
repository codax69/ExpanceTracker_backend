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

from django.contrib.auth.decorators import login_required
from api.views.auth_views import login_view, register_view, logout_view, profile_view, password_reset_view

urlpatterns = [
    path('', login_required(TemplateView.as_view(template_name='index.html')), name='home'),
    path('expenses/', login_required(TemplateView.as_view(template_name='expenses.html')), name='expenses'),
    path('budget/', login_required(TemplateView.as_view(template_name='budget.html')), name='budget'),
    path('categories/', login_required(TemplateView.as_view(template_name='categories.html')), name='categories'),

    path('settings/', login_required(TemplateView.as_view(template_name='settings.html')), name='settings'),
    path('profile/', profile_view, name='profile'),
    
    # Auth Routes
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', password_reset_view, name='password_reset'),

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
