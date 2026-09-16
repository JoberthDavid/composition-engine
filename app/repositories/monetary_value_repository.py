from datetime import date

from concurrent.futures import ThreadPoolExecutor

from app.domain.monetary_value import MonetaryValue
from app.infrastructure.monetary_value_api_client import (
    MonetaryValueApiClient,
)


class MonetaryValueRepository:
    """
    Repositório responsável pelo acesso e armazenamento em cache
    dos valores monetários utilizados pelo motor de cálculo.

    O cache é organizado por código de item monetário.

    Os type systems utilizados pelo SICRO dependem do grupo:

        EQ -> ON
        MO -> ON
        MA -> NA

    O cache é incremental quando o contexto de cálculo permanece
    o mesmo. Quando o contexto muda, o cache anterior é invalidado.
    """

    GROUPS = ("EQ", "MO", "MA")

    GROUP_TYPE_SYSTEMS = {
        "EQ": "ON",
        "MO": "ON",
        "MA": "NA",
    }

    BATCH_SIZE = 20


    def __init__(
        self,
        api_client: MonetaryValueApiClient,
    ) -> None:
        self.api_client = api_client

        self._cache: dict[str, list[MonetaryValue]] = {}

        self._cache_source_file_uf: str | None = None
        self._cache_source_file_data_base: date | None = None
        self._cache_type_system: str | None = None
        
    def get_by_code(
        self,
        code: str,
    ) -> list[MonetaryValue]:
        normalized_code = str(code)

        if normalized_code in self._cache:
            return self._cache[normalized_code]

        print(
            f"[CACHE MISS] MonetaryValueRepository.get_by_code("
            f"{normalized_code})"
        )

        values = self.api_client.get_values_by_code(
            normalized_code,
        )

        monetary_values = [
            MonetaryValue.from_api_data(value)
            for value in values
        ]

        self._cache[normalized_code] = monetary_values

        return monetary_values

    def get_by_codes(
        self,
        codes: list[str],
    ) -> list[MonetaryValue]:
        """
        Retorna os valores monetários dos códigos solicitados.

        Códigos já existentes no cache não são consultados novamente.
        """
        normalized_codes = [
            str(code)
            for code in codes
        ]

        values: list[MonetaryValue] = []
        missing_codes: list[str] = []

        for code in normalized_codes:
            if code in self._cache:
                values.extend(self._cache[code])
            else:
                missing_codes.append(code)

        if missing_codes:
            values_data = self.api_client.get_values(
                generic_item=",".join(missing_codes),
            )

            values_by_code: dict[
                str,
                list[MonetaryValue],
            ] = {}

            for value_data in values_data:
                value = MonetaryValue.from_api_data(
                    value_data,
                )

                value_code = str(value.generic_item)

                self._cache.setdefault(
                    value_code,
                    [],
                ).append(value)

                values_by_code.setdefault(
                    value_code,
                    [],
                ).append(value)

            for code in missing_codes:
                values.extend(
                    values_by_code.get(code, [])
                )

        return values


    def load_cache(
        self,
        codes_by_group: dict[str, set[str]],
        type_system: str | None = None,
        source_file_uf: str | None = None,
        source_file_data_base: date | None = None,
    ) -> None:
        """
        Carrega no cache somente os valores monetários necessários.

        Os códigos são agrupados por grupo e enviados em lotes de
        até BATCH_SIZE itens. Os lotes independentes são executados
        em paralelo para reduzir o tempo total das requisições HTTP.
        """

        if not self._has_same_context(
            type_system=type_system,
            source_file_uf=source_file_uf,
            source_file_data_base=source_file_data_base,
        ):
            self.clear_cache()

            self._cache_source_file_uf = source_file_uf
            self._cache_source_file_data_base = (
                source_file_data_base
            )
            self._cache_type_system = type_system

        source_file = (
            source_file_data_base.isoformat()
            if source_file_data_base is not None
            else None
        )

        requests_to_make = []

        for group, codes in codes_by_group.items():
            group_type_system = self.GROUP_TYPE_SYSTEMS[group]

            missing_codes = sorted(
                code
                for code in codes
                if code not in self._cache
            )

            for index in range(
                0,
                len(missing_codes),
                self.BATCH_SIZE,
            ):
                batch = missing_codes[
                    index:index + self.BATCH_SIZE
                ]

                if not batch:
                    continue

                requests_to_make.append(
                    (
                        batch,
                        group_type_system,
                        source_file,
                        group,
                    )
                )

        if not requests_to_make:
            return

        with ThreadPoolExecutor(
            max_workers=8,
        ) as executor:
            futures = [
                executor.submit(
                    self._load_values_for_batch,
                    codes,
                    group_type_system,
                    source_file,
                    group,
                )
                for (
                    codes,
                    group_type_system,
                    source_file,
                    group,
                ) in requests_to_make
            ]

            # for future in futures:
            #     values = future.result()
            #     self._store_values(values)
            for future in futures:
                values = future.result()

                print(
                    f"[BATCH] valores recebidos: {len(values)}"
                )

                self._store_values(values)

                print(
                    f"[CACHE] códigos armazenados: "
                    f"{self.cache_size}"
                )



    def _store_values(
        self,
        values_data: list[dict],
    ) -> None:
        """
        Converte os dados retornados pela API e armazena
        os valores monetários no cache por código.
        """
        for value_data in values_data:
            value = MonetaryValue.from_api_data(
                value_data,
            )

            code = str(value.generic_item)

            self._cache.setdefault(
                code,
                [],
            ).append(value)

    def _has_same_context(
        self,
        type_system: str | None,
        source_file_uf: str | None,
        source_file_data_base: date | None,
    ) -> bool:
        """
        Verifica se o cache pertence ao mesmo contexto
        de cálculo.
        """
        return (
            self._cache_source_file_uf == source_file_uf
            and self._cache_source_file_data_base
            == source_file_data_base
            and self._cache_type_system == type_system
        )

    def clear_cache(self) -> None:
        """
        Limpa os valores monetários e o contexto do cache.
        """
        self._cache.clear()

        self._cache_source_file_uf = None
        self._cache_source_file_data_base = None
        self._cache_type_system = None

    @property
    def cache_size(self) -> int:
        """Retorna a quantidade de códigos armazenados no cache."""
        return len(self._cache)

    @property
    def is_cache_loaded(self) -> bool:
        """Indica se existe um contexto carregado no cache."""
        return (
            self._cache_source_file_uf is not None
            or self._cache_source_file_data_base is not None
            or self._cache_type_system is not None
        )

    @property
    def cache_context(self) -> dict[str, object | None]:
        """
        Retorna o contexto associado ao cache.
        """
        return {
            "source_file_uf": self._cache_source_file_uf,
            "source_file_data_base": (
                self._cache_source_file_data_base
            ),
            "type_system": self._cache_type_system,
        }

    def _load_values_for_code(
        self,
        code: str,
        type_system: str,
        source_file: str | None,
        group: str,
    ) -> list[dict]:
        """
        Consulta os valores monetários de um código.

        Este método é executado pelas threads durante o carregamento
        paralelo do cache.
        """
        return self.api_client.get_values(
            generic_item=code,
            type_system=type_system,
            source_file=source_file,
            group=group,
        )

    def _load_values_for_batch(
        self,
        codes: list[str],
        type_system: str,
        source_file: str | None,
        group: str,
    ) -> list[dict]:
        """
        Consulta os valores monetários de um lote de códigos.

        O lote é enviado em uma única requisição à API.
        """
        return self.api_client.get_values(
            generic_item_in=codes,
            type_system=type_system,
            source_file=source_file,
            group=group,
        )