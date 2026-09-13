from unittest.mock import MagicMock, patch

from app.domain.composition_explosion_result import (
CompositionExplosionResult,
)
from app.services.composition_explosion import (
CompositionExplosion,
)

def test_composition_explosion_uses_optimized_resolver_by_default():
    """
    Garante que o CompositionExplosion padrão constrói
    um CompositionResolver configurado com o repositório
    otimizado.

    ```
    Nenhuma chamada HTTP é realizada.
    """

    composition_data_base = "2021-10-01"

    with (
        patch(
            "app.services.composition_explosion.CompositionApiClient"
        ) as api_client_class,
        patch(
            "app.services.composition_explosion.CompositionRepository"
        ) as composition_repository_class,
        patch(
            "app.services.composition_explosion.OptimizedCompositionRepository"
        ) as optimized_repository_class,
        patch(
            "app.services.composition_explosion.CompositionResolver"
        ) as resolver_class,
    ):
        api_client = api_client_class.return_value
        composition_repository = (
            composition_repository_class.return_value
        )
        optimized_repository = (
            optimized_repository_class.return_value
        )
        resolver = resolver_class.return_value

        explosion = CompositionExplosion(
            composition_data_base=composition_data_base,
        )

        api_client_class.assert_called_once_with()

        composition_repository_class.assert_called_once_with(
            api_client=api_client,
        )

        optimized_repository_class.assert_called_once_with(
            api_client=api_client,
            composition_data_base=composition_data_base,
        )

        resolver_class.assert_called_once_with(
            repository=composition_repository,
            optimized_repository=optimized_repository,
        )

        assert explosion.resolver is resolver


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


def test_composition_explosion_preserves_explicit_resolver():
    """
    Garante que um resolver explicitamente injetado pelo chamador
    é preservado e utilizado sem criar dependências adicionais.
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

    with (
        patch(
            "app.services.composition_explosion.CompositionApiClient"
        ) as api_client_class,
        patch(
            "app.services.composition_explosion.CompositionRepository"
        ) as composition_repository_class,
        patch(
            "app.services.composition_explosion.OptimizedCompositionRepository"
        ) as optimized_repository_class,
        patch(
            "app.services.composition_explosion.CompositionResolver"
        ) as resolver_class,
    ):
        explosion = CompositionExplosion(
            resolver=resolver,
            composition_aggregator=composition_aggregator,
            input_aggregator=input_aggregator,
            composition_data_base="2021-10-01",
        )

    assert explosion.resolver is resolver

    api_client_class.assert_not_called()
    composition_repository_class.assert_not_called()
    optimized_repository_class.assert_not_called()
    resolver_class.assert_not_called()

    explosion.explode("0919013")

    resolver.resolve_tree_optimized.assert_called_once_with(
        composition_code="0919013",
    )