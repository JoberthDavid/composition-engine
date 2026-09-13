from decimal import Decimal


class AggregatedComposition:
    """
    Representa uma composição após a agregação de todas
    as suas ocorrências na árvore de composições.
    """

    def __init__(
        self,
        identifier: int,
        group: str,
        code: str,
        description: str,
        unit: str,
        quantity: Decimal,
    ) -> None:

        self.identifier = identifier
        self.group = group
        self.code = code
        self.description = description
        self.unit = unit
        self.quantity = quantity

    def add_quantity(
        self,
        quantity: Decimal,
    ) -> None:
        """
        Adiciona uma quantidade ao total agregado.
        """

        self.quantity += quantity

    def __repr__(self) -> str:

        return (
            f"AggregatedComposition("
            f"code='{self.code}', "
            f"quantity={self.quantity}"
            f")"
        )
