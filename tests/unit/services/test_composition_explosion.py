from unittest.mock import MagicMock, patch

from app.domain.composition_explosion_result import (
CompositionExplosionResult,
)
from app.services.composition_explosion import (
CompositionExplosion,
)


def test_composition_explosion_orchestrates_optimized_resolution_and_aggregation():
    """
    Garante que explode():

    ```
    1. chama resolve_tree_optimized();
    2. envia a raiz retornada ao CompositionAggregator;
    3. envia a mesma raiz ao InputAggregator;
    4. retorna um CompositionExplosionResult.

    Nenhuma chamada HTTP é realizada.
    """

    code = "0919013"

    resolver = MagicMock()
    composition_aggregator = MagicMock()
    input_aggregator = MagicMock()

    root_node = MagicMock(
        name="root_node",
    )

    compositions = MagicMock(
        name="compositions",
    )

    inputs = MagicMock(
        name="inputs",
    )

    resolver.resolve_tree_optimized.return_value = (
        root_node
    )

    composition_aggregator.aggregate.return_value = (
        compositions
    )

    input_aggregator.aggregate.return_value = (
        inputs
    )

    explosion = CompositionExplosion(
        resolver=resolver,
        composition_aggregator=composition_aggregator,
        input_aggregator=input_aggregator,
    )

    result = explosion.explode(code)

    resolver.resolve_tree_optimized.assert_called_once_with(
        composition_code=code,
    )

    resolver.resolve_tree.assert_not_called()

    composition_aggregator.aggregate.assert_called_once_with(
        root_node,
    )

    input_aggregator.aggregate.assert_called_once_with(
        root_node,
    )

    assert isinstance(
        result,
        CompositionExplosionResult,
    )

    assert result.root_node is root_node
    assert result.compositions is compositions
    assert result.inputs is inputs

def test_composition_explosion_uses_injected_resolver():
    """
    Garante que o CompositionExplosion utiliza o resolver
    fornecido por injeção de dependência.
    """

    resolver = MagicMock()

    composition_aggregator = MagicMock()
    input_aggregator = MagicMock()

    root_node = MagicMock()

    resolver.resolve_tree_optimized.return_value = (
        root_node
    )

    composition_aggregator.aggregate.return_value = []
    input_aggregator.aggregate.return_value = []

    explosion = CompositionExplosion(
        resolver=resolver,
        composition_aggregator=composition_aggregator,
        input_aggregator=input_aggregator,
    )

    result = explosion.explode(
        "0919013",
    )

    assert explosion.resolver is resolver

    resolver.resolve_tree_optimized.assert_called_once_with(
        composition_code="0919013",
    )

    composition_aggregator.aggregate.assert_called_once_with(
        root_node,
    )

    input_aggregator.aggregate.assert_called_once_with(
        root_node,
    )

    assert result.root_node is root_node