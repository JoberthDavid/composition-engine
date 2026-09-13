from datetime import date
from decimal import Decimal

from app.domain.calculation_context import (
    CalculationContext,
)
from app.domain.composition_input import (
    CompositionInput,
)
from app.domain.monetary_value import (
    MonetaryValue,
)
from app.services.equipment_calculator import (
    EquipmentCalculator,
)


# ============================================================
# FAKE MONETARY VALUE RESOLVER
# ============================================================


class FakeMonetaryValueResolver:
    """
    Implementação falsa do MonetaryValueResolver
    utilizada exclusivamente para testes unitários.

    Não realiza chamadas para:

        - API;
        - banco de dados;
        - rede.

    Retorna valores previamente definidos para as
    classificações:

        PR
        IM
    """

    def __init__(
        self,
        productive_value: Decimal,
        unproductive_value: Decimal,
    ) -> None:

        self.productive_value = (
            productive_value
        )

        self.unproductive_value = (
            unproductive_value
        )

        self.calls: list[dict] = []

    def resolve(
        self,
        code: str,
        context: CalculationContext,
        classification: str | None = None,
    ) -> MonetaryValue:
        """
        Retorna um MonetaryValue fictício conforme
        a classificação solicitada.
        """

        self.calls.append(
            {
                "code": code,
                "context": context,
                "classification": classification,
            }
        )

        if classification == "PR":

            return MonetaryValue(
                id=1,
                generic_item=code,
                monetary_value=(
                    self.productive_value
                ),
                unit="h",
                classification="PR",
                group="",
                type_system="ON",
                source_file_id=None,
                source_file_uf="DF",
                source_file_data_base=(
                    date(
                        2021,
                        10,
                        1,
                    )
                ),
            )

        if classification == "IM":

            return MonetaryValue(
                id=2,
                generic_item=code,
                monetary_value=(
                    self.unproductive_value
                ),
                unit="h",
                classification="IM",
                group="",
                type_system="ON",
                source_file_id=None,
                source_file_uf="DF",
                source_file_data_base=(
                    date(
                        2021,
                        10,
                        1,
                    )
                ),
            )

        raise ValueError(
            "Unexpected classification: "
            f"{classification}"
        )


# ============================================================
# HELPERS
# ============================================================


def create_context() -> CalculationContext:
    """
    Cria um CalculationContext fictício
    para os testes.
    """

    return CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(
            2021,
            10,
            1,
        ),
        type_system="ON",
    )


def create_equipment(
    quantity: Decimal,
    use: Decimal | None,
    input_group: str = "EQ",
) -> CompositionInput:
    """
    Cria um equipamento fictício para os testes.
    """

    return CompositionInput(
        id=1,
        input_group=input_group,
        generic_item="E0001",
        generic_description=(
            "Equipamento de teste"
        ),
        unit="h",
        input_quantity=quantity,
        input_use=use,
    )


def create_calculator(
    productive_value: Decimal,
    unproductive_value: Decimal,
) -> tuple[
    EquipmentCalculator,
    FakeMonetaryValueResolver,
]:
    """
    Cria um EquipmentCalculator utilizando
    um FakeMonetaryValueResolver.
    """

    resolver = (
        FakeMonetaryValueResolver(
            productive_value=productive_value,
            unproductive_value=unproductive_value,
        )
    )

    context = create_context()

    calculator = EquipmentCalculator(
        monetary_value_resolver=resolver,
        calculation_context=context,
    )

    return (
        calculator,
        resolver,
    )


# ============================================================
# TESTE 1
# ============================================================


