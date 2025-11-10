from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # authentication 
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),  # All your app URLs
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
