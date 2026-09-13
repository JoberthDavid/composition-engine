from decimal import Decimal

from app.domain.aggregated_input import (
AggregatedInput,
)

def test_aggregated_input_adds_quantities() -> None:
    """
    Verifica que um AggregatedInput acumula corretamente
    as quantidades adicionadas.
    """

    aggregated_input = AggregatedInput(
        identifier=1,
        group="M",
        code="1234567",
        description="Insumo de teste",
        unit="kg",
        quantity=Decimal("10.5"),
    )

    assert aggregated_input.identifier == 1
    assert aggregated_input.group == "M"
    assert aggregated_input.code == "1234567"
    assert aggregated_input.description == "Insumo de teste"
    assert aggregated_input.unit == "kg"
    assert aggregated_input.quantity == Decimal("10.5")

    aggregated_input.add_quantity(
        Decimal("5.25")
    )

    assert aggregated_input.quantity == Decimal(
        "15.75"
    )


def test_aggregated_input_accepts_zero_quantity() -> None:
    """
    Verifica a acumulação quando a quantidade inicial é zero.
    """

    aggregated_input = AggregatedInput(
        identifier=1,
        group="M",
        code="1234567",
        description="Insumo de teste",
        unit="kg",
        quantity=Decimal("0"),
    )

    aggregated_input.add_quantity(
        Decimal("5.25")
    )

    assert aggregated_input.quantity == Decimal(
        "5.25"
    )


def test_aggregated_input_preserves_decimal_precision() -> None:
    """
    Verifica que a acumulação preserva a precisão do Decimal.
    """

    aggregated_input = AggregatedInput(
        identifier=1,
        group="M",
        code="1234567",
        description="Insumo de teste",
        unit="kg",
        quantity=Decimal("0.00000"),
    )

    aggregated_input.add_quantity(
        Decimal("0.00017")
    )

    aggregated_input.add_quantity(
        Decimal("0.00003")
    )

    assert aggregated_input.quantity == Decimal(
        "0.00020"
    )