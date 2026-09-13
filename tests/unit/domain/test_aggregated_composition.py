from decimal import Decimal

from app.domain.aggregated_composition import (
AggregatedComposition,
)

def test_aggregated_composition_adds_quantities() -> None:
    """
    Verifica que uma AggregatedComposition acumula corretamente
    as quantidades adicionadas.
    """

    composition = AggregatedComposition(
        identifier=1,
        group="11",
        code="1107892",
        description="Concreto fck = 20 MPa",
        unit="m³",
        quantity=Decimal("18.28817"),
    )

    assert composition.identifier == 1
    assert composition.group == "11"
    assert composition.code == "1107892"
    assert composition.description == "Concreto fck = 20 MPa"
    assert composition.unit == "m³"
    assert composition.quantity == Decimal("18.28817")

    composition.add_quantity(
        Decimal("32.40000")
    )

    composition.add_quantity(
        Decimal("11.43300")
    )

    composition.add_quantity(
        Decimal("9.10000")
    )

    expected_quantity = Decimal(
        "71.22117"
    )

    assert composition.quantity == expected_quantity


def test_aggregated_composition_accepts_zero_quantity() -> None:
    """
    Verifica o comportamento da composição agregada quando
    sua quantidade inicial é zero.
    """

    composition = AggregatedComposition(
        identifier=1,
        group="11",
        code="1107892",
        description="Concreto fck = 20 MPa",
        unit="m³",
        quantity=Decimal("0"),
    )

    composition.add_quantity(
        Decimal("10.50000")
    )

    assert composition.quantity == Decimal(
        "10.50000"
    )


def test_aggregated_composition_preserves_decimal_precision() -> None:
    """
    Verifica que a agregação utiliza Decimal sem introduzir
    perdas de precisão de ponto flutuante.
    """

    composition = AggregatedComposition(
        identifier=1,
        group="11",
        code="1107892",
        description="Concreto fck = 20 MPa",
        unit="m³",
        quantity=Decimal("0.00000"),
    )

    composition.add_quantity(
        Decimal("0.00017")
    )

    composition.add_quantity(
        Decimal("0.00003")
    )

    assert composition.quantity == Decimal(
        "0.00020"
    )