from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jwt
from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed

from lens.authentication import OktaAuthentication, _get_jwks, _jwks_cache


@override_settings(
    OKTA_DOMAIN="https://example.okta.com/oauth2/default",
    OKTA_AUDIENCE="api://default",
)
class OktaAuthenticationTests(SimpleTestCase):
    def setUp(self):
        _jwks_cache.clear()
        self.authentication = OktaAuthentication()

    def test_missing_bearer_header_defers_to_other_authentication_backends(self):
        request = SimpleNamespace(META={})

        self.assertIsNone(self.authentication.authenticate(request))

    def test_empty_bearer_token_is_rejected_without_internal_detail(self):
        request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer "})

        with self.assertRaisesMessage(AuthenticationFailed, "Invalid access token."):
            self.authentication.authenticate(request)

    @patch("lens.authentication.requests.get")
    def test_jwks_response_is_cached(self, get):
        response = MagicMock()
        response.json.return_value = {"keys": []}
        get.return_value = response

        first = _get_jwks("https://example.okta.com/oauth2/default/v1/keys")
        second = _get_jwks("https://example.okta.com/oauth2/default/v1/keys")

        self.assertEqual(first, second)
        get.assert_called_once_with(
            "https://example.okta.com/oauth2/default/v1/keys",
            timeout=5,
        )
        response.raise_for_status.assert_called_once()

    def test_valid_verified_subject_returns_allowlisted_user(self):
        request = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer token"})
        user = SimpleNamespace(is_authenticated=True)

        with (
            patch.object(self.authentication, "verify_token", return_value={"sub": "okta-sub"}),
            patch.object(self.authentication, "get_user", return_value=user),
        ):
            result = self.authentication.authenticate(request)

        self.assertEqual(result, (user, "token"))

    @patch("lens.authentication.RSAAlgorithm.from_jwk")
    @patch("lens.authentication.jwt.get_unverified_header")
    @patch("lens.authentication._get_jwks")
    @patch("lens.authentication.jwt.decode")
    def test_expired_token_returns_generic_error(
        self,
        decode,
        get_jwks,
        get_header,
        from_jwk,
    ):
        get_jwks.return_value = {"keys": [{"kid": "key-1"}]}
        get_header.return_value = {"kid": "key-1"}
        from_jwk.return_value = object()
        decode.side_effect = jwt.ExpiredSignatureError()

        with self.assertRaisesMessage(AuthenticationFailed, "Invalid access token."):
            self.authentication.verify_token("expired-token")

    def test_unknown_subject_returns_generic_error(self):
        with patch("lens.authentication.User.objects.get", side_effect=User.DoesNotExist):
            with self.assertRaisesMessage(AuthenticationFailed, "Invalid access token."):
                self.authentication.get_user({"sub": "unknown"})
