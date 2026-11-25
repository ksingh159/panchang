from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.conf import settings

from core.views.user_views import ThrottledLoginView, rate_limit
from core.views import app_views

urlpatterns = [
    # Install-as-app and the morning notification: one app and one service worker for both languages
    path('sw.js', app_views.service_worker, name='service_worker'),
    path('manifest.webmanifest', app_views.manifest, name='manifest'),
    path('manifest-hi.webmanifest', app_views.manifest, {'hindi': True}, name='manifest_hi'),
    path('offline/', app_views.offline, name='offline'),
    path('push/subscribe/', rate_limit('push-subscribe', 10)(app_views.push_subscribe), name='push_subscribe'),
    path('push/unsubscribe/', rate_limit('push-unsubscribe', 10)(app_views.push_unsubscribe), name='push_unsubscribe'),
    path(settings.ADMIN_URL, admin.site.urls),
    path('accounts/login/', ThrottledLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),  # authentication 
    path('accounts/', include('allauth.urls')),
]
urlpatterns += i18n_patterns(path('', include('core.urls')), prefix_default_language=False)  # /hi/... is the Hindi site
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
