from decimal import Decimal

import pytest

from app.domain.aggregated_input import AggregatedInput
from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree
from app.services.input_aggregator import InputAggregator


# ============================================================
# HELPERS
# ============================================================


def _build_input(
    identifier: int = 1,
    code: str = "INPUT",
    group: str = "MA",
    quantity: str = "1",
    use: str | None = None,
    description: str = "Input",
    unit: str = "un",
    proprietary_item: str | None = None,
) -> CompositionInput:
    """
    Cria um CompositionInput para os testes.
    """

    return CompositionInput(
        id=identifier,
        input_group=group,
        generic_item=code,
        generic_description=description,
        unit=unit,
        input_quantity=Decimal(quantity),
        input_use=(
            Decimal(use)
            if use is not None
            else None
        ),
        proprietary_item=proprietary_item,
    )


def _build_composition(
    identifier: int = 1,
    code: str = "ROOT",
    description: str = "Root composition",
    unit: str = "un",
    production: str = "1",
) -> Composition:
    """
    Cria uma composição vazia para os testes.
    """

    return Composition(
        id=identifier,
        composition_group="CC",
        generic_item=code,
        generic_description=description,
        unit=unit,
        fic=Decimal("0"),
        production=Decimal(production),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[],
        transports=[],
    )


def _build_reference_input(
    identifier: int = 1,
    code: str = "CHILD",
    quantity: str = "1",
    group: str = "AX",
) -> CompositionInput:
    """
    Cria um CompositionInput utilizado para referenciar
    uma composição filha.
    """

    return _build_input(
        identifier=identifier,
        code=code,
        group=group,
        quantity=quantity,
        description="Composition reference",
    )


def _build_tree(
    root_node: CompositionNode,
) -> CompositionTree:
    """
    Cria uma CompositionTree a partir do nó raiz.

    A árvore deve ser criada somente depois que todos
    os filhos necessários tiverem sido adicionados.
    """

    return CompositionTree(root_node)


def _get_result_by_code(
    results: list[AggregatedInput],
    code: str,
) -> AggregatedInput:
    """
    Retorna o resultado agregado correspondente ao código.
    """

    for result in results:
        if result.code == code:
            return result

    raise AssertionError(
        f"AggregatedInput with code '{code}' not found."
    )


# ============================================================
# EQUIPMENT
# ============================================================


def test_aggregates_equipment_productive_and_unproductive_quantities() -> None:
    """
    Verifica a divisão da quantidade de equipamento em
    produtiva e improdutiva.

    quantidade = 10
    produção = 2
    uso = 0.75

    base = 10 / 2 = 5

    produtiva:
        5 × 0.75 = 3.75

    improdutiva:
        5 × 0.25 = 1.25
    """

    equipment = _build_input(
        code="E0001",
        group="EQ",
        quantity="10",
        use="0.75",
    )

    composition = _build_composition(
        production="2",
    )

    composition.equipments.append(
        equipment
    )

    root_node = CompositionNode(
        composition=composition,
    )

    composition_tree = _build_tree(
        root_node
    )

    result = InputAggregator().aggregate(
        composition_tree
    )

    equipment_result = _get_result_by_code(
        result,
        "E0001",
    )

    assert equipment_result.productive_quantity == Decimal("3.75")
    assert equipment_result.unproductive_quantity == Decimal("1.25")


def test_equipment_without_use_is_fully_productive() -> None:
    """
    Verifica que equipamento sem uso informado é considerado
    integralmente produtivo.
    """

    equipment = _build_input(
        code="E0001",
        group="EQ",
        quantity="10",
    )

    composition = _build_composition(
        production="2",
    )

    composition.equipments.append(
        equipment
    )

    root_node = CompositionNode(
        composition=composition,
    )

    composition_tree = _build_tree(
        root_node
    )

    result = InputAggregator().aggregate(
        composition_tree
    )

    equipment_result = _get_result_by_code(
        result,
        "E0001",
    )

    assert equipment_result.productive_quantity == Decimal("5")
    assert equipment_result.unproductive_quantity == Decimal("0")


# ============================================================
# WORKMAN
# ============================================================


def test_aggregates_workman_using_composition_production() -> None:
    """
    Verifica que a mão de obra é dividida pela produção
    da composição.

    quantidade = 10
    produção = 2

    resultado = 10 / 2 = 5
    """

    workman = _build_input(
        code="P0001",
        group="MO",
        quantity="10",
    )

    composition = _build_composition(
        production="2",
    )

    composition.workmen.append(
        workman
    )

    root_node = CompositionNode(
        composition=composition,
    )

    composition_tree = _build_tree(
        root_node
    )

    result = InputAggregator().aggregate(
        composition_tree
    )

    workman_result = _get_result_by_code(
        result,
        "P0001",
    )

    assert workman_result.quantity == Decimal("5")


# ============================================================
# MATERIAL
# ============================================================


def test_aggregates_material_without_dividing_by_production() -> None:
    """
    Verifica que materiais não são divididos pela produção.

    quantidade = 10
    produção = 2

    resultado = 10
    """

    material = _build_input(
        code="M0001",
        group="MA",
        quantity="10",
    )

    composition = _build_composition(
        production="2",
    )

    composition.materials.append(
        material
    )

    root_node = CompositionNode(
        composition=composition,
    )

    composition_tree = _build_tree(
        root_node
    )

    result = InputAggregator().aggregate(
        composition_tree
    )

    material_result = _get_result_by_code(
        result,
        "M0001",
    )

    assert material_result.quantity == Decimal("10")


# ============================================================
# REPEATED INPUTS
# ============================================================


