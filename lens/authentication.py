import json

import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import User
from jwt.algorithms import RSAAlgorithm
from rest_framework import authentication, exceptions


class OktaAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        
        try:
            # Verify and decode the JWT token
            user_info = self.verify_token(token)
            user = self.get_user(user_info)
            
            return (user, token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')

    def verify_token(self, token):
        # Get Okta's public keys
        jwks_url = f"{settings.OKTA_DOMAIN}/v1/keys"
        jwks_response = requests.get(
            jwks_url, 
            # verify=False
        )
        jwks = jwks_response.json()
        
        # Decode the token header to get the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header['kid']
        
        # Find the correct key
        public_key = None
        for key in jwks['keys']:
            if key['kid'] == kid:
                public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            raise exceptions.AuthenticationFailed('Unable to find appropriate key')
        
        # Verify and decode the token
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=settings.OKTA_AUDIENCE,
                issuer=f"{settings.OKTA_DOMAIN}",
                # verify=False
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')

    def get_user(self, user_info):
        username = user_info.get('sub') # Okta uses 'sub' as the unique identifier
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        
        return user
