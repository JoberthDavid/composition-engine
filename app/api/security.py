from __future__ import annotations

import base64
import time
from dataclasses import dataclass

import jwt
import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.algorithms import OKPAlgorithm

from app.config import get_settings


bearer_scheme = HTTPBearer(
    scheme_name="ManifoldJWT",
    description=(
        "Token JWT emitido pelo Manifold API "
        "para autenticação entre serviços."
    ),
    auto_error=False,
)


class JwtAuthenticationError(Exception):
    """Erro interno de validação de autenticação JWT."""


@dataclass(frozen=True)
class CachedJwks:
    """
    JWKS obtido do Manifold e mantido temporariamente em memória.
    """

    keys: dict[str, object]
    expires_at: float


_jwks_cache: CachedJwks | None = None


def _load_jwks() -> dict:
    """
    Obtém o JWKS público do Manifold.
    """

    settings = get_settings()

    try:
        response = requests.get(
            settings.manifold_jwks_url,
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise JwtAuthenticationError(
            "Não foi possível consultar o JWKS do Manifold."
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise JwtAuthenticationError(
            "A resposta do JWKS do Manifold não contém JSON válido."
        ) from exc

    if not isinstance(data, dict):
        raise JwtAuthenticationError(
            "A resposta do JWKS do Manifold possui formato inválido."
        )

    keys = data.get("keys")

    if not isinstance(keys, list):
        raise JwtAuthenticationError(
            "A resposta do JWKS não contém uma lista de chaves."
        )

    return data


def _get_jwks() -> dict:
    """
    Obtém o JWKS utilizando cache em memória.
    """

    global _jwks_cache

    now = time.time()

    if (
        _jwks_cache is not None
        and _jwks_cache.expires_at > now
    ):
        return {
            "keys": [
                {
                    "kid": kid,
                    **_jwk,
                }
                for kid, _jwk in _jwks_cache.keys.items()
            ]
        }

    jwks = _load_jwks()

    parsed_keys: dict[str, object] = {}

    for jwk in jwks["keys"]:
        if not isinstance(jwk, dict):
            continue

        kid = jwk.get("kid")

        if not isinstance(kid, str) or not kid:
            continue

        parsed_keys[kid] = jwk

    _jwks_cache = CachedJwks(
        keys=parsed_keys,
        expires_at=now + 300,
    )

    return jwks


def _get_token_header(token: str) -> dict:
    """
    Lê o header do JWT sem validar o conteúdo do token.

    A validação criptográfica ocorre posteriormente.
    """

    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise JwtAuthenticationError(
            "O header do JWT é inválido."
        ) from exc

    if not isinstance(header, dict):
        raise JwtAuthenticationError(
            "O header do JWT possui formato inválido."
        )

    algorithm = header.get("alg")

    if algorithm != "EdDSA":
        raise JwtAuthenticationError(
            "O algoritmo do JWT não é suportado."
        )

    kid = header.get("kid")

    if not isinstance(kid, str) or not kid:
        raise JwtAuthenticationError(
            "O JWT não possui kid."
        )

    return header


def _get_jwk_for_token(token: str) -> dict:
    """
    Localiza no JWKS a chave pública correspondente ao kid do JWT.
    """

    header = _get_token_header(token)

    kid = header["kid"]

    jwks = _get_jwks()

    for jwk in jwks["keys"]:
        if not isinstance(jwk, dict):
            continue

        if jwk.get("kid") == kid:
            return jwk

    raise JwtAuthenticationError(
        "A chave pública do JWT não foi encontrada no JWKS."
    )


def _get_public_key(token: str):
    """
    Constrói a chave pública Ed25519 a partir do JWK.
    """

    jwk = _get_jwk_for_token(token)

    if jwk.get("kty") != "OKP":
        raise JwtAuthenticationError(
            "O tipo da chave pública não é suportado."
        )

    if jwk.get("crv") != "Ed25519":
        raise JwtAuthenticationError(
            "A curva da chave pública não é suportada."
        )

    if jwk.get("alg") != "EdDSA":
        raise JwtAuthenticationError(
            "O algoritmo da chave pública não é suportado."
        )

    try:
        public_key = OKPAlgorithm.from_jwk(
            {
                "kty": "OKP",
                "crv": "Ed25519",
                "x": jwk["x"],
            }
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise JwtAuthenticationError(
            "A chave pública JWK é inválida."
        ) from exc

    return public_key


def _decode_token(token: str) -> dict:
    """
    Valida criptograficamente o JWT emitido pelo Manifold.

    São validados:

    - assinatura Ed25519;
    - algoritmo EdDSA;
    - issuer;
    - audience;
    - expiração;
    - estrutura básica do subject;
    - presença do scope.
    """

    settings = get_settings()

    public_key = _get_public_key(token)

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["EdDSA"],
            audience=settings.manifold_jwt_audience,
            issuer=settings.manifold_jwt_issuer,
            options={
                "require": [
                    "iss",
                    "sub",
                    "aud",
                    "scope",
                    "iat",
                    "exp",
                    "jti",
                ],
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise JwtAuthenticationError(
            "O JWT expirou."
        ) from exc
    except jwt.InvalidIssuerError as exc:
        raise JwtAuthenticationError(
            "O issuer do JWT é inválido."
        ) from exc
    except jwt.InvalidAudienceError as exc:
        raise JwtAuthenticationError(
            "O audience do JWT é inválido."
        ) from exc
    except jwt.InvalidSignatureError as exc:
        raise JwtAuthenticationError(
            "A assinatura do JWT é inválida."
        ) from exc
    except jwt.MissingRequiredClaimError as exc:
        raise JwtAuthenticationError(
            f"O JWT não contém o claim obrigatório: {exc.claim}."
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise JwtAuthenticationError(
            "O JWT é inválido."
        ) from exc

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise JwtAuthenticationError(
            "O subject do JWT é inválido."
        )

    if not subject.startswith("user:"):
        raise JwtAuthenticationError(
            "O subject do JWT não possui o formato esperado."
        )

    scopes = payload.get("scope")

    if not isinstance(scopes, list):
        raise JwtAuthenticationError(
            "O scope do JWT deve ser uma lista."
        )

    if any(
        not isinstance(scope, str) or not scope
        for scope in scopes
    ):
        raise JwtAuthenticationError(
            "O JWT contém scopes inválidos."
        )

    return payload


def require_jwt(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> dict:
    """
    Autentica uma requisição utilizando JWT emitido pelo Manifold.

    Retorna o payload validado para que dependências ou endpoints
    possam utilizar as informações de identidade e autorização.
    """

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        return _decode_token(credentials.credentials)
    except JwtAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc


def require_scope(
    required_scope: str,
):
    """
    Cria uma dependência que exige determinado scope no JWT.

    Exemplo:

        Depends(require_scope("composition:calculate"))
    """

    if not required_scope:
        raise ValueError(
            "O scope obrigatório não pode ser vazio."
        )

    def dependency(
        payload: dict = Depends(require_jwt),
    ) -> dict:
        scopes = payload.get("scope", [])

        if required_scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail="Insufficient scope",
            )

        return payload

    return dependency


def clear_jwks_cache() -> None:
    """
    Limpa o cache local do JWKS.

    Útil principalmente para testes e rotação de chaves.
    """

    global _jwks_cache

    _jwks_cache = None
