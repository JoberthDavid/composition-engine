from __future__ import annotations

import pytest

from app.config import (
    ConfigurationError,
    get_settings,
)


def test_get_settings_requires_scraper_api_base_url(
    monkeypatch,
):
    monkeypatch.delenv(
        "SCRAPER_API_BASE_URL",
        raising=False,
    )
    monkeypatch.setenv(
        "MANIFOLD_JWKS_URL",
        "http://manifold/.well-known/jwks.json",
    )

    get_settings.cache_clear()

    with pytest.raises(
        ConfigurationError,
        match="SCRAPER_API_BASE_URL",
    ):
        get_settings()


def test_get_settings_requires_manifold_jwks_url(
    monkeypatch,
):
    monkeypatch.setenv(
        "SCRAPER_API_BASE_URL",
        "http://scraper",
    )
    monkeypatch.delenv(
        "MANIFOLD_JWKS_URL",
        raising=False,
    )

    get_settings.cache_clear()

    with pytest.raises(
        ConfigurationError,
        match="MANIFOLD_JWKS_URL",
    ):
        get_settings()


def test_get_settings_loads_jwt_configuration(
    monkeypatch,
):
    monkeypatch.setenv(
        "SCRAPER_API_BASE_URL",
        "http://scraper/",
    )
    monkeypatch.setenv(
        "MANIFOLD_JWKS_URL",
        "https://manifold.example/.well-known/jwks.json",
    )
    monkeypatch.setenv(
        "MANIFOLD_JWT_ISSUER",
        "manifold-api",
    )
    monkeypatch.setenv(
        "MANIFOLD_JWT_AUDIENCE",
        "composition-engine",
    )

    get_settings.cache_clear()

    settings = get_settings()

    assert (
        settings.scraper_api_base_url
        == "http://scraper"
    )

    assert (
        settings.manifold_jwks_url
        == "https://manifold.example/.well-known/jwks.json"
    )

    assert (
        settings.manifold_jwt_issuer
        == "manifold-api"
    )

    assert (
        settings.manifold_jwt_audience
        == "composition-engine"
    )


def test_jwt_issuer_has_default_value(
    monkeypatch,
):
    monkeypatch.setenv(
        "SCRAPER_API_BASE_URL",
        "http://scraper",
    )
    monkeypatch.setenv(
        "MANIFOLD_JWKS_URL",
        "http://manifold/.well-known/jwks.json",
    )
    monkeypatch.delenv(
        "MANIFOLD_JWT_ISSUER",
        raising=False,
    )
    monkeypatch.delenv(
        "MANIFOLD_JWT_AUDIENCE",
        raising=False,
    )

    get_settings.cache_clear()

    settings = get_settings()

    assert settings.manifold_jwt_issuer == "manifold-api"
    assert (
        settings.manifold_jwt_audience
        == "composition-engine"
    )


def test_settings_do_not_expose_legacy_api_key(
    monkeypatch,
):
    monkeypatch.setenv(
        "SCRAPER_API_BASE_URL",
        "http://scraper",
    )
    monkeypatch.setenv(
        "MANIFOLD_JWKS_URL",
        "http://manifold/.well-known/jwks.json",
    )
    monkeypatch.delenv(
        "COMPOSITION_ENGINE_API_KEY",
        raising=False,
    )

    get_settings.cache_clear()

    settings = get_settings()

    assert not hasattr(
        settings,
        "composition_engine_api_key",
    )