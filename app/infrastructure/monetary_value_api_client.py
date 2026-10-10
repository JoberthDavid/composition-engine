from __future__ import annotations

from typing import Any

from app.infrastructure.manifold_api_client import (
    ManifoldApiClient,
)


class MonetaryValueApiError(RuntimeError):
    """Erro de comunicação com a API de valores monetários."""


class MonetaryValueApiClient:
    """
    Cliente da API de valores monetários através do Manifold.

    O composition-engine não conhece a localização do Scraper.
    """

    def __init__(
        self,
        manifold_client: ManifoldApiClient | None = None,
        timeout: int = 30,
        metrics=None,
    ) -> None:
        self.manifold_client = (
            manifold_client
            or ManifoldApiClient(
                timeout=timeout,
            )
        )
        self.metrics = metrics

    def get_values_by_code(
        self,
        code: str,
    ) -> list[dict[str, Any]]:
        return self.get_values(
            generic_item=code,
        )

    def get_values(
        self,
        *,
        generic_item: str | None = None,
        generic_item_in: list[str] | None = None,
        type_system: str | None = None,
        source_file: str | None = None,
        classification: str | None = None,
        group: str | None = None,
        unit: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}

        if generic_item:
            params["generic_item"] = generic_item

        if generic_item_in:
            params["generic_item__in"] = ",".join(
                str(value)
                for value in generic_item_in
            )

        if type_system:
            params["type_system"] = type_system

        if source_file:
            params["source_file"] = source_file

        if classification:
            params["classification"] = classification

        if group:
            params["group"] = group

        if unit:
            params["unit"] = unit

        try:
            return self._get_all_pages(
                params=params,
            )
        except Exception as exc:
            raise MonetaryValueApiError(
                "Não foi possível consultar os valores monetários."
            ) from exc

    def _get_all_pages(
        self,
        *,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        response = self.manifold_client.get(
            "/api/integrations/"
            "scraper/buscar-valores-monetarios/",
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