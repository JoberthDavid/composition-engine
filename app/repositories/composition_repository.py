from app.domain.composition import Composition
from app.infrastructure.composition_api_client import CompositionApiClient


class CompositionRepository:
    """
    Repositório responsável pelo acesso às composições.

    Mantém um cache em memória durante a execução do processo
    para evitar consultas repetidas à API para o mesmo código.
    """

    """
    BATCH_SIZE é o limite de registros retornados pela API em uma única página.
    """

    BATCH_SIZE = 20


    def __init__(
        self,
        api_client: CompositionApiClient | None = None,
    ) -> None:
        self.api_client = (
            api_client
            if api_client is not None
            else CompositionApiClient()
        )

        self._cache: dict[str, Composition] = {}

    def get_by_code(
        self,
        code: str,
    ) -> Composition | None:
        """
        Retorna uma composição pelo código.

        Se a composição já estiver no cache, evita uma nova
        requisição à API.
        """
        normalized_code = str(code)

        if normalized_code in self._cache:
            return self._cache[normalized_code]

        compositions = self.api_client.get_compositions_by_codes(
            [normalized_code]
        )

        if not compositions:
            return None

        composition = Composition.from_api_data(
            compositions[0]
        )

        self._cache[normalized_code] = composition

        return composition

    def get_by_codes(
        self,
        codes: list[str],
    ) -> list[Composition]:
        """
        Retorna várias composições.

        O cache é consultado antes da API. Somente os códigos
        ainda não presentes no cache são consultados.

        Os códigos ausentes são enviados em lotes limitados por
        BATCH_SIZE para respeitar a paginação da API.
        """

        normalized_codes = list(
            dict.fromkeys(
                str(code)
                for code in codes
            )
        )

        compositions_by_code: dict[str, Composition] = {}
        missing_codes: list[str] = []

        for code in normalized_codes:
            if code in self._cache:
                compositions_by_code[code] = self._cache[code]
            else:
                missing_codes.append(code)

        for batch in self._build_batches(
            missing_codes,
        ):
            compositions_data = (
                self.api_client.get_compositions_by_codes(
                    batch
                )
            )

            for composition_data in compositions_data:
                composition = Composition.from_api_data(
                    composition_data
                )

                composition_code = str(
                    composition.code
                )

                self._cache[composition_code] = composition
                compositions_by_code[composition_code] = composition

        return [
            compositions_by_code[code]
            for code in normalized_codes
            if code in compositions_by_code
        ]

    def _build_batches(
        self,
        codes: list[str],
    ) -> list[list[str]]:
        """
        Divide os códigos em lotes compatíveis com o limite
        de registros da API.
        """
        return [
            codes[index:index + self.BATCH_SIZE]
            for index in range(
                0,
                len(codes),
                self.BATCH_SIZE,
            )
        ]

    def clear_cache(self) -> None:
        """
        Limpa o cache de composições.
        """
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        """
        Retorna a quantidade de composições armazenadas no cache.
        """
        return len(self._cache)