# core/views/page_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
import pytz

from ..utils.astro_calculations import get_panchang
from ..utils import prefs
from ..models import UserProfile



def panchang_datetime_html(request, year, month, day, hour, minute=0, lat=None, lon=None, city=None):
    """Render panchang data in HTML format"""
    from django.http import Http404
    try:
        datetime(year, month, day, hour, minute)
    except ValueError:
        raise Http404("No such date or time")
    city_name = city or ''
    try:
        # Get location preferences
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            lat = float(request.GET.get('lat', profile.latitude if profile else 19.0760))
            lon = float(request.GET.get('lon', profile.longitude if profile else 72.8777))
            timezone_str = request.GET.get('tz', profile.timezone if profile else 'Asia/Kolkata')
            city_name = request.GET.get('city', profile.city if profile else 'Mumbai')
        else:
            lat = float(request.GET.get('lat', request.session.get('lat', 19.0760)))
            lon = float(request.GET.get('lon', request.session.get('lon', 72.8777)))
            timezone_str = request.GET.get('tz', request.session.get('timezone', 'Asia/Kolkata'))
            city_name = request.GET.get('city', request.session.get('city', 'Mumbai'))
        
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.timezone('Asia/Kolkata')
        
        target_datetime = datetime(year, month, day, hour, minute)
        target_datetime = tz.localize(target_datetime)
        
        panchang_data = get_panchang(
            target_date=target_datetime,
            user=request.user if request.user.is_authenticated else None,
            lat=lat,
            lon=lon,
            timezone_str=timezone_str,
            city_name=city_name
        )
        
        context = {
            'paksha_tithi': panchang_data.get('paksha_tithi', 'N/A'),
            'tithi_end': panchang_data.get('tithi_end', 'N/A'),
            'nakshatra': panchang_data.get('nakshatra', 'N/A'),
            'nakshatra_end': panchang_data.get('nakshatra_end', 'N/A'),
            'yoga': panchang_data.get('yoga', 'N/A'),
            'yoga_end': panchang_data.get('yoga_end', 'N/A'),
            'karana': panchang_data.get('karana', 'N/A'),
            'karana_end': panchang_data.get('karana_end', 'N/A'),
            'sunrise': panchang_data.get('sunrise', 'N/A'),
            'sunset': panchang_data.get('sunset', 'N/A'),
            'moonrise': panchang_data.get('moonrise', 'N/A'),
            'moonset': panchang_data.get('moonset', 'N/A'),
            'moon_phase': panchang_data.get('moon_phase', {'illumination': 0}),
            'weekday': panchang_data.get('weekday', 'N/A'),
            'amanta_month': panchang_data.get('amanta_month', 'N/A'),
            'purnimanta_month': panchang_data.get('purnimanta_month', 'N/A'),
            'ritu_sayana': panchang_data.get('ritu_sayana', ''),
            'month_system': prefs.month_system(request),
            'ritu': panchang_data.get('ritu', 'N/A'),
            'city': city_name,
            'coordinates': f"{lat:.4f}, {lon:.4f}",
            'timezone': timezone_str,
            'planetary_positions': panchang_data.get('planetary_positions', {}),
            'target_datetime': target_datetime.strftime("%B %d, %Y %I:%M %p"),
        }
        
        return render(request, 'home.html', context)
        
    except Exception as e:
        context = {
            'error': f"Error: {str(e)}",
            'target_datetime': f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            'city': city_name,
            'coordinates': f"{lat:.4f}, {lon:.4f}",
            'timezone': timezone_str,
        }
        return render(request, 'home.html', context)

def welcome_redirect(request):
    """The landing page used to live at /welcome/; it is the home page now."""
    return redirect('home', permanent=True)

def about(request):
    from ..utils.localized import localized
    return render(request, localized('static_pages/about.html'))


def welcome(request):
    """Landing page for new visitors: what the site does, with a few live numbers to make it concrete."""
    from datetime import timedelta
    from ..utils import festival_calculations as fc, grahan as gr
    from .seo_views import user_location, _today
    lat, lon, tz, city = user_location(request)
    today = _today(tz)
    live = {"city": city}
    try:
        p = get_panchang(target_date=datetime.now(pytz.timezone(tz)), lat=lat, lon=lon, timezone_str=tz,
                         city_name=city)
        live.update(tithi=p.get("paksha_tithi"), nakshatra=p.get("nakshatra"),
                    masa=prefs.panchang_month(request, p), ritu=(p.get("ritu_sayana") or "").split(" ")[0])
    except Exception:
        pass
    try:
        fest = [f for f in fc.get_festivals_between(today, today + timedelta(days=60)) if f["importance"] == "high"]
        live["festival"] = fest[0] if fest else None
    except Exception:
        live["festival"] = None
    try:
        nxt = gr.upcoming(today, 1)
        live["grahan"] = {**nxt[0], "when": gr.local_date(nxt[0], tz)} if nxt else None
    except Exception:
        live["grahan"] = None
    return render(request, 'static_pages/welcome.html', {"live": live})

def how_it_works(request):
    from django.urls import reverse
    from ..utils.how_it_works_content import SECTIONS
    sections = [dict(s, href=reverse(s["url"]) if s.get("url") else "") for s in SECTIONS]
    return render(request, 'static_pages/how_it_works.html', {'sections': sections})

