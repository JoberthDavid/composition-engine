from collections import deque
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from time import perf_counter

from app.domain.calculation_context import CalculationContext
from app.infrastructure.api_query_metrics import ApiQueryMetrics
from app.infrastructure.composition_api_client import CompositionApiClient
from app.infrastructure.monetary_value_api_client import (
MonetaryValueApiClient,
)
from app.repositories.composition_repository import CompositionRepository
from app.repositories.monetary_value_repository import (
MonetaryValueRepository,
)
from app.repositories.optimized_composition_repository import (
OptimizedCompositionRepository,
)
from app.services.composition_calculator import CompositionCalculator
from app.services.composition_resolver import CompositionResolver
from app.services.equipment_calculator import EquipmentCalculator
from app.services.fic_calculator import FicCalculator
from app.services.labor_calculator import LaborCalculator
from app.services.material_calculator import MaterialCalculator
from app.services.monetary_value_resolver import (
MonetaryValueResolver,
)
from app.services.operational_cost_calculator import (
OperationalCostCalculator,
)

ROOT_COMPOSITION_CODE = "0919013"
COMPOSITION_DATA_BASE = "2021-10-01"
MONETARY_DATA_BASE = date.fromisoformat("2021-10-01")

def _build_calculation_context() -> CalculationContext:
    """
    Cria o contexto monetário utilizado pela regressão histórica.
    """

    return CalculationContext(
        source_file_uf="DF",
        source_file_data_base=MONETARY_DATA_BASE,
        type_system="ON",
    )


def _load_monetary_cache(
    tree,
    calculation_context: CalculationContext,
    monetary_value_repository: MonetaryValueRepository,
    ) -> None:
    """
    Carrega antecipadamente todos os valores monetários necessários
    para o cálculo da árvore.
    """

    monetary_value_repository.load_cache(
        codes_by_group=tree.monetary_item_codes_by_group,
        type_system=calculation_context.type_system,
        source_file_uf=calculation_context.source_file_uf,
        source_file_data_base=(
            calculation_context.source_file_data_base
        ),
    )


def _build_composition_calculator(
    calculation_context: CalculationContext,
    monetary_value_repository: MonetaryValueRepository,
    ) -> CompositionCalculator:
    """
    Cria o CompositionCalculator completo utilizando os serviços
    reais da aplicação.
    """

    
    monetary_value_resolver = MonetaryValueResolver(
        repository=monetary_value_repository,
    )

    equipment_calculator = EquipmentCalculator(
        monetary_value_resolver=monetary_value_resolver,
        calculation_context=calculation_context,
    )

    labor_calculator = LaborCalculator(
        monetary_value_resolver=monetary_value_resolver,
        calculation_context=calculation_context,
    )

    material_calculator = MaterialCalculator(
        monetary_value_resolver=monetary_value_resolver,
        calculation_context=calculation_context,
    )

    operational_cost_calculator = OperationalCostCalculator()
    fic_calculator = FicCalculator()


    def round_2(value: Decimal) -> Decimal:
        return value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )


    def round_4(value: Decimal) -> Decimal:
        return value.quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP,
        )

    return CompositionCalculator(
        calculation_context=calculation_context,
        equipment_calculator=equipment_calculator,
        labor_calculator=labor_calculator,
        material_calculator=material_calculator,
        operational_cost_calculator=operational_cost_calculator,
        fic_calculator=fic_calculator,
        round_2=round_2,
        round_4=round_4,
    )


def _get_root_node(tree):
    """
    Obtém o nó raiz da árvore de composição.
    """

    nodes = tree.find_by_code(ROOT_COMPOSITION_CODE)

    assert nodes

    return nodes[0]


def _get_tree_edges(tree):
    """
    Retorna todas as relações pai → filho da árvore.
    """

    edges = set()

    for parent_node in tree.walk():
        parent_code = str(parent_node.composition.code)

        for child_node in parent_node.children:
            child_code = str(child_node.composition.code)

            edges.add(
                (
                    parent_code,
                    child_code,
                )
            )

    return edges


