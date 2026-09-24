from datetime import date
from decimal import Decimal

from app.composition_root import CompositionRoot
from app.domain.calculation_context import CalculationContext


ROOT_COMPOSITION_CODE = "0919013"
COMPOSITION_DATA_BASE = "2021-10-01"
MONETARY_DATA_BASE = date(2021, 10, 1)


def test_composition_root_reproduces_historical_calculation() -> None:
    context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=MONETARY_DATA_BASE,
        type_system="ON",
    )

    root = CompositionRoot(
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    service = root.create_composition_calculation(
        calculation_context=context,
    )

    result = service.calculate(
        composition_id=ROOT_COMPOSITION_CODE,
    )

    assert result.composition_unit_cost == Decimal(
        "105890.00"
    )