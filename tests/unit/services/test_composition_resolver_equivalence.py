from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree
from app.services.composition_resolver import CompositionResolver


def _build_composition(
    code: str,
    references: list[CompositionInput] | None = None,
) -> Composition:
    composition = Composition(
        id=1,
        composition_group="C",
        generic_item=code,
        generic_description=f"Composição {code}",
        unit="UN",
        fic=Decimal("0"),
        production=Decimal("1"),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[],
        transports=[],
    )

    if references:
        composition.activities = references

    return composition


def _build_reference(
    code: str,
    quantity: str = "1",
) -> CompositionInput:
    return CompositionInput(
        id=1,
        input_group="AX",
        generic_item=code,
        generic_description=f"Referência {code}",
        unit="UN",
        input_quantity=Decimal(quantity),
    )


def _build_tree_signature(
    tree: CompositionTree,
) -> list[tuple[str, str | None, str | None, Decimal | None]]:
    """
    Cria uma representação determinística da árvore para comparação.

    Cada ocorrência é representada por:

        (
            código da composição,
            código do pai,
            grupo da referência,
            quantidade da referência,
        )

    A posição dos nós na lista corresponde à ordem de caminhada
    da árvore.
    """

    signature = []

    for node in tree.walk():
        parent_code = (
            str(node.parent.composition.code)
            if node.parent is not None
            else None
        )

        reference_group = (
            node.reference_input.input_group
            if node.reference_input is not None
            else None
        )

        reference_quantity = (
            node.reference_input.input_quantity
            if node.reference_input is not None
            else None
        )

        signature.append(
            (
                str(node.composition.code),
                parent_code,
                reference_group,
                reference_quantity,
            )
        )

    return signature


def _build_repositories() -> tuple[MagicMock, MagicMock]:
    root_reference_1 = _build_reference(
        code="B",
        quantity="2",
    )

    root_reference_2 = _build_reference(
        code="C",
        quantity="3",
    )

    composition_a = _build_composition(
        code="A",
        references=[
            root_reference_1,
            root_reference_2,
        ],
    )

    composition_b = _build_composition(
        code="B",
    )

    composition_c = _build_composition(
        code="C",
    )

    compositions_by_code = {
        "A": composition_a,
        "B": composition_b,
        "C": composition_c,
    }

    repository = MagicMock()

    repository.get_by_code.side_effect = (
        lambda code: compositions_by_code.get(code)
    )

    repository.get_by_codes.side_effect = (
        lambda codes: [
            compositions_by_code[code]
            for code in codes
            if code in compositions_by_code
        ]
    )

    optimized_repository = MagicMock()

    optimized_repository.get_child_codes_by_composition_codes.side_effect = (
        lambda codes: {
            code: [
                reference.generic_item
                for reference in compositions_by_code[
                    code
                ].composition_references
            ]
            for code in codes
        }
    )

    return repository, optimized_repository


def test_resolve_tree_strategies_are_semantically_equivalent() -> None:
    """
    O resolver tradicional e o resolver otimizado devem produzir
    a mesma estrutura semântica para a mesma composição raiz.
    """

    repository, optimized_repository = _build_repositories()

    baseline_resolver = CompositionResolver(
        repository=repository,
    )

    optimized_resolver = CompositionResolver(
        repository=repository,
        optimized_repository=optimized_repository,
    )

    baseline_tree = baseline_resolver.resolve_tree(
        composition_code="A",
    )

    optimized_tree = optimized_resolver.resolve_tree_optimized(
        composition_code="A",
    )

    baseline_signature = _build_tree_signature(
        baseline_tree,
    )

    optimized_signature = _build_tree_signature(
        optimized_tree,
    )

    assert baseline_signature == optimized_signature

    assert len(baseline_tree) == len(optimized_tree)

