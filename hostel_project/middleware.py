import time
import logging
from collections import defaultdict
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('django.security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Appends Content-Security-Policy and Permissions-Policy headers to responses.
    """
    def process_response(self, request, response):
        # Content Security Policy (allows bootstrap CDN, google fonts, chart.js CDN, local assets)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com data:",
            "img-src 'self' data: https: blob:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        # Don't overwrite if already set
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = "; ".join(csp_directives)

        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = "camera=(), microphone=(), geolocation=(), payment=()"

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Lightweight, thread-safe IP-based rate limiting middleware.
    Throttles sensitive endpoints (e.g. login, register, password reset)
    to protect against credential stuffing and brute-force attacks.
    """
    # Rate limits per minute
    AUTH_LIMIT = getattr(settings, 'RATE_LIMIT_AUTH', 15)       # 15 requests/min on auth
    GLOBAL_LIMIT = getattr(settings, 'RATE_LIMIT_GLOBAL', 200)   # 200 requests/min general

    AUTH_PREFIXES = (
        '/accounts/login/',
        '/accounts/staff-login/',
        '/accounts/register/',
        '/accounts/password-reset/',
        '/accounts/change-password/',
    )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip

    def process_request(self, request):
        # Skip static and media files
        path = request.path
        if path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL):
            return None

        ip = self.get_client_ip(request)
        now = int(time.time())
        window = now // 60  # 1-minute window bucket

        is_auth = any(path.startswith(prefix) for prefix in self.AUTH_PREFIXES)
        limit = self.AUTH_LIMIT if is_auth else self.GLOBAL_LIMIT
        scope = 'auth' if is_auth else 'global'

        cache_key = f"ratelimit:{scope}:{ip}:{window}"

        try:
            current_count = cache.get(cache_key, 0)
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for IP {ip} on {path} ({current_count}/{limit})")
                retry_after = 60 - (now % 60)
                response = HttpResponse(
                    f"<!DOCTYPE html><html><head><title>Too Many Requests</title></head>"
                    f"<body style='font-family:sans-serif;text-align:center;padding:50px;'>"
                    f"<h2>429 - Too Many Requests</h2>"
                    f"<p>Rate limit exceeded for your IP address. Please wait {retry_after} seconds before trying again.</p>"
                    f"</body></html>",
                    status=429,
                    content_type="text/html"
                )
                response['Retry-After'] = str(retry_after)
                return response

            # Increment count
            if current_count == 0:
                cache.set(cache_key, 1, timeout=90)
            else:
                try:
                    cache.incr(cache_key)
                except Exception:
                    cache.set(cache_key, current_count + 1, timeout=90)
        except Exception as e:
            # If cache is unavailable, fail open so app keeps functioning
            logger.debug(f"Rate limiting cache error: {e}")

        return None
