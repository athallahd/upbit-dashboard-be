import json
from typing import List, Optional, Type

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user, get_user_model, login, logout
from django.contrib.auth.models import AbstractUser
from django.http import (HttpRequest, HttpResponse, HttpResponseForbidden,
                         HttpResponseRedirect)
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class CloudflareJwtAdminAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # only authenticate when PRODUCTION mode
        if settings.DEBUG:
            return

        # only authenticate for admin access
        if not request.path.startswith(reverse('admin:index')):
            return

        if 'CF_Authorization' not in request.COOKIES:
            logout(request)
            return HttpResponseForbidden('No Authorization token was provided from Cloudflare.')

        token: str = request.COOKIES['CF_Authorization']
        keys = _get_public_keys()

        access_email = _get_access_email_from_token(token, keys)

        if not access_email:
            logout(request)
            return HttpResponseForbidden('Authorization token provided by Cloudflare could not be identified.')

        if not get_user(request).is_authenticated:
            access_user = _get_or_create_superuser(access_email)
            login(request, access_user)

        return


def _get_access_email_from_token(token: str, keys: List[str]) -> Optional[str]:
    for key in keys:
        try:
            decoded: dict = jwt.decode(token, key=key, audience=settings.CLOUDFLARE_AUTH_POLICY_AUD)
            if 'email' in decoded.keys():
                return decoded.get('email')
        except Exception:
            pass

    return


def _get_public_keys() -> List[str]:
    """Return list of RSA public keys usable by PyJWT."""
    jwk_set: dict = requests.get(f'{settings.CLOUDFLARE_AUTH_DOMAIN}/cdn-cgi/access/certs').json()
    public_keys: List[str] = []

    for key_dict in jwk_set['keys']:
        public_key: str = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_dict))
        public_keys.append(public_key)

    return public_keys


def _get_or_create_superuser(email: str) -> AbstractUser:
    user_model: Type[AbstractUser] = get_user_model()
    if user_model.objects.using('reporter').filter(email=email).exists():
        return user_model.objects.using('reporter').get(email=email)

    username = email.split('@')[0]
    return user_model.objects.using('reporter').create_superuser(username, email)


class SAMLRequiredMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    # Check if request is for admin login page (adjust path if needed)
    if request.path == '/admin/login/':
        # If valid assertion (or no assertion check):
        if request.user.is_authenticated:
            return self.get_response(request)
        else:
            # Redirect to SAML login initiation endpoint
            return HttpResponseRedirect('https://dunamu.okta.com/')
    else:
        # Pass through for other URLs (optional, can be removed)
        return self.get_response(request)
