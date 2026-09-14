from decimal import Decimal

from app.domain.aggregated_input import AggregatedInput
from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree
from app.services.input_aggregator import InputAggregator

def _build_input(
    identifier: int = 1,
    code: str = "INPUT",
    group: str = "MA",
    quantity: str = "1",
    use: str | None = None,
    description: str = "Input",
    unit: str = "un",
    ) -> CompositionInput:
    """
    Cria um CompositionInput mínimo para os testes arquiteturais.
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
    )

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
        composition_group="CC",
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

def _get_result_by_code(
    results: list[AggregatedInput],
    code: str,
    ) -> AggregatedInput:
    """
    Retorna o resultado agregado correspondente ao código.
    """
    return next(
        item
        for item in results
        if item.code == code
    )

def test_input_aggregator_aggregates_only_monetary_input_groups() -> None:
    """
    Verifica que o InputAggregator agrega somente EQ, MO e MA.
    """
    root = _build_node()

    equipment = _build_input(
        identifier=1,
        code="E0001",
        group="EQ",
        quantity="2",
    )

    workman = _build_input(
        identifier=2,
        code="P0001",
        group="MO",
        quantity="3",
    )

    material = _build_input(
        identifier=3,
        code="M0001",
        group="MA",
        quantity="4",
    )

    root.composition.equipments.append(equipment)
    root.composition.workmen.append(workman)
    root.composition.materials.append(material)

    tree = CompositionTree(root)

    result = InputAggregator().aggregate(tree)

    assert {
        item.code
        for item in result
    } == {
        "E0001",
        "P0001",
        "M0001",
    }


def test_input_aggregator_ignores_composition_references_and_transport_inputs() -> None:
    """
    Verifica que AX, TF, LN, RP, PV e FR não são agregados.
    """
    root = _build_node()

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

    root.composition.activities.append(
        auxiliary_activity
    )

    root.composition.activities.append(
        fixed_time
    )

    root.composition.transports.extend(
        [
            transport_ln,
            transport_rp,
            transport_pv,
            transport_fr,
        ]
    )

    tree = CompositionTree(root)

    result = InputAggregator().aggregate(tree)

    assert result == []


def test_input_aggregator_uses_accumulated_quantity_not_effective_quantity() -> None:
    """
    Verifica que a quantidade dos insumos é calculada a partir
    da accumulated_quantity da ocorrência, e não da effective_quantity.

    ```
    A ocorrência possui:

        quantidade da referência = 4
        produção da composição = 2

    Portanto:

        accumulated_quantity = 4
        effective_quantity = 2

    Para um material com quantidade 3:

        resultado esperado = 3 × 4 = 12
    """
    root = _build_node(
        identifier=1,
        code="ROOT",
        production="1",
    )

    reference = _build_input(
        identifier=10,
        code="COMP",
        group="AX",
        quantity="4",
    )

    material = _build_input(
        identifier=20,
        code="M0001",
        group="MA",
        quantity="3",
    )

    root.composition.activities.append(reference)

    child_composition = _build_composition(
        identifier=2,
        code="COMP",
        production="2",
    )

    child_composition.materials.append(material)

    child = CompositionNode(
        composition=child_composition,
        reference_input=reference,
    )

    root.add_child(child)

    tree = CompositionTree(root)

    result = InputAggregator().aggregate(tree)

    material_result = _get_result_by_code(
        result,
        "M0001",
    )

    assert child.accumulated_quantity == Decimal("4")
    assert child.effective_quantity == Decimal("2")
    assert material_result.quantity == Decimal("12")


def test_input_aggregator_preserves_equipment_productive_and_unproductive_quantities() -> None:
    """
    Verifica que o resultado de equipamento mantém separadas
    as quantidades produtiva e improdutiva.
    """
    root = _build_node(
    production="2",
    )

    equipment = _build_input(
        identifier=1,
        code="E0001",
        group="EQ",
        quantity="10",
        use="0.75",
    )

    root.composition.equipments.append(
        equipment
    )

    tree = CompositionTree(root)

    result = InputAggregator().aggregate(tree)

    equipment_result = _get_result_by_code(
        result,
        "E0001",
    )

    assert equipment_result.productive_quantity == Decimal("3.75")
    assert equipment_result.unproductive_quantity == Decimal("1.25")


def test_input_aggregator_aggregates_repeated_inputs_by_code() -> None:
    """
    Verifica que ocorrências do mesmo insumo são agregadas
    pelo código.
    """
    root = _build_node()

    material_a = _build_input(
        identifier=1,
        code="M0001",
        group="MA",
        quantity="2",
    )

    material_b = _build_input(
        identifier=2,
        code="M0001",
        group="MA",
        quantity="3",
    )

    root.composition.materials.extend(
        [
            material_a,
            material_b,
        ]
    )

    tree = CompositionTree(root)

    result = InputAggregator().aggregate(tree)

    aggregated = [
        item
        for item in result
        if item.code == "M0001"
    ]

    assert len(aggregated) == 1
    assert aggregated[0].quantity == Decimal("5")


def test_input_aggregator_preserves_first_occurrence_order() -> None:
    """
    Verifica que a ordem dos resultados segue a ordem da primeira
    ocorrência de cada insumo na travessia da árvore.
    """
    root = _build_node()

    material_a_1 = _build_input(
        identifier=1,
        code="M0001",
        group="MA",
        quantity="1",
    )

    material_b = _build_input(
        identifier=2,
        code="M0002",
        group="MA",
        quantity="1",
    )

    material_a_2 = _build_input(
        identifier=3,
        code="M0001",
        group="MA",
        quantity="1",
    )

    root.composition.materials.extend(
        [
            material_a_1,
            material_b,
            material_a_2,
        ]
    )

    tree = CompositionTree(root)

    result = InputAggregator().aggregate(tree)

    assert [
        item.code
        for item in result
    ] == [
        "M0001",
        "M0002",
    ]


def test_input_aggregator_does_not_resolve_compositions() -> None:
    """
    Verifica que o InputAggregator não possui responsabilidade
    de resolver ou carregar composições.
    """
    source = InputAggregator.aggregate.__code__.co_names


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


def test_input_aggregator_module_does_not_import_infrastructure() -> None:
    """
    Verifica que o módulo do InputAggregator não depende
    diretamente de infraestrutura ou repositórios.
    """
    import ast
    from pathlib import Path

    file_path = Path(
        "app/services/input_aggregator.py"
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


def test_input_aggregator_does_not_leak_state_between_calls() -> None:
    """
    Verifica que chamadas independentes não compartilham
    estado de agregação.
    """
    aggregator = InputAggregator()

    root_1 = _build_node(
        identifier=1,
        code="ROOT_A",
    )

    material_1 = _build_input(
        identifier=10,
        code="M0001",
        group="MA",
        quantity="2",
    )

    root_1.composition.materials.append(
        material_1
    )

    tree_1 = CompositionTree(root_1)

    result_1 = aggregator.aggregate(tree_1)

    root_2 = _build_node(
        identifier=2,
        code="ROOT_B",
    )

    material_2 = _build_input(
        identifier=20,
        code="M0002",
        group="MA",
        quantity="3",
    )

    root_2.composition.materials.append(
        material_2
    )

    tree_2 = CompositionTree(root_2)

    result_2 = aggregator.aggregate(tree_2)

    assert [
        item.code
        for item in result_1
    ] == ["M0001"]

    assert [
        item.code
        for item in result_2
    ] == ["M0002"]


def test_input_aggregator_returns_aggregated_inputs() -> None:
    """
    Verifica que a saída do InputAggregator é composta por
    resultados do tipo AggregatedInput.
    """
    root = _build_node()

    material = _build_input(
        identifier=1,
        code="M0001",
        group="MA",
        quantity="2",
    )

    root.composition.materials.append(
        material
    )

    tree = CompositionTree(root)

    result = InputAggregator().aggregate(tree)

    assert all(
        isinstance(item, AggregatedInput)
        for item in result
    )