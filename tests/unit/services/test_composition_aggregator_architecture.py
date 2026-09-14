from decimal import Decimal

from app.domain.aggregated_composition import AggregatedComposition
from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree
from app.services.composition_aggregator import CompositionAggregator


def _build_composition(
    identifier: int = 1,
    code: str = "ROOT",
    production: str = "1",
    ) -> Composition:
    """
    Cria uma composição mínima para os testes arquiteturais.
    """
    return Composition(
        id=identifier,
        composition_group="C",
        generic_item=code,
        generic_description=f"Item {code}",
        unit="un",
        fic=Decimal("0"),
        production=Decimal(production),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[],
        transports=[],
    )

def _build_node(
    identifier: int = 1,
    code: str = "ROOT",
    production: str = "1",
    ) -> CompositionNode:
    """
    Cria um nó mínimo para os testes arquiteturais.
    """
    return CompositionNode(
        composition=_build_composition(
        identifier=identifier,
        code=code,
        production=production,
        )
    )

def test_composition_aggregator_aggregates_compositions_by_code() -> None:
    """
    Verifica que composições com o mesmo código são agregadas.
    """
    root = _build_node(
    identifier=1,
    code="ROOT",
    )

    child_1 = _build_node(
        identifier=2,
        code="COMP",
    )

    child_2 = _build_node(
        identifier=3,
        code="COMP",
    )

    root.add_child(child_1)
    root.add_child(child_2)

    tree = CompositionTree(root)
    aggregator = CompositionAggregator()

    result = aggregator.aggregate(tree)

    aggregated = [
        item
        for item in result
        if item.code == "COMP"
    ]

    assert len(aggregated) == 1
    assert aggregated[0].quantity == Decimal("2")


def test_composition_aggregator_preserves_distinct_occurrences() -> None:
    """
    Verifica que ocorrências distintas da mesma composição são
    agregadas pelo código, sem eliminar ocorrências da árvore.
    """
    root = _build_node(
    identifier=1,
    code="ROOT",
    )

    child_1 = _build_node(
        identifier=2,
        code="COMP",
    )

    child_2 = _build_node(
        identifier=3,
        code="COMP",
    )

    root.add_child(child_1)
    root.add_child(child_2)

    tree = CompositionTree(root)
    aggregator = CompositionAggregator()

    result = aggregator.aggregate(tree)

    assert len(tree.find_by_code("COMP")) == 2

    aggregated = next(
        item
        for item in result
        if item.code == "COMP"
    )

    assert aggregated.quantity == Decimal("2")


def test_composition_aggregator_uses_effective_quantity() -> None:
    """
    Verifica que a agregação utiliza a quantidade efetiva da ocorrência.
    """
    root = _build_node(
    identifier=1,
    code="ROOT",
    production="1",
    )

    reference = CompositionInput(
        id=10,
        input_group="TF",
        generic_item="COMP",
        generic_description="Item COMP",
        unit="un",
        input_quantity=Decimal("4"),
    )

    root.composition.activities.append(reference)

    child = CompositionNode(
        composition=_build_composition(
            identifier=2,
            code="COMP",
            production="2",
        ),
        reference_input=reference,
    )

    root.add_child(child)

    tree = CompositionTree(root)

    aggregator = CompositionAggregator()

    result = aggregator.aggregate(tree)

    aggregated = next(
        item
        for item in result
        if item.code == "COMP"
    )

    assert child.effective_quantity == Decimal("2")
    assert aggregated.quantity == Decimal("2")


def test_composition_aggregator_preserves_composition_metadata() -> None:
    """
    Verifica que os metadados da primeira ocorrência da composição
    são preservados no resultado agregado.
    """
    root = _build_node(
    identifier=1,
    code="ROOT",
    )

    child = _build_node(
        identifier=25,
        code="COMP",
    )

    root.add_child(child)

    tree = CompositionTree(root)
    aggregator = CompositionAggregator()

    result = aggregator.aggregate(tree)

    aggregated = next(
        item
        for item in result
        if item.code == "COMP"
    )

    assert aggregated.identifier == child.composition.id
    assert aggregated.group == child.composition.composition_group
    assert aggregated.code == child.composition.generic_item
    assert aggregated.description == child.composition.generic_description
    assert aggregated.unit == child.composition.unit


