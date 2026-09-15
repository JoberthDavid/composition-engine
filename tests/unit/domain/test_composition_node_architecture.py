from decimal import Decimal
from pathlib import Path

import pytest
from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode


def _build_composition(
    *,
    identifier: int = 1,
    code: str = "0919013",
    production: str = "1",
) -> Composition:
    """
    Cria uma composição mínima para os testes arquiteturais.
    """
    return Composition(
        id=identifier,
        composition_group=code[:2],
        generic_item=code,
        generic_description=f"Composição {code}",
        unit="un",
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
    Cria uma referência de composição mínima.
    """
    return CompositionInput(
        id=identifier,
        input_group=group,
        generic_item=code,
        generic_description=f"Referência {code}",
        unit="un",
        input_quantity=Decimal(quantity),
    )


def _build_node(
    *,
    identifier: int = 1,
    code: str = "0919013",
    production: str = "1",
    reference_input: CompositionInput | None = None,
) -> CompositionNode:
    """
    Cria uma ocorrência mínima de composição.
    """
    return CompositionNode(
        composition=_build_composition(
            identifier=identifier,
            code=code,
            production=production,
        ),
        reference_input=reference_input,
    )


# ============================================================================
# INTEGRIDADE DA ÁRVORE DE OCORRÊNCIAS
# ============================================================================


def test_node_rejects_itself_as_child() -> None:
    """
    Verifica que uma ocorrência não pode ser filha de si mesma.
    """
    node = _build_node()

    with pytest.raises(
        ValueError,
        match="O nó não pode ser seu próprio filho",
    ):
        node.add_child(node)


def test_node_rejects_child_with_another_parent() -> None:
    """
    Verifica que uma ocorrência não pode possuir dois pais.
    """
    parent_a = _build_node(
        identifier=1,
        code="PARENT_A",
    )

    parent_b = _build_node(
        identifier=2,
        code="PARENT_B",
    )

    child = _build_node(
        identifier=3,
        code="CHILD",
    )

    parent_a.add_child(child)

    with pytest.raises(
        ValueError,
        match="O nó não pode ter mais de um nó pai.",
    ):
        parent_b.add_child(child)


def test_node_rejects_duplicate_child() -> None:
    """
    Verifica que uma mesma ocorrência não pode aparecer duas vezes
    entre os filhos do mesmo pai.
    """
    parent = _build_node(
        identifier=1,
        code="PARENT",
    )

    child = _build_node(
        identifier=2,
        code="CHILD",
    )

    parent.add_child(child)

    with pytest.raises(
        ValueError,
        match="O nó já é filho deste nó pai.",
    ):
        parent.add_child(child)


def test_node_rejects_cycle_through_descendant() -> None:
    """
    Verifica que a estrutura de ocorrências não permite ciclos.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
    )

    child = _build_node(
        identifier=2,
        code="CHILD",
    )

    grandchild = _build_node(
        identifier=3,
        code="GRANDCHILD",
    )

    root.add_child(child)
    child.add_child(grandchild)

    with pytest.raises(
        ValueError,
        match="O nó não pode ser adicionado abaixo de seu descendente",
    ):
        grandchild.add_child(root)


def test_node_preserves_child_insertion_order() -> None:
    """
    Verifica que o nó preserva a ordem em que as ocorrências filhas
    foram adicionadas.

    A ordem é importante porque a travessia da árvore deve ser
    determinada pelo CompositionTree sem que CompositionNode
    reorganize suas ocorrências.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
    )

    first = _build_node(
        identifier=2,
        code="FIRST",
    )

    second = _build_node(
        identifier=3,
        code="SECOND",
    )

    third = _build_node(
        identifier=4,
        code="THIRD",
    )

    root.add_child(first)
    root.add_child(second)
    root.add_child(third)

    assert root.children == [first, second, third]


# ============================================================================
# CÁLCULOS PRÓPRIOS DA OCORRÊNCIA
# ============================================================================


def test_node_calculates_effective_quantity_from_parent() -> None:
    """
    Verifica a propagação da quantidade efetiva através da hierarquia.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
        production="2",
    )

    child_reference = _build_reference_input(
        identifier=10,
        code="CHILD",
        quantity="4",
    )

    child = _build_node(
        identifier=2,
        code="CHILD",
        production="4",
        reference_input=child_reference,
    )

    root.add_child(child)

    assert root.effective_quantity == Decimal("1")
    assert child.effective_quantity == Decimal("1")


def test_node_calculates_accumulated_quantity_without_production() -> None:
    """
    Verifica que accumulated_quantity acumula somente as quantidades
    das referências e não incorpora a produção das composições.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
        production="10",
    )

    child_reference = _build_reference_input(
        identifier=10,
        code="CHILD",
        quantity="4",
    )

    child = _build_node(
        identifier=2,
        code="CHILD",
        production="20",
        reference_input=child_reference,
    )

    grandchild_reference = _build_reference_input(
        identifier=20,
        code="GRANDCHILD",
        quantity="3",
    )

    grandchild = _build_node(
        identifier=3,
        code="GRANDCHILD",
        production="30",
        reference_input=grandchild_reference,
    )

    root.add_child(child)
    child.add_child(grandchild)

    assert root.accumulated_quantity == Decimal("1")
    assert child.accumulated_quantity == Decimal("4")
    assert grandchild.accumulated_quantity == Decimal("12")


# ============================================================================
# LIMITE DE RESPONSABILIDADE — TRAVESSIA
# ============================================================================


def test_node_does_not_implement_tree_traversal() -> None:
    """
    Verifica que CompositionNode não implementa travessia da árvore.

    A travessia é responsabilidade exclusiva de CompositionTree.
    """
    node = _build_node()

    assert not hasattr(node, "walk")
    assert not hasattr(node, "walk_post_order")


def test_node_does_not_expose_tree_search_operations() -> None:
    """
    Verifica que CompositionNode não implementa consultas estruturais
    que pertencem ao CompositionTree.
    """
    node = _build_node()

    assert not hasattr(node, "find_by_code")
    assert not hasattr(node, "get_leaves")


# ============================================================================
# LIMITE DE RESPONSABILIDADE — AGREGAÇÃO
# ============================================================================


def test_node_does_not_implement_composition_aggregation() -> None:
    """
    Verifica que CompositionNode não implementa agregação de
    ocorrências de composição.

    A agregação é responsabilidade do CompositionAggregator.
    """
    node = _build_node()

    assert not hasattr(node, "aggregate")
    assert not hasattr(node, "aggregate_compositions")


def test_node_does_not_implement_input_aggregation() -> None:
    """
    Verifica que CompositionNode não implementa agregação de insumos.

    A agregação de insumos é responsabilidade do InputAggregator.
    """
    node = _build_node()

    assert not hasattr(node, "aggregate_inputs")
    assert not hasattr(node, "aggregated_inputs")


# ============================================================================
# LIMITE DE RESPONSABILIDADE — INFRAESTRUTURA
# ============================================================================


def test_composition_node_module_does_not_import_infrastructure() -> None:
    """
    Verifica arquiteturalmente que o módulo de domínio do
    CompositionNode não importa infraestrutura, repositórios ou serviços.
    """
    import ast

    module_path = Path(__file__).resolve().parents[3] / (
        "app/domain/composition_node.py"
    )

    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_prefixes = (
        "app.infrastructure",
        "app.repositories",
        "app.services",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names = [
                alias.name
                for alias in node.names
            ]

            assert not any(
                name.startswith(forbidden_prefixes)
                for name in imported_names
            )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            assert not module.startswith(forbidden_prefixes)