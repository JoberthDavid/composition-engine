from app.infrastructure.composition_api_client import (
    CompositionApiClient,
)
from app.repositories.composition_repository import (
    CompositionRepository,
)
from app.repositories.optimized_composition_repository import (
    OptimizedCompositionRepository,
)
from app.services.composition_explosion import (
    CompositionExplosion,
)
from app.services.composition_resolver import (
    CompositionResolver,
)


class CompositionRoot:
    """
    Ponto central de composição das dependências da aplicação.

    O CompositionRoot é responsável por construir o grafo concreto
    de objetos necessário aos serviços da aplicação.

    Serviços de aplicação não devem conhecer ou instanciar diretamente
    componentes de infraestrutura. Essa responsabilidade pertence ao
    CompositionRoot.
    """

    def __init__(
        self,
        composition_data_base: str | None = None,
    ) -> None:
        self.composition_data_base = composition_data_base

    def create_composition_explosion(
        self,
    ) -> CompositionExplosion:
        """
        Cria um CompositionExplosion completamente configurado.

        Grafo de dependências:

            CompositionApiClient
                    │
                    ├── CompositionRepository
                    │
                    └── OptimizedCompositionRepository
                                │
                                ▼
                       CompositionResolver
                                │
                                ▼
                       CompositionExplosion
        """

        api_client = CompositionApiClient()

        composition_repository = CompositionRepository(
            api_client=api_client,
        )

        optimized_repository = (
            OptimizedCompositionRepository(
                api_client=api_client,
                composition_data_base=self.composition_data_base,
            )
        )

        resolver = CompositionResolver(
            repository=composition_repository,
            optimized_repository=optimized_repository,
        )

        return CompositionExplosion(
            resolver=resolver,
        )