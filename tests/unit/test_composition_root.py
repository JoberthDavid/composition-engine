from unittest.mock import patch

from app.composition_root import CompositionRoot
from app.services.composition_explosion import CompositionExplosion


def test_composition_root_creates_composition_explosion():
    """
    Garante que o CompositionRoot monta corretamente o grafo
    de dependências do CompositionExplosion.
    """

    composition_data_base = "2021-10-01"

    with (
        patch(
            "app.composition_root.CompositionApiClient"
        ) as api_client_class,
        patch(
            "app.composition_root.CompositionRepository"
        ) as composition_repository_class,
        patch(
            "app.composition_root.OptimizedCompositionRepository"
        ) as optimized_repository_class,
        patch(
            "app.composition_root.CompositionResolver"
        ) as resolver_class,
        patch(
            "app.composition_root.CompositionExplosion"
        ) as explosion_class,
    ):
        api_client = api_client_class.return_value
        composition_repository = (
            composition_repository_class.return_value
        )
        optimized_repository = (
            optimized_repository_class.return_value
        )
        resolver = resolver_class.return_value
        explosion = explosion_class.return_value

        root = CompositionRoot(
            composition_data_base=composition_data_base,
        )

        result = root.create_composition_explosion()

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

        explosion_class.assert_called_once_with(
            resolver=resolver,
        )

        assert result is explosion


def test_composition_root_preserves_composition_data_base():
    """
    Garante que a configuração da data-base pertence ao
    CompositionRoot e é propagada para o repositório otimizado.
    """

    composition_data_base = "2021-10-01"

    with (
        patch(
            "app.composition_root.CompositionApiClient"
        ) as api_client_class,
        patch(
            "app.composition_root.CompositionRepository"
        ),
        patch(
            "app.composition_root.OptimizedCompositionRepository"
        ) as optimized_repository_class,
        patch(
            "app.composition_root.CompositionResolver"
        ),
        patch(
            "app.composition_root.CompositionExplosion"
        ),
    ):
        api_client = api_client_class.return_value

        root = CompositionRoot(
            composition_data_base=composition_data_base,
        )

        root.create_composition_explosion()

        optimized_repository_class.assert_called_once_with(
            api_client=api_client,
            composition_data_base=composition_data_base,
        )


def test_composition_root_without_data_base_uses_default_configuration():
    """
    Garante que a ausência de data-base explícita não impede
    a construção do grafo.
    """

    with (
        patch(
            "app.composition_root.CompositionApiClient"
        ) as api_client_class,
        patch(
            "app.composition_root.CompositionRepository"
        ),
        patch(
            "app.composition_root.OptimizedCompositionRepository"
        ) as optimized_repository_class,
        patch(
            "app.composition_root.CompositionResolver"
        ),
        patch(
            "app.composition_root.CompositionExplosion"
        ),
    ):
        api_client = api_client_class.return_value

        root = CompositionRoot()

        root.create_composition_explosion()

        optimized_repository_class.assert_called_once_with(
            api_client=api_client,
            composition_data_base=None,
        )