def _get_tree_reference_data(tree):
    """
    Retorna os dados das referências utilizadas
    para criar cada ocorrência da árvore.
    """

    references = []

    for parent_node in tree.walk():
        parent_code = str(
            parent_node.composition.code
        )

        for child_node in parent_node.children:
            reference_input = (
                child_node.reference_input
            )

            references.append(
                (
                    parent_code,
                    str(child_node.composition.code),
                    reference_input.input_group,
                    reference_input.input_quantity,
                    reference_input.proprietary_item,
                )
            )

    return references


def _discover_optimized_tree_edges(
    optimized_repository,
    api_client,
    root_code,
    ):
    """
    Descobre recursivamente as relações pai → filho usando
    os endpoints otimizados.

    ```
    Este helper pertence exclusivamente à infraestrutura de testes.
    """

    visited_compositions = set()
    pending_compositions = deque(
        [str(root_code)]
    )
    edges = set()

    while pending_compositions:
        parent_code = (
            pending_compositions.popleft()
        )

        if parent_code in visited_compositions:
            continue

        visited_compositions.add(
            parent_code
        )

        children_by_parent = (
            optimized_repository
            .get_child_codes_by_composition_codes(
                [parent_code]
            )
        )

        child_codes = children_by_parent.get(
            parent_code,
            [],
        )

        if not child_codes:
            continue

        compositions = (
            api_client.get_compositions_by_codes(
                child_codes
            )
        )

        composition_codes = {
            str(composition["generic_item"])
            for composition in compositions
        }

        for child_code in child_codes:
            child_code = str(child_code)

            if child_code not in composition_codes:
                continue

            edges.add(
                (
                    parent_code,
                    child_code,
                )
            )

            if (
                child_code
                not in visited_compositions
            ):
                pending_compositions.append(
                    child_code
                )

    return edges


def _discover_optimized_tree_edges_by_levels(
    optimized_repository,
    api_client,
    root_code,
    ):
    """
    Descobre as relações pai → filho trabalhando por níveis.

    ```
    A deduplicação ocorre apenas para reduzir consultas à API.
    As relações estruturais encontradas continuam sendo preservadas.
    """

    processed_compositions = set()
    frontier = [str(root_code)]
    edges = set()

    while frontier:
        current_level = list(
            dict.fromkeys(frontier)
        )

        current_level = [
            code
            for code in current_level
            if code
            not in processed_compositions
        ]

        if not current_level:
            break

        processed_compositions.update(
            current_level
        )

        children_by_parent = (
            optimized_repository
            .get_child_codes_by_composition_codes(
                current_level
            )
        )

        candidate_codes = []

        for parent_code in current_level:
            children = (
                children_by_parent.get(
                    parent_code,
                    [],
                )
            )

            for child_code in children:
                child_code = str(child_code)

                if child_code not in candidate_codes:
                    candidate_codes.append(
                        child_code
                    )

        if not candidate_codes:
            continue

        compositions = (
            api_client.get_compositions_by_codes(
                candidate_codes
            )
        )

        composition_codes = {
            str(composition["generic_item"])
            for composition in compositions
        }

        next_frontier = []

        for parent_code in current_level:
            children = (
                children_by_parent.get(
                    parent_code,
                    [],
                )
            )

            for child_code in children:
                child_code = str(child_code)

                if child_code not in composition_codes:
                    continue

                edges.add(
                    (
                        str(parent_code),
                        child_code,
                    )
                )

                if (
                    child_code
                    not in processed_compositions
                    and child_code
                    not in next_frontier
                ):
                    next_frontier.append(
                        child_code
                    )

        frontier = next_frontier

    return edges


