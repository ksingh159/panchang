from pathlib import Path
import os

from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# Secrets and deployment switches come from the environment or a .env file
# (never commit .env).  The fallbacks below are for local development only.
SECRET_KEY = config('DJANGO_SECRET_KEY', default='dev-only-insecure-key-change-me')
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('DJANGO_CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.humanize',

    # Third party
    'rest_framework',

    # Social Auth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.twitter',
    'allauth.socialaccount.providers.instagram',

    # Our app
    'core',
]

MIDDLEWARE = [
    'core.middleware.CanonicalHostMiddleware',          # www -> bare domain, 301, one hop (needs SITE_URL)
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',      # serves /static/ itself (waitress, gunicorn, Railway)
    'core.security.ContentSecurityPolicyMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.DailyHousekeepingMiddleware',     # daily PDF purge on the server (core/utils/pdf_store.py)
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ROOT_URLCONF = 'astroproj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site',
                'core.security.csp_nonce',
            ],
        },
    },
]

WSGI_APPLICATION = 'astroproj.wsgi.application'

# Database: SQLite on this machine; on Railway the Postgres service sets DATABASE_URL and that is used instead
# (Railway's disk is wiped on every deploy, so SQLite there would lose all users and orders).
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600)
}

if not DEBUG and SECRET_KEY == 'dev-only-insecure-key-change-me':
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY on the server before turning DEBUG off.')

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
LANGUAGES = [('en', 'English'), ('hi', 'हिन्दी')]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = False

# Static files
# AGPL section 13: every visitor must be able to get the source
SOURCE_URL = config('SOURCE_URL', default='https://github.com/ksingh159/panchang')

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SEO / monetisation
SITE_NAME = config('SITE_NAME', default='Varanasi Panchang')   # the site's name, here or in .env
SITE_NAME_HI = config('SITE_NAME_HI', default='वाराणसी पंचांग')
SITE_TAGLINE = config('SITE_TAGLINE', default='Know Your Time')
SITE_TAGLINE_HI = config('SITE_TAGLINE_HI', default='अपना समय जानें')
SITE_DESCRIPTION = ("Know your time: free Hindu panchang, festival calendar by Kashi (Varanasi) rules, shubh muhurat, "
                    "kundali, kundali milan and planetary transits.")
INDEXNOW_KEY = config('INDEXNOW_KEY', default='')         # Bing/IndexNow ping after the 05:30 IST build; off when empty
SITE_URL = config('SITE_URL', default='')                 # e.g. https://www.example.com (used for canonical + sitemap)
# Morning panchang notification (Web Push). Make the pair once with `python manage.py vapid_keys` and never change
# it: browsers subscribed with the old public key stop receiving. The button is hidden while these are empty.
VAPID_PUBLIC_KEY = config('VAPID_PUBLIC_KEY', default='')
VAPID_PRIVATE_KEY = config('VAPID_PRIVATE_KEY', default='')
VAPID_SUBJECT = config('VAPID_SUBJECT', default='') or SITE_URL or 'https://localhost'   # push services' contact
ADSENSE_CLIENT_ID = config('ADSENSE_CLIENT_ID', default='')  # e.g. ca-pub-1234567890123456
ADSENSE_SLOT_ID = config('ADSENSE_SLOT_ID', default='')      # display ad unit id for in-content slots
GA_MEASUREMENT_ID = config('GA_MEASUREMENT_ID', default='')
# Shown on About / Contact / Privacy pages - set real values before applying for AdSense
SITE_OWNER = config('SITE_OWNER', default='')
CONTACT_EMAIL = config('CONTACT_EMAIL', default='')
# Razorpay's website check wants the legal name, an address and a phone number on the Contact page.
CONTACT_PHONE = config('CONTACT_PHONE', default='')
BUSINESS_ADDRESS = config('BUSINESS_ADDRESS', default='')     # e.g. "12 Example Road, Varanasi, Uttar Pradesh 221001"
GRIEVANCE_OFFICER = config('GRIEVANCE_OFFICER', default='')   # name shown under the IT Rules 2021 grievance clause
JURISDICTION_CITY = config('JURISDICTION_CITY', default='')   # courts named in the Terms, e.g. Varanasi
# Outgoing mail (contact-form alerts). For Gmail: smtp.gmail.com, 587, the address, and a Google "app password".
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'webmaster@localhost')
# Railway's Hobby plan blocks outgoing SMTP, so on the server mail goes out over HTTPS through Resend when
# RESEND_API_KEY is set (DEFAULT_FROM_EMAIL must then be an address on the domain verified in Resend).
RESEND_API_KEY = config('RESEND_API_KEY', default='')
if RESEND_API_KEY:
    EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
    ANYMAIL = {'RESEND_API_KEY': RESEND_API_KEY, 'REQUESTS_TIMEOUT': 10}