def test_aggregates_repeated_inputs_by_code() -> None:
    """
    Verifica que ocorrências do mesmo insumo são agregadas
    pelo código.
    """

    material_a = _build_input(
        identifier=1,
        code="M0001",
        group="MA",
        quantity="2.5",
    )

    material_b = _build_input(
        identifier=2,
        code="M0001",
        group="MA",
        quantity="1.75",
    )

    composition_a = _build_composition(
        identifier=2,
        code="COMP_A",
        production="1",
    )

    composition_b = _build_composition(
        identifier=3,
        code="COMP_B",
        production="1",
    )

    composition_a.materials.append(
        material_a
    )

    composition_b.materials.append(
        material_b
    )

    root_node = CompositionNode(
        composition=_build_composition()
    )

    child_a = CompositionNode(
        composition=composition_a,
    )

    child_b = CompositionNode(
        composition=composition_b,
    )

    root_node.add_child(
        child_a
    )

    root_node.add_child(
        child_b
    )

    composition_tree = _build_tree(
        root_node
    )

    result = InputAggregator().aggregate(
        composition_tree
    )

    material_result = _get_result_by_code(
        result,
        "M0001",
    )

    assert material_result.quantity == Decimal("4.25")


def test_aggregates_equipment_from_multiple_occurrences() -> None:
    """
    Verifica que ocorrências de um mesmo equipamento são agregadas
    somando separadamente as parcelas produtiva e improdutiva.

    Equipamento A:

        quantidade = 4
        produção = 2
        uso = 0.50

        base = 4 / 2 = 2
        produtiva = 1
        improdutiva = 1

    Equipamento B:

        quantidade = 6
        produção = 3
        uso = 0.50

        base = 6 / 3 = 2
        produtiva = 1
        improdutiva = 1

    Resultado:

        produtiva = 2
        improdutiva = 2
    """

    equipment_a = _build_input(
        identifier=1,
        code="E0001",
        group="EQ",
        quantity="4",
        use="0.50",
    )

    equipment_b = _build_input(
        identifier=2,
        code="E0001",
        group="EQ",
        quantity="6",
        use="0.50",
    )

    composition_a = _build_composition(
        identifier=2,
        code="COMP_A",
        production="2",
    )

    composition_b = _build_composition(
        identifier=3,
        code="COMP_B",
        production="3",
    )

    composition_a.equipments.append(
        equipment_a
    )

    composition_b.equipments.append(
        equipment_b
    )

    root_node = CompositionNode(
        composition=_build_composition()
    )

    child_a = CompositionNode(
        composition=composition_a,
    )

    child_b = CompositionNode(
        composition=composition_b,
    )

    root_node.add_child(
        child_a
    )

    root_node.add_child(
        child_b
    )

    composition_tree = _build_tree(
        root_node
    )

    result = InputAggregator().aggregate(
        composition_tree
    )

    equipment_result = _get_result_by_code(
        result,
        "E0001",
    )

    assert equipment_result.productive_quantity == Decimal("2")
    assert equipment_result.unproductive_quantity == Decimal("2")


# ============================================================
# IGNORED INPUTS
# ============================================================


def test_ignores_composition_references_and_transport_inputs() -> None:
    """
    Verifica que AX, TF, LN, RP, PV e FR não são agregados
    nesta etapa.

    Apenas EQ, MO e MA devem aparecer no resultado.
    """

    auxiliary_activity = _build_input(
        identifier=1,
        code="AX0001",
        group="AX",
        quantity="10",
    )

    fixed_time = _build_input(
        identifier=2,
        code="TF0001",
        group="TF",
        quantity="10",
    )

    transport_ln = _build_input(
        identifier=3,
        code="LN0001",
        group="LN",
        quantity="10",
    )

    transport_rp = _build_input(
        identifier=4,
        code="RP0001",
        group="RP",
        quantity="10",
    )

    transport_pv = _build_input(
        identifier=5,
        code="PV0001",
        group="PV",
        quantity="10",
    )

    transport_fr = _build_input(
        identifier=6,
        code="FR0001",
        group="FR",
        quantity="10",
    )

    material = _build_input(
        identifier=7,
        code="M0001",
        group="MA",
        quantity="2",
    )

    composition = _build_composition()

    composition.activities.append(
        auxiliary_activity
    )

    composition.transports.extend(
        [
            fixed_time,
            transport_ln,
            transport_rp,
            transport_pv,
            transport_fr,
        ]
    )

    composition.materials.append(
        material
    )

    root_node = CompositionNode(
        composition=composition
    )

    composition_tree = _build_tree(
        root_node
    )

    result = InputAggregator().aggregate(
        composition_tree
    )

    codes = {
        item.code
        for item in result
    }

    assert codes == {
        "M0001",
    }


# ============================================================
# ZERO PRODUCTION
# ============================================================


@pytest.mark.parametrize(
    "group",
    ["EQ", "MO"],
)
def test_raises_error_when_production_is_zero(
    group: str,
) -> None:
    """
    Verifica que EQ e MO não podem ser agregados quando
    a produção da composição é zero.
    """

    composition_input = _build_input(
        code=(
            "E0001"
            if group == "EQ"
            else "P0001"
        ),
        group=group,
        quantity="10",
        use=(
            "1"
            if group == "EQ"
            else None
        ),
    )

    composition = _build_composition(
        production="0",
    )

    if group == "EQ":
        composition.equipments.append(
            composition_input
        )
    else:
        composition.workmen.append(
            composition_input
        )

    root_node = CompositionNode(
        composition=composition,
    )

    composition_tree = _build_tree(
        root_node
    )

    with pytest.raises(
        ValueError,
        match=r"^Composition production cannot be zero: ROOT$",
    ):
        InputAggregator().aggregate(
            composition_tree
        )