import json
import logging
from time import monotonic

import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import User
from jwt.algorithms import RSAAlgorithm
from rest_framework import authentication, exceptions


logger = logging.getLogger(__name__)
JWKS_CACHE_TTL_SECONDS = 300
_jwks_cache = {}


def _get_jwks(jwks_url):
    """Fetch and cache Okta signing keys while allowing key rotation."""

    cached = _jwks_cache.get(jwks_url)
    if cached and cached[0] > monotonic():
        return cached[1]

    response = requests.get(jwks_url, timeout=5)
    response.raise_for_status()
    jwks = response.json()
    if not isinstance(jwks.get('keys'), list):
        raise ValueError('Okta JWKS response does not contain keys.')

    _jwks_cache[jwks_url] = (monotonic() + JWKS_CACHE_TTL_SECONDS, jwks)
    return jwks


class OktaAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.removeprefix('Bearer ').strip()
        if not token:
            raise exceptions.AuthenticationFailed('Invalid access token.')

        try:
            user_info = self.verify_token(token)
            user = self.get_user(user_info)
            return (user, token)
        except exceptions.AuthenticationFailed:
            raise
        except Exception:
            logger.warning('Okta token authentication failed.', exc_info=True)
            raise exceptions.AuthenticationFailed('Invalid access token.')

    def verify_token(self, token):
        jwks_url = f"{settings.OKTA_DOMAIN}/v1/keys"
        jwks = _get_jwks(jwks_url)

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header['kid']

        public_key = None
        for key in jwks['keys']:
            if key['kid'] == kid:
                public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                break

        if not public_key:
            _jwks_cache.pop(jwks_url, None)
            jwks = _get_jwks(jwks_url)
            for key in jwks['keys']:
                if key['kid'] == kid:
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                    break

        if not public_key:
            raise exceptions.AuthenticationFailed('Invalid access token.')

        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=settings.OKTA_AUDIENCE,
                issuer=f"{settings.OKTA_DOMAIN}",
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Invalid access token.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid access token.')

    def get_user(self, user_info):
        username = user_info.get('sub')
        if not username:
            raise exceptions.AuthenticationFailed('Invalid access token.')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid access token.')

        return user
