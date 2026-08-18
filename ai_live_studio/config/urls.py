from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import landing_view
from studio.views import obs_browser_source_view, watch_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_dashboard/', include('admin_dashboard.urls')),
    path('', landing_view, name='landing'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('studio/', include('studio.urls')),
    path('analytics/', include('analytics.urls')),
    path('billing/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('api/', include('api.urls')),
    path('pages/', include('core.pages_urls')),

    # Public, no-login-required routes
    path('watch/<uuid:stream_id>/', watch_view, name='watch'),
    path('obs/<str:token>/', obs_browser_source_view, name='obs_browser_source'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
