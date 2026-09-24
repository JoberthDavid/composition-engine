from app.domain.calculation_context import CalculationContext
from app.domain.composition_calculation_result import (
    CompositionCalculationResult,
)
from app.repositories.monetary_value_repository import (
    MonetaryValueRepository,
)
from app.services.composition_calculator import CompositionCalculator
from app.services.composition_resolver import CompositionResolver


class CompositionCalculationService:
    """
    Serviço de aplicação responsável pelo cálculo de uma composição.

    A classe não conhece FastAPI, HTTP ou schemas da API.

    Todas as dependências concretas são recebidas por injeção.
    """

    def __init__(
        self,
        resolver: CompositionResolver,
        monetary_value_repository: MonetaryValueRepository,
        composition_calculator: CompositionCalculator,
        calculation_context: CalculationContext,
    ) -> None:
        self._resolver = resolver
        self._monetary_value_repository = (
            monetary_value_repository
        )
        self._composition_calculator = (
            composition_calculator
        )
        self._calculation_context = calculation_context

    def calculate(
        self,
        composition_id: str,
    ) -> CompositionCalculationResult:
        """
        Resolve a árvore, carrega os valores monetários necessários
        e executa o cálculo completo da composição.
        """

        composition_tree = (
            self._resolver.resolve_tree_optimized(
                composition_id,
            )
        )

        codes_by_group = (
            composition_tree.monetary_item_codes_by_group
        )

        self._monetary_value_repository.load_cache(
            codes_by_group=codes_by_group,
            type_system=(
                self._calculation_context.type_system
            ),
            source_file_uf=(
                self._calculation_context.source_file_uf
            ),
            source_file_data_base=(
                self._calculation_context.source_file_data_base
            ),
        )

        return self._composition_calculator.calculate(
            composition_tree,
        )