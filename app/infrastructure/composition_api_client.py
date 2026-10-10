from __future__ import annotations

from typing import Any

from app.infrastructure.manifold_api_client import (
    ManifoldApiClient,
)


class CompositionApiError(RuntimeError):
    """Erro de comunicação com a API de composições."""


class CompositionApiClient:
    """
    Cliente da API de composições através do Manifold.

    O composition-engine não conhece a localização do Scraper.
    """

    def __init__(
        self,
        manifold_client: ManifoldApiClient | None = None,
        metrics=None,
    ) -> None:
        self.manifold_client = (
            manifold_client
            or ManifoldApiClient()
        )
        self.metrics = metrics

    def get_compositions_by_codes(
        self,
        codes: list[str],
    ) -> list[dict[str, Any]]:
        if not codes:
            return []

        try:
            response = self.manifold_client.get(
                "/api/integrations/"
                "scraper/buscar-composicoes/",
                params={
                    "generic_item__code__in": ",".join(
                        str(code)
                        for code in codes
                    ),
                },
            )
        except Exception as exc:
            raise CompositionApiError(
                "Não foi possível consultar as composições."
            ) from exc

        return self._extract_results(response)

    def get_composition_activities_by_codes(
        self,
        codes: list[str],
        data_base: str | None = None,
    ) -> list[dict[str, Any]]:
        if not codes:
            return []

        params = {
            "composition_code__in": ",".join(
                str(code)
                for code in codes
            ),
            "limit": 1000,
        }

        if data_base:
            params["data_base"] = data_base

        return self._get_all_pages(
            path=(
                "/api/integrations/"
                "scraper/buscar-atividades-composicao/"
            ),
            params=params,
        )

    def get_composition_transports_by_codes(
        self,
        codes: list[str],
        data_base: str | None = None,
    ) -> list[dict[str, Any]]:
        if not codes:
            return []

        params = {
            "composition_code__in": ",".join(
                str(code)
                for code in codes
            ),
            "limit": 1000,
        }

        if data_base:
            params["data_base"] = data_base

        return self._get_all_pages(
            path=(
                "/api/integrations/"
                "scraper/buscar-transportes-composicao/"
            ),
            params=params,
        )

    def _get_all_pages(
        self,
        *,
        path: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        response = self.manifold_client.get(
            path,
            params=params,
        )

        while response:
            results.extend(
                response.get("results", [])
            )

            next_url = response.get("next")

            if not next_url:
                break

            response = self.manifold_client.get(
                next_url
            )

        return results

    @staticmethod
    def _extract_results(
        response: Any,
    ) -> list[dict[str, Any]]:
        if response is None:
            return []

        if isinstance(response, list):
            return response

        if isinstance(response, dict):
            return response.get("results", [])

        raise CompositionApiError(
            "Resposta inválida da API de composições."
        )