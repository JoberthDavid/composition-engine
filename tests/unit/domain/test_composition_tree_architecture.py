from decimal import Decimal

import pytest

from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree


def _build_composition(
    *,
    identifier: int = 1,
    code: str = "ROOT",
    production: str = "1",
    equipments: list[CompositionInput] | None = None,
    workmen: list[CompositionInput] | None = None,
    materials: list[CompositionInput] | None = None,
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
        equipments=equipments or [],
        workmen=workmen or [],
        materials=materials or [],
        activities=[],
        transports=[],
    )


def _build_reference_input(
    *,
    identifier: int,
    code: str,
    group: str,
    quantity: str = "1",
) -> CompositionInput:
    """
    Cria um insumo de referência ou monetário para os testes.
    """
    return CompositionInput(
        id=identifier,
        input_group=group,
        generic_item=code,
        generic_description=f"Item {code}",
        unit="un",
        input_quantity=Decimal(quantity),
    )


def _build_node(
    *,
    identifier: int = 1,
    code: str = "ROOT",
    production: str = "1",
    equipments: list[CompositionInput] | None = None,
    workmen: list[CompositionInput] | None = None,
    materials: list[CompositionInput] | None = None,
) -> CompositionNode:
    """
    Cria uma ocorrência mínima de composição.
    """
    return CompositionNode(
        composition=_build_composition(
            identifier=identifier,
            code=code,
            production=production,
            equipments=equipments,
            workmen=workmen,
            materials=materials,
        )
    )


# ============================================================================
# TRAVESSIA EM PRÉ-ORDEM
# ============================================================================


def test_tree_walk_returns_nodes_in_pre_order() -> None:
    """
    Verifica que walk() percorre a árvore em pré-ordem.

    A ordem deve ser:
        pai → filho → neto → próximo filho.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
    )

    child_a = _build_node(
        identifier=2,
        code="A",
    )

    child_b = _build_node(
        identifier=3,
        code="B",
    )

    grandchild_a = _build_node(
        identifier=4,
        code="A1",
    )

    root.add_child(child_a)
    root.add_child(child_b)
    child_a.add_child(grandchild_a)

    tree = CompositionTree(root)

    result = tree.walk()

    assert result == [
        root,
        child_a,
        grandchild_a,
        child_b,
    ]


def test_tree_walk_preserves_sibling_order() -> None:
    """
    Verifica que walk() preserva a ordem de inserção dos irmãos.
    """
    root = _build_node(code="ROOT")

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

    tree = CompositionTree(root)

    assert tree.walk() == [
        root,
        first,
        second,
        third,
    ]


# ============================================================================
# TRAVESSIA EM PÓS-ORDEM
# ============================================================================


def test_tree_walk_post_order_returns_nodes_in_post_order() -> None:
    """
    Verifica que walk_post_order() percorre a árvore em pós-ordem.

    A ordem deve ser:
        filhos → pai.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
    )

    child_a = _build_node(
        identifier=2,
        code="A",
    )

    child_b = _build_node(
        identifier=3,
        code="B",
    )

    grandchild_a = _build_node(
        identifier=4,
        code="A1",
    )

    root.add_child(child_a)
    root.add_child(child_b)
    child_a.add_child(grandchild_a)

    tree = CompositionTree(root)

    result = tree.walk_post_order()

    assert result == [
        grandchild_a,
        child_a,
        child_b,
        root,
    ]


def test_tree_walk_post_order_preserves_sibling_order() -> None:
    """
    Verifica que a pós-ordem preserva a ordem dos irmãos.
    """
    root = _build_node(code="ROOT")

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

    tree = CompositionTree(root)

    assert tree.walk_post_order() == [
        first,
        second,
        third,
        root,
    ]


# ============================================================================
# CONSULTAS ESTRUTURAIS
# ============================================================================


def test_tree_get_leaves_returns_only_leaf_occurrences() -> None:
    """
    Verifica que get_leaves() retorna somente ocorrências sem filhos.
    """
    root = _build_node(code="ROOT")

    child_a = _build_node(
        identifier=2,
        code="A",
    )

    child_b = _build_node(
        identifier=3,
        code="B",
    )

    grandchild = _build_node(
        identifier=4,
        code="A1",
    )

    root.add_child(child_a)
    root.add_child(child_b)
    child_a.add_child(grandchild)

    tree = CompositionTree(root)

    assert tree.get_leaves() == [
        grandchild,
        child_b,
    ]


