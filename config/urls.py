"""
Event Management System - Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from apps.management.home_views import home_view, quote_submit, how_we_work_view

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    # Redirect bare root → /en/
    path('', RedirectView.as_view(url='/en/', permanent=False)),
]

urlpatterns += i18n_patterns(
    # Admin Panel
    path('admin/', admin.site.urls),

    # AV Company Landing Page
    path('', home_view, name='home'),
    path('how-we-work/', how_we_work_view, name='how_we_work'),
    path('quote/submit/', quote_submit, name='quote_submit'),

    # Apps URLs
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('events/', include('apps.events.urls', namespace='events')),
    path('management/', include('apps.management.urls', namespace='management')),

    # API URLs
    path('api/v1/', include('apps.events.api_urls', namespace='api')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
