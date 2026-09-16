from concurrent.futures import ThreadPoolExecutor
from datetime import date

from app.domain.calculation_context import CalculationContext
from app.infrastructure.composition_api_client import CompositionApiClient
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.repositories.monetary_value_repository import MonetaryValueRepository
from app.services.composition_resolver import CompositionResolver


def _load_cache_parallel(
    repository: MonetaryValueRepository,
    codes_by_group: dict[str, set[str]],
    context: CalculationContext,
) -> None:
    """
    Carrega os valores monetários em paralelo.

    Esta implementação existe somente para validar a equivalência
    com o carregamento sequencial atual antes de alterar o código
    de produção.
    """
    group_type_systems = {
        "EQ": "ON",
        "MO": "ON",
        "MA": "NA",
    }

    requests = []

    source_file = (
        context.source_file_data_base.isoformat()
        if context.source_file_data_base is not None
        else None
    )

    for group, codes in codes_by_group.items():
        type_system = group_type_systems[group]

        for code in sorted(codes):
            requests.append(
                (
                    code,
                    type_system,
                    source_file,
                    context.source_file_uf,
                    group,
                )
            )

    def load_one(request):
        code, type_system, source_file, source_file_uf, group = request

        api_client = MonetaryValueApiClient()

        values = api_client.get_values(
            generic_item=code,
            type_system=type_system,
            source_file=source_file,
            group=group,
        )

        return values

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(load_one, requests)
        )

    for values in results:
        repository._store_values(values)


def _serialize_cache(
    repository: MonetaryValueRepository,
) -> dict[str, list[tuple]]:
    """
    Cria uma representação imutável e comparável do cache.

    A ordenação elimina diferenças causadas pela ordem
    em que as requisições HTTP são concluídas.
    """
    serialized = {}

    for code, values in repository._cache.items():
        serialized[code] = sorted(
            (
                (
                    value.id,
                    str(value.generic_item),
                    value.monetary_value,
                    str(value.unit),
                    str(value.classification),
                    str(value.group),
                    str(value.type_system),
                    value.source_file_id,
                )
                for value in values
            ),
            key=lambda item: item,
        )

    return serialized


def test_monetary_value_cache_parallel_equivalence():
    composition_code = "0919013"

    context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
        type_system="ON",
    )

    # Resolve a árvore da composição.
    api_client = CompositionApiClient()

    composition_repository = CompositionRepository(
        api_client=api_client,
    )

    composition_resolver = CompositionResolver(
        repository=composition_repository,
    )

    tree = composition_resolver.resolve_tree(
        composition_code=composition_code,
    )

    codes_by_group = tree.monetary_item_codes_by_group

    # ------------------------------------------------------------
    # Carregamento sequencial atual.
    # ------------------------------------------------------------

    sequential_api_client = MonetaryValueApiClient()

    sequential_repository = MonetaryValueRepository(
        api_client=sequential_api_client,
    )

    sequential_repository.load_cache(
        codes_by_group=codes_by_group,
        type_system=context.type_system,
        source_file_uf=context.source_file_uf,
        source_file_data_base=context.source_file_data_base,
    )

    # ------------------------------------------------------------
    # Carregamento paralelo de referência.
    # ------------------------------------------------------------

    parallel_api_client = MonetaryValueApiClient()

    parallel_repository = MonetaryValueRepository(
        api_client=parallel_api_client,
    )

    _load_cache_parallel(
        repository=parallel_repository,
        codes_by_group=codes_by_group,
        context=context,
    )

    # ------------------------------------------------------------
    # Comparação.
    # ------------------------------------------------------------

    sequential_cache = _serialize_cache(
        sequential_repository
    )

    parallel_cache = _serialize_cache(
        parallel_repository
    )

    assert sequential_repository.cache_size == parallel_repository.cache_size
    assert sequential_cache == parallel_cache