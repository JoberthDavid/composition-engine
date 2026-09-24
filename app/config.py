from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from os import getenv


class ConfigurationError(RuntimeError):
    """Erro de configuração obrigatória da aplicação."""


@dataclass(frozen=True)
class Settings:
    scraper_api_base_url: str
    composition_engine_api_key: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    scraper_api_base_url = getenv(
        "SCRAPER_API_BASE_URL"
    )

    composition_engine_api_key = getenv(
        "COMPOSITION_ENGINE_API_KEY"
    )

    missing = []

    if not scraper_api_base_url:
        missing.append("SCRAPER_API_BASE_URL")

    if not composition_engine_api_key:
        missing.append("COMPOSITION_ENGINE_API_KEY")

    if missing:
        raise ConfigurationError(
            "Variáveis de ambiente obrigatórias não configuradas: "
            + ", ".join(missing)
        )

    return Settings(
        scraper_api_base_url=scraper_api_base_url.rstrip("/"),
        composition_engine_api_key=composition_engine_api_key,
    )