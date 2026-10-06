from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import base64
import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from app.api.security import (
    clear_jwks_cache,
    require_jwt,
    require_scope,
)
from app.config import get_settings


MANIFOLD_ISSUER = "manifold-api"
COMPOSITION_ENGINE_AUDIENCE = "composition-engine"


def _base64url_encode(value: bytes) -> str:
    return (
        base64.urlsafe_b64encode(value)
        .rstrip(b"=")
        .decode("ascii")
    )

@pytest.fixture
def app():
    application = FastAPI()

    @application.get("/protected")
    def protected(
        payload: dict = Depends(require_jwt),
    ):
        return {
            "authenticated": True,
            "subject": payload["sub"],
        }

    @application.get("/calculate")
    def calculate(
        payload: dict = Depends(
            require_scope("composition:calculate")
        ),
    ):
        return {
            "calculated": True,
            "subject": payload["sub"],
        }

    return application

@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_jwks_cache():
    clear_jwks_cache()
    yield
    clear_jwks_cache()

def _build_jwk(
    private_key: Ed25519PrivateKey,
    kid: str,
) -> dict:
    public_key = private_key.public_key()

    raw_public_key = public_key.public_bytes_raw()

    return {
        "kty": "OKP",
        "crv": "Ed25519",
        "use": "sig",
        "alg": "EdDSA",
        "kid": kid,
        "x": _base64url_encode(raw_public_key),
    }


def _build_token(
    private_key: Ed25519PrivateKey,
    *,
    kid: str = "manifold-test-key",
    subject: str = "user:123",
    audience: str = COMPOSITION_ENGINE_AUDIENCE,
    issuer: str = MANIFOLD_ISSUER,
    scopes: list[str] | None = None,
    expires_in: int = 300,
) -> str:
    now = int(time.time())

    payload = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "scope": (
            scopes
            if scopes is not None
            else ["composition:calculate"]
        ),
        "iat": now,
        "exp": now + expires_in,
        "jti": "test-jti",
    }

    return jwt.encode(
        payload,
        private_key,
        algorithm="EdDSA",
        headers={
            "kid": kid,
            "typ": "JWT",
        },
    )



class TestRequireJwt:

    def test_valid_jwt_is_accepted(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(signing_key)

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 200
        assert response.json() == {
            "authenticated": True,
            "subject": "user:123",
        }

    def test_missing_authorization_returns_401(
        self,
        client,
    ):
        response = client.get("/protected")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert (
            response.headers["WWW-Authenticate"]
            == "Bearer"
        )

    def test_non_bearer_scheme_returns_401(
        self,
        client,
        signing_key,
    ):
        token = _build_token(signing_key)

        response = client.get(
            "/protected",
            headers={
                "Authorization": f"Basic {token}",
            },
        )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Not authenticated"
        )

    def test_malformed_jwt_returns_401(
        self,
        client,
    ):
        with patch(
            "app.api.security._load_jwks",
            return_value={"keys": []},
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": "Bearer invalid-token",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "O header do JWT é inválido."
        )

    def test_invalid_signature_returns_401(
        self,
        client,
        jwks,
    ):
        signing_key = Ed25519PrivateKey.generate()
        another_key = Ed25519PrivateKey.generate()

        token = _build_token(
            signing_key,
            kid="manifold-test-key",
        )

        invalid_jwks = {
            "keys": [
                _build_jwk(
                    another_key,
                    "manifold-test-key",
                )
            ]
        }

        with patch(
            "app.api.security._load_jwks",
            return_value=invalid_jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "A assinatura do JWT é inválida."
        )

    def test_wrong_issuer_returns_401(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(
            signing_key,
            issuer="another-service",
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "O issuer do JWT é inválido."
        )

    def test_wrong_audience_returns_401(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(
            signing_key,
            audience="budget-engine",
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "O audience do JWT é inválido."
        )

    def test_expired_token_returns_401(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(
            signing_key,
            expires_in=-1,
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "O JWT expirou."
        )

    def test_unknown_kid_returns_401(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(
            signing_key,
            kid="unknown-key",
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "A chave pública do JWT não foi encontrada no JWKS."
        )

    def test_wrong_algorithm_returns_401(
        self,
        client,
        jwks,
    ):
        token = jwt.encode(
            {
                "iss": MANIFOLD_ISSUER,
                "sub": "user:123",
                "aud": COMPOSITION_ENGINE_AUDIENCE,
                "scope": ["composition:calculate"],
                "iat": int(time.time()),
                "exp": int(time.time()) + 300,
                "jti": "test-jti",
            },
            "test-secret-that-is-at-least-32-bytes-long",
            algorithm="HS256",
            headers={
                "kid": "manifold-test-key",
                "typ": "JWT",
            },
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "O algoritmo do JWT não é suportado."
        )

    def test_invalid_subject_returns_401(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(
            signing_key,
            subject="service:123",
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "O subject do JWT não possui o formato esperado."
        )

    def test_jwks_failure_returns_401(
        self,
        client,
        signing_key,
    ):
        token = _build_token(signing_key)

        import requests

        with patch(
            "app.api.security.requests.get",
            side_effect=requests.RequestException(
                "JWKS unavailable"
            ),
        ):
            response = client.get(
                "/protected",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 401
        assert (
            response.json()["detail"]
            == "Não foi possível consultar o JWKS do Manifold."
        )

    def test_required_scope_is_accepted(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(
            signing_key,
            scopes=["composition:calculate"],
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/calculate",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 200
        assert response.json() == {
            "calculated": True,
            "subject": "user:123",
        }

    def test_missing_required_scope_returns_403(
        self,
        client,
        signing_key,
        jwks,
    ):
        token = _build_token(
            signing_key,
            scopes=["composition:read"],
        )

        with patch(
            "app.api.security._load_jwks",
            return_value=jwks,
        ):
            response = client.get(
                "/calculate",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "Insufficient scope"
        )
