from datetime import date
from decimal import Decimal

class MonetaryValue:
    """
    Representa um valor monetário de um insumo.


    Um valor monetário possui:

    - código do insumo;
    - valor monetário;
    - unidade;
    - classificação;
    - grupo;
    - sistema;
    - informações do arquivo de origem.
    """

    def __init__(
        self,
        id: int,
        generic_item: str,
        monetary_value: Decimal,
        unit: str,
        classification: str,
        group: str,
        type_system: str,
        source_file_id: int | None = None,
        source_file_uf: str | None = None,
        source_file_data_base: date | None = None,
    ) -> None:

        self.id = id
        self.generic_item = generic_item
        self.monetary_value = monetary_value
        self.unit = unit
        self.classification = classification
        self.group = group
        self.type_system = type_system

        self.source_file_id = source_file_id
        self.source_file_uf = source_file_uf
        self.source_file_data_base = source_file_data_base

    @classmethod
    def from_api_data(
        cls,
        data: dict,
    ) -> "MonetaryValue":
        """
        Cria um MonetaryValue a partir de um registro
        retornado pela API Django.
        """

        source_file = data.get(
            "source_file"
        )

        source_file_id = None
        source_file_uf = None
        source_file_data_base = None

        if source_file is not None:

            source_file_id = (
                source_file.get("id")
            )

            source_file_uf = (
                source_file.get("uf")
            )

            data_base = (
                source_file.get("data_base")
            )

            if data_base is not None:

                source_file_data_base = (
                    date.fromisoformat(
                        data_base
                    )
                )

        return cls(
            id=data["id"],
            generic_item=data["generic_item"],
            monetary_value=Decimal(
                data["monetary_value"]
            ),
            unit=data["unit"],
            classification=data["classification"],
            group=data["group"],
            type_system=data["type_system"],
            source_file_id=source_file_id,
            source_file_uf=source_file_uf,
            source_file_data_base=source_file_data_base,
        )

    def __repr__(
        self,
    ) -> str:
        """
        Retorna uma representação textual do valor monetário.
        """

        return (
            "MonetaryValue("
            f"id={self.id}, "
            f"generic_item='{self.generic_item}', "
            f"monetary_value={self.monetary_value}, "
            f"unit='{self.unit}', "
            f"classification='{self.classification}', "
            f"group='{self.group}', "
            f"type_system='{self.type_system}', "
            f"source_file_uf='{self.source_file_uf}', "
            f"source_file_data_base="
            f"{self.source_file_data_base}"
            ")"
        )