def test_mixed_productive_and_unproductive_cost() -> None:
    """
    Testa o cálculo misto entre custo produtivo
    e improdutivo.

    Dados:

        quantidade = 1
        uso = 0.5

        PR = 100
        IM = 20

    Fórmula:

        1 × (
            (0.5 × 100)
            +
            ((1 - 0.5) × 20)
        )

        =

        1 × (
            50
            +
            10
        )

        =

        60
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 1 - CÁLCULO MISTO PR E IM"
    )
    print(
        "-" * 100
    )

    calculator, resolver = (
        create_calculator(
            productive_value=Decimal("100"),
            unproductive_value=Decimal("20"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("1"),
        use=Decimal("0.5"),
    )

    result = calculator.calculate(
        equipment=equipment,
    )

    expected = Decimal("60")

    print()
    print(
        "Quantidade:"
    )
    print(
        equipment.input_quantity
    )

    print()
    print(
        "Uso:"
    )
    print(
        equipment.input_use
    )

    print()
    print(
        "PR:"
    )
    print(
        "100"
    )

    print()
    print(
        "IM:"
    )
    print(
        "20"
    )

    print()
    print(
        "Resultado:"
    )
    print(
        result
    )

    print()
    print(
        "Esperado:"
    )
    print(
        expected
    )

    assert result == expected

    # Verifica se PR e IM foram resolvidos.
    assert len(
        resolver.calls
    ) == 2

    assert (
        resolver.calls[0][
            "classification"
        ]
        == "PR"
    )

    assert (
        resolver.calls[1][
            "classification"
        ]
        == "IM"
    )

    print()
    print(
        "TESTE APROVADO"
    )


# ============================================================
# TESTE 2
# ============================================================


def test_fully_productive_equipment() -> None:
    """
    Testa equipamento totalmente produtivo.

    Dados:

        quantidade = 2
        uso = 1

        PR = 50
        IM = 10

    Fórmula:

        2 × (
            (1 × 50)
            +
            ((1 - 1) × 10)
        )

        =

        2 × 50

        =

        100
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 2 - EQUIPAMENTO 100% PRODUTIVO"
    )
    print(
        "-" * 100
    )

    calculator, _ = (
        create_calculator(
            productive_value=Decimal("50"),
            unproductive_value=Decimal("10"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("2"),
        use=Decimal("1"),
    )

    result = calculator.calculate(
        equipment=equipment,
    )

    expected = Decimal("100")

    print()
    print(
        "Resultado:"
    )
    print(
        result
    )

    print()
    print(
        "Esperado:"
    )
    print(
        expected
    )

    assert result == expected

    print()
    print(
        "TESTE APROVADO"
    )


# ============================================================
# TESTE 3
# ============================================================


def test_fully_unproductive_equipment() -> None:
    """
    Testa equipamento totalmente improdutivo.

    Dados:

        quantidade = 2
        uso = 0

        PR = 100
        IM = 20

    Fórmula:

        2 × (
            (0 × 100)
            +
            ((1 - 0) × 20)
        )

        =

        2 × 20

        =

        40
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 3 - EQUIPAMENTO 100% IMPRODUTIVO"
    )
    print(
        "-" * 100
    )

    calculator, _ = (
        create_calculator(
            productive_value=Decimal("100"),
            unproductive_value=Decimal("20"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("2"),
        use=Decimal("0"),
    )

    result = calculator.calculate(
        equipment=equipment,
    )

    expected = Decimal("40")

    print()
    print(
        "Resultado:"
    )
    print(
        result
    )

    print()
    print(
        "Esperado:"
    )
    print(
        expected
    )

    assert result == expected

    print()
    print(
        "TESTE APROVADO"
    )


# ============================================================
# TESTE 4
# ============================================================


def test_partial_equipment_use() -> None:
    """
    Testa equipamento com uso parcial.

    Dados:

        quantidade = 3
        uso = 0.25

        PR = 80
        IM = 10

    Fórmula:

        3 × (
            (0.25 × 80)
            +
            ((1 - 0.25) × 10)
        )

        =

        3 × (
            20
            +
            7.5
        )

        =

        82.5
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 4 - EQUIPAMENTO COM USO PARCIAL"
    )
    print(
        "-" * 100
    )

    calculator, _ = (
        create_calculator(
            productive_value=Decimal("80"),
            unproductive_value=Decimal("10"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("3"),
        use=Decimal("0.25"),
    )

    result = calculator.calculate(
        equipment=equipment,
    )

    expected = Decimal("82.5")

    print()
    print(
        "Resultado:"
    )
    print(
        result
    )

    print()
    print(
        "Esperado:"
    )
    print(
        expected
    )

    assert result == expected

    print()
    print(
        "TESTE APROVADO"
    )


# ============================================================
# TESTES DE VALIDAÇÃO
# ============================================================


def test_invalid_input_group() -> None:
    """
    Verifica se o EquipmentCalculator rejeita
    um insumo cujo grupo não seja EQ.
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 5 - GRUPO INVÁLIDO"
    )
    print(
        "-" * 100
    )

    calculator, _ = (
        create_calculator(
            productive_value=Decimal("100"),
            unproductive_value=Decimal("20"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("1"),
        use=Decimal("0.5"),
        input_group="MA",
    )

    try:

        calculator.calculate(
            equipment=equipment,
        )

    except ValueError as error:

        print()
        print(
            "Erro esperado:"
        )
        print(
            error
        )

        assert (
            "Expected equipment input group"
            in str(error)
        )

        print()
        print(
            "TESTE APROVADO"
        )

        return

    raise AssertionError(
        "Expected ValueError was not raised."
    )


def test_input_use_none() -> None:
    """
    Verifica se input_use=None gera erro.
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 6 - INPUT USE NONE"
    )
    print(
        "-" * 100
    )

    calculator, _ = (
        create_calculator(
            productive_value=Decimal("100"),
            unproductive_value=Decimal("20"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("1"),
        use=None,
    )

    try:

        calculator.calculate(
            equipment=equipment,
        )

    except ValueError as error:

        print()
        print(
            "Erro esperado:"
        )
        print(
            error
        )

        assert (
            "input_use cannot be None"
            in str(error)
        )

        print()
        print(
            "TESTE APROVADO"
        )

        return

    raise AssertionError(
        "Expected ValueError was not raised."
    )


def test_negative_input_use() -> None:
    """
    Verifica se input_use negativo gera erro.
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 7 - INPUT USE NEGATIVO"
    )
    print(
        "-" * 100
    )

    calculator, _ = (
        create_calculator(
            productive_value=Decimal("100"),
            unproductive_value=Decimal("20"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("1"),
        use=Decimal("-0.01"),
    )

    try:

        calculator.calculate(
            equipment=equipment,
        )

    except ValueError as error:

        print()
        print(
            "Erro esperado:"
        )
        print(
            error
        )

        assert (
            "cannot be negative"
            in str(error)
        )

        print()
        print(
            "TESTE APROVADO"
        )

        return

    raise AssertionError(
        "Expected ValueError was not raised."
    )


def test_input_use_greater_than_one() -> None:
    """
    Verifica se input_use maior que 1 gera erro.
    """

    print()
    print(
        "-" * 100
    )
    print(
        "TESTE 8 - INPUT USE MAIOR QUE 1"
    )
    print(
        "-" * 100
    )

    calculator, _ = (
        create_calculator(
            productive_value=Decimal("100"),
            unproductive_value=Decimal("20"),
        )
    )

    equipment = create_equipment(
        quantity=Decimal("1"),
        use=Decimal("1.01"),
    )

    try:

        calculator.calculate(
            equipment=equipment,
        )

    except ValueError as error:

        print()
        print(
            "Erro esperado:"
        )
        print(
            error
        )

        assert (
            "cannot be greater than 1"
            in str(error)
        )

        print()
        print(
            "TESTE APROVADO"
        )

        return

    raise AssertionError(
        "Expected ValueError was not raised."
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """
    Executa todos os testes unitários.
    """

    print()
    print(
        "=" * 100
    )
    print(
        "TESTES UNITÁRIOS DO EQUIPMENT CALCULATOR"
    )
    print(
        "=" * 100
    )

    # Cálculos
    test_mixed_productive_and_unproductive_cost()

    test_fully_productive_equipment()

    test_fully_unproductive_equipment()

    test_partial_equipment_use()

    # Validações
    test_invalid_input_group()

    test_input_use_none()

    test_negative_input_use()

    test_input_use_greater_than_one()

    print()
    print(
        "=" * 100
    )
    print(
        "TODOS OS TESTES FORAM CONCLUÍDOS COM SUCESSO"
    )
    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()