from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.domain.calculation_context import CalculationContext
from app.infrastructure.composition_api_client import (
    CompositionApiClient,
)
from app.infrastructure.monetary_value_api_client import (
    MonetaryValueApiClient,
)
from app.repositories.composition_repository import (
    CompositionRepository,
)
from app.repositories.monetary_value_repository import (
    MonetaryValueRepository,
)
from app.repositories.optimized_composition_repository import (
    OptimizedCompositionRepository,
)
from app.services.composition_calculation_service import (
    CompositionCalculationService,
)
from app.services.composition_calculator import (
    CompositionCalculator,
)
from app.services.composition_explosion import (
    CompositionExplosion,
)
from app.services.composition_resolver import (
    CompositionResolver,
)
from app.services.equipment_calculator import (
    EquipmentCalculator,
)
from app.services.fic_calculator import (
    FicCalculator,
)
from app.services.labor_calculator import (
    LaborCalculator,
)
from app.services.material_calculator import (
    MaterialCalculator,
)
from app.services.monetary_value_resolver import (
    MonetaryValueResolver,
)
from app.services.operational_cost_calculator import (
    OperationalCostCalculator,
)


class CompositionRoot:
    """
    Ponto central de composição das dependências da aplicação.

    O CompositionRoot constrói o grafo concreto de objetos
    utilizado pelos serviços da aplicação.

    Ele não contém regras de cálculo. Sua responsabilidade é
    exclusivamente montar e conectar as dependências.
    """

    def __init__(
        self,
        composition_data_base: str | None = None,
    ) -> None:
        self.composition_data_base = composition_data_base

    def create_composition_explosion(
        self,
    ) -> CompositionExplosion:
        """
        Cria um CompositionExplosion completamente configurado.
        """

        api_client = CompositionApiClient()

        composition_repository = CompositionRepository(
            api_client=api_client,
        )

        optimized_repository = (
            OptimizedCompositionRepository(
                api_client=api_client,
                composition_data_base=(
                    self.composition_data_base
                ),
            )
        )

        resolver = CompositionResolver(
            repository=composition_repository,
            optimized_repository=optimized_repository,
        )

        return CompositionExplosion(
            resolver=resolver,
        )

    def create_composition_calculation(
        self,
        calculation_context: CalculationContext,
    ) -> CompositionCalculationService:
        """
        Cria o serviço completo de cálculo de composição.

        O grafo construído é:

            CompositionApiClient
                    │
                    ├── CompositionRepository
                    │
                    └── OptimizedCompositionRepository
                                │
                                ▼
                       CompositionResolver
                                │
                                ▼
                       CompositionCalculationService
                                │
                                ├── MonetaryValueRepository
                                │          │
                                │          ▼
                                │   MonetaryValueResolver
                                │          │
                                │     ┌────┼────┐
                                │     ▼    ▼    ▼
                                │    EQ   MO   MA
                                │
                                └── CompositionCalculator
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                         Operational     FIC       Calculators
                          CostCalc                 EQ/MO/MA
        """

        composition_api_client = (
            CompositionApiClient()
        )

        composition_repository = (
            CompositionRepository(
                api_client=composition_api_client,
            )
        )

        optimized_repository = (
            OptimizedCompositionRepository(
                api_client=composition_api_client,
                composition_data_base=(
                    self.composition_data_base
                ),
            )
        )

        resolver = CompositionResolver(
            repository=composition_repository,
            optimized_repository=optimized_repository,
        )

        monetary_value_api_client = (
            MonetaryValueApiClient()
        )

        monetary_value_repository = (
            MonetaryValueRepository(
                api_client=monetary_value_api_client,
            )
        )

        monetary_value_resolver = (
            MonetaryValueResolver(
                repository=monetary_value_repository,
            )
        )

        equipment_calculator = EquipmentCalculator(
            monetary_value_resolver=(
                monetary_value_resolver
            ),
            calculation_context=(
                calculation_context
            ),
        )

        labor_calculator = LaborCalculator(
            monetary_value_resolver=(
                monetary_value_resolver
            ),
            calculation_context=(
                calculation_context
            ),
        )

        material_calculator = MaterialCalculator(
            monetary_value_resolver=(
                monetary_value_resolver
            ),
            calculation_context=(
                calculation_context
            ),
        )

        operational_cost_calculator = (
            OperationalCostCalculator()
        )

        fic_calculator = FicCalculator()

        def round_2(
            value: Decimal,
        ) -> Decimal:
            return value.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        def round_4(
            value: Decimal,
        ) -> Decimal:
            return value.quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP,
            )

        composition_calculator = (
            CompositionCalculator(
                calculation_context=(
                    calculation_context
                ),
                equipment_calculator=(
                    equipment_calculator
                ),
                labor_calculator=(
                    labor_calculator
                ),
                material_calculator=(
                    material_calculator
                ),
                operational_cost_calculator=(
                    operational_cost_calculator
                ),
                fic_calculator=(
                    fic_calculator
                ),
                round_2=round_2,
                round_4=round_4,
            )
        )

        return CompositionCalculationService(
            resolver=resolver,
            monetary_value_repository=(
                monetary_value_repository
            ),
            composition_calculator=(
                composition_calculator
            ),
            calculation_context=(
                calculation_context
            ),
        )