def test_tree_get_leaves_returns_root_when_tree_has_only_root() -> None:
    """
    Verifica que a raiz é considerada folha quando não possui filhos.
    """
    root = _build_node(code="ROOT")

    tree = CompositionTree(root)

    assert tree.get_leaves() == [root]


def test_tree_find_by_code_returns_all_occurrences() -> None:
    """
    Verifica que find_by_code() retorna todas as ocorrências do código.

    Ocorrências diferentes podem representar a mesma composição.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
    )

    first = _build_node(
        identifier=2,
        code="DUPLICATE",
    )

    second = _build_node(
        identifier=3,
        code="DUPLICATE",
    )

    third = _build_node(
        identifier=4,
        code="OTHER",
    )

    root.add_child(first)
    root.add_child(second)
    root.add_child(third)

    tree = CompositionTree(root)

    assert tree.find_by_code("DUPLICATE") == [
        first,
        second,
    ]


def test_tree_find_by_code_returns_empty_list_when_code_does_not_exist() -> None:
    """
    Verifica que uma busca sem correspondência retorna lista vazia.
    """
    root = _build_node(code="ROOT")

    tree = CompositionTree(root)

    assert tree.find_by_code("NOT_FOUND") == []


# ============================================================================
# ITERAÇÃO E TAMANHO
# ============================================================================


def test_tree_iteration_uses_pre_order() -> None:
    """
    Verifica que iterar diretamente sobre a árvore utiliza a
    travessia em pré-ordem.
    """
    root = _build_node(code="ROOT")

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

    tree = CompositionTree(root)

    assert list(tree) == [
        root,
        child,
        grandchild,
    ]


def test_tree_length_returns_number_of_occurrences() -> None:
    """
    Verifica que len(tree) representa a quantidade de ocorrências.
    """
    root = _build_node(code="ROOT")

    child_a = _build_node(
        identifier=2,
        code="A",
    )

    child_b = _build_node(
        identifier=3,
        code="B",
    )

    root.add_child(child_a)
    root.add_child(child_b)

    tree = CompositionTree(root)

    assert len(tree) == 3


# ============================================================================
# ÁRVORE DE OCORRÊNCIAS
# ============================================================================


def test_tree_preserves_distinct_occurrences_with_same_code() -> None:
    """
    Verifica que ocorrências distintas da mesma composição permanecem
    distintas dentro da árvore.
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
    )

    occurrence_a = _build_node(
        identifier=2,
        code="SAME",
    )

    occurrence_b = _build_node(
        identifier=2,
        code="SAME",
    )

    root.add_child(occurrence_a)
    root.add_child(occurrence_b)

    tree = CompositionTree(root)

    result = tree.find_by_code("SAME")

    assert result == [
        occurrence_a,
        occurrence_b,
    ]

    assert result[0] is not result[1]


def test_tree_does_not_deduplicate_occurrences_during_walk() -> None:
    """
    Verifica que walk() preserva todas as ocorrências da árvore,
    mesmo quando elas representam a mesma composição.
    """
    root = _build_node(code="ROOT")

    first = _build_node(
        identifier=2,
        code="SAME",
    )

    second = _build_node(
        identifier=2,
        code="SAME",
    )

    root.add_child(first)
    root.add_child(second)

    tree = CompositionTree(root)

    result = tree.walk()

    assert result == [
        root,
        first,
        second,
    ]

    assert len(result) == 3
    assert result[1] is not result[2]


# ============================================================================
# DETECÇÃO DEFENSIVA DE CICLO
# ============================================================================


def test_tree_walk_post_order_detects_cycle() -> None:
    """
    Verifica que a travessia em pós-ordem detecta um ciclo estrutural.
    """
    root = _build_node(code="ROOT")
    child = _build_node(
        identifier=2,
        code="CHILD",
    )

    root.add_child(child)

    # Cria manualmente um ciclo para testar a defesa da árvore.
    child.children.append(root)

    tree = CompositionTree(root)

    with pytest.raises(
        ValueError,
        match="Cycle detected in composition tree",
    ):
        tree.walk_post_order()


