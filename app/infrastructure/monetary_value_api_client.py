import requests

from time import perf_counter

from app.infrastructure.api_query_metrics import (
    ApiQueryMetrics,
)

# URL = "http://127.0.0.1:8000"
URL = "https://web-production-5eeb7.up.railway.app"

class MonetaryValueApiError(Exception):
    """
    Erro durante a comunicação com a API
    de valores monetários.
    """

class MonetaryValueApiClient:
    """
    Cliente responsável pelo consumo da API
    de valores monetários.


    A responsabilidade desta classe é exclusivamente:

    - realizar requisições HTTP;
    - aplicar filtros disponíveis na API;
    - tratar erros de comunicação;
    - percorrer páginas quando necessário;
    - retornar os dados brutos da API.

    A conversão para MonetaryValue é responsabilidade
    do MonetaryValueRepository.
    """


    def __init__(
        self,
        base_url: str = (
            URL
        ),
        timeout: int = 30,
        metrics: ApiQueryMetrics | None = None,
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.metrics = metrics



    # ============================================================
    # MÉTODOS PÚBLICOS
    # ============================================================

    def get_values_by_code(
        self,
        code: str,
    ) -> list[dict]:
        """
        Obtém todos os valores monetários associados
        a um código de insumo.

        Parameters
        ----------
        code:
            Código do item genérico.

        Returns
        -------
        list[dict]
            Lista contendo todos os registros retornados
            pela API para o código informado.
        """

        return self.get_values(
            generic_item=code,
        )

    def get_values(
        self,
        generic_item: str | None = None,
        generic_item_in: list[str] | None = None,
        type_system: str | None = None,
        source_file: str | None = None,
        classification: str | None = None,
        group: str | None = None,
        unit: str | None = None,
    ) -> list[dict]:
        """
        Obtém valores monetários utilizando os filtros
        disponíveis no endpoint da API.

        Todos os parâmetros são opcionais.

        Parameters
        ----------
        generic_item:
            Código do insumo.

        type_system:
            Tipo de sistema.

        source_file:
            Identificador do arquivo de origem.

        classification:
            Classificação do valor monetário.

        group:
            Grupo do insumo.

        unit:
            Unidade do insumo.

        Returns
        -------
        list[dict]
            Todos os registros encontrados, incluindo
            todas as páginas retornadas pela API.
        """

        endpoint = (
            f"{self.base_url}"
            "/valores-monetarios/"
        )

        params = self._build_params(
            generic_item=generic_item,
            generic_item_in=generic_item_in,
            type_system=type_system,
            source_file=source_file,
            classification=classification,
            group=group,
            unit=unit,
        )

        return self._get_all_pages(
            url=endpoint,
            params=params,
        )

    # ============================================================
    # CONSTRUÇÃO DOS PARÂMETROS
    # ============================================================

    def _build_params(
        self,
        generic_item: str | None = None,
        generic_item_in: list[str] | None = None,
        type_system: str | None = None,
        source_file: str | None = None,
        classification: str | None = None,
        group: str | None = None,
        unit: str | None = None,
    ) -> dict[str, str]:
        """
        Constrói os parâmetros da requisição.

        Apenas parâmetros com valores definidos são enviados
        para a API.
        """

        params: dict[str, str] = {}

        if generic_item is not None:
            params["generic_item"] = str(generic_item)

        if generic_item_in is not None:
            normalized_codes = [
                str(code)
                for code in generic_item_in
                if str(code)
            ]

            if normalized_codes:
                params["generic_item__in"] = ",".join(
                    normalized_codes
                )

        if type_system is not None:
            params["type_system"] = str(type_system)

        if source_file is not None:
            params["source_file"] = str(source_file)

        if classification is not None:
            params["classification"] = str(classification)

        if group is not None:
            params["group"] = str(group)

        if unit is not None:
            params["unit"] = str(unit)

        return params

    # ============================================================
    # PAGINAÇÃO
    # ============================================================

    def _get_all_pages(
        self,
        url: str,
        params: dict | None = None,
    ) -> list[dict]:
        """
        Obtém todos os registros de todas as páginas.

        A API Django REST Framework retorna normalmente
        uma estrutura semelhante a:

            {
                "count": ...,
                "next": "...",
                "previous": "...",
                "results": [...]
            }

        Enquanto existir uma URL em "next", novas páginas
        são consultadas.
        """

        results: list[dict] = []

        current_url = url
        current_params = params

        while current_url is not None:

            data = self._request(
                url=current_url,
                params=current_params,
            )

            page_results = data.get(
                "results",
                [],
            )

            results.extend(
                page_results
            )

            current_url = data.get(
                "next"
            )

            # A URL retornada pela API em "next" já possui
            # os parâmetros de paginação necessários.
            #
            # Portanto, após a primeira requisição não devemos
            # enviar novamente os parâmetros originais.
            current_params = None

        return results

    # ============================================================
    # REQUISIÇÃO HTTP
    # ============================================================

    def _request(
        self,
        url: str,
        params: dict | None = None,
    ) -> dict:
        """
        Executa uma requisição GET e retorna o JSON.

        Todos os erros de comunicação são encapsulados em
        MonetaryValueApiError.
        """

        start_time = perf_counter()

        try:

            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as error:

            raise MonetaryValueApiError(
                "Erro ao consultar a API de "
                "valores monetários."
            ) from error

        except ValueError as error:

            raise MonetaryValueApiError(
                "A API de valores monetários retornou "
                "uma resposta JSON inválida."
            ) from error

        duration = perf_counter() - start_time

        if self.metrics is not None:
            self.metrics.record(
                service="monetary_value",
                method="GET",
                url=url,
                params=params,
                duration_seconds=duration,
                result_count=len(
                    data.get("results", [])
                ),
            )

        return data