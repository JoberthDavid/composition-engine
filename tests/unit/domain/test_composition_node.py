from decimal import Decimal

from app.domain.composition import Composition
from app.domain.composition_node import CompositionNode


def create_composition(
    code: str = "0919013",
    description: str = "Composição de teste",
    *,
    identifier: int = 1,
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
        unit="un",
        fic=Decimal("0"),
        production=Decimal(production),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[],
        transports=[],
    )


def test_composition_node_builds_parent_child_hierarchy() -> None:
    """
    Verifica a construção da hierarquia pai → filho → neto.
    """

    root_node = CompositionNode(
        composition=create_composition(
            code="0919013",
            description=(
                "Montagem e desmontagem da usina "
                "de asfalto a quente"
            ),
            identifier=1,
        )
    )

    child_node = CompositionNode(
        composition=create_composition(
            code="0919079",
            description=(
                "Dique de contenção para usina "
                "de asfalto a quente"
            ),
            identifier=2,
        )
    )

    grandchild_node = CompositionNode(
        composition=create_composition(
            code="2009619",
            description="Alvenaria de blocos de concreto",
            identifier=3,
        )
    )

    child_node.add_child(grandchild_node)
    root_node.add_child(child_node)

    assert root_node.children == [child_node]
    assert child_node.children == [grandchild_node]

    assert child_node.parent is root_node
    assert grandchild_node.parent is child_node


def test_composition_node_identifies_children() -> None:
    """
    Verifica has_children() e get_children_count().
    """

    root_node = CompositionNode(
        composition=create_composition(
            code="0919013",
            description="Root composition",
        )
    )

    child_node = CompositionNode(
        composition=create_composition(
            code="0919079",
            description="Child composition",
            identifier=2,
        )
    )

    assert not root_node.has_children()
    assert root_node.get_children_count() == 0

    root_node.add_child(child_node)

    assert root_node.has_children()
    assert root_node.get_children_count() == 1

    assert not child_node.has_children()
    assert child_node.get_children_count() == 0


def test_composition_node_preserves_composition_data() -> None:
    """
    Verifica que o nó mantém a composição associada.
    """

    composition = create_composition(
        code="0919013",
        description="Root composition",
    )

    node = CompositionNode(
        composition=composition,
    )

    assert node.composition is composition
    assert node.composition.code == "0919013"
    assert node.composition.generic_description == "Root composition"