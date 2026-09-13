from decimal import Decimal

from app.domain.aggregated_composition import AggregatedComposition
from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree
from app.services.composition_aggregator import CompositionAggregator


# ============================================================
# HELPERS
# ============================================================


def _build_composition(
    *,
    identifier: int = 1,
    code: str = "ROOT",
    description: str = "Composição de teste",
    unit: str = "un",
    production: str = "1",
) -> Composition:
    """
    Cria uma composição simples para os testes.
    """

    return Composition(
        id=identifier,
        composition_group=code[:2],
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
    *,
    identifier: int,
    code: str,
    quantity: str,
    group: str = "AX",
) -> CompositionInput:
    """
    Cria um CompositionInput que representa uma referência
    para outra composição.
    """

    return CompositionInput(
        id=identifier,
        input_group=group,
        generic_item=code,
        generic_description=f"Referência {code}",
        unit="un",
        input_quantity=Decimal(quantity),
    )


def _build_tree(
    root_node: CompositionNode,
) -> CompositionTree:
    """
    Cria uma CompositionTree a partir do nó raiz.

    A árvore deve ser criada somente depois que todos
    os filhos necessários tiverem sido adicionados.
    """

    return CompositionTree(
        root=root_node,
    )


# ============================================================
# TESTES
# ============================================================


def test_aggregates_repeated_compositions() -> None:
    """
    Verifica que ocorrências da mesma composição são agrupadas
    em um único resultado.

    Estrutura:

        ROOT
        ├── CHILD × 2.5
        └── CHILD × 1.75

    Como a produção de CHILD é 1:

        CHILD = 2.5 + 1.75 = 4.25
    """

    root_node = CompositionNode(
        composition=_build_composition(
            identifier=1,
            code="ROOT",
            description="Root composition",
        )
    )

    first_child = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="CHILD",
            description="Child composition",
        ),
        reference_input=_build_reference_input(
            identifier=1,
            code="CHILD",
            quantity="2.5",
        ),
    )

    second_child = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="CHILD",
            description="Child composition",
        ),
        reference_input=_build_reference_input(
            identifier=2,
            code="CHILD",
            quantity="1.75",
        ),
    )

    root_node.add_child(
        first_child
    )

    root_node.add_child(
        second_child
    )

    composition_tree = _build_tree(
        root_node
    )

    aggregator = CompositionAggregator()

    compositions = aggregator.aggregate(
        composition_tree
    )

    child_compositions = [
        composition
        for composition in compositions
        if composition.code == "CHILD"
    ]

    assert len(child_compositions) == 1

    assert (
        child_compositions[0].quantity
        == Decimal("4.25")
    )


def test_aggregator_preserves_unique_compositions() -> None:
    """
    Verifica que composições com códigos diferentes permanecem
    como resultados distintos.

    Estrutura:

        ROOT
        ├── CHILD_A × 2
        └── CHILD_B × 3
    """

    root_node = CompositionNode(
        composition=_build_composition(
            identifier=1,
            code="ROOT",
            description="Root composition",
        )
    )

    child_a = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="CHILD_A",
            description="Child A",
        ),
        reference_input=_build_reference_input(
            identifier=1,
            code="CHILD_A",
            quantity="2",
        ),
    )

    child_b = CompositionNode(
        composition=_build_composition(
            identifier=3,
            code="CHILD_B",
            description="Child B",
        ),
        reference_input=_build_reference_input(
            identifier=2,
            code="CHILD_B",
            quantity="3",
        ),
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

    aggregator = CompositionAggregator()

    compositions = aggregator.aggregate(
        composition_tree
    )

    codes = [
        composition.code
        for composition in compositions
    ]

    assert codes == [
        "ROOT",
        "CHILD_A",
        "CHILD_B",
    ]


def test_aggregator_preserves_composition_attributes() -> None:
    """
    Verifica que os atributos da composição agregada correspondem
    à composição original.
    """

    root_node = CompositionNode(
        composition=_build_composition(
            identifier=10,
            code="ROOT",
            description="Root composition",
            unit="m³",
        )
    )

    composition_tree = _build_tree(
        root_node
    )

    aggregator = CompositionAggregator()

    compositions = aggregator.aggregate(
        composition_tree
    )

    assert len(compositions) == 1

    aggregated = compositions[0]

    assert isinstance(
        aggregated,
        AggregatedComposition,
    )

    assert aggregated.identifier == 10
    assert aggregated.group == "RO"
    assert aggregated.code == "ROOT"
    assert aggregated.description == "Root composition"
    assert aggregated.unit == "m³"
    assert aggregated.quantity == Decimal("1")