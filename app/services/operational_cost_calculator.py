from decimal import Decimal


class OperationalCostCalculator:
    """
    Responsável pelo cálculo do custo operacional
    de uma composição.

    O custo operacional é composto pelos custos de:

        - equipamentos
        - mão de obra

    O custo operacional unitário corresponde ao
    custo operacional dividido pela produção da composição.
    """

    def calculate_total(
        self,
        equipment_cost: Decimal,
        labor_cost: Decimal,
    ) -> Decimal:
        """
        Calcula o custo operacional total.

        Fórmula:

            custo operacional
            =
            custo de equipamentos
            +
            custo de mão de obra
        """
        self._validate_cost(
            equipment_cost,
            "Equipment cost",
        )

        self._validate_cost(
            labor_cost,
            "Labor cost",
        )

        return equipment_cost + labor_cost

    def calculate_unit(
        self,
        operational_total: Decimal,
        production: Decimal,
    ) -> Decimal:
        """
        Calcula o custo operacional unitário.

        Fórmula:

            custo operacional unitário
            =
            custo operacional total
            ÷
            produção
        """
        self._validate_cost(
            operational_total,
            "Operational total",
        )

        if production <= Decimal("0"):
            raise ValueError(
                "Production must be greater than zero."
            )

        return operational_total / production

    def _validate_cost(
        self,
        value: Decimal,
        name: str,
    ) -> None:
        """
        Valida um valor de custo.
        """
        if value < Decimal("0"):
            raise ValueError(
                f"{name} cannot be negative."
            )