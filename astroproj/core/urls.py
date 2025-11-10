from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views, views_mantra, views_eclipse, views_settings, view_kundali

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # path('transit_chart/', views.transit_chart_new, name = 'transit_chart'),
    
    # Static pages
    path('about/', views.about, name='about'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('faq/', views.faq, name='faq'),
    path('blog/', views.blog, name='blog'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    
    # Registration
    path('register/', views.register, name='register'),

    
    # Location preferences
    path('set-location/', views.save_location_preferences, name='set_location'),

    # Panchang URLs
    path('panchang/', views.panchang_view, name='panchang'),
    path('panchang/<int:year>/<int:month>/<int:day>/<int:hour>/', 
         views.panchang_datetime_html, name='panchang_datetime_html'),
    
    # API endpoints
    path('api/panchang/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/<lat>/<lon>/<str:city>',
         views.panchang_datetime, name='panchang_datetime_api'),
    path('api/panchang/sarvarth_sidhi/<int:year>/<int:month>/', views.sarvarth_sidhi, name='sarvarth_sidhi_api'),
    path('api/panchang/amrit_sidhi/<int:year>/<int:month>/', views.amrit_sidhi, name='amrit_sidhi_api'),
    path('api/panchang/pushkar_yog/<int:year>/<int:month>/', views.all_pushkar_yog, name='all_pushkar_api'),
    path('api/panchang/ravi_yoga/<int:year>/<int:month>/', views.ravi_yoga, name='ravi_yoga_api'),
    path('panchang/anonymous/', views.panchang_anonymous, name='panchang-anonymous'),
    path('api/kundali/<int:kundali_id>/', view_kundali.kundali_api, name='kundali_api'),

     # Auspicious Yogas
    path('auspicious-yogas/', views.auspicious_yogas_dashboard, name='auspicious_yogas'),
    path('auspicious-yogas/search/', views.yoga_search, name='yoga_search'),
    path('auspicious-yogas/stats/', views.yoga_combinations_stats, name='yoga_stats'),
    
    # Mantra endpoints
    path('mantra/analyze/', views_mantra.analyze_mantra, name='analyze_mantra'),
    
    # Eclipse endpoints
    path('eclipses/update/', views_eclipse.update_eclipse_database, name='update_eclipses'),
    path('eclipses/', views_eclipse.list_eclipses, name='list_eclipses'),
    path('eclipses/<int:eclipse_id>/', views_eclipse.eclipse_detail, name='eclipse_detail'),
    path('eclipses/<int:eclipse_id>/path/', views_eclipse.eclipse_path_visualization, name='eclipse_path'),
    path('eclipses/cleanup/', views_eclipse.cleanup_eclipse_data, name='cleanup_eclipse_data'),
    path('eclipses/debug-db/', views_eclipse.debug_database_eclipses, name='debug_database'),

    # Settings
    path('settings/', views_settings.user_settings, name='user-settings'),
    path('settings/sync/', views_settings.sync_settings, name='sync-settings'),

    # Kundali URLs
    path('kundali/create', view_kundali.kundali_form, name='create_kundali'),
    path('kundali/generate', view_kundali.generate_kundali, name='generate_kundali'),
    path('kundali/<int:kundali_id>/', view_kundali.kundali_detail, name='kundali_detail'),
    path('kundali/<int:kundali_id>/delete/', view_kundali.delete_kundali, name='delete_kundali'),

    
    # User Kundali management
    path('my-kundalis/', views.kundali_list, name='kundali_list'),
    
    # Keep the existing one if you need individual kundali access
    path('my-kundalis/<int:kundali_id>/', views.kundali_list, name='kundali_list_detail'),
    # path('create-kundali/', views.create_kundali, name='create_kundali'),

    # Other features
    path('compatibility/', views.compatibility, name='compatibility'),
    path('compatibility/calculate/', views.calculate_compatibility, name='calculate_compatibility'),
    path('compatibility/city-autocomplete/', views.city_autocomplete, name='city_autocomplete'),

    path('transits/', views.transit_chart_new, name='transits'),
    path('contact/', views.contact_view, name='contact'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update-birth-details/', views.update_birth_details, name='update_birth_details'),
    path('profile/update-location/', views.update_location, name='update_location'),
     path('api/city-autocomplete/', views.city_autocomplete, name='city_autocomplete'),

    path('debug-profile/', views.debug_profile, name='debug_profile'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)