from decimal import Decimal

from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode


def _build_composition(
    *,
    identifier: int = 1,
    code: str = "0919013",
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
    group: str = "AX",
    quantity: str = "1",
) -> CompositionInput:
    """
    Cria um insumo utilizado como referência de composição.
    """

    return CompositionInput(
        id=identifier,
        input_group=group,
        generic_item=code,
        generic_description=f"Referência {code}",
        unit="un",
        input_quantity=Decimal(quantity),
    )


def test_composition_node_identifies_root() -> None:
    """
    Verifica que um nó criado sem pai é identificado como raiz.
    """

    node = CompositionNode(
        composition=_build_composition(
            code="ROOT",
        ),
    )

    assert node.is_root()
    assert node.parent is None


def test_composition_node_identifies_reference_information() -> None:
    """
    Verifica que um nó filho expõe corretamente as informações
    da referência que originou sua criação.
    """

    reference_input = _build_reference_input(
        identifier=10,
        code="0919079",
        group="AX",
        quantity="2.5",
    )

    child_node = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="0919079",
        ),
        reference_input=reference_input,
    )

    assert child_node.reference_quantity == Decimal("2.5")
    assert child_node.reference_code == "0919079"
    assert child_node.reference_group == "AX"

    assert child_node.is_auxiliary_activity()
    assert not child_node.is_fixed_time()
    assert child_node.is_composition_reference()


def test_composition_node_identifies_fixed_time_reference() -> None:
    """
    Verifica que uma referência TF é identificada corretamente.
    """

    reference_input = _build_reference_input(
        identifier=20,
        code="0919013",
        group="TF",
        quantity="3",
    )

    child_node = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="0919013",
        ),
        reference_input=reference_input,
    )

    assert child_node.reference_quantity == Decimal("3")
    assert child_node.reference_code == "0919013"
    assert child_node.reference_group == "TF"

    assert not child_node.is_auxiliary_activity()
    assert child_node.is_fixed_time()
    assert child_node.is_composition_reference()


def test_composition_node_add_child_sets_parent() -> None:
    """
    Verifica que add_child() associa automaticamente o pai ao filho.
    """

    root_node = CompositionNode(
        composition=_build_composition(
            identifier=1,
            code="ROOT",
        ),
    )

    child_node = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="CHILD",
        ),
    )

    root_node.add_child(child_node)

    assert child_node.parent is root_node
    assert root_node.children == [child_node]
    assert root_node.has_children()
    assert root_node.get_children_count() == 1