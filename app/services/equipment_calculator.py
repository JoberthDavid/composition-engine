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

DECIMAL_ONE = Decimal("1")

class EquipmentCalculator:
    """
    Responsável por calcular o custo de uma linha
    de equipamento.

    ```
    Para equipamentos, o SICRO possui dois valores
    monetários distintos:

        - PR: custo produtivo;
        - IM: custo improdutivo.

    A fórmula utilizada é:

        custo do equipamento
        =
        quantidade
        ×
        (
            (uso × custo produtivo)
            +
            ((1 - uso) × custo improdutivo)
        )
    """

    PRODUCTIVE_CLASSIFICATION = "PR"

    UNPRODUCTIVE_CLASSIFICATION = "IM"

    def __init__(
        self,
        monetary_value_resolver: MonetaryValueResolver,
        calculation_context: CalculationContext,
    ) -> None:
        """
        Inicializa o calculador de equipamentos.

        Parameters
        ----------
        monetary_value_resolver:
            Responsável por localizar os valores monetários
            produtivo e improdutivo do equipamento.

        calculation_context:
            Contexto utilizado para selecionar os valores,
            como:

            - UF;
            - data-base;
            - grupo;
            - sistema.
        """

        self.monetary_value_resolver = (
            monetary_value_resolver
        )

        self.calculation_context = (
            calculation_context
        )

    def calculate(
        self,
        equipment: CompositionInput,
    ) -> Decimal:
        """
        Calcula o custo bruto de uma linha de equipamento.

        Fluxo:

            CompositionInput
                    ↓
            resolve PR
                    ↓
            resolve IM
                    ↓
            calcula custo produtivo
                    +
            calcula custo improdutivo
                    ↓
            multiplica pela quantidade
                    ↓
            resultado

        Parameters
        ----------
        equipment:
            Insumo de equipamento da composição.

        Returns
        -------
        Decimal
            Custo bruto da linha de equipamento.
        """

        self._validate_equipment(
            equipment=equipment,
        )

        productive_value = (
            self._resolve_productive_value(
                equipment=equipment,
            )
        )

        unproductive_value = (
            self._resolve_unproductive_value(
                equipment=equipment,
            )
        )

        productive_cost = (
            equipment.input_use
            * productive_value
        )

        unproductive_cost = (
            (
                DECIMAL_ONE
                - equipment.input_use
            )
            * unproductive_value
        )

        total_cost = (
            equipment.input_quantity
            * (
                productive_cost
                + unproductive_cost
            )
        )

        return total_cost

    # ============================================================
    # VALORES MONETÁRIOS
    # ============================================================

    def _resolve_productive_value(
        self,
        equipment: CompositionInput,
    ) -> Decimal:
        """
        Resolve o valor monetário produtivo (PR)
        do equipamento.
        """

        monetary_value = (
            self.monetary_value_resolver.resolve(
                code=equipment.generic_item,
                context=self.calculation_context,
                classification=(
                    self.PRODUCTIVE_CLASSIFICATION
                ),
            )
        )

        return monetary_value.monetary_value

    def _resolve_unproductive_value(
        self,
        equipment: CompositionInput,
    ) -> Decimal:
        """
        Resolve o valor monetário improdutivo (IM)
        do equipamento.
        """

        monetary_value = (
            self.monetary_value_resolver.resolve(
                code=equipment.generic_item,
                context=self.calculation_context,
                classification=(
                    self.UNPRODUCTIVE_CLASSIFICATION
                ),
            )
        )

        return monetary_value.monetary_value

    # ============================================================
    # VALIDAÇÕES
    # ============================================================

    def _validate_equipment(
        self,
        equipment: CompositionInput,
    ) -> None:
        """
        Valida os dados necessários para o cálculo
        de uma linha de equipamento.
        """

        if equipment.input_group != "EQ":

            raise ValueError(
                "Expected equipment input group 'EQ'. "
                f"Received: "
                f"{equipment.input_group}"
            )

        if equipment.input_use is None:

            raise ValueError(
                "Equipment input_use cannot be None. "
                f"Equipment: "
                f"{equipment.generic_item}"
            )

        if equipment.input_use < Decimal("0"):

            raise ValueError(
                "Equipment input_use cannot be negative. "
                f"Equipment: "
                f"{equipment.generic_item}"
            )

        if equipment.input_use > DECIMAL_ONE:

            raise ValueError(
                "Equipment input_use cannot be greater "
                "than 1. "
                f"Equipment: "
                f"{equipment.generic_item}"
            )