def faq(request):
    import json
    from django.utils.translation import get_language
    from ..utils.faq_content import FAQ
    faq = FAQ
    if (get_language() or "").startswith("hi"):
        from ..utils.faq_content_hi import localize
        faq = localize(FAQ)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
        for _, items in faq for q, a in items]}
    # Escape '<' so no answer text can close the <script> tag
    return render(request, 'static_pages/faq.html',
                  {'faq': faq, 'faq_ld': json.dumps(ld, ensure_ascii=False).replace('<', '\\u003c')})

def blog(request):
    from ..models import Article
    topic = request.GET.get('topic', '')
    articles = Article.objects.filter(status='published')
    if topic in dict(Article.TOPICS):
        articles = articles.filter(topic=topic)
    return render(request, 'static_pages/blog.html', {'articles': articles[:60], 'topics': Article.TOPICS,
                                                       'topic': topic})


def article(request, slug):
    from django.shortcuts import get_object_or_404
    from ..models import Article
    import json
    from django.conf import settings
    from ..utils import muhurat as mu
    from ..utils.articles import render_body, render_markdown
    qs = Article.objects.all() if request.user.is_staff else Article.objects.filter(status='published')
    a = get_object_or_404(qs, slug=slug)        # staff can preview drafts
    more = Article.objects.filter(status='published', topic=a.topic).exclude(pk=a.pk)[:4]
    body = render_markdown(a.body) if a.body_format == 'markdown' else render_body(a.body)
    url = settings.SITE_URL.rstrip('/') + a.get_absolute_url()
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": a.title, "description": a.summary,
           "mainEntityOfPage": url, "inLanguage": "en-IN",
           "datePublished": a.published_at.isoformat() if a.published_at else None,
           "dateModified": a.updated_at.isoformat() if a.updated_at else None,
           "author": {"@type": "Organization", "name": settings.SITE_NAME},
           "publisher": {"@type": "Organization", "name": settings.SITE_NAME}}]
    if a.faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in a.faq]})
    year = (a.published_at or a.updated_at).year
    muhurat_links = [(p, mu.PURPOSES[p]["title"], year) for p in a.muhurat_purposes if p in mu.PURPOSES]
    return render(request, 'static_pages/article.html', {
        'a': a, 'body': body, 'more': more, 'muhurat_links': muhurat_links,
        # Escape '<' so no text can close the <script> tag
        'ld': [json.dumps(x, ensure_ascii=False).replace('<', '\\u003c') for x in ld]})


def shipping_policy(request):
    from ..utils import payments as pay
    from ..utils.localized import localized
    return render(request, localized('static_pages/shipping_policy.html'),
                  {'limit': pay.DOWNLOAD_LIMIT, 'days': pay.DOWNLOAD_DAYS})

def privacy(request):
    from ..utils.localized import localized
    return render(request, localized('static_pages/privacy.html'))

def terms(request):
    from ..utils.localized import localized
    return render(request, localized('static_pages/terms.html'))

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    """Contact details and the feedback form. Messages are saved for the admin and, when mail is set up, emailed."""
    from django.conf import settings
    from django.contrib import messages
    from django.utils.translation import gettext
    from ..forms import ContactForm
    from .user_views import _throttled
    initial = {'kind': request.GET.get('kind', 'feedback'), 'order_ref': request.GET.get('order', ''),
               'page': request.GET.get('from', '')[:200]}
    if request.user.is_authenticated:
        initial.update(name=request.user.get_full_name() or request.user.username, email=request.user.email)
    form = ContactForm(request.POST or None, initial=initial)
    if request.method == 'POST':
        if form.is_valid() and not form.cleaned_data.get('website'):      # 'website' is a hidden honeypot
            if _throttled(request, 'contact', 5, 3600):
                messages.error(request, gettext('Too many messages from this connection. Please try again in an hour.'))
            else:
                msg = form.save(commit=False)
                msg.user = request.user if request.user.is_authenticated else None
                msg.save()
                _notify_owner(msg, settings)
                messages.success(request, gettext('Thank you. Your message has reached us; we reply by email.'))
                return redirect('contact')
        elif form.is_valid():
            return redirect('contact')        # a bot filled the honeypot: pretend all went well
    return render(request, 'static_pages/contact.html', {'form': form})


def _notify_owner(msg, settings):
    """Email the owner about a new message, in a background thread: the visitor's page never waits on the mail
    service (the message is already saved for the admin either way)."""
    if not (settings.CONTACT_EMAIL and getattr(settings, 'EMAIL_READY', False)):
        return
    import logging
    import threading
    from django.core.mail import EmailMessage
    email = EmailMessage(subject=f"[{settings.SITE_NAME}] {msg.get_kind_display()} from {msg.name}",
                         body=f"{msg.message}\n\nFrom: {msg.name} <{msg.email}>\nOrder: {msg.order_ref or '-'}\n"
                              f"Page: {msg.page or '-'}",
                         to=[settings.CONTACT_EMAIL], reply_to=[msg.email])

    def send():
        try:
            email.send()
        except Exception:
            logging.getLogger(__name__).exception("Could not email the owner about contact message %s", msg.pk)

    threading.Thread(target=send, name="contact-mail", daemon=True).start()

def panchang(request):
    # Panchang data logic
    return render(request, 'panchang2.html')