def test_optimized_repository_reproduces_root_composition_structure():
    """
    Compara a descoberta estrutural otimizada da composição raiz
    com a estrutura obtida pelo resolver baseline.

    ```
    Valida que:

    - as activities são obtidas pelo endpoint otimizado;
    - os candidatos são identificados pelo endpoint de composições;
    - os filhos estruturais coincidem com o resolver baseline;
    - a ordem dos códigos é preservada.
    """

    optimized_metrics = ApiQueryMetrics()

    api_client = CompositionApiClient(
        metrics=optimized_metrics,
    )

    optimized_repository = OptimizedCompositionRepository(
        api_client=api_client,
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    optimized_start = perf_counter()

    activities_by_composition = (
        optimized_repository
        .get_child_codes_by_composition_codes(
            [ROOT_COMPOSITION_CODE]
        )
    )

    optimized_duration = (
        perf_counter()
        - optimized_start
    )

    assert (
        ROOT_COMPOSITION_CODE
        in activities_by_composition
    )

    activity_codes = (
        activities_by_composition[
            ROOT_COMPOSITION_CODE
        ]
    )

    assert len(activity_codes) == 12

    compositions = api_client.get_compositions_by_codes(
        activity_codes
    )

    composition_codes = {
        str(composition["generic_item"])
        for composition in compositions
    }

    composition_repository = CompositionRepository(
        api_client=api_client,
    )

    resolver = CompositionResolver(
        repository=composition_repository,
    )

    resolver_start = perf_counter()

    tree = resolver.resolve_tree(
        ROOT_COMPOSITION_CODE
    )

    resolver_duration = (
        perf_counter()
        - resolver_start
    )

    root_node = _get_root_node(tree)

    resolver_child_codes = [
        str(child.composition.code)
        for child in root_node.children
    ]

    resolver_child_code_set = set(
        resolver_child_codes
    )

    assert composition_codes == (
        resolver_child_code_set
    )

    print()
    print("=== ESTRUTURA DA COMPOSIÇÃO RAIZ ===")
    print(
        f"Composição: "
        f"{ROOT_COMPOSITION_CODE}"
    )
    print(
        f"Data base da composição: "
        f"{COMPOSITION_DATA_BASE}"
    )
    print(
        f"Activities: "
        f"{len(activity_codes)}"
    )
    print(
        f"Candidatos identificados como "
        f"composições: {len(composition_codes)}"
    )
    print(
        f"Filhos no resolver baseline: "
        f"{len(resolver_child_codes)}"
    )
    print()
    print("Activities:")
    print(activity_codes)
    print()
    print("Composições identificadas:")
    print(
        sorted(composition_codes)
    )
    print()
    print("Filhos no baseline:")
    print(
        resolver_child_codes
    )
    print()
    print(
        f"Tempo repository otimizado: "
        f"{optimized_duration:.3f}s"
    )
    print(
        f"Tempo resolver baseline: "
        f"{resolver_duration:.3f}s"
    )

    optimized_metrics.print_report()


def test_optimized_repository_identifies_composition_children():
    """
    Verifica que os generic_item retornados pela API de activities
    podem ser identificados como composições pelo endpoint tradicional.
    """

    api_client = CompositionApiClient()

    repository = OptimizedCompositionRepository(
        api_client=api_client,
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    result = repository.get_child_codes_by_composition_codes(
        [ROOT_COMPOSITION_CODE]
    )

    activity_codes = result[ROOT_COMPOSITION_CODE]

    assert len(activity_codes) == 12

    compositions = api_client.get_compositions_by_codes(
        activity_codes
    )

    composition_codes = {
        str(composition["generic_item"])
        for composition in compositions
    }

    assert composition_codes == set(activity_codes)

    print()
    print("=== IDENTIFICAÇÃO DE COMPOSIÇÕES ===")
    print(
        f"Activities: "
        f"{len(activity_codes)}"
    )
    print(
        f"Composições: "
        f"{len(composition_codes)}"
    )
    print(
        f"Códigos de composição: "
        f"{sorted(composition_codes)}"
    )


def test_optimized_repository_preserves_activity_order():
    """
    Verifica que o repository preserva a ordem das relações
    retornadas pela API, removendo somente duplicidades.
    """

    api_client = CompositionApiClient()

    repository = OptimizedCompositionRepository(
        api_client=api_client,
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    result = (
        repository
        .get_child_codes_by_composition_codes(
            [ROOT_COMPOSITION_CODE]
        )
    )

    activity_codes = result[
        ROOT_COMPOSITION_CODE
    ]

    expected_codes = [
        "0407819",
        "3807864",
        "1107892",
        "1106057",
        "1619004",
        "1619003",
        "0919079",
        "4805751",
        "3107997",
        "0903848",
        "0909617",
        "4815671",
    ]

    assert activity_codes == expected_codes


def test_optimized_repository_reproduces_complete_tree_structure():
    """
    Compara todas as relações pai → filho da árvore completa
    entre o resolver baseline e a descoberta otimizada.
    """

    resolver_metrics = ApiQueryMetrics()

    resolver_api_client = CompositionApiClient(
        metrics=resolver_metrics,
    )

    composition_repository = CompositionRepository(
        api_client=resolver_api_client,
    )

    resolver = CompositionResolver(
        repository=composition_repository,
    )

    resolver_start = perf_counter()

    baseline_tree = resolver.resolve_tree(
        ROOT_COMPOSITION_CODE
    )

    resolver_duration = (
        perf_counter()
        - resolver_start
    )

    resolver_edges = _get_tree_edges(
        baseline_tree
    )

    optimized_metrics = ApiQueryMetrics()

    optimized_api_client = CompositionApiClient(
        metrics=optimized_metrics,
    )

    optimized_repository = OptimizedCompositionRepository(
        api_client=optimized_api_client,
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    optimized_start = perf_counter()

    optimized_edges = _discover_optimized_tree_edges(
        optimized_repository=optimized_repository,
        api_client=optimized_api_client,
        root_code=ROOT_COMPOSITION_CODE,
    )

    optimized_duration = (
        perf_counter()
        - optimized_start
    )

    only_in_resolver = (
        resolver_edges
        - optimized_edges
    )

    only_in_optimized = (
        optimized_edges
        - resolver_edges
    )

    print()
    print("=== COMPARAÇÃO COMPLETA DA ÁRVORE ===")
    print(
        f"Composição: "
        f"{ROOT_COMPOSITION_CODE}"
    )
    print(
        f"Data base da composição: "
        f"{COMPOSITION_DATA_BASE}"
    )
    print()
    print(
        f"Relações baseline: "
        f"{len(resolver_edges)}"
    )
    print(
        f"Relações otimizadas: "
        f"{len(optimized_edges)}"
    )
    print(
        f"Somente baseline: "
        f"{len(only_in_resolver)}"
    )
    print(
        f"Somente otimizado: "
        f"{len(only_in_optimized)}"
    )
    print()
    print(
        f"Tempo baseline: "
        f"{resolver_duration:.3f}s"
    )
    print(
        f"Tempo otimizado: "
        f"{optimized_duration:.3f}s"
    )

    if only_in_resolver:
        print()
        print(
            "=== RELAÇÕES SOMENTE NO BASELINE ==="
        )

        for edge in sorted(
            only_in_resolver
        ):
            print(edge)

    if only_in_optimized:
        print()
        print(
            "=== RELAÇÕES SOMENTE NO OTIMIZADO ==="
        )

        for edge in sorted(
            only_in_optimized
        ):
            print(edge)

    print()
    print("=== MÉTRICAS DO BASELINE ===")
    resolver_metrics.print_report()

    print()
    print("=== MÉTRICAS DO OTIMIZADO ===")
    optimized_metrics.print_report()

    assert not only_in_resolver
    assert not only_in_optimized
    assert resolver_edges == optimized_edges


def test_optimized_repository_uses_only_tf_transports():
    """
    Garante que somente transportes do grupo TF sejam utilizados
    como relações estruturais pelo repository otimizado.
    """

    api_client = CompositionApiClient()

    repository = OptimizedCompositionRepository(
        api_client=api_client,
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    children = (
        repository
        .get_child_codes_by_composition_codes(
            ["0407819"]
        )
    )

    assert "0407819" in children

    assert "5914655" in children[
        "0407819"
    ]

    assert "5914449" not in children[
        "0407819"
    ]

    assert "5914464" not in children[
        "0407819"
    ]

    assert "5914479" not in children[
        "0407819"
    ]


def test_optimized_resolver_reproduces_complete_tree_structure():
    """
    Compara a árvore construída pelo resolver otimizado
    com a árvore construída pelo resolver baseline.

    ```
    Além das relações, compara todas as referências que criaram
    as ocorrências dos nós filhos.
    """

    resolver_metrics = ApiQueryMetrics()

    baseline_api_client = CompositionApiClient(
        metrics=resolver_metrics,
    )

    baseline_repository = CompositionRepository(
        api_client=baseline_api_client,
    )

    baseline_resolver = CompositionResolver(
        repository=baseline_repository,
    )

    baseline_start = perf_counter()

    baseline_tree = (
        baseline_resolver.resolve_tree(
            ROOT_COMPOSITION_CODE
        )
    )

    baseline_duration = (
        perf_counter()
        - baseline_start
    )

    optimized_metrics = ApiQueryMetrics()

    optimized_api_client = CompositionApiClient(
        metrics=optimized_metrics,
    )

    optimized_repository = CompositionRepository(
        api_client=optimized_api_client,
    )

    optimized_structure_repository = (
        OptimizedCompositionRepository(
            api_client=optimized_api_client,
            composition_data_base=COMPOSITION_DATA_BASE,
        )
    )

    optimized_resolver = CompositionResolver(
        repository=optimized_repository,
        optimized_repository=(
            optimized_structure_repository
        ),
    )

    optimized_start = perf_counter()

    optimized_tree = (
        optimized_resolver
        .resolve_tree_optimized(
            ROOT_COMPOSITION_CODE
        )
    )

    optimized_duration = (
        perf_counter()
        - optimized_start
    )

    baseline_edges = _get_tree_edges(
        baseline_tree
    )

    optimized_edges = _get_tree_edges(
        optimized_tree
    )

    baseline_references = (
        _get_tree_reference_data(
            baseline_tree
        )
    )

    optimized_references = (
        _get_tree_reference_data(
            optimized_tree
        )
    )

    only_in_baseline = (
        baseline_edges
        - optimized_edges
    )

    only_in_optimized = (
        optimized_edges
        - baseline_edges
    )

    print()
    print("=== RESOLVER BASELINE ===")
    print(
        f"Relações: "
        f"{len(baseline_edges)}"
    )
    print(
        f"Referências: "
        f"{len(baseline_references)}"
    )
    print(
        f"Tempo: "
        f"{baseline_duration:.3f}s"
    )

    print()
    print("=== RESOLVER OTIMIZADO ===")
    print(
        f"Relações: "
        f"{len(optimized_edges)}"
    )
    print(
        f"Referências: "
        f"{len(optimized_references)}"
    )
    print(
        f"Tempo: "
        f"{optimized_duration:.3f}s"
    )

    print()
    print("=== COMPARAÇÃO ===")
    print(
        f"Relações baseline: "
        f"{len(baseline_edges)}"
    )
    print(
        f"Relações otimizado: "
        f"{len(optimized_edges)}"
    )
    print(
        f"Referências baseline: "
        f"{len(baseline_references)}"
    )
    print(
        f"Referências otimizado: "
        f"{len(optimized_references)}"
    )
    print(
        f"Somente baseline: "
        f"{len(only_in_baseline)}"
    )
    print(
        f"Somente otimizado: "
        f"{len(only_in_optimized)}"
    )

    if only_in_baseline:
        print()
        print(
            "=== RELAÇÕES SOMENTE NO BASELINE ==="
        )

        for edge in sorted(
            only_in_baseline
        ):
            print(edge)

    if only_in_optimized:
        print()
        print(
            "=== RELAÇÕES SOMENTE NO OTIMIZADO ==="
        )

        for edge in sorted(
            only_in_optimized
        ):
            print(edge)

    assert baseline_edges == optimized_edges
    assert baseline_references == optimized_references


def test_debug_missing_composition_codes():
    """
    Investiga códigos identificados pelo resolver tradicional
    que precisam ser analisados em relação aos endpoints otimizados.

    ```
    Este teste é diagnóstico e utiliza somente componentes de produção.
    """

    api_client = CompositionApiClient()

    codes = [
        "5914655",
        "5914647",
        "5914675",
    ]

    print()
    print(
        "=== INVESTIGAÇÃO DOS CÓDIGOS ==="
    )

    for code in codes:
        print()
        print(f"=== {code} ===")

        compositions = (
            api_client.get_compositions_by_codes(
                [code]
            )
        )

        print(
            "Endpoint /composicoes/:"
        )
        print(
            f"Quantidade: "
            f"{len(compositions)}"
        )

        for composition in compositions:
            print(composition)

        activities = (
            api_client
            .get_composition_activities_by_codes(
                [code],
                data_base=COMPOSITION_DATA_BASE,
            )
        )

        print()
        print(
            "Endpoint /compositions/activities/:"
        )
        print(
            f"Quantidade: "
            f"{len(activities)}"
        )

        for activity in activities:
            print(activity)

def test_debug_missing_edges():
    """
    Investiga as relações existentes na árvore baseline
    para um conjunto específico de composições.
    """

    api_client = CompositionApiClient()

    parent_codes = [
        "0407819",
        "3807864",
        "1107892",
        "1106057",
        "1619003",
        "1619004",
    ]

    print()
    print(
        "=== INVESTIGAÇÃO DAS RELAÇÕES ==="
    )

    activities = (
        api_client
        .get_composition_activities_by_codes(
            parent_codes,
            data_base=COMPOSITION_DATA_BASE,
        )
    )

    activities_by_parent = {}

    for activity in activities:
        parent_code = str(
            activity["composition_code"]
        )

        child_code = str(
            activity["generic_item"]
        )

        activities_by_parent.setdefault(
            parent_code,
            [],
        ).append(child_code)

    for parent_code in parent_codes:
        children = activities_by_parent.get(
            parent_code,
            [],
        )

        print()
        print(
            f"=== {parent_code} ==="
        )
        print(
            f"Activities encontradas: "
            f"{len(children)}"
        )

        for child_code in children:
            print(
                f"  → {child_code}"
            )


def test_debug_transport_composition_children():
    """
    Exibe os registros retornados pelo endpoint otimizado
    de transportes para um conjunto de composições.
    """

    api_client = CompositionApiClient()

    parent_codes = [
        "0407819",
        "3807864",
        "3107997",
        "2009619",
        "0903818",
        "0903860",
        "0909620",
        "1106057",
        "1107892",
        "1109622",
        "1109669",
        "1109675",
        "1109697",
        "1619003",
        "1619004",
    ]

    print()
    print(
        "=== INVESTIGAÇÃO DO ENDPOINT DE TRANSPORTES ==="
    )

    transports = (
        api_client
        .get_composition_transports_by_codes(
            parent_codes,
            data_base=COMPOSITION_DATA_BASE,
        )
    )

    for transport in transports:
        print(transport)


def test_optimized_transport_endpoint_returns_missing_compositions():
    """
    Verifica quais registros do endpoint de transports
    podem corresponder a composições.
    """

    api_client = CompositionApiClient()

    parent_codes = [
        "0407819",
        "3807864",
        "3107997",
        "2009619",
        "0903818",
        "0903860",
        "0909620",
        "1106057",
        "1107892",
        "1109622",
        "1109669",
        "1109675",
        "1109697",
        "1619003",
        "1619004",
    ]

    transports = (
        api_client
        .get_composition_transports_by_codes(
            parent_codes,
            data_base=COMPOSITION_DATA_BASE,
        )
    )

    print()
    print(
        "=== TRANSPORTES ENCONTRADOS ==="
    )
    print(
        f"Quantidade: "
        f"{len(transports)}"
    )

    for transport in transports:
        print(transport)


def test_debug_transport_structure():
    """
    Compara os registros de transportes retornados pela API
    com os códigos que também existem como composições.
    """

    api_client = CompositionApiClient()

    parent_codes = [
        "0407819",
        "3807864",
        "3107997",
        "2009619",
        "0903818",
        "0903860",
        "0909620",
        "1106057",
        "1107892",
        "1109622",
        "1109669",
        "1109675",
        "1109697",
        "1619003",
        "1619004",
    ]

    transports = (
        api_client
        .get_composition_transports_by_codes(
            parent_codes,
            data_base=COMPOSITION_DATA_BASE,
        )
    )

    transport_codes = [
        str(transport["generic_item"])
        for transport in transports
    ]

    compositions = (
        api_client.get_compositions_by_codes(
            transport_codes
        )
    )

    composition_codes = {
        str(composition["generic_item"])
        for composition in compositions
    }

    print()
    print(
        "=== TRANSPORTES QUE TAMBÉM SÃO COMPOSIÇÕES ==="
    )

    for transport in transports:
        generic_item = str(
            transport["generic_item"]
        )

        if generic_item not in composition_codes:
            continue

        print(
            transport["composition_code"],
            "|",
            transport["input_group"],
            "|",
            generic_item,
            "|",
            transport["proprietary_item"],
        )


def test_optimized_resolver_calculates_root_composition():
    """
    Verifica se a composição 0919013 produz o custo unitário
    histórico esperado quando a árvore é construída pelo
    resolver otimizado.

    ```
    O valor de referência esperado é:

        105890.00
    """

    calculation_context = (
        _build_calculation_context()
    )

    composition_api_client = CompositionApiClient()

    composition_repository = CompositionRepository(
        api_client=composition_api_client,
    )

    optimized_repository = (
        OptimizedCompositionRepository(
            api_client=composition_api_client,
            composition_data_base=COMPOSITION_DATA_BASE,
        )
    )

    resolver = CompositionResolver(
        repository=composition_repository,
        optimized_repository=optimized_repository,
    )

    tree = resolver.resolve_tree_optimized(
        ROOT_COMPOSITION_CODE
    )

    monetary_value_api_client = (
        MonetaryValueApiClient()
    )

    monetary_value_repository = (
        MonetaryValueRepository(
            api_client=monetary_value_api_client,
        )
    )

    _load_monetary_cache(
        tree=tree,
        calculation_context=calculation_context,
        monetary_value_repository=(
            monetary_value_repository
        ),
    )

    calculator = _build_composition_calculator(
        calculation_context=calculation_context,
        monetary_value_repository=(
            monetary_value_repository
        ),
    )

    result = calculator.calculate(tree)

    expected_value = Decimal(
        "105890.00"
    )

    print()
    print("=== CÁLCULO OTIMIZADO ===")
    print(
        f"Composição: "
        f"{result.composition_code}"
    )
    print(
        f"Resultado calculado: "
        f"{result.composition_unit_cost}"
    )
    print(
        f"Resultado esperado: "
        f"{expected_value}"
    )
    print(
        f"Diferença: "
        f"{result.composition_unit_cost - expected_value}"
    )

    print()
    print("=== DETALHAMENTO ===")
    print(
        f"Equipamentos: "
        f"{result.equipment_cost}"
    )
    print(
        f"Mão de obra: "
        f"{result.labor_cost}"
    )
    print(
        f"FIC: "
        f"{result.fic_cost}"
    )
    print(
        f"Operacional: "
        f"{result.operational_unit}"
    )
    print(
        f"Materiais: "
        f"{result.materials_cost}"
    )
    print(
        f"Atividades auxiliares: "
        f"{result.auxiliary_cost}"
    )
    print(
        f"Tempos fixos: "
        f"{result.fixed_time_cost}"
    )
    print(
        f"Total bruto: "
        f"{result.composition_total_raw}"
    )

    assert (
        result.composition_code
        == ROOT_COMPOSITION_CODE
    )

    assert (
        result.composition_unit_cost
        == expected_value
    )