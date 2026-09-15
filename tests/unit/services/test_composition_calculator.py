from decimal import Decimal
from unittest.mock import MagicMock

from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree
from app.services.composition_calculator import CompositionCalculator


def _build_composition(
    code: str = "0919001",
    production: str = "1",
    fic: str = "0",
    equipments: list[CompositionInput] | None = None,
    workmen: list[CompositionInput] | None = None,
    materials: list[CompositionInput] | None = None,
) -> Composition:
    return Composition(
        id=1,
        composition_group="C",
        generic_item=code,
        generic_description="Composição de teste",
        unit="UN",
        fic=Decimal(fic),
        production=Decimal(production),
        equipments=equipments or [],
        workmen=workmen or [],
        materials=materials or [],
        activities=[],
        transports=[],
    )


def _build_input(
    input_group: str,
    code: str,
    quantity: str = "1",
) -> CompositionInput:
    return CompositionInput(
        id=1,
        input_group=input_group,
        generic_item=code,
        generic_description="Insumo de teste",
        unit="UN",
        input_quantity=Decimal(quantity),
    )


def _build_calculator() -> CompositionCalculator:
    calculation_context = MagicMock()

    equipment_calculator = MagicMock()
    labor_calculator = MagicMock()
    material_calculator = MagicMock()
    operational_cost_calculator = MagicMock()
    fic_calculator = MagicMock()

    calculator = CompositionCalculator(
        calculation_context=calculation_context,
        equipment_calculator=equipment_calculator,
        labor_calculator=labor_calculator,
        material_calculator=material_calculator,
        operational_cost_calculator=operational_cost_calculator,
        fic_calculator=fic_calculator,
        round_2=lambda value: value,
        round_4=lambda value: value,
    )

    return calculator


def _configure_zero_cost_calculators(
    calculator: CompositionCalculator,
) -> None:
    calculator.equipment_calculator.calculate.return_value = Decimal("0")

    calculator.labor_calculator.calculate.return_value = Decimal("0")

    calculator.material_calculator.calculate.return_value = Decimal("0")

    calculator.operational_cost_calculator.calculate_total.return_value = (
        Decimal("0")
    )

    calculator.operational_cost_calculator.calculate_unit.return_value = (
        Decimal("0")
    )

    calculator.fic_calculator.calculate.return_value = Decimal("0")


def test_calculate_returns_result_associated_with_root_occurrence() -> None:
    """
    O resultado retornado por calculate() deve estar associado
    à ocorrência exata do nó raiz da árvore.
    """

    calculator = _build_calculator()
    _configure_zero_cost_calculators(calculator)

    composition = _build_composition()

    root = CompositionNode(
        composition=composition,
    )

    tree = CompositionTree(
        root=root,
    )

    result = calculator.calculate(tree)

    assert result.node is root
    assert result.composition_unit_cost == Decimal("0")


def test_calculate_processes_children_before_parent() -> None:
    """
    O cálculo deve respeitar a pós-ordem da árvore:

        filho -> pai

    Isso garante que os resultados dos filhos estejam disponíveis
    quando o custo da composição pai for calculado.
    """

    calculator = _build_calculator()
    _configure_zero_cost_calculators(calculator)

    child_reference = _build_input(
        input_group="AX",
        code="0919002",
        quantity="2",
    )

    parent_composition = _build_composition(
        code="0919001",
    )

    child_composition = _build_composition(
        code="0919002",
    )

    root = CompositionNode(
        composition=parent_composition,
    )

    child = CompositionNode(
        composition=child_composition,
        reference_input=child_reference,
    )

    root.add_child(child)

    tree = CompositionTree(
        root=root,
    )

    calculator.operational_cost_calculator.calculate_total.side_effect = [
        Decimal("10"),
        Decimal("20"),
    ]

    calculator.operational_cost_calculator.calculate_unit.side_effect = [
        Decimal("10"),
        Decimal("20"),
    ]

    result = calculator.calculate(tree)

    assert result.node is root

    assert (
        calculator.operational_cost_calculator.calculate_total.call_count
        == 2
    )

    assert (
        calculator.operational_cost_calculator.calculate_unit.call_count
        == 2
    )


