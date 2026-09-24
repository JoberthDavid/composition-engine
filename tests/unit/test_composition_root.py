from datetime import date
from decimal import Decimal

from app.composition_root import CompositionRoot
from app.domain.calculation_context import CalculationContext
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
from app.services.fic_calculator import (
    FicCalculator,
)


def test_create_composition_explosion_returns_configured_service() -> None:
    root = CompositionRoot(
        composition_data_base="2021-10-01",
    )

    explosion = root.create_composition_explosion()

    assert isinstance(
        explosion,
        CompositionExplosion,
    )

    assert isinstance(
        explosion.resolver,
        CompositionResolver,
    )


def test_create_composition_calculation_returns_service() -> None:
    context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
        type_system="ON",
    )

    root = CompositionRoot(
        composition_data_base="2021-10-01",
    )

    service = root.create_composition_calculation(
        calculation_context=context,
    )

    assert isinstance(
        service,
        CompositionCalculationService,
    )


def test_create_composition_calculation_builds_complete_graph() -> None:
    context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
        type_system="ON",
    )

    root = CompositionRoot(
        composition_data_base="2021-10-01",
    )

    service = root.create_composition_calculation(
        calculation_context=context,
    )

    assert isinstance(
        service._resolver,
        CompositionResolver,
    )

    assert isinstance(
        service._monetary_value_repository,
        type(
            service._monetary_value_repository
        ),
    )

    calculator = service._composition_calculator

    assert isinstance(
        calculator,
        CompositionCalculator,
    )

    assert calculator.calculation_context is context

    assert isinstance(
        calculator.equipment_calculator,
        EquipmentCalculator,
    )

    assert isinstance(
        calculator.labor_calculator,
        LaborCalculator,
    )

    assert isinstance(
        calculator.material_calculator,
        MaterialCalculator,
    )

    assert isinstance(
        calculator.operational_cost_calculator,
        OperationalCostCalculator,
    )

    assert isinstance(
        calculator.fic_calculator,
        FicCalculator,
    )


def test_create_composition_calculation_preserves_calculation_context() -> None:
    context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
        type_system="ON",
    )

    root = CompositionRoot(
        composition_data_base="2021-10-01",
    )

    service = root.create_composition_calculation(
        calculation_context=context,
    )

    calculator = service._composition_calculator

    assert calculator.calculation_context is context

    assert (
        calculator.equipment_calculator.calculation_context
        is context
    )

    assert (
        calculator.labor_calculator.calculation_context
        is context
    )

    assert (
        calculator.material_calculator.calculation_context
        is context
    )