def test_resolve_tree_strategies_preserve_multiple_occurrences() -> None:
    """
    As estratégias tradicional e otimizada devem preservar todas as
    ocorrências de uma mesma composição na árvore.

    Cenário:

        A
        ├── B  (quantidade 2)
        └── B  (quantidade 3)

    A composição B possui o mesmo código nas duas ocorrências,
    mas cada ocorrência representa uma referência distinta do pai.

    Portanto, nenhuma das estratégias pode deduplicar B por código.
    """

    first_reference = _build_reference(
        code="B",
        quantity="2",
    )

    second_reference = _build_reference(
        code="B",
        quantity="3",
    )

    composition_a = _build_composition(
        code="A",
        references=[
            first_reference,
            second_reference,
        ],
    )

    composition_b = _build_composition(
        code="B",
    )

    compositions_by_code = {
        "A": composition_a,
        "B": composition_b,
    }

    repository = MagicMock()

    repository.get_by_code.side_effect = (
        lambda code: compositions_by_code.get(code)
    )

    repository.get_by_codes.side_effect = (
        lambda codes: [
            compositions_by_code[code]
            for code in codes
            if code in compositions_by_code
        ]
    )

    optimized_repository = MagicMock()

    optimized_repository.get_child_codes_by_composition_codes.side_effect = (
        lambda codes: {
            code: [
                reference.generic_item
                for reference in compositions_by_code[
                    code
                ].composition_references
            ]
            for code in codes
        }
    )

    baseline_resolver = CompositionResolver(
        repository=repository,
    )

    optimized_resolver = CompositionResolver(
        repository=repository,
        optimized_repository=optimized_repository,
    )

    baseline_tree = baseline_resolver.resolve_tree(
        composition_code="A",
    )

    optimized_tree = optimized_resolver.resolve_tree_optimized(
        composition_code="A",
    )

    baseline_nodes = list(baseline_tree.walk())
    optimized_nodes = list(optimized_tree.walk())

    baseline_children = baseline_nodes[1:]
    optimized_children = optimized_nodes[1:]

    assert len(baseline_children) == 2
    assert len(optimized_children) == 2

    assert all(
        node.composition.code == "B"
        for node in baseline_children
    )

    assert all(
        node.composition.code == "B"
        for node in optimized_children
    )

    assert [
        node.reference_input.input_quantity
        for node in baseline_children
    ] == [
        Decimal("2"),
        Decimal("3"),
    ]

    assert [
        node.reference_input.input_quantity
        for node in optimized_children
    ] == [
        Decimal("2"),
        Decimal("3"),
    ]

    assert baseline_tree is not optimized_tree
    assert baseline_children[0] is not baseline_children[1]
    assert optimized_children[0] is not optimized_children[1]

    assert (
        baseline_children[0].reference_input
        is not baseline_children[1].reference_input
    )

    assert (
        optimized_children[0].reference_input
        is not optimized_children[1].reference_input
    )

def test_resolve_tree_strategies_preserve_reference_order_and_data() -> None:
    """
    As estratégias tradicional e otimizada devem preservar a ordem
    e os dados das referências que originam cada ocorrência.

    Cenário:

        A
        ├── B ← AX, quantidade 2
        ├── C ← TF, quantidade 3
        └── D ← AX, quantidade 5

    AX pertence a activities e TF pertence a transports.

    A ocorrência deve permanecer associada à referência que a
    originou, sem alteração de ordem, grupo, quantidade ou código.
    """

    reference_b = _build_reference(
        code="B",
        quantity="2",
    )

    reference_c = _build_reference(
        code="C",
        quantity="3",
    )

    reference_c.input_group = "TF"

    reference_d = _build_reference(
        code="D",
        quantity="5",
    )

    composition_a = Composition(
        id=1,
        composition_group="C",
        generic_item="A",
        generic_description="Composição A",
        unit="UN",
        fic=Decimal("0"),
        production=Decimal("1"),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[
            reference_b,
            reference_d,
        ],
        transports=[
            reference_c,
        ],
    )

    composition_b = _build_composition(
        code="B",
    )

    composition_c = _build_composition(
        code="C",
    )

    composition_d = _build_composition(
        code="D",
    )

    compositions_by_code = {
        "A": composition_a,
        "B": composition_b,
        "C": composition_c,
        "D": composition_d,
    }

    repository = MagicMock()

    repository.get_by_code.side_effect = (
        lambda code: compositions_by_code.get(code)
    )

    repository.get_by_codes.side_effect = (
        lambda codes: [
            compositions_by_code[code]
            for code in codes
            if code in compositions_by_code
        ]
    )

    optimized_repository = MagicMock()

    optimized_repository.get_child_codes_by_composition_codes.side_effect = (
        lambda codes: {
            code: [
                reference.generic_item
                for reference in compositions_by_code[
                    code
                ].composition_references
            ]
            for code in codes
        }
    )

    baseline_resolver = CompositionResolver(
        repository=repository,
    )

    optimized_resolver = CompositionResolver(
        repository=repository,
        optimized_repository=optimized_repository,
    )

    baseline_tree = baseline_resolver.resolve_tree(
        composition_code="A",
    )

    optimized_tree = optimized_resolver.resolve_tree_optimized(
        composition_code="A",
    )

    baseline_data = [
        (
            node.composition.code,
            node.reference_input.generic_item,
            node.reference_input.input_group,
            node.reference_input.input_quantity,
        )
        for node in baseline_tree.walk()
        if node.reference_input is not None
    ]

    optimized_data = [
        (
            node.composition.code,
            node.reference_input.generic_item,
            node.reference_input.input_group,
            node.reference_input.input_quantity,
        )
        for node in optimized_tree.walk()
        if node.reference_input is not None
    ]

    expected = [
        (
            "B",
            "B",
            "AX",
            Decimal("2"),
        ),
        (
            "D",
            "D",
            "AX",
            Decimal("5"),
        ),
        (
            "C",
            "C",
            "TF",
            Decimal("3"),
        ),
    ]

    assert baseline_data == expected
    assert optimized_data == expected

    assert baseline_data == optimized_data