def test_composition_aggregator_preserves_first_occurrence_order() -> None:
    """
    Verifica que a ordem dos resultados segue a ordem da primeira
    ocorrência de cada composição na árvore.
    """
    root = _build_node(
    identifier=1,
    code="ROOT",
    )

    child_1 = _build_node(
        identifier=2,
        code="COMP_A",
    )

    child_2 = _build_node(
        identifier=3,
        code="COMP_B",
    )

    child_3 = _build_node(
        identifier=4,
        code="COMP_A",
    )

    root.add_child(child_1)
    root.add_child(child_2)
    root.add_child(child_3)

    tree = CompositionTree(root)
    aggregator = CompositionAggregator()

    result = aggregator.aggregate(tree)

    assert [
        item.code
        for item in result
    ] == [
        "ROOT",
        "COMP_A",
        "COMP_B",
    ]


def test_composition_aggregator_does_not_aggregate_inputs() -> None:
    """
    Verifica que a responsabilidade de agregar insumos não pertence
    ao CompositionAggregator.
    """
    root = _build_node(
    identifier=1,
    code="ROOT",
    )

    material = CompositionInput(
        id=10,
        input_group="MA",
        generic_item="MAT",
        generic_description="Material",
        unit="un",
        input_quantity=Decimal("2"),
    )

    root.composition.materials.append(material)

    tree = CompositionTree(root)
    aggregator = CompositionAggregator()

    result = aggregator.aggregate(tree)

    assert all(
        not hasattr(item, "input_quantity")
        for item in result
    )


def test_composition_aggregator_does_not_implement_tree_traversal() -> None:
    """
    Verifica que o CompositionAggregator delega a travessia estrutural
    para CompositionTree.
    """
    source = CompositionAggregator.aggregate.__code__.co_names

    assert "walk" in source

def test_composition_aggregator_does_not_resolve_compositions() -> None:
    """
    Verifica que o CompositionAggregator não possui responsabilidade
    de resolver composições.
    """
    source = CompositionAggregator.aggregate.__code__.co_names

    forbidden_names = {
        "resolve",
        "resolver",
        "repository",
        "repositories",
        "CompositionResolver",
    }

    assert not (
        forbidden_names.intersection(source)
    )


def test_composition_aggregator_module_does_not_import_infrastructure() -> None:
    """
    Verifica que o módulo do CompositionAggregator não depende
    diretamente de infraestrutura ou repositórios.
    """
    import ast
    from pathlib import Path

    file_path = Path(
        "app/services/composition_aggregator.py"
    )

    tree = ast.parse(
        file_path.read_text(encoding="utf-8")
    )

    forbidden_prefixes = (
        "app.infrastructure",
        "app.repositories",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names = [
                alias.name
                for alias in node.names
            ]

            assert not any(
                imported_name.startswith(prefix)
                for imported_name in imported_names
                for prefix in forbidden_prefixes
            )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            assert not any(
                module.startswith(prefix)
                for prefix in forbidden_prefixes
            )


def test_composition_aggregator_does_not_leak_state_between_calls() -> None:
    """
    Verifica que duas chamadas independentes não compartilham
    estado de agregação.
    """
    aggregator = CompositionAggregator()

    root_1 = _build_node(
        identifier=1,
        code="ROOT_A",
    )

    tree_1 = CompositionTree(root_1)

    result_1 = aggregator.aggregate(tree_1)

    root_2 = _build_node(
        identifier=2,
        code="ROOT_B",
    )

    tree_2 = CompositionTree(root_2)

    result_2 = aggregator.aggregate(tree_2)

    assert [
        item.code
        for item in result_1
    ] == ["ROOT_A"]

    assert [
        item.code
        for item in result_2
    ] == ["ROOT_B"]


def test_composition_aggregator_returns_aggregated_compositions() -> None:
    """
    Verifica que a saída do CompositionAggregator é composta por
    resultados do tipo AggregatedComposition.
    """
    root = _build_node(
    identifier=1,
    code="ROOT",
    )

    child = _build_node(
        identifier=2,
        code="COMP",
    )

    root.add_child(child)

    tree = CompositionTree(root)
    aggregator = CompositionAggregator()

    result = aggregator.aggregate(tree)

    assert all(
        isinstance(item, AggregatedComposition)
        for item in result
    )