EMAIL_TIMEOUT = 10          # seconds; a stuck mail server must never hang a page
# True when some way of sending mail is configured; without it, nothing tries to send.
EMAIL_READY = bool(RESEND_API_KEY or EMAIL_HOST_USER)

# Paid PDFs. Keys come from the Razorpay and PhonePe dashboards; leave blank to hide a gateway.
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='')
RAZORPAY_WEBHOOK_SECRET = config('RAZORPAY_WEBHOOK_SECRET', default='')
PHONEPE_CLIENT_ID = config('PHONEPE_CLIENT_ID', default='')
PHONEPE_CLIENT_SECRET = config('PHONEPE_CLIENT_SECRET', default='')
PHONEPE_CLIENT_VERSION = config('PHONEPE_CLIENT_VERSION', default='1')
PHONEPE_ENV = config('PHONEPE_ENV', default='SANDBOX')            # SANDBOX or PRODUCTION
PHONEPE_WEBHOOK_USER = config('PHONEPE_WEBHOOK_USER', default='')
PHONEPE_WEBHOOK_PASSWORD = config('PHONEPE_WEBHOOK_PASSWORD', default='')
# "Test payment" button that marks an order paid without a gateway; never shown when DEBUG is off
PAYMENTS_ALLOW_TEST = config('PAYMENTS_ALLOW_TEST', default=True, cast=bool)

# Errors and audit lines. Everything goes to the console, which Railway keeps as the service log; server errors (500)
# are also emailed to ERROR_EMAIL. Without this, Django drops production tracebacks (its console handler is DEBUG-only
# and ADMINS was empty).
ERROR_EMAIL = config('ERROR_EMAIL', default='')
ADMINS = [('Site owner', ERROR_EMAIL)] if ERROR_EMAIL else []
SERVER_EMAIL = DEFAULT_FROM_EMAIL
DEFAULT_EXCEPTION_REPORTER_FILTER = 'core.security.PrivateExceptionReporterFilter'   # no personal data in crash emails
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'plain': {'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'}},
    'filters': {'prod': {'()': 'django.utils.log.RequireDebugFalse'}},
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'plain'},
        'mail_admins': {'class': 'django.utils.log.AdminEmailHandler', 'level': 'ERROR', 'filters': ['prod']},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django.request': {'handlers': ['console', 'mail_admins'], 'level': 'WARNING', 'propagate': False},
        'django.security': {'handlers': ['console', 'mail_admins'], 'level': 'WARNING', 'propagate': False},
    },
}
# Request header carrying the visitor's country from the CDN (Cloudflare sends CF-IPCountry)
COUNTRY_HEADER = config('COUNTRY_HEADER', default='HTTP_CF_IPCOUNTRY')
# Owner password for PDF permissions (no copying or editing). Derived from SECRET_KEY if unset.
PDF_OWNER_PASSWORD = config('PDF_OWNER_PASSWORD', default='')

