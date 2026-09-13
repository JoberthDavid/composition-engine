from decimal import Decimal


class AggregatedInput:
    """
    Representa um insumo após a agregação de todas
    as suas ocorrências nas composições.

    Para equipamentos, as quantidades são separadas em:

    - productive_quantity;
    - unproductive_quantity.

    Para mão de obra e materiais é utilizada apenas:

    - quantity.
    """

    def __init__(
        self,
        identifier: int,
        group: str,
        code: str,
        description: str,
        unit: str,
        quantity: Decimal = Decimal("0"),
        productive_quantity: Decimal = Decimal("0"),
        unproductive_quantity: Decimal = Decimal("0"),
        proprietary_item: str | None = None,
    ) -> None:

        self.identifier = identifier
        self.group = group
        self.code = code
        self.description = description
        self.unit = unit

        # Utilizado para mão de obra e materiais.
        self.quantity = quantity

        # Utilizados exclusivamente para equipamentos.
        self.productive_quantity = productive_quantity
        self.unproductive_quantity = unproductive_quantity

        self.proprietary_item = proprietary_item

    def is_equipment(self) -> bool:
        """Verifica se o insumo é um equipamento."""

        return self.group == "EQ"

    def is_workman(self) -> bool:
        """Verifica se o insumo é mão de obra."""

        return self.group == "MO"

    def is_material(self) -> bool:
        """Verifica se o insumo é material."""

        return self.group == "MA"

    def add_quantity(
        self,
        quantity: Decimal,
    ) -> None:
        """
        Adiciona quantidade para mão de obra ou material.
        """

        self.quantity += quantity

    def add_equipment_quantity(
        self,
        productive_quantity: Decimal,
        unproductive_quantity: Decimal,
    ) -> None:
        """
        Adiciona as quantidades produtiva e improdutiva
        de um equipamento.
        """

        self.productive_quantity += productive_quantity
        self.unproductive_quantity += unproductive_quantity

    def has_proprietary_item(self) -> bool:
        """Verifica se o insumo está vinculado a um item proprietário."""

        return self.proprietary_item is not None

    def __repr__(self) -> str:

        return (
            f"AggregatedInput("
            f"code='{self.code}', "
            f"group='{self.group}', "
            f"quantity={self.quantity}, "
            f"productive_quantity={self.productive_quantity}, "
            f"unproductive_quantity={self.unproductive_quantity}"
            f")"
        )