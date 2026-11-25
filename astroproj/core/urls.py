from django.urls import path
from django.templatetags.static import static as static_url
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import index as sitemap_index, sitemap

from .sitemaps import SITEMAPS

from . import views, views_eclipse, views_settings, view_kundali
from .views import payment_views as pv
from .views.user_views import rate_limit

# Heavy astronomy for anonymous callers: cap per IP so a script cannot tie up the server.
api_limit = rate_limit('panchang-api', 60, methods=('GET',))

urlpatterns = [
    # Landing page is the home page; the daily panchang lives at /panchang/
    path('', views.welcome, name='home'),
    path('panchang/', views.home, name='panchang'),
    path('aaj-ka-panchang/', views.aaj_ka_panchang, name='aaj_ka_panchang'),
    path('aaj-ka-panchang/<slug:city>/', views.aaj_ka_panchang_city, name='aaj_ka_panchang_city'),
    path('aaj-ka-choghadiya/', views.choghadiya, name='choghadiya'),
    path('aaj-ka-choghadiya/<slug:city>/', views.choghadiya, name='choghadiya_city'),
    path('aaj-ki-hora/', views.hora, name='hora'),
    path('aaj-ki-hora/<slug:city>/', views.hora, name='hora_city'),
    path('rashifal/', views.rashifal, name='rashifal'),
    path('rashifal/<slug:sign>/', views.rashifal_sign, name='rashifal_sign'),
    path('vrat/', views.vrat_hub, name='vrat_hub'),
    path('vrat/<slug:kind>/<int:year>/', views.vrat_list, name='vrat_list'),
    path('hindu-calendar/', views.hindu_calendar, name='hindu_calendar'),
    path('hindu-calendar/<int:year>/<slug:month>/', views.hindu_calendar, name='hindu_calendar_month'),
    path('hindu-calendar/<int:year>/<slug:month>/pdf/', rate_limit('calendar-pdf', 20, methods=('GET',))(views.hindu_calendar_pdf),
         name='hindu_calendar_pdf'),
    path('kumbh-mela/', views.kumbh_mela, name='kumbh_mela'),

    # path('transit_chart/', views.transit_chart_new, name = 'transit_chart'),
    
    # Static pages
    path('welcome/', views.welcome_redirect, name='welcome'),
    path('about/', views.about, name='about'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('faq/', views.faq, name='faq'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.article, name='article'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('refund-policy/', pv.refund_policy, name='refund_policy'),

    # Paid PDFs
    path('pay/kundali/<int:kundali_id>/', pv.buy_kundali_pdf, name='buy_kundali_pdf'),
    path('pay/aahaar/', pv.buy_aahaar_pdf, name='buy_aahaar_pdf'),
    path('pay/razorpay/verify/', pv.razorpay_verify, name='razorpay_verify'),
    path('pay/phonepe/return/<str:token>/', pv.phonepe_return, name='phonepe_return'),
    path('pay/webhook/razorpay/', pv.razorpay_webhook, name='razorpay_webhook'),
    path('pay/webhook/phonepe/', pv.phonepe_webhook, name='phonepe_webhook'),
    path('pay/order/<str:token>/', rate_limit('order-unlock', 10)(pv.order_status), name='order_status'),
    path('pay/order/<str:token>/download/', pv.order_download, name='order_download'),
    path('my-orders/', pv.my_orders, name='my_orders'),
    
    # Registration
    path('register/', views.register, name='register'),
    path('register/check-email/', views.check_email, name='check_email'),
    path('account/delete/', views.delete_account, name='delete_account'),

    
    # Location preferences
    path('set-location/', views.save_location_preferences, name='set_location'),

    # Panchang URLs
    path('festivals/', views.festival_calendar, name='festival_calendar'),
    path('festivals/<int:year>/', views.festival_calendar, name='festival_year'),
    path('festivals/<int:year>/<slug:slug>/', views.festival_detail, name='festival_detail'),
    path('panchang/date/<str:ymd>/', views.panchang_on_date, name='panchang_on_date'),

    # Panchang finder, muhurat and yoga calendars (shared cache, instant)
    path('panchang-finder/', views.panchang_finder, name='panchang_finder'),
    path('shubh-muhurat/', views.shubh_muhurat, name='shubh_muhurat'),
    path('shubh-muhurat/<slug:purpose>/<int:year>/', views.muhurat_purpose, name='muhurat_purpose'),
    path('yogas/<slug:yoga>/<int:year>/', views.yoga_calendar, name='yoga_calendar'),

    # SEO plumbing
    path('favicon.ico', RedirectView.as_view(url=static_url('favicon.svg'), permanent=True)),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('ads.txt', views.ads_txt, name='ads_txt'),
    path('<slug:key>.txt', views.indexnow_key, name='indexnow_key'),   # IndexNow ownership file (Bing)
    path('sitemap.xml', sitemap_index, {'sitemaps': SITEMAPS, 'sitemap_url_name': 'sitemap_section'}, name='sitemap'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': SITEMAPS}, name='sitemap_section'),
    path('panchang/<int:year>/<int:month>/<int:day>/<int:hour>/', 
         api_limit(views.panchang_datetime_html), name='panchang_datetime_html'),
    
    # API endpoints
    path('api/panchang/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/<lat>/<lon>/<city>',
         api_limit(views.panchang_datetime), name='panchang_datetime_api'),
    path('api/panchang/sarvarth_sidhi/<int:year>/<int:month>/', api_limit(views.sarvarth_sidhi), name='sarvarth_sidhi_api'),
    path('api/panchang/amrit_sidhi/<int:year>/<int:month>/', api_limit(views.amrit_sidhi), name='amrit_sidhi_api'),
    path('api/panchang/pushkar_yog/<int:year>/<int:month>/', api_limit(views.all_pushkar_yog), name='all_pushkar_api'),
    path('api/panchang/ravi_yoga/<int:year>/<int:month>/', api_limit(views.ravi_yoga), name='ravi_yoga_api'),
    path('panchang/anonymous/', api_limit(views.panchang_anonymous), name='panchang-anonymous'),
    path('api/kundali/<int:kundali_id>/', view_kundali.kundali_api, name='kundali_api'),

     # Auspicious Yogas
    path('auspicious-yogas/', views.auspicious_yogas_dashboard, name='auspicious_yogas'),
    path('auspicious-yogas/search/', views.yoga_search, name='yoga_search'),
    path('auspicious-yogas/stats/', views.yoga_combinations_stats, name='yoga_stats'),
    
    # Grahan and Aahaar
    path('grahan/', views.grahan_calendar, name='grahan_calendar'),
    path('grahan/<int:year>/', views.grahan_calendar, name='grahan_year'),
    path('grahan/<slug:slug>/', views.grahan_detail, name='grahan_detail'),
    path('grahan/<slug:slug>/globe.json', views.grahan_globe, name='grahan_globe'),
    path('aahaar/', views.aahaar, name='aahaar'),
    path('naamkaran/', views.naamkaran, name='naamkaran'),

    # Eclipse endpoints
    path('eclipses/', views_eclipse.list_eclipses, name='list_eclipses'),
    path('eclipses/<int:eclipse_id>/', views_eclipse.eclipse_detail, name='eclipse_detail'),

    # Settings
    path('settings/', views_settings.user_settings, name='user-settings'),
    path('settings/sync/', views_settings.sync_settings, name='sync-settings'),

    # Kundali URLs
    path('kundali/create', view_kundali.kundali_form, name='create_kundali'),
    path('kundali/generate', rate_limit('kundali-generate', 20)(view_kundali.generate_kundali), name='generate_kundali'),
    path('kundali/<int:kundali_id>/', view_kundali.kundali_detail, name='kundali_detail'),
    path('kundali/<int:kundali_id>/delete/', view_kundali.delete_kundali, name='delete_kundali'),

    
    # User Kundali management
    path('my-kundalis/', views.kundali_list, name='kundali_list'),
    
    # Keep the existing one if you need individual kundali access
    path('my-kundalis/<int:kundali_id>/', views.kundali_list, name='kundali_list_detail'),
    # path('create-kundali/', views.create_kundali, name='create_kundali'),

    # Other features
    # "kundali milan" is what people search for; the old /compatibility/ address keeps working via a 301.
    path('kundali-milan/', views.compatibility, name='compatibility'),
    path('compatibility/', RedirectView.as_view(pattern_name='compatibility', permanent=True, query_string=True)),
    path('compatibility/calculate/', views.calculate_compatibility, name='calculate_compatibility'),
    path('compatibility/city-autocomplete/', views.city_autocomplete, name='compat_city_autocomplete'),

    path('transits/', views.transit_chart_new, name='transits'),
    path('contact/', views.contact_view, name='contact'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update-birth-details/', views.update_birth_details, name='update_birth_details'),
    path('profile/update-location/', views.update_location, name='update_location'),
    path('preferences/', views.save_preferences, name='save_preferences'),
     path('api/city-autocomplete/', views.city_autocomplete, name='city_autocomplete'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
