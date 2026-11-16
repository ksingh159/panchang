"""
Content-Security-Policy.

Every HTML response gets a fresh random nonce. Templates put it on each <script> tag (``nonce="{{ csp_nonce }}"``),
so only scripts we wrote run: an injected <script> or onclick="" has no nonce and the browser refuses it. That is
why templates use data-click / data-change attributes instead of inline handlers (see the helper in base.html).

'strict-dynamic' lets a trusted script load the scripts it needs (AdSense, Google Analytics and Razorpay load more
files from Google / Razorpay hosts we cannot list in advance). 'https:' and 'unsafe-inline' are only fallbacks for
old browsers that do not understand nonces; modern browsers ignore them when a nonce is present.

The admin uses its own static files only, so it gets a plain 'self' policy. Set CSP_REPORT_ONLY=True to watch for
breakage in the browser console without blocking anything.
"""
import secrets

from django.conf import settings


def _site_policy(nonce):
    parts = [
        "default-src 'self'",
        f"script-src 'nonce-{nonce}' 'strict-dynamic' https: 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "img-src 'self' data: blob: https:",
        "font-src 'self' data: https://fonts.gstatic.com",
        "connect-src 'self' https:",
        "frame-src https:",
        "worker-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self' https:",       # Google sign-in and PhonePe are reached by form POST + redirect
        "frame-ancestors 'none'",
    ]
    if not settings.DEBUG:
        parts.append("upgrade-insecure-requests")
    return "; ".join(parts)


_ADMIN_POLICY = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                 "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'")


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(18)
        response = self.get_response(request)
        if not response.get("Content-Type", "").startswith("text/html"):
            return response
        header = "Content-Security-Policy-Report-Only" if getattr(settings, "CSP_REPORT_ONLY", False) \
            else "Content-Security-Policy"
        if header in response:
            return response
        admin = "/" + settings.ADMIN_URL.strip("/") + "/"
        response[header] = _ADMIN_POLICY if request.path.startswith(admin) else _site_policy(request.csp_nonce)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), usb=(), geolocation=(self)")
        return response


def csp_nonce(request):
    """Context processor: {{ csp_nonce }} in every template rendered with a request."""
    return {"csp_nonce": getattr(request, "csp_nonce", "")}


from django.views.debug import SafeExceptionReporterFilter


class PrivateExceptionReporterFilter(SafeExceptionReporterFilter):
    """What a crash email may contain. Django's default filter hides values by *name* only, so the session cookie
    ("sessionid") and every local variable (birth date, place, buyer email) would be sent in clear. Here every POST
    value, cookie, local variable and request header except a few harmless ones is replaced with stars; the
    traceback lines, the URL and the error itself stay, which is what fixing the bug needs."""
    KEEP_META = {"REQUEST_METHOD", "PATH_INFO", "SERVER_NAME", "SERVER_PORT", "HTTP_HOST", "CONTENT_TYPE",
                 "HTTP_USER_AGENT", "HTTP_ACCEPT_LANGUAGE"}

    def is_active(self, request):
        return True

    def get_post_parameters(self, request):
        if request is None:
            return {}
        post = request.POST.copy()
        for k in post:
            post[k] = self.cleansed_substitute
        return post

    def get_safe_cookies(self, request):
        return {k: self.cleansed_substitute for k in getattr(request, "COOKIES", {})}

    def get_safe_request_meta(self, request):
        meta = getattr(request, "META", {})
        return {k: (v if k in self.KEEP_META else self.cleansed_substitute) for k, v in meta.items()}

    def get_traceback_frame_variables(self, request, tb_frame):
        return [(name, self.cleansed_substitute) for name in tb_frame.f_locals]