def test_calculate_preserves_distinct_occurrences_with_same_composition_code() -> None:
    """
    Duas ocorrências da mesma composição devem ser calculadas
    como nós distintos da árvore.
    """

    calculator = _build_calculator()
    _configure_zero_cost_calculators(calculator)

    composition = _build_composition(
        code="0919001",
    )

    root = CompositionNode(
        composition=composition,
    )

    child_1 = CompositionNode(
        composition=composition,
    )

    child_2 = CompositionNode(
        composition=composition,
    )

    root.add_child(child_1)
    root.add_child(child_2)

    tree = CompositionTree(
        root=root,
    )

    result = calculator.calculate(tree)

    assert result.node is root

    assert (
        calculator.operational_cost_calculator.calculate_total.call_count
        == 3
    )

    assert (
        calculator.operational_cost_calculator.calculate_unit.call_count
        == 3
    )

    assert calculator.fic_calculator.calculate.call_count == 3


def test_calculate_delegates_cost_components_to_specialized_calculators() -> None:
    """
    CompositionCalculator deve delegar o cálculo dos componentes
    de custo aos calculadores especializados.
    """

    equipment = _build_input(
        input_group="EQ",
        code="E0001",
        quantity="1",
    )

    labor = _build_input(
        input_group="MO",
        code="M0001",
        quantity="1",
    )

    material = _build_input(
        input_group="MA",
        code="MAT0001",
        quantity="1",
    )

    calculator = _build_calculator()

    calculator.equipment_calculator.calculate.return_value = Decimal(
        "10"
    )

    calculator.labor_calculator.calculate.return_value = Decimal(
        "20"
    )

    calculator.material_calculator.calculate.return_value = Decimal(
        "30"
    )

    calculator.operational_cost_calculator.calculate_total.return_value = (
        Decimal("40")
    )

    calculator.operational_cost_calculator.calculate_unit.return_value = (
        Decimal("40")
    )

    calculator.fic_calculator.calculate.return_value = Decimal(
        "5"
    )

    composition = _build_composition(
        equipments=[equipment],
        workmen=[labor],
        materials=[material],
    )

    root = CompositionNode(
        composition=composition,
    )

    tree = CompositionTree(
        root=root,
    )

    result = calculator.calculate(tree)

    assert result.node is root

    calculator.equipment_calculator.calculate.assert_called_once_with(
        equipment
    )

    calculator.labor_calculator.calculate.assert_called_once_with(
        labor
    )

    calculator.material_calculator.calculate.assert_called_once_with(
        material
    )

    calculator.operational_cost_calculator.calculate_total.assert_called_once_with(
        equipment_cost=Decimal("10"),
        labor_cost=Decimal("20"),
    )

    calculator.operational_cost_calculator.calculate_unit.assert_called_once_with(
        operational_total=Decimal("40"),
        production=Decimal("1"),
    )

    calculator.fic_calculator.calculate.assert_called_once_with(
        operational_unit_cost=Decimal("40"),
        fic_percentage=Decimal("0"),
    )

def test_calculate_uses_child_unit_cost_for_auxiliary_activity() -> None:
    """
    Uma composição pai com uma referência AX deve utilizar o
    custo unitário final da ocorrência filha calculada na mesma
    execução.

    Neste cenário:

        custo unitário da filha = 10
        quantidade da referência AX = 2

    Portanto:

        custo AX do pai = 2 × 10 = 20
    """

    calculator = _build_calculator()

    _configure_zero_cost_calculators(calculator)

    child_reference = _build_input(
        input_group="AX",
        code="0919002",
        quantity="2",
    )

    parent_composition = _build_composition(
        code="0919001",
    )

    child_composition = _build_composition(
        code="0919002",
    )

    root = CompositionNode(
        composition=parent_composition,
    )

    child = CompositionNode(
        composition=child_composition,
        reference_input=child_reference,
    )

    root.add_child(child)

    tree = CompositionTree(
        root=root,
    )

    # A filha será calculada primeiro:
    #
    #   custo operacional unitário = 10
    #
    # O pai será calculado depois:
    #
    #   custo operacional unitário = 0
    #
    # Assim, o único custo do pai será o AX:
    #
    #   2 × 10 = 20
    calculator.operational_cost_calculator.calculate_total.side_effect = [
        Decimal("10"),
        Decimal("0"),
    ]

    calculator.operational_cost_calculator.calculate_unit.side_effect = [
        Decimal("10"),
        Decimal("0"),
    ]

    result = calculator.calculate(tree)

    assert result.node is root

    assert result.auxiliary_cost == Decimal("20")

    assert result.composition_total_raw == Decimal("20")

    assert result.composition_unit_cost == Decimal("20")