# Bought PDFs are saved on first download and served from here after (see core/utils/pdf_store.py).
# Private: outside MEDIA_ROOT and STATIC_ROOT, so no URL reaches it. For S3 / Cloudflare R2 set
# PDF_STORAGE_BACKEND=storages.backends.s3.S3Storage and the AWS_* settings of django-storages.
# Purge expired files daily: `python manage.py purge_order_pdfs`.
PDF_STORAGE_ROOT = config('PDF_STORAGE_ROOT', default=str(BASE_DIR / 'private' / 'order_pdfs'))
# The web service deletes expired PDFs itself once a day (a Railway volume belongs to one service only).
PDF_PURGE_IN_WEB = config('PDF_PURGE_IN_WEB', default=not DEBUG, cast=bool)
PDF_STORAGE_BACKEND = config('PDF_STORAGE_BACKEND', default='django.core.files.storage.FileSystemStorage')
_pdf_on_disk = PDF_STORAGE_BACKEND.endswith('FileSystemStorage')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    # Manifest storage writes each file under a content-hashed name (pages.3f9a1c2b4d5e.css) and {% static %} links to
    # it, so WhiteNoise can tell browsers and Cloudflare to keep it for a year: a changed file gets a new name.
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    'pdfs': {'BACKEND': PDF_STORAGE_BACKEND,
             'OPTIONS': {'location': PDF_STORAGE_ROOT, 'base_url': None} if _pdf_on_disk else {}},
}
import sys
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    # Tests run without collectstatic, so there are no hashed copies to link to.
    STORAGES['staticfiles'] = {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}

# Shared, persistent cache for computed muhurat / yoga results: one visitor computes,
# everyone after gets it instantly.  DB cache needs `manage.py createcachetable`;
# point CACHE_BACKEND at Redis (django.core.cache.backends.redis.RedisCache) when available.
CACHES = {
    'default': {
        'BACKEND': config('CACHE_BACKEND', default='django.core.cache.backends.db.DatabaseCache'),
        'LOCATION': config('CACHE_LOCATION', default='django_cache'),
        'TIMEOUT': 60 * 60 * 6,
    }
}
if CACHES['default']['BACKEND'].endswith('DatabaseCache'):
    # The default of 300 entries would make every rate-limit key push a cached panchang or muhurat out.
    CACHES['default']['OPTIONS'] = {'MAX_ENTRIES': 200000, 'CULL_FREQUENCY': 4}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    # Railway's healthcheck calls /robots.txt over plain HTTP with Host healthcheck.railway.app and needs a 200.
    SECURE_REDIRECT_EXEMPT = [r'^robots\.txt$']
    if 'healthcheck.railway.app' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('healthcheck.railway.app')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# WhiteNoise: while DEBUG is on, serve straight from static/ (no collectstatic needed); in production it serves the
# collected, gzip/brotli-compressed copies in STATIC_ROOT, so run `collectstatic` in the build step.
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG
# A file missing from the manifest (or no manifest, as in tests) falls back to its plain name instead of a 500.
WHITENOISE_MANIFEST_STRICT = False

# The admin lives at a secret address. Set ADMIN_URL in the server's environment (this repo is public, so the default
# below is not a secret): e.g. ADMIN_URL=ops-7f3k2q9x/
ADMIN_URL = config('ADMIN_URL', default='site-admin/').strip('/') + '/'

# Content-Security-Policy (core/security.py). True = only report violations in the browser console.
CSP_REPORT_ONLY = config('CSP_REPORT_ONLY', default=False, cast=bool)

# How many proxies sit in front of Django and append to X-Forwarded-For (Railway: 1; Railway behind Cloudflare: 2).
# Used to find the visitor's real IP for rate limits; anything left of that is client-supplied and ignored.
NUM_PROXIES = config('NUM_PROXIES', default=0 if DEBUG else 1, cast=int)

# The API speaks JSON only: no browsable HTML pages to probe.
REST_FRAMEWORK = {'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer']}

# Site ID for allauth
SITE_ID = 1

# Session settings - 30 days
SESSION_COOKIE_AGE = 30 * 24 * 60 * 60  # 30 days in seconds
SESSION_SAVE_EVERY_REQUEST = False   # True would write the session row on every page view (a DB write per request)
SESSION_COOKIE_HTTPONLY = True

# Allauth settings
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_METHODS = ['email']
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Social Account Settings
ACCOUNT_ADAPTER = 'core.adapters.SafeMailAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'core.adapters.CustomSocialAccountAdapter'  # FIXED THIS LINE
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True

# Social Auth Providers
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": config('GOOGLE_OAUTH_CLIENT_ID', default=''),
            "secret": config('GOOGLE_OAUTH_SECRET', default=''),
            "key": "",
        },
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        }
    }
}

# Redirect URLs
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'


# Static files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'