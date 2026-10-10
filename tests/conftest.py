import base64
import os
import time

import jwt
import pytest

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)


os.environ.setdefault(
    "MANIFOLD_JWKS_URL",
    "http://manifold.test/.well-known/jwks.json",
)

os.environ.setdefault(
    "MANIFOLD_JWT_ISSUER",
    "manifold-api",
)

os.environ.setdefault(
    "MANIFOLD_JWT_AUDIENCE",
    "composition-engine",
)


MANIFOLD_ISSUER = "manifold-api"
COMPOSITION_ENGINE_AUDIENCE = "composition-engine"


def _base64url_encode(value: bytes) -> str:
    return (
        base64.urlsafe_b64encode(value)
        .rstrip(b"=")
        .decode("ascii")
    )


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


@pytest.fixture
def signing_key():
    return Ed25519PrivateKey.generate()


@pytest.fixture
def jwks(signing_key):
    return {
        "keys": [
            _build_jwk(
                signing_key,
                "manifold-test-key",
            )
        ]
    }


@pytest.fixture
def jwt_token(signing_key):
    return _build_token(signing_key)


@pytest.fixture
def jwt_headers(signing_key, jwks, monkeypatch):
    from app.api import security

    monkeypatch.setattr(
        security,
        "_load_jwks",
        lambda: jwks,
    )

    security.clear_jwks_cache()

    def build_headers(
        scopes: list[str] | None = None,
        *,
        subject: str = "user:123",
        audience: str = COMPOSITION_ENGINE_AUDIENCE,
        issuer: str = MANIFOLD_ISSUER,
        expires_in: int = 300,
    ) -> dict[str, str]:
        token = _build_token(
            signing_key,
            subject=subject,
            audience=audience,
            issuer=issuer,
            scopes=scopes,
            expires_in=expires_in,
        )

        return {
            "Authorization": f"Bearer {token}",
        }

    return build_headers
