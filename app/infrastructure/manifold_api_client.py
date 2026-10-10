from __future__ import annotations

from typing import Any

import requests

from app.config import get_settings


class ManifoldApiError(RuntimeError):
    """Erro de comunicação com o Manifold API."""


class ManifoldApiClient:
    """
    Cliente HTTP mínimo para comunicação com o Manifold API.

    O composition-engine não conhece diretamente as integrações
    externas. O Manifold é responsável por encaminhar as requisições.
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: int = 30,
    ) -> None:
        settings = get_settings()

        self.base_url = (
            base_url or settings.manifold_api_base_url
        ).rstrip("/")

        self.token = (
            token if token is not None
            else settings.manifold_api_token
        )

        self.timeout = timeout

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request(
            method="GET",
            path=path,
            params=params,
        )

    def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request(
            method="POST",
            path=path,
            params=params,
            json=json,
        )

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"

        headers = {
            "Accept": "application/json",
        }

        if self.token:
            headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        request_kwargs = {
            "headers": headers,
            "params": params,
            "timeout": self.timeout,
        }

        if json is not None:
            request_kwargs["json"] = json

        try:
            response = requests.request(
                method,
                url,
                **request_kwargs,
            )
        except requests.RequestException as exc:
            raise ManifoldApiError(
                "Não foi possível comunicar com o Manifold API."
            ) from exc

        if response.status_code in (401, 403):
            raise ManifoldApiError(
                "O Manifold API rejeitou a autenticação."
            )

        if response.status_code >= 400:
            raise ManifoldApiError(
                f"O Manifold API retornou HTTP "
                f"{response.status_code}."
            )

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise ManifoldApiError(
                "O Manifold API retornou uma resposta JSON inválida."
            ) from exc