def test_resolve_tree_strategies_raise_same_error_for_missing_composition() -> None:
    """
    As estratégias tradicional e otimizada devem apresentar o mesmo
    comportamento quando uma referência aponta para uma composição
    inexistente.

    Cenário:

        A
        └── B  ← composição inexistente

    O erro deve ser equivalente nos dois caminhos.
    """

    reference_b = _build_reference(
        code="B",
        quantity="1",
    )

    composition_a = _build_composition(
        code="A",
        references=[
            reference_b,
        ],
    )

    compositions_by_code = {
        "A": composition_a,
    }

    repository = MagicMock()

    repository.get_by_code.side_effect = (
        lambda code: compositions_by_code.get(code)
    )

    repository.get_by_codes.side_effect = (
        lambda codes: [
            compositions_by_code[code]
            for code in codes
            if code in compositions_by_code
        ]
    )

    optimized_repository = MagicMock()

    optimized_repository.get_child_codes_by_composition_codes.side_effect = (
        lambda codes: {
            code: [
                reference.generic_item
                for reference in compositions_by_code[
                    code
                ].composition_references
            ]
            for code in codes
        }
    )

    baseline_resolver = CompositionResolver(
        repository=repository,
    )

    optimized_resolver = CompositionResolver(
        repository=repository,
        optimized_repository=optimized_repository,
    )

    with pytest.raises(ValueError) as baseline_error:
        baseline_resolver.resolve_tree(
            composition_code="A",
        )

    with pytest.raises(ValueError) as optimized_error:
        optimized_resolver.resolve_tree_optimized(
            composition_code="A",
        )

    assert type(baseline_error.value) is type(
        optimized_error.value
    )

    assert "B" in str(baseline_error.value)
    assert "B" in str(optimized_error.value)

def test_resolve_tree_strategies_raise_same_error_for_cycle() -> None:
    """
    As estratégias tradicional e otimizada devem apresentar o mesmo
    comportamento quando as referências formam um ciclo.

    Cenário:

        A
        └── B
            └── A

    Ambos os caminhos devem detectar o ciclo e rejeitar a resolução.
    """

    reference_b = _build_reference(
        code="B",
        quantity="1",
    )

    reference_a = _build_reference(
        code="A",
        quantity="1",
    )

    composition_a = _build_composition(
        code="A",
        references=[
            reference_b,
        ],
    )

    composition_b = _build_composition(
        code="B",
        references=[
            reference_a,
        ],
    )

    compositions_by_code = {
        "A": composition_a,
        "B": composition_b,
    }

    repository = MagicMock()

    repository.get_by_code.side_effect = (
        lambda code: compositions_by_code.get(code)
    )

    repository.get_by_codes.side_effect = (
        lambda codes: [
            compositions_by_code[code]
            for code in codes
            if code in compositions_by_code
        ]
    )

    optimized_repository = MagicMock()

    optimized_repository.get_child_codes_by_composition_codes.side_effect = (
        lambda codes: {
            code: [
                reference.generic_item
                for reference in compositions_by_code[
                    code
                ].composition_references
            ]
            for code in codes
        }
    )

    baseline_resolver = CompositionResolver(
        repository=repository,
    )

    optimized_resolver = CompositionResolver(
        repository=repository,
        optimized_repository=optimized_repository,
    )

    with pytest.raises(ValueError) as baseline_error:
        baseline_resolver.resolve_tree(
            composition_code="A",
        )

    with pytest.raises(ValueError) as optimized_error:
        optimized_resolver.resolve_tree_optimized(
            composition_code="A",
        )

    assert type(baseline_error.value) is type(
        optimized_error.value
    )

    assert "cycle" in str(
        baseline_error.value
    ).lower()

    assert "cycle" in str(
        optimized_error.value
    ).lower()
