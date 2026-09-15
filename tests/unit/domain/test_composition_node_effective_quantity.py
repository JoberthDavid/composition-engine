from decimal import Decimal

import pytest

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


def test_composition_node_effective_quantity_propagates_through_tree() -> None:
    """
    Verifica a propagação da quantidade efetiva ao longo da árvore.

    Estrutura:

        ROOT
        └── CHILD × 10
            └── GRANDCHILD × 0.5

    Considerando produção igual a 1:

        ROOT = 1
        CHILD = 1 × 10 / 1 = 10
        GRANDCHILD = 10 × 0.5 / 1 = 5
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
        reference_input=_build_reference_input(
            identifier=1,
            code="CHILD",
            quantity="10",
        ),
    )

    grandchild_node = CompositionNode(
        composition=_build_composition(
            identifier=3,
            code="GRANDCHILD",
        ),
        reference_input=_build_reference_input(
            identifier=2,
            code="GRANDCHILD",
            quantity="0.5",
        ),
    )

    root_node.add_child(child_node)
    child_node.add_child(grandchild_node)

    assert root_node.effective_quantity == Decimal("1")
    assert child_node.effective_quantity == Decimal("10")
    assert grandchild_node.effective_quantity == Decimal("5")


def test_root_composition_has_unit_effective_quantity() -> None:
    """
    Verifica que a composição raiz possui quantidade efetiva unitária.
    """

    root_node = CompositionNode(
        composition=_build_composition(
            identifier=1,
            code="ROOT",
        ),
    )

    assert root_node.effective_quantity == Decimal("1")


def test_effective_quantity_considers_composition_production() -> None:
    """
    Verifica que a produção da composição filha participa
    do cálculo da quantidade efetiva.

    Exemplo:

        referência = 10
        produção = 2

        effective_quantity = 1 × 10 / 2 = 5
    """

    root_node = CompositionNode(
        composition=_build_composition(
            identifier=1,
            code="ROOT",
            production="1",
        ),
    )

    child_node = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="CHILD",
            production="2",
        ),
        reference_input=_build_reference_input(
            identifier=1,
            code="CHILD",
            quantity="10",
        ),
    )

    root_node.add_child(child_node)

    assert child_node.effective_quantity == Decimal("5")


def test_effective_quantity_supports_decimal_precision() -> None:
    """
    Verifica que o cálculo preserva a precisão de Decimal.
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
        reference_input=_build_reference_input(
            identifier=1,
            code="CHILD",
            quantity="0.3333",
        ),
    )

    grandchild_node = CompositionNode(
        composition=_build_composition(
            identifier=3,
            code="GRANDCHILD",
        ),
        reference_input=_build_reference_input(
            identifier=2,
            code="GRANDCHILD",
            quantity="0.3333",
        ),
    )

    root_node.add_child(child_node)
    child_node.add_child(grandchild_node)

    expected_quantity = (
        Decimal("0.3333")
        * Decimal("0.3333")
    )

    assert grandchild_node.effective_quantity == expected_quantity