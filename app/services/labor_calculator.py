from decimal import Decimal

from app.domain.calculation_context import (
CalculationContext,
)
from app.domain.composition_input import (
CompositionInput,
)
from app.services.monetary_value_resolver import (
MonetaryValueResolver,
)

class LaborCalculator:
    """
    Responsável por calcular o custo de uma linha
    de mão de obra.

    ```
    A fórmula utilizada é:

        custo da mão de obra
        =
        quantidade
        ×
        valor monetário
    """

    def __init__(
        self,
        monetary_value_resolver: MonetaryValueResolver,
        calculation_context: CalculationContext,
    ) -> None:
        """
        Inicializa o calculador de mão de obra.
        """

        self.monetary_value_resolver = (
            monetary_value_resolver
        )

        self.calculation_context = (
            calculation_context
        )

    def calculate(
        self,
        labor: CompositionInput,
    ) -> Decimal:
        """
        Calcula o custo bruto de uma linha
        de mão de obra.

        Fluxo:

            CompositionInput
                    ↓
            MonetaryValueResolver
                    ↓
            MonetaryValue
                    ↓
            quantidade
                    ×
            valor monetário
                    ↓
            resultado
        """

        self._validate_labor(
            labor=labor,
        )

        monetary_value = (
            self.monetary_value_resolver.resolve(
                code=labor.generic_item,
                context=self.calculation_context,
            )
        )

        return (
            labor.input_quantity
            * monetary_value.monetary_value
        )

    # ============================================================
    # VALIDAÇÕES
    # ============================================================

    def _validate_labor(
        self,
        labor: CompositionInput,
    ) -> None:
        """
        Valida os dados necessários para o cálculo
        da mão de obra.
        """

        if labor.input_group != "MO":

            raise ValueError(
                "Expected labor input group 'MO'. "
                f"Received: "
                f"{labor.input_group}"
            )