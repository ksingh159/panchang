from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.conf import settings

from core.views.user_views import ThrottledLoginView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('accounts/login/', ThrottledLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),  # authentication 
    path('accounts/', include('allauth.urls')),
]
urlpatterns += i18n_patterns(path('', include('core.urls')), prefix_default_language=False)  # /hi/... is the Hindi site
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
