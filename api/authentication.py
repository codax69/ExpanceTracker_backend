"""
Custom JWT Cookie Authentication for ExpenseIQ.
Reads access tokens from HTTP-only cookies instead of Authorization headers.
This prevents XSS attacks from stealing tokens.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads the access token from an
    HTTP-only cookie ('access_token') instead of the Authorization header.
    Falls back to header-based auth if no cookie is present.
    """

    def authenticate(self, request):
        # 1. Try reading from the HTTP-only cookie first
        raw_token = request.COOKIES.get(settings.JWT_COOKIE_NAMES['access'])

        if raw_token is None:
            # 2. Fall back to standard Authorization header
            return super().authenticate(request)

        # 3. Validate the token from the cookie
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except (InvalidToken, TokenError):
            return None


def get_tokens_for_user(user):
    """Generate access + refresh token pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def set_token_cookies(response, tokens):
    """
    Set access and refresh tokens as HTTP-only, secure cookies.
    - access_token:  short-lived (15 min), used for API auth
    - refresh_token: long-lived (7 days), used to rotate access tokens
    """
    access_max_age = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
    refresh_max_age = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
    secure = not settings.DEBUG  # Only Secure in production (HTTPS)

    response.set_cookie(
        key=settings.JWT_COOKIE_NAMES['access'],
        value=tokens['access'],
        max_age=int(access_max_age),
        httponly=True,
        secure=secure,
        samesite='Lax',
        path='/',
    )
    response.set_cookie(
        key=settings.JWT_COOKIE_NAMES['refresh'],
        value=tokens['refresh'],
        max_age=int(refresh_max_age),
        httponly=True,
        secure=secure,
        samesite='Lax',
        path='/',
    )
    return response


def clear_token_cookies(response):
    """Delete both token cookies on logout."""
    response.delete_cookie(settings.JWT_COOKIE_NAMES['access'], path='/', samesite='Lax')
    response.delete_cookie(settings.JWT_COOKIE_NAMES['refresh'], path='/', samesite='Lax')
    return response
