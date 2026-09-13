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

class MaterialCalculator:
    """
    Responsável por calcular o custo de uma linha
    de material.

    ```
    A fórmula utilizada é:

        custo do material
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
        Inicializa o calculador de materiais.
        """

        self.monetary_value_resolver = (
            monetary_value_resolver
        )

        self.calculation_context = (
            calculation_context
        )

    def calculate(
        self,
        material: CompositionInput,
    ) -> Decimal:
        """
        Calcula o custo bruto de uma linha de material.

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

        self._validate_material(
            material=material,
        )

        monetary_value = self.monetary_value_resolver.resolve(
            code=material.generic_item,
            context=self.calculation_context,
            group="MA",
            type_system="NA",
        )

        return (
            material.input_quantity
            * monetary_value.monetary_value
        )

    # ============================================================
    # VALIDAÇÕES
    # ============================================================

    def _validate_material(
        self,
        material: CompositionInput,
    ) -> None:
        """
        Valida os dados necessários para o cálculo
        de uma linha de material.
        """

        if material.input_group != "MA":

            raise ValueError(
                "Expected material input group 'MA'. "
                f"Received: "
                f"{material.input_group}"
            )