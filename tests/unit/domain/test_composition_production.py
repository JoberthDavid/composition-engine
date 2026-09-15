from decimal import Decimal

import pytest

from app.domain.composition import Composition
from app.domain.composition_node import CompositionNode


def _build_composition(*, production: str = "1") -> Composition:
    """
    Cria uma composição mínima para os testes de produção.
    """
    return Composition(
        id=1,
        composition_group="09",
        generic_item="0919013",
        generic_description="Composição de teste",
        unit="un",
        fic=Decimal("0"),
        production=Decimal(production),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[],
        transports=[],
    )


def test_composition_node_accepts_positive_production() -> None:
    """
    Garante que uma ocorrência aceita produção estritamente positiva.
    """
    composition = _build_composition(production="1")

    node = CompositionNode(composition=composition)

    assert node.composition.production == Decimal("1")


def test_composition_node_accepts_small_positive_production() -> None:
    """
    Garante que a regra é production > 0, e não production >= 1.
    """
    composition = _build_composition(production="0.000001")

    node = CompositionNode(composition=composition)

    assert node.composition.production == Decimal("0.000001")


def test_composition_node_rejects_zero_production() -> None:
    """
    Garante que uma ocorrência não pode ser criada com produção zero.
    """
    composition = _build_composition(production="0")

    with pytest.raises(
        ValueError,
        match=r"^Composition production must be greater than zero: 0919013$",
    ):
        CompositionNode(composition=composition)


def test_composition_node_rejects_negative_production() -> None:
    """
    Garante que uma ocorrência não pode ser criada com produção negativa.
    """
    composition = _build_composition(production="-1")

    with pytest.raises(
        ValueError,
        match=r"^Composition production must be greater than zero: 0919013$",
    ):
        CompositionNode(composition=composition)

def test_composition_node_accepts_positive_production() -> None:
    composition = _build_composition(production="1")

    node = CompositionNode(composition=composition)

    assert node.composition.production > Decimal("0")

def test_composition_node_accepts_small_positive_production() -> None:
    composition = _build_composition(production="0.000001")

    node = CompositionNode(composition=composition)

    assert node.composition.production > Decimal("0")