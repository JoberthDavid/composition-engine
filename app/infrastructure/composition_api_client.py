import requests


from time import perf_counter

from app.infrastructure.api_query_metrics import (
    ApiQueryMetrics,
)

# URL = "http://127.0.0.1:8000"
URL = "https://web-production-5eeb7.up.railway.app"

class CompositionApiError(Exception):
    """Erro durante a comunicação com a API de composições."""


class CompositionApiClient:
    """Cliente responsável pelo consumo da API de composições.
    URL = "http://127.0.0.1:8000",
    URL = "https://web-production-5eeb7.up.railway.app"
    """


    def __init__(
        self,
        base_url: str = (
            URL
        ),
        metrics: ApiQueryMetrics | None = None,
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.metrics = metrics



    def get_composition_by_code(
        self,
        code: str,
    ) -> dict | None:
        """Obtém uma composição pelo seu código."""

        compositions = self.get_compositions_by_codes(
            [code]
        )

        if not compositions:
            return None

        return compositions[0]

    def get_compositions_by_codes(
        self,
        codes: list[str],
    ) -> list[dict]:
        """Obtém composições utilizando uma lista de códigos."""

        endpoint = f"{self.base_url}/composicoes/"

        params = {
            "generic_item__code__in": ",".join(
                str(code)
                for code in codes
            )
        }


        start_time = perf_counter()

        try:

            response = requests.get(
                endpoint,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

        except requests.RequestException as error:

            raise CompositionApiError(
                "Erro ao consultar a API de composições."
            ) from error

        data = response.json()

        duration = perf_counter() - start_time

        if self.metrics is not None:
            self.metrics.record(
                service="composition",
                method="GET",
                url=endpoint,
                params=params,
                duration_seconds=duration,
                result_count=len(
                    data.get("results", [])
                ),
            )

        return data.get(
            "results",
            [],
        )

    def get_composition_activities_by_codes(
        self,
        codes: list[str],
        data_base: str | None = None,
    ) -> list[dict]:
        """
        Consulta as atividades auxiliares de várias composições
        em uma única chamada ao endpoint otimizado.
        """
        normalized_codes = list(
            dict.fromkeys(
                str(code)
                for code in codes
                if str(code)
            )
        )

        if not normalized_codes:
            return []

        endpoint = f"{self.base_url}/compositions/activities/"
        params = {
            "composition_code__in": ",".join(normalized_codes),
            "limit": 1000,
        }

        if data_base is not None:
            params["data_base"] = str(data_base)

        results = []
        next_url = endpoint
        next_params = params

        while next_url:
            start_time = perf_counter()

            try:
                response = requests.get(
                    next_url,
                    params=next_params,
                    timeout=30,
                )
                response.raise_for_status()
            except requests.RequestException as error:
                raise CompositionApiError(
                    "Erro ao consultar as atividades das composições."
                ) from error

            data = response.json()

            duration = perf_counter() - start_time

            page_results = data.get("results", [])
            results.extend(page_results)

            if self.metrics is not None:
                self.metrics.record(
                    service="composition_activity",
                    method="GET",
                    url=next_url,
                    params=next_params,
                    duration_seconds=duration,
                    result_count=len(page_results),
                )

            next_url = data.get("next")
            next_params = None

        return results

    def get_composition_transports_by_codes(
        self,
        codes: list[str],
        data_base: str | None = None,
    ) -> list[dict]:
        """
        Consulta os transportes de várias composições
        em uma única chamada ao endpoint otimizado.
        """
        normalized_codes = list(
            dict.fromkeys(
                str(code)
                for code in codes
                if str(code)
            )
        )

        if not normalized_codes:
            return []

        endpoint = f"{self.base_url}/compositions/transports/"
        params = {
            "composition_code__in": ",".join(normalized_codes),
            "limit": 1000,
        }

        if data_base is not None:
            params["data_base"] = str(data_base)

        results = []
        next_url = endpoint
        next_params = params

        while next_url:
            start_time = perf_counter()

            try:
                response = requests.get(
                    next_url,
                    params=next_params,
                    timeout=30,
                )
                response.raise_for_status()
            except requests.RequestException as error:
                raise CompositionApiError(
                    "Erro ao consultar os transportes das composições."
                ) from error

            data = response.json()

            duration = perf_counter() - start_time

            page_results = data.get("results", [])
            results.extend(page_results)

            if self.metrics is not None:
                self.metrics.record(
                    service="composition_transport",
                    method="GET",
                    url=next_url,
                    params=next_params,
                    duration_seconds=duration,
                    result_count=len(page_results),
                )

            next_url = data.get("next")
            next_params = None

        return results