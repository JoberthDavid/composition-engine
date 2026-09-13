from dataclasses import dataclass
from typing import Any

from time import perf_counter


@dataclass
class ApiQueryRecord:
    """Representa uma requisição realizada contra uma API."""

    service: str
    method: str
    url: str
    params: dict[str, Any]
    duration_seconds: float
    result_count: int


class ApiQueryMetrics:
    """
    Coleta métricas das requisições realizadas pelas APIs.

    ```
    Além das métricas gerais, permite analisar:
        - repetição de consultas de composição;
        - repetição de consultas de valores monetários por código;
        - repetição de consultas de valores monetários por assinatura
        completa dos parâmetros efetivamente enviados.

    A assinatura completa é baseada nos parâmetros registrados na
    requisição HTTP, e não nos argumentos originais dos métodos.
    """

    def __init__(self) -> None:
        self.records: list[ApiQueryRecord] = []

    def record(
        self,
        service: str,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        duration_seconds: float,
        result_count: int,
    ) -> None:
        """
        Registra uma requisição realizada contra uma API.

        Os parâmetros são copiados para evitar que alterações posteriores
        no dicionário original modifiquem o histórico da métrica.
        """
        self.records.append(
            ApiQueryRecord(
                service=service,
                method=method,
                url=url,
                params=dict(params or {}),
                duration_seconds=duration_seconds,
                result_count=result_count,
            )
        )

    @property
    def total_requests(self) -> int:
        """Retorna o número total de requisições registradas."""
        return len(self.records)

    @property
    def total_duration_seconds(self) -> float:
        """Retorna a duração total das requisições registradas."""
        return sum(record.duration_seconds for record in self.records)

    @property
    def average_duration_seconds(self) -> float:
        """Retorna a duração média das requisições."""
        if not self.records:
            return 0.0

        return self.total_duration_seconds / len(self.records)

    def get_records_by_service(
        self,
        service: str,
    ) -> list[ApiQueryRecord]:
        """Retorna as requisições pertencentes a um determinado serviço."""
        return [
            record
            for record in self.records
            if record.service == service
        ]

    # ------------------------------------------------------------------
    # Métricas de composição
    # ------------------------------------------------------------------

    @property
    def composition_records(self) -> list[ApiQueryRecord]:
        """Retorna as requisições realizadas para a API de composições."""
        return self.get_records_by_service("composition")

    @property
    def composition_requests(self) -> int:
        """Retorna o número de requisições de composição."""
        return len(self.composition_records)

    @property
    def composition_duration_seconds(self) -> float:
        """Retorna a duração total das consultas de composição."""
        return sum(
            record.duration_seconds
            for record in self.composition_records
        )

    @property
    def composition_codes(self) -> list[str]:
        """Retorna os códigos de composição consultados."""
        codes: list[str] = []

        for record in self.composition_records:
            code = record.params.get("generic_item__code__in")

            if code is not None:
                codes.append(str(code))

        return codes

    @property
    def unique_composition_codes(self) -> set[str]:
        """Retorna os códigos de composição distintos consultados."""
        return set(self.composition_codes)

    @property
    def composition_code_counts(self) -> dict[str, int]:
        """Retorna a quantidade de consultas por código de composição."""
        counts: dict[str, int] = {}

        for code in self.composition_codes:
            counts[code] = counts.get(code, 0) + 1

        return counts

    @property
    def repeated_composition_requests(self) -> int:
        """
        Retorna o número de requisições de composição além da primeira
        ocorrência de cada código.
        """
        return sum(
            max(count - 1, 0)
            for count in self.composition_code_counts.values()
        )

    @property
    def composition_repetition_percentage(self) -> float:
        """Retorna o percentual de repetição das consultas de composição."""
        if self.composition_requests == 0:
            return 0.0

        return (
            self.repeated_composition_requests
            / self.composition_requests
            * 100
        )

    @property
    def most_queried_composition_codes(
        self,
    ) -> list[tuple[str, int]]:
        """Retorna os códigos de composição mais consultados."""
        return sorted(
            self.composition_code_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Métricas de valores monetários por código
    # ------------------------------------------------------------------

    @property
    def monetary_value_records(self) -> list[ApiQueryRecord]:
        """Retorna as requisições realizadas para valores monetários."""
        return self.get_records_by_service("monetary_value")

    @property
    def monetary_value_requests(self) -> int:
        """Retorna o número de requisições de valores monetários."""
        return len(self.monetary_value_records)

    @property
    def monetary_value_duration_seconds(self) -> float:
        """Retorna a duração total das consultas de valores monetários."""
        return sum(
            record.duration_seconds
            for record in self.monetary_value_records
        )

    @property
    def monetary_value_codes(self) -> list[str]:
        """Retorna os códigos consultados na API de valores monetários."""
        codes: list[str] = []

        for record in self.monetary_value_records:
            code = record.params.get("generic_item")

            if code is not None:
                codes.append(str(code))

        return codes

    @property
    def unique_monetary_value_codes(self) -> set[str]:
        """Retorna os códigos monetários distintos consultados."""
        return set(self.monetary_value_codes)

    @property
    def monetary_value_code_counts(self) -> dict[str, int]:
        """Retorna a quantidade de consultas por código monetário."""
        counts: dict[str, int] = {}

        for code in self.monetary_value_codes:
            counts[code] = counts.get(code, 0) + 1

        return counts

    @property
    def unique_monetary_value_count(self) -> int:
        """Retorna a quantidade de códigos monetários distintos."""
        return len(self.unique_monetary_value_codes)

    @property
    def repeated_monetary_value_requests(self) -> int:
        """
        Retorna o número de consultas monetárias além da primeira
        ocorrência de cada código.
        """
        return sum(
            max(count - 1, 0)
            for count in self.monetary_value_code_counts.values()
        )

    @property
    def monetary_value_repetition_percentage(self) -> float:
        """Retorna o percentual de repetição por código monetário."""
        if self.monetary_value_requests == 0:
            return 0.0

        return (
            self.repeated_monetary_value_requests
            / self.monetary_value_requests
            * 100
        )

    @property
    def most_queried_monetary_value_codes(
        self,
    ) -> list[tuple[str, int]]:
        """Retorna os códigos monetários mais consultados."""
        return sorted(
            self.monetary_value_code_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Métricas de tempo por código monetário
    # ------------------------------------------------------------------

    @property
    def unique_monetary_value_duration_seconds(self) -> float:
        """
        Retorna o tempo das primeiras consultas de cada código monetário.
        """
        seen_codes: set[str] = set()
        total_duration = 0.0

        for record in self.monetary_value_records:
            code = record.params.get("generic_item")

            if code is None:
                continue

            code = str(code)

            if code not in seen_codes:
                seen_codes.add(code)
                total_duration += record.duration_seconds

        return total_duration

    @property
    def repeated_monetary_value_duration_seconds(self) -> float:
        """
        Retorna o tempo gasto nas consultas monetárias repetidas
        considerando a repetição por código.
        """
        return (
            self.monetary_value_duration_seconds
            - self.unique_monetary_value_duration_seconds
        )

    @property
    def unique_monetary_value_requests(self) -> int:
        """
        Retorna a quantidade de primeiras consultas de cada código.
        """
        return self.unique_monetary_value_count

    @property
    def unique_monetary_value_average_duration_seconds(self) -> float:
        """Retorna a duração média das consultas monetárias únicas."""
        if self.unique_monetary_value_requests == 0:
            return 0.0

        return (
            self.unique_monetary_value_duration_seconds
            / self.unique_monetary_value_requests
        )

    @property
    def repeated_monetary_value_average_duration_seconds(self) -> float:
        """Retorna a duração média das consultas monetárias repetidas."""
        if self.repeated_monetary_value_requests == 0:
            return 0.0

        return (
            self.repeated_monetary_value_duration_seconds
            / self.repeated_monetary_value_requests
        )

    @property
    def monetary_value_repeated_time_percentage(self) -> float:
        """
        Retorna o percentual do tempo monetário gasto em consultas
        repetidas por código.
        """
        if self.monetary_value_duration_seconds == 0:
            return 0.0

        return (
            self.repeated_monetary_value_duration_seconds
            / self.monetary_value_duration_seconds
            * 100
        )

    # ------------------------------------------------------------------
    # Assinatura completa da requisição monetária
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_signature_value(value: Any) -> str:
        """
        Normaliza um valor de parâmetro para composição da assinatura.
        """
        if value is None:
            return "None"

        return str(value)

    @classmethod
    def _build_request_signature(
        cls,
        params: dict[str, Any],
    ) -> tuple[tuple[str, str], ...]:
        """
        Constrói uma assinatura canônica dos parâmetros da requisição.

        A ordenação das chaves garante que duas requisições com os mesmos
        parâmetros, mas em ordens diferentes, sejam consideradas iguais.
        """
        return tuple(
            (
                str(key),
                cls._normalize_signature_value(value),
            )
            for key, value in sorted(
                params.items(),
                key=lambda item: str(item[0]),
            )
        )

    @property
    def monetary_value_request_signatures(
        self,
    ) -> list[tuple[tuple[str, str], ...]]:
        """
        Retorna as assinaturas completas das requisições monetárias.
        """
        return [
            self._build_request_signature(record.params)
            for record in self.monetary_value_records
        ]

    @property
    def unique_monetary_value_signatures(
        self,
    ) -> set[tuple[tuple[str, str], ...]]:
        """Retorna as assinaturas monetárias distintas."""
        return set(self.monetary_value_request_signatures)

    @property
    def monetary_value_signature_counts(
        self,
    ) -> dict[tuple[tuple[str, str], ...], int]:
        """Retorna a quantidade de consultas para cada assinatura."""
        counts: dict[tuple[tuple[str, str], ...], int] = {}

        for signature in self.monetary_value_request_signatures:
            counts[signature] = counts.get(signature, 0) + 1

        return counts

    @property
    def unique_monetary_value_signature_count(self) -> int:
        """Retorna a quantidade de assinaturas monetárias distintas."""
        return len(self.unique_monetary_value_signatures)

    @property
    def repeated_monetary_value_signature_requests(self) -> int:
        """
        Retorna o número de requisições monetárias além da primeira
        ocorrência de cada assinatura completa.
        """
        return sum(
            max(count - 1, 0)
            for count in self.monetary_value_signature_counts.values()
        )

    @property
    def monetary_value_signature_repetition_percentage(self) -> float:
        """Retorna o percentual de repetição por assinatura completa."""
        if self.monetary_value_requests == 0:
            return 0.0

        return (
            self.repeated_monetary_value_signature_requests
            / self.monetary_value_requests
            * 100
        )

    @property
    def unique_monetary_value_signature_duration_seconds(self) -> float:
        """
        Retorna o tempo das primeiras consultas de cada assinatura.
        """
        seen_signatures: set[
            tuple[tuple[str, str], ...]
        ] = set()

        total_duration = 0.0

        for record in self.monetary_value_records:
            signature = self._build_request_signature(record.params)

            if signature not in seen_signatures:
                seen_signatures.add(signature)
                total_duration += record.duration_seconds

        return total_duration

    @property
    def repeated_monetary_value_signature_duration_seconds(self) -> float:
        """
        Retorna o tempo gasto em consultas repetidas considerando
        a assinatura completa.
        """
        return (
            self.monetary_value_duration_seconds
            - self.unique_monetary_value_signature_duration_seconds
        )

    @property
    def unique_monetary_value_signature_requests(self) -> int:
        """Retorna o número de assinaturas consultadas pela primeira vez."""
        return self.unique_monetary_value_signature_count

    @property
    def unique_monetary_value_signature_average_duration_seconds(
        self,
    ) -> float:
        """Retorna a duração média das consultas únicas por assinatura."""
        if self.unique_monetary_value_signature_requests == 0:
            return 0.0

        return (
            self.unique_monetary_value_signature_duration_seconds
            / self.unique_monetary_value_signature_requests
        )

    @property
    def repeated_monetary_value_signature_average_duration_seconds(
        self,
    ) -> float:
        """Retorna a duração média das consultas repetidas por assinatura."""
        if self.repeated_monetary_value_signature_requests == 0:
            return 0.0

        return (
            self.repeated_monetary_value_signature_duration_seconds
            / self.repeated_monetary_value_signature_requests
        )

    @property
    def monetary_value_signature_repeated_time_percentage(self) -> float:
        """
        Retorna o percentual do tempo monetário gasto em consultas
        repetidas por assinatura completa.
        """
        if self.monetary_value_duration_seconds == 0:
            return 0.0

        return (
            self.repeated_monetary_value_signature_duration_seconds
            / self.monetary_value_duration_seconds
            * 100
        )

    @property
    def most_queried_monetary_value_signatures(
        self,
    ) -> list[
        tuple[tuple[tuple[str, str], ...], int]
    ]:
        """
        Retorna as assinaturas monetárias mais consultadas.
        """
        return sorted(
            self.monetary_value_signature_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

    @staticmethod
    def format_signature(
        signature: tuple[tuple[str, str], ...],
    ) -> str:
        """
        Converte uma assinatura interna para uma representação legível.
        """
        return " | ".join(
            f"{key}={value}"
            for key, value in signature
        )

    @property
    def repeated_monetary_value_signatures(
        self,
    ) -> list[
        tuple[tuple[tuple[str, str], ...], int]
    ]:
        """Retorna somente as assinaturas que foram repetidas."""
        return [
            (signature, count)
            for signature, count in self.most_queried_monetary_value_signatures
            if count > 1
        ]

    # ------------------------------------------------------------------
    # Resumo geral
    # ------------------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """Retorna um resumo de todas as métricas coletadas."""
        return {
            "total_requests": self.total_requests,
            "total_duration_seconds": self.total_duration_seconds,
            "average_duration_seconds": self.average_duration_seconds,
            "service_summary": self.service_summary,
            "composition_requests": self.composition_requests,
            "composition_duration_seconds": (
                self.composition_duration_seconds
            ),
            "unique_composition_codes": len(
                self.unique_composition_codes
            ),
            "repeated_composition_requests": (
                self.repeated_composition_requests
            ),
            "composition_repetition_percentage": (
                self.composition_repetition_percentage
            ),

            "monetary_value_requests": self.monetary_value_requests,
            "monetary_value_duration_seconds": (
                self.monetary_value_duration_seconds
            ),
            "unique_monetary_value_codes": (
                self.unique_monetary_value_count
            ),
            "repeated_monetary_value_requests": (
                self.repeated_monetary_value_requests
            ),
            "monetary_value_repetition_percentage": (
                self.monetary_value_repetition_percentage
            ),

            "unique_monetary_value_duration_seconds": (
                self.unique_monetary_value_duration_seconds
            ),
            "repeated_monetary_value_duration_seconds": (
                self.repeated_monetary_value_duration_seconds
            ),
            "unique_monetary_value_requests": (
                self.unique_monetary_value_requests
            ),
            "unique_monetary_value_average_duration_seconds": (
                self.unique_monetary_value_average_duration_seconds
            ),
            "repeated_monetary_value_average_duration_seconds": (
                self.repeated_monetary_value_average_duration_seconds
            ),
            "monetary_value_repeated_time_percentage": (
                self.monetary_value_repeated_time_percentage
            ),

            "unique_monetary_value_signatures": (
                self.unique_monetary_value_signature_count
            ),
            "repeated_monetary_value_signature_requests": (
                self.repeated_monetary_value_signature_requests
            ),
            "monetary_value_signature_repetition_percentage": (
                self.monetary_value_signature_repetition_percentage
            ),
            "unique_monetary_value_signature_duration_seconds": (
                self.unique_monetary_value_signature_duration_seconds
            ),
            "repeated_monetary_value_signature_duration_seconds": (
                self.repeated_monetary_value_signature_duration_seconds
            ),
            "unique_monetary_value_signature_requests": (
                self.unique_monetary_value_signature_requests
            ),
            "unique_monetary_value_signature_average_duration_seconds": (
                self.unique_monetary_value_signature_average_duration_seconds
            ),
            "repeated_monetary_value_signature_average_duration_seconds": (
                self.repeated_monetary_value_signature_average_duration_seconds
            ),
            "monetary_value_signature_repeated_time_percentage": (
                self.monetary_value_signature_repeated_time_percentage
            ),
        }

    def print_report(self) -> None:
        """Imprime um relatório das métricas coletadas."""
        print("\n" + "=" * 80)
        print("RELATÓRIO DE CONSULTAS À API")
        print("=" * 80)

        print("\nGERAL")
        print("-" * 80)
        print(f"Total de requisições: {self.total_requests}")
        print(
            f"Tempo total HTTP: "
            f"{self.total_duration_seconds:.3f} s"
        )
        print(
            f"Tempo médio por requisição: "
            f"{self.average_duration_seconds:.3f} s"
        )

        print("\nRESUMO POR SERVIÇO")
        print("-" * 80)

        print(
            f"{'Serviço':<30}"
            f"{'Req.':>8}"
            f"{'Registros':>12}"
            f"{'Tempo':>12}"
            f"{'Média':>12}"
            f"{'Mín.':>12}"
            f"{'Máx.':>12}"
        )

        print("-" * 80)

        for service, data in sorted(
            self.service_summary.items()
        ):
            print(
                f"{service:<30}"
                f"{data['requests']:>8}"
                f"{data['result_count']:>12}"
                f"{data['duration_seconds']:>12.3f}"
                f"{data['average_duration_seconds']:>12.3f}"
                f"{data['min_duration_seconds']:>12.3f}"
                f"{data['max_duration_seconds']:>12.3f}"
            )


        print("\nCOMPOSIÇÕES")
        print("-" * 80)
        print(
            f"Requisições: "
            f"{self.composition_requests}"
        )
        print(
            f"Tempo total: "
            f"{self.composition_duration_seconds:.3f} s"
        )
        print(
            f"Códigos distintos: "
            f"{len(self.unique_composition_codes)}"
        )
        print(
            f"Requisições repetidas: "
            f"{self.repeated_composition_requests}"
        )
        print(
            f"Repetição: "
            f"{self.composition_repetition_percentage:.2f}%"
        )

        print("\nVALORES MONETÁRIOS — POR CÓDIGO")
        print("-" * 80)
        print(
            f"Requisições: "
            f"{self.monetary_value_requests}"
        )
        print(
            f"Códigos distintos: "
            f"{self.unique_monetary_value_count}"
        )
        print(
            f"Requisições repetidas: "
            f"{self.repeated_monetary_value_requests}"
        )
        print(
            f"Repetição: "
            f"{self.monetary_value_repetition_percentage:.2f}%"
        )
        print(
            f"Tempo total: "
            f"{self.monetary_value_duration_seconds:.3f} s"
        )
        print(
            f"Tempo consultas únicas: "
            f"{self.unique_monetary_value_duration_seconds:.3f} s"
        )
        print(
            f"Tempo consultas repetidas: "
            f"{self.repeated_monetary_value_duration_seconds:.3f} s"
        )
        print(
            f"Média consultas únicas: "
            f"{self.unique_monetary_value_average_duration_seconds:.3f} s"
        )
        print(
            f"Média consultas repetidas: "
            f"{self.repeated_monetary_value_average_duration_seconds:.3f} s"
        )
        print(
            f"% do tempo em repetidas: "
            f"{self.monetary_value_repeated_time_percentage:.2f}%"
        )

        print("\nVALORES MONETÁRIOS — ASSINATURA COMPLETA")
        print("-" * 80)
        print(
            f"Requisições: "
            f"{self.monetary_value_requests}"
        )
        print(
            f"Assinaturas distintas: "
            f"{self.unique_monetary_value_signature_count}"
        )
        print(
            f"Requisições repetidas: "
            f"{self.repeated_monetary_value_signature_requests}"
        )
        print(
            f"Repetição: "
            f"{self.monetary_value_signature_repetition_percentage:.2f}%"
        )
        print(
            f"Tempo consultas únicas: "
            f"{self.unique_monetary_value_signature_duration_seconds:.3f} s"
        )
        print(
            f"Tempo consultas repetidas: "
            f"{self.repeated_monetary_value_signature_duration_seconds:.3f} s"
        )
        print(
            f"Média consultas únicas: "
            f"{self.unique_monetary_value_signature_average_duration_seconds:.3f} s"
        )
        print(
            f"Média consultas repetidas: "
            f"{self.repeated_monetary_value_signature_average_duration_seconds:.3f} s"
        )
        print(
            f"% do tempo em repetidas: "
            f"{self.monetary_value_signature_repeated_time_percentage:.2f}%"
        )

        print("\nTOP CÓDIGOS MONETÁRIOS")
        print("-" * 80)

        for code, count in self.most_queried_monetary_value_codes[:10]:
            print(
                f"{code}: "
                f"{count} consultas"
            )

        print("\nTOP ASSINATURAS MONETÁRIAS REPETIDAS")
        print("-" * 80)

        for signature, count in self.repeated_monetary_value_signatures[:10]:
            print(
                f"{count} consultas | "
                f"{self.format_signature(signature)}"
            )

        print("\n" + "=" * 80)


    @property
    def service_summary(self) -> dict[str, dict[str, Any]]:
        """
        Retorna um resumo agregado das requisições por serviço.

        Para cada serviço são informados:
            - quantidade de requisições;
            - quantidade total de registros retornados;
            - tempo total;
            - tempo médio;
            - menor duração;
            - maior duração.
        """
        summary: dict[str, dict[str, Any]] = {}

        for record in self.records:
            service_summary = summary.setdefault(
                record.service,
                {
                    "requests": 0,
                    "result_count": 0,
                    "duration_seconds": 0.0,
                    "min_duration_seconds": None,
                    "max_duration_seconds": None,
                },
            )

            service_summary["requests"] += 1
            service_summary["result_count"] += record.result_count
            service_summary["duration_seconds"] += (
                record.duration_seconds
            )

            current_min = service_summary["min_duration_seconds"]

            if (
                current_min is None
                or record.duration_seconds < current_min
            ):
                service_summary["min_duration_seconds"] = (
                    record.duration_seconds
                )

            current_max = service_summary["max_duration_seconds"]

            if (
                current_max is None
                or record.duration_seconds > current_max
            ):
                service_summary["max_duration_seconds"] = (
                    record.duration_seconds
                )

        for service_summary in summary.values():
            requests = service_summary["requests"]

            service_summary["average_duration_seconds"] = (
                service_summary["duration_seconds"]
                / requests
                if requests
                else 0.0
            )

        return summary