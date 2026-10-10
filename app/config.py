from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env",
)


class ConfigurationError(RuntimeError):
    """Erro de configuração da aplicação."""


@dataclass(frozen=True)
class Settings:
    manifold_api_base_url: str
    manifold_api_token: str

    manifold_jwks_url: str
    manifold_jwt_issuer: str
    manifold_jwt_audience: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    manifold_api_base_url = getenv(
        "MANIFOLD_API_BASE_URL",
        "",
    )

    manifold_api_token = getenv(
        "MANIFOLD_API_TOKEN",
        "",
    )

    manifold_jwks_url = getenv(
        "MANIFOLD_JWKS_URL",
        "",
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

    if not manifold_api_base_url:
        missing.append("MANIFOLD_API_BASE_URL")

    if not manifold_jwks_url:
        missing.append("MANIFOLD_JWKS_URL")

    if missing:
        raise ConfigurationError(
            "Variáveis de ambiente obrigatórias ausentes: "
            + ", ".join(missing)
        )

    return Settings(
        manifold_api_base_url=manifold_api_base_url.rstrip("/"),
        manifold_api_token=manifold_api_token,
        manifold_jwks_url=manifold_jwks_url,
        manifold_jwt_issuer=manifold_jwt_issuer,
        manifold_jwt_audience=manifold_jwt_audience,
    )