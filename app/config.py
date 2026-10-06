from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from os import getenv


class ConfigurationError(RuntimeError):
    """Erro de configuração obrigatória da aplicação."""


@dataclass(frozen=True)
class Settings:
    scraper_api_base_url: str
    manifold_jwks_url: str
    manifold_jwt_issuer: str
    manifold_jwt_audience: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    scraper_api_base_url = getenv(
        "SCRAPER_API_BASE_URL"
    )

    manifold_jwks_url = getenv(
        "MANIFOLD_JWKS_URL"
    )

    manifold_jwt_issuer = getenv(
        "MANIFOLD_JWT_ISSUER",
        "manifold-api",
    )

    manifold_jwt_audience = getenv(
        "MANIFOLD_JWT_AUDIENCE",
        "composition-engine",
    )

    missing = []

    if not scraper_api_base_url:
        missing.append("SCRAPER_API_BASE_URL")

    if not manifold_jwks_url:
        missing.append("MANIFOLD_JWKS_URL")

    if missing:
        raise ConfigurationError(
            "Variáveis de ambiente obrigatórias não configuradas: "
            + ", ".join(missing)
        )

    return Settings(
        scraper_api_base_url=scraper_api_base_url.rstrip("/"),
        manifold_jwks_url=manifold_jwks_url.rstrip("/"),
        manifold_jwt_issuer=manifold_jwt_issuer,
        manifold_jwt_audience=manifold_jwt_audience,
    )
