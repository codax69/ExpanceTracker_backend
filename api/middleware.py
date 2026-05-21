"""
Rate-limiting middleware for ExpenseIQ.
Uses Django's cache framework for per-IP request throttling.
"""

import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.middleware.csrf import get_token


class EnsureCsrfCookieMiddleware:
    """
    Ensures the CSRF cookie is set on every response.
    This is required so that JavaScript can read the csrftoken cookie
    and include it as X-CSRFToken header on POST/PUT/DELETE requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Force Django to set the CSRF cookie
        get_token(request)
        response = self.get_response(request)
        return response


class RateLimitMiddleware:
    """
    Per-IP rate limiter that blocks excessive requests.

    Settings (in settings.py):
        RATE_LIMIT_CONFIG = {
            'GLOBAL_RATE': '200/minute',     # max requests per window
            'AUTH_RATE': '10/minute',         # stricter limit for auth endpoints
            'AUTH_PATHS': ['/api/v1/auth/'],  # paths that use AUTH_RATE
            'BLOCK_DURATION': 300,            # seconds to block after exceeding
        }
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.config = getattr(settings, "RATE_LIMIT_CONFIG", {})
        self.global_limit, self.global_window = self._parse_rate(
            self.config.get("GLOBAL_RATE", "200/minute")
        )
        self.auth_limit, self.auth_window = self._parse_rate(
            self.config.get("AUTH_RATE", "10/minute")
        )
        self.auth_paths = self.config.get("AUTH_PATHS", ["/api/v1/auth/"])
        self.block_duration = self.config.get("BLOCK_DURATION", 300)

    @staticmethod
    def _parse_rate(rate_string):
        """Parse '200/minute' into (200, 60)."""
        count, period = rate_string.split("/")
        count = int(count)
        period_map = {
            "second": 1,
            "sec": 1,
            "s": 1,
            "minute": 60,
            "min": 60,
            "m": 60,
            "hour": 3600,
            "hr": 3600,
            "h": 3600,
            "day": 86400,
            "d": 86400,
        }
        seconds = period_map.get(period.lower(), 60)
        return count, seconds

    def _get_client_ip(self, request):
        """Extract the real client IP (handles proxies)."""
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def _is_rate_limited(self, key, limit, window):
        """
        Sliding window rate limiter using Django cache.
        Returns (is_limited, requests_remaining, retry_after).
        """
        now = time.time()
        cache_key = f"ratelimit:{key}"

        # Check if IP is blocked
        block_key = f"ratelimit_blocked:{key}"
        if cache.get(block_key):
            ttl = cache.ttl(block_key) if hasattr(cache, "ttl") else self.block_duration
            return True, 0, ttl

        # Get request timestamps from cache
        timestamps = cache.get(cache_key, [])
        # Remove expired timestamps
        cutoff = now - window
        timestamps = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= limit:
            # Block the IP
            cache.set(block_key, True, self.block_duration)
            return True, 0, self.block_duration

        # Record this request
        timestamps.append(now)
        cache.set(cache_key, timestamps, window + 10)
        remaining = limit - len(timestamps)
        return False, remaining, 0

    # Paths that are exempt from all rate limiting
    EXEMPT_PATHS = ["/api/v1/auth/me"]

    def __call__(self, request):
        ip = self._get_client_ip(request)
        path = request.path

        # Skip rate limiting for exempt paths
        if any(path.rstrip("/") == p.rstrip("/") for p in self.EXEMPT_PATHS):
            return self.get_response(request)

        # Determine which rate limit to apply
        is_auth_path = any(path.startswith(p) for p in self.auth_paths)
        if is_auth_path:
            limit, window = self.auth_limit, self.auth_window
            key = f"auth:{ip}"
        else:
            limit, window = self.global_limit, self.global_window
            key = f"global:{ip}"

        is_limited, remaining, retry_after = self._is_rate_limited(key, limit, window)

        if is_limited:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Too many requests. Please slow down.",
                    "retryAfter": int(retry_after),
                },
                status=429,
            )

        response = self.get_response(request)

        # Add rate limit headers to response
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(remaining)
        return response
