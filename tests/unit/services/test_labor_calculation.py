from datetime import date
from decimal import Decimal

import pytest

from app.domain.calculation_context import CalculationContext
from app.domain.composition_input import CompositionInput
from app.domain.monetary_value import MonetaryValue
from app.services.labor_calculator import LaborCalculator


class FakeMonetaryValueResolver:
    """
    Resolver falso utilizado exclusivamente
    para testes unitários.

    Evita chamadas para:
        - API;
        - banco de dados;
        - MonetaryValueRepository.

    O valor monetário é controlado diretamente pelo teste.
    """

    def __init__(
        self,
        monetary_value: Decimal,
    ) -> None:
        self.monetary_value = monetary_value
        self.last_code: str | None = None
        self.last_context: CalculationContext | None = None

    def resolve(
        self,
        code: str,
        context: CalculationContext,
    ) -> MonetaryValue:
        """
        Registra os argumentos recebidos e retorna
        um valor monetário artificial.
        """

        self.last_code = code
        self.last_context = context

        return MonetaryValue(
            id=1,
            generic_item=code,
            monetary_value=self.monetary_value,
            unit="h",
            classification="",
            group="",
            type_system="ON",
            source_file_id=1,
            source_file_uf="DF",
            source_file_data_base=date(2021, 10, 1),
        )


def create_labor(
    code: str = "P0001",
    quantity: Decimal = Decimal("1"),
    input_group: str = "MO",
) -> CompositionInput:
    """
    Cria uma linha de mão de obra para os testes.
    """

    return CompositionInput(
        id=1,
        input_group=input_group,
        generic_item=code,
        generic_description="Mão de obra de teste",
        unit="h",
        input_quantity=quantity,
    )


def create_calculator(
    monetary_value: Decimal,
    context: CalculationContext | None = None,
) -> tuple[LaborCalculator, FakeMonetaryValueResolver, CalculationContext]:
    """
    Cria o LaborCalculator com um resolver falso.
    """

    resolver = FakeMonetaryValueResolver(
        monetary_value=monetary_value,
    )

    if context is None:
        context = CalculationContext()

    calculator = LaborCalculator(
        monetary_value_resolver=resolver,
        calculation_context=context,
    )

    return calculator, resolver, context


def test_labor_basic_calculation() -> None:
    """
    Verifica o cálculo básico de mão de obra.

    quantidade × valor monetário
    8 × 25 = 200
    """

    calculator, _, _ = create_calculator(
        monetary_value=Decimal("25"),
    )

    labor = create_labor(
        quantity=Decimal("8"),
    )

    result = calculator.calculate(
        labor=labor,
    )

    assert result == Decimal("200")


def test_labor_fractional_quantity() -> None:
    """
    Verifica o cálculo com quantidade decimal.

    6.5 × 20 = 130
    """

    calculator, _, _ = create_calculator(
        monetary_value=Decimal("20"),
    )

    labor = create_labor(
        quantity=Decimal("6.5"),
    )

    result = calculator.calculate(
        labor=labor,
    )

    assert result == Decimal("130")


def test_labor_zero_quantity() -> None:
    """
    Verifica que quantidade zero produz custo zero.
    """

    calculator, _, _ = create_calculator(
        monetary_value=Decimal("50"),
    )

    labor = create_labor(
        quantity=Decimal("0"),
    )

    result = calculator.calculate(
        labor=labor,
    )

    assert result == Decimal("0")


def test_labor_decimal_result() -> None:
    """
    Verifica a preservação do cálculo decimal.

    3.25 × 18.40 = 59.8000
    """

    calculator, _, _ = create_calculator(
        monetary_value=Decimal("18.40"),
    )

    labor = create_labor(
        quantity=Decimal("3.25"),
    )

    result = calculator.calculate(
        labor=labor,
    )

    assert result == Decimal("59.8000")


def test_labor_invalid_group() -> None:
    """
    Verifica que LaborCalculator aceita somente
    insumos do grupo MO.
    """

    calculator, resolver, _ = create_calculator(
        monetary_value=Decimal("20"),
    )

    labor = create_labor(
        input_group="MA",
    )

    with pytest.raises(
        ValueError,
        match="^Expected labor input group 'MO'\\. Received: MA$",
    ):
        calculator.calculate(
            labor=labor,
        )

    # A validação deve ocorrer antes da consulta monetária.
    assert resolver.last_code is None
    assert resolver.last_context is None


def test_resolver_receives_correct_code() -> None:
    """
    Verifica que o código do trabalhador é encaminhado
    corretamente ao MonetaryValueResolver.
    """

    calculator, resolver, _ = create_calculator(
        monetary_value=Decimal("30"),
    )

    labor = create_labor(
        code="P9824",
        quantity=Decimal("6"),
    )

    calculator.calculate(
        labor=labor,
    )

    assert resolver.last_code == "P9824"


def test_resolver_receives_correct_context() -> None:
    """
    Verifica que o mesmo CalculationContext fornecido
    ao LaborCalculator é encaminhado ao resolver.
    """

    context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
        type_system="ON",
    )

    calculator, resolver, _ = create_calculator(
        monetary_value=Decimal("30"),
        context=context,
    )

    labor = create_labor()

    calculator.calculate(
        labor=labor,
    )

    assert resolver.last_context is context