# ============================================================================
# FRONTEIRA ARQUITETURAL — COMPOSITION NODE
# ============================================================================


def test_tree_is_responsible_for_traversal_not_node() -> None:
    """
    Verifica a separação de responsabilidades entre Tree e Node.
    """
    root = _build_node(code="ROOT")
    tree = CompositionTree(root)

    assert hasattr(tree, "walk")
    assert hasattr(tree, "walk_post_order")

    assert not hasattr(root, "walk")
    assert not hasattr(root, "walk_post_order")


# ============================================================================
# FRONTEIRA ARQUITETURAL — AGREGAÇÃO
# ============================================================================


def test_tree_does_not_implement_aggregation() -> None:
    """
    Verifica que CompositionTree não implementa agregação.

    A agregação de composições pertence ao CompositionAggregator e a
    agregação de insumos pertence ao InputAggregator.
    """
    root = _build_node(code="ROOT")
    tree = CompositionTree(root)

    assert not hasattr(tree, "aggregate")
    assert not hasattr(tree, "aggregate_compositions")
    assert not hasattr(tree, "aggregate_inputs")
    assert not hasattr(tree, "aggregated_inputs")


# ============================================================================
# CONSULTA DE CÓDIGOS MONETÁRIOS
# ============================================================================


def test_tree_collects_monetary_item_codes_by_group() -> None:
    """
    Verifica que a consulta estrutural de códigos monetários mantém
    a separação por grupo.
    """
    equipment = _build_reference_input(
        identifier=10,
        code="EQ001",
        group="EQ",
    )

    workman = _build_reference_input(
        identifier=20,
        code="MO001",
        group="MO",
    )

    material = _build_reference_input(
        identifier=30,
        code="MA001",
        group="MA",
    )

    root = _build_node(
        code="ROOT",
        equipments=[equipment],
        workmen=[workman],
        materials=[material],
    )

    tree = CompositionTree(root)

    assert tree.monetary_item_codes_by_group == {
        "EQ": {"EQ001"},
        "MO": {"MO001"},
        "MA": {"MA001"},
    }


def test_tree_collects_monetary_item_codes_from_all_occurrences() -> None:
    """
    Verifica que os códigos monetários são pesquisados em todas
    as ocorrências da árvore.
    """
    root = _build_node(code="ROOT")

    equipment_root = _build_reference_input(
        identifier=10,
        code="EQ001",
        group="EQ",
    )

    equipment_child = _build_reference_input(
        identifier=20,
        code="EQ002",
        group="EQ",
    )

    root.composition.equipments.append(equipment_root)

    child = _build_node(
        identifier=2,
        code="CHILD",
        equipments=[equipment_child],
    )

    root.add_child(child)

    tree = CompositionTree(root)

    assert tree.monetary_item_codes_by_group["EQ"] == {
        "EQ001",
        "EQ002",
    }


def test_tree_monetary_item_codes_are_unique() -> None:
    """
    Verifica que a consulta de códigos monetários retorna valores únicos.
    """
    equipment_a = _build_reference_input(
        identifier=10,
        code="EQ001",
        group="EQ",
    )

    equipment_b = _build_reference_input(
        identifier=11,
        code="EQ001",
        group="EQ",
    )

    root = _build_node(
        code="ROOT",
        equipments=[
            equipment_a,
            equipment_b,
        ],
    )

    tree = CompositionTree(root)

    assert tree.monetary_item_codes == {"EQ001"}


# ============================================================================
# DEPENDÊNCIA DE INFRAESTRUTURA
# ============================================================================


def test_composition_tree_module_does_not_import_infrastructure() -> None:
    """
    Verifica que CompositionTree não possui dependências de
    infraestrutura, repositories ou services.
    """
    import ast
    from pathlib import Path

    module_path = (
        Path(__file__).resolve().parents[3]
        / "app/domain/composition_tree.py"
    )

    source = module_path.read_text(
        encoding="utf-8",
    )

    syntax_tree = ast.parse(source)

    forbidden_prefixes = (
        "app.infrastructure",
        "app.repositories",
        "app.services",
    )

    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(
                    forbidden_prefixes
                )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            assert not module.startswith(
                forbidden_prefixes
            )

