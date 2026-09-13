from decimal import Decimal


class FicCalculator:
    """
    Responsável por calcular o custo referente ao FIC
    de uma composição.

    A fórmula utilizada é:

        custo do FIC
        =
        custo operacional unitário
        ×
        percentual do FIC
    """

    def calculate(
        self,
        operational_unit_cost: Decimal,
        fic_percentage: Decimal,
    ) -> Decimal:
        """
        Calcula o custo unitário referente ao FIC.

        Parâmetros:

            operational_unit_cost:
                Custo operacional unitário da composição,
                antes da aplicação do FIC.

            fic_percentage:
                Percentual do FIC armazenado na composição.

        Retorna:

            Custo unitário correspondente ao FIC.
        """

        self._validate_inputs(
            operational_unit_cost=operational_unit_cost,
            fic_percentage=fic_percentage,
        )

        return (
            operational_unit_cost
            * fic_percentage
        )

    def _validate_inputs(
        self,
        operational_unit_cost: Decimal,
        fic_percentage: Decimal,
    ) -> None:
        """
        Valida os valores utilizados no cálculo do FIC.
        """

        if operational_unit_cost < Decimal("0"):
            raise ValueError(
                "Operational unit cost cannot be negative."
            )

        if fic_percentage < Decimal("0"):
            raise ValueError(
                "FIC percentage cannot be negative."
            )