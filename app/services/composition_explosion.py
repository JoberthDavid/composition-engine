from app.domain.composition_explosion_result import (
    CompositionExplosionResult,
)
from app.infrastructure.composition_api_client import (
    CompositionApiClient,
)
from app.repositories.composition_repository import (
    CompositionRepository,
)
from app.repositories.optimized_composition_repository import (
    OptimizedCompositionRepository,
)
from app.services.composition_aggregator import (
    CompositionAggregator,
)
from app.services.composition_resolver import (
    CompositionResolver,
)
from app.services.input_aggregator import (
    InputAggregator,
)


class CompositionExplosion:
    """
    Serviço responsável por orquestrar a explosão completa
    de uma composição.

    O processo consiste em:

    1. Resolver a árvore completa de composições;
    2. Agregar as composições da árvore;
    3. Agregar os insumos presentes nas composições.

    A resolução estrutural utiliza, por padrão, a estratégia
    otimizada.

    A data-base estrutural da composição é independente da
    data-base utilizada posteriormente para os valores monetários.
    """

    def __init__(
        self,
        resolver: CompositionResolver | None = None,
        composition_aggregator: (
            CompositionAggregator | None
        ) = None,
        input_aggregator: (
            InputAggregator | None
        ) = None,
        composition_data_base: str | None = None,
    ) -> None:

        if resolver is not None:
            self.resolver = resolver

        else:
            api_client = CompositionApiClient()

            composition_repository = (
                CompositionRepository(
                    api_client=api_client,
                )
            )

            optimized_repository = (
                OptimizedCompositionRepository(
                    api_client=api_client,
                    composition_data_base=(
                        composition_data_base
                    ),
                )
            )

            self.resolver = CompositionResolver(
                repository=composition_repository,
                optimized_repository=optimized_repository,
            )

        self.composition_aggregator = (
            composition_aggregator
            if composition_aggregator is not None
            else CompositionAggregator()
        )

        self.input_aggregator = (
            input_aggregator
            if input_aggregator is not None
            else InputAggregator()
        )

    def explode(
        self,
        code: str,
    ) -> CompositionExplosionResult:
        """
        Executa a explosão completa de uma composição.

        A árvore é resolvida utilizando a estratégia otimizada
        quando o resolver padrão é utilizado.

        Retorna a árvore de composições, as composições
        agregadas e os insumos agregados.
        """

        root_node = self.resolver.resolve_tree_optimized(
            composition_code=code,
        )

        compositions = (
            self.composition_aggregator.aggregate(
                root_node,
            )
        )

        inputs = (
            self.input_aggregator.aggregate(
                root_node,
            )
        )

        return CompositionExplosionResult(
            root_node=root_node,
            compositions=compositions,
            inputs=inputs,
        )