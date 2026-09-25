from app.domain.composition_explosion_result import (
    CompositionExplosionResult,
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
from app.domain.composition_operation_context import (
    CompositionOperationContext,
)

class CompositionExplosion:
    """
    Serviço responsável por orquestrar a explosão completa
    de uma composição.

    O serviço recebe suas dependências já construídas.
    A responsabilidade pela composição concreta dessas
    dependências pertence ao CompositionRoot.

    O processo consiste em:

    1. Resolver a árvore completa de composições;
    2. Agregar as composições da árvore;
    3. Agregar os insumos presentes nas composições.
    """

    def __init__(
        self,
        resolver: CompositionResolver,
        context: CompositionOperationContext,
        composition_aggregator: (
            CompositionAggregator | None
        ) = None,
        input_aggregator: (
            InputAggregator | None
        ) = None,
    ) -> None:
        self.resolver = resolver
        self.context = context

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

        A árvore é resolvida utilizando a estratégia otimizada.

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