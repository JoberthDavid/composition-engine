from datetime import date


class CalculationContext:
    """
    Representa o contexto utilizado para calcular
    uma composição.

    Os valores são definidos pelo usuário no frontend
    e representam os critérios utilizados para selecionar
    os valores monetários dos insumos.
    """

    def __init__(
        self,
        source_file_uf: str | None = None,
        source_file_data_base: date | None = None,
        classification: str | None = None,
        group: str | None = None,
        type_system: str | None = None,
    ) -> None:

        self.source_file_uf = source_file_uf
        self.source_file_data_base = (
            source_file_data_base
        )

        self.classification = classification
        self.group = group
        self.type_system = type_system

    def __repr__(
        self,
    ) -> str:

        return (
            "CalculationContext("
            f"source_file_uf="
            f"'{self.source_file_uf}', "
            f"source_file_data_base="
            f"{self.source_file_data_base}, "
            f"classification="
            f"'{self.classification}', "
            f"group='{self.group}', "
            f"type_system="
            f"'{self.type_system}'"
            ")"
        )