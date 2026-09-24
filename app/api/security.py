from __future__ import annotations

from secrets import compare_digest

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.config import get_settings


api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="CompositionEngineApiKey",
    description=(
        "Chave de acesso à API do Composition Engine."
    ),
    auto_error=False,
)


def require_api_key(
    api_key: str | None = Depends(api_key_header),
) -> None:
    """
    Valida a chave de acesso da API.

    A comparação utiliza compare_digest para evitar
    comparação ingênua de segredos.
    """

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={
                "WWW-Authenticate": "APIKey",
            },
        )

    expected_api_key = (
        get_settings().composition_engine_api_key
    )

    if not compare_digest(
        api_key,
        expected_api_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={
                "WWW-Authenticate": "APIKey",
            },
        )