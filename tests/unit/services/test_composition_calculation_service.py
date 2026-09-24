from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from app.domain.calculation_context import CalculationContext
from app.services.composition_calculation_service import (
    CompositionCalculationService,
)


def test_calculate_resolves_tree_loads_values_and_calculates() -> None:
    resolver = Mock()
    monetary_value_repository = Mock()
    composition_calculator = Mock()

    calculation_context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(
            2021,
            10,
            1,
        ),
        type_system="ON",
    )

    tree = Mock()

    tree.monetary_item_codes_by_group = {
        "EQ": {"EQ001"},
        "MO": {"MO001"},
        "MA": {"MA001"},
    }

    expected_result = Mock(
        composition_unit_cost=Decimal(
            "105890.00"
        )
    )

    resolver.resolve_tree_optimized.return_value = tree

    composition_calculator.calculate.return_value = (
        expected_result
    )

    service = CompositionCalculationService(
        resolver=resolver,
        monetary_value_repository=(
            monetary_value_repository
        ),
        composition_calculator=(
            composition_calculator
        ),
        calculation_context=calculation_context,
    )

    result = service.calculate(
        composition_id="0919013",
    )

    resolver.resolve_tree_optimized.assert_called_once_with(
        "0919013",
    )

    monetary_value_repository.load_cache.assert_called_once_with(
        codes_by_group={
            "EQ": {"EQ001"},
            "MO": {"MO001"},
            "MA": {"MA001"},
        },
        type_system="ON",
        source_file_uf="DF",
        source_file_data_base=date(
            2021,
            10,
            1,
        ),
    )

    composition_calculator.calculate.assert_called_once_with(
        tree,
    )

    assert result is expected_result


def test_calculate_does_not_calculate_before_loading_values() -> None:
    resolver = Mock()
    monetary_value_repository = Mock()
    composition_calculator = Mock()

    calculation_context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(
            2021,
            10,
            1,
        ),
        type_system="ON",
    )

    tree = Mock()

    tree.monetary_item_codes_by_group = {
        "EQ": {"EQ001"},
    }

    resolver.resolve_tree_optimized.return_value = tree

    call_order: list[str] = []

    def load_cache(**kwargs) -> None:
        call_order.append("load_cache")

    def calculate(tree) -> None:
        call_order.append("calculate")

    monetary_value_repository.load_cache.side_effect = (
        load_cache
    )

    composition_calculator.calculate.side_effect = (
        calculate
    )

    service = CompositionCalculationService(
        resolver=resolver,
        monetary_value_repository=(
            monetary_value_repository
        ),
        composition_calculator=(
            composition_calculator
        ),
        calculation_context=calculation_context,
    )

    service.calculate(
        composition_id="0919013",
    )

    assert call_order == [
        "load_cache",
        "calculate",
    ]