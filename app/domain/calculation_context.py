from datetime import date


class CalculationContext:
    """
    Representa o contexto utilizado para calcular
    uma composição.
    """
    def __init__(
        self,
        source_file_uf: str | None = None,
        source_file_data_base: date | None = None,
        classification: str | None = None,
        group: str | None = None,
        type_system: str | None = None,
        methodology: str | None = None,
    ) -> None:

        self.source_file_uf = source_file_uf
        self.source_file_data_base = source_file_data_base

        self.classification = classification
        self.group = group
        self.type_system = type_system
        self.methodology = methodology

    def __repr__(
        self,
    ) -> str:

        return (
            "CalculationContext("
            f"source_file_uf='{self.source_file_uf}', "
            f"source_file_data_base={self.source_file_data_base}, "
            f"classification='{self.classification}', "
            f"group='{self.group}', "
            f"type_system='{self.type_system}', "
            f"methodology='{self.methodology}'"
            ")"
        )