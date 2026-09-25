from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from time import perf_counter
from collections import Counter

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
from app.services.monetary_value_resolver import MonetaryValueResolver
from app.services.operational_cost_calculator import (
OperationalCostCalculator,
)


COMPOSITION_CODE = "0919013"
COMPOSITION_DATA_BASE = "2021-10-01"
MONETARY_DATA_BASE = date(2021, 10, 1)

def round_2(value: Decimal) -> Decimal:
    """Arredonda um valor para duas casas decimais."""
    return value.quantize(
    Decimal("0.01"),
    rounding=ROUND_HALF_UP,
    )

def round_4(value: Decimal) -> Decimal:
    """Arredonda um valor para quatro casas decimais."""
    return value.quantize(
    Decimal("0.0001"),
    rounding=ROUND_HALF_UP,
    )

def test_composition_0919013_regression() -> None:
    """
    Verifica a regressão do cálculo da composição 0919013.

    ```
    Este teste utiliza a API real e, portanto, é um teste de integração.
    """
    metrics = ApiQueryMetrics()

    composition_api_client = CompositionApiClient(
        metrics=metrics,
    )

    monetary_value_api_client = MonetaryValueApiClient(
        metrics=metrics,
    )

    composition_repository = CompositionRepository(
        api_client=composition_api_client,
    )

    monetary_value_repository = MonetaryValueRepository(
        api_client=monetary_value_api_client,
    )

    calculation_context = CalculationContext(
        methodology="SC",
        source_file_uf="DF",
        source_file_data_base=MONETARY_DATA_BASE,
        type_system="ON",
    )

    composition_resolver = CompositionResolver(
        repository=composition_repository,
    )


    start = perf_counter()

    composition_tree = composition_resolver.resolve_tree(
        COMPOSITION_CODE,
    )

    tree_resolution_time = perf_counter() - start

    start = perf_counter()

    codes_by_group = (
        composition_tree.monetary_item_codes_by_group
    )

    code_discovery_time = perf_counter() - start

    start = perf_counter()

    monetary_value_repository.load_cache(
        codes_by_group=codes_by_group,
        type_system=calculation_context.type_system,
        source_file_uf=calculation_context.source_file_uf,
        source_file_data_base=(
            calculation_context.source_file_data_base
        ),
    )

    cache_load_time = perf_counter() - start

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

    composition_calculator = CompositionCalculator(
        calculation_context=calculation_context,
        equipment_calculator=equipment_calculator,
        labor_calculator=labor_calculator,
        material_calculator=material_calculator,
        operational_cost_calculator=operational_cost_calculator,
        fic_calculator=fic_calculator,
        round_2=round_2,
        round_4=round_4,
    )

    start = perf_counter()

    result = composition_calculator.calculate(
        composition_tree,
    )

    calculation_time = perf_counter() - start

    print()
    print("=" * 70)
    print(f"PERFIL DE EXECUÇÃO — COMPOSIÇÃO {COMPOSITION_CODE}")
    print("=" * 70)

    print()
    print("ETAPAS DO MOTOR")
    print("-" * 70)
    print(
        f"Resolução da árvore:       {tree_resolution_time:>8.3f} s"
    )
    print(
        f"Descoberta dos códigos:    {code_discovery_time:>8.3f} s"
    )
    print(
        f"Carregamento do cache:     {cache_load_time:>8.3f} s"
    )
    print(
        f"Cálculo da composição:     {calculation_time:>8.3f} s"
    )

    engine_time = (
        tree_resolution_time
        + code_discovery_time
        + cache_load_time
        + calculation_time
    )

    print("-" * 70)
    print(
        f"Tempo das etapas medidas:   {engine_time:>8.3f} s"
    )

    print()
    print("CÓDIGOS MONETÁRIOS")
    print("-" * 70)

    for group, codes in codes_by_group.items():
        print(
            f"{group}: {len(codes):>3} códigos"
        )

    print(
        f"Total de códigos únicos:    "
        f"{len(composition_tree.monetary_item_codes):>3}"
    )

    print()
    print("ÁRVORE")
    print("-" * 70)
    print(
        f"Quantidade de nós:          "
        f"{len(composition_tree):>3}"
    )

    print()
    print("RESULTADO")
    print("-" * 70)
    print(
        f"Custo unitário calculado:  "
        f"R$ {result.composition_unit_cost}"
    )

    print()
    print("REQUISIÇÕES HTTP")
    print("-" * 70)

    summary = metrics.summary()

    print()
    print("DETALHAMENTO DOS REQUESTS DE COMPOSIÇÃO")
    print("-" * 70)

    for index, record in enumerate(
        metrics.composition_records,
        start=1,
    ):
        print(
            f"Request {index}:"
        )
        print(
            f"  Tempo:        {record.duration_seconds:.3f} s"
        )
        print(
            f"  Resultado:    {record.result_count}"
        )
        print(
            f"  Parâmetros:   {record.params}"
        )

    print(
        f"Requisições de composição:  "
        f"{summary['composition_requests']:>3}"
    )
    print(
        f"Requisições monetárias:     "
        f"{summary['monetary_value_requests']:>3}"
    )
    print(
        f"Requisições HTTP totais:    "
        f"{summary['total_requests']:>3}"
    )

    print()
    print("TEMPO HTTP")
    print("-" * 70)

    print(
        f"Tempo composição:           "
        f"{summary['composition_duration_seconds']:>8.3f} s"
    )
    print(
        f"Tempo valores monetários:   "
        f"{summary['monetary_value_duration_seconds']:>8.3f} s"
    )
    print(
        f"Tempo HTTP total:            "
        f"{summary['total_duration_seconds']:>8.3f} s"
    )

    print()
    print("=" * 70)

    assert result.composition_code == COMPOSITION_CODE
    assert result.composition_unit_cost == Decimal("105890.00")

    composition_code_counts = Counter(
    node.composition.generic_item
    for node in composition_tree.walk()
    )

    print()
    print("COMPOSIÇÕES NA ÁRVORE")
    print("-" * 70)
    print(
        f"Composições distintas: "
        f"{len(composition_code_counts)}"
    )
    print(
        f"Total de nós:           "
        f"{len(composition_tree)}"
    )

    for code, count in composition_code_counts.most_common():
        print(
            f"{code}: {count} ocorrência(s)"
        )

def test_composition_0919013_optimized_regression() -> None:
    """
    Verifica se o cálculo da composição 0919013 permanece
    idêntico utilizando o resolver otimizado.

    O valor de referência esperado é:

        105890.00
    """

    # ============================================================
    # CONTEXTO
    # ============================================================

    calculation_context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
        type_system="ON",
    )

    # ============================================================
    # CLIENTES E MÉTRICAS
    # ============================================================

    metrics = ApiQueryMetrics()

    composition_api_client = CompositionApiClient(
        metrics=metrics,
    )

    monetary_value_api_client = MonetaryValueApiClient(
        metrics=metrics,
    )

    # ============================================================
    # REPOSITÓRIOS
    # ============================================================

    composition_repository = CompositionRepository(
        api_client=composition_api_client,
    )

    optimized_repository = OptimizedCompositionRepository(
        api_client=composition_api_client,
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    monetary_value_repository = MonetaryValueRepository(
        api_client=monetary_value_api_client,
    )

    # ============================================================
    # RESOLVER OTIMIZADO
    # ============================================================

    composition_resolver = CompositionResolver(
        repository=composition_repository,
        optimized_repository=optimized_repository,
    )

    start = perf_counter()

    composition_tree = (
        composition_resolver.resolve_tree_optimized(
            COMPOSITION_CODE,
        )
    )

    tree_resolution_time = (
        perf_counter() - start
    )

    # ============================================================
    # CÓDIGOS MONETÁRIOS
    # ============================================================

    start = perf_counter()

    codes_by_group = (
        composition_tree.monetary_item_codes_by_group
    )

    code_discovery_time = (
        perf_counter() - start
    )

    # ============================================================
    # CACHE MONETÁRIO
    # ============================================================

    start = perf_counter()

    monetary_value_repository.load_cache(
        codes_by_group=codes_by_group,
        type_system=calculation_context.type_system,
        source_file_uf=calculation_context.source_file_uf,
        source_file_data_base=(
            calculation_context.source_file_data_base
        ),
    )

    cache_load_time = (
        perf_counter() - start
    )

    # ============================================================
    # RESOLVER MONETÁRIO
    # ============================================================

    monetary_value_resolver = MonetaryValueResolver(
        repository=monetary_value_repository,
    )

    # ============================================================
    # CALCULADORES
    # ============================================================

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

    operational_cost_calculator = (
        OperationalCostCalculator()
    )

    fic_calculator = FicCalculator()

    # ============================================================
    # CALCULATOR
    # ============================================================

    composition_calculator = CompositionCalculator(
        calculation_context=calculation_context,
        equipment_calculator=equipment_calculator,
        labor_calculator=labor_calculator,
        material_calculator=material_calculator,
        operational_cost_calculator=operational_cost_calculator,
        fic_calculator=fic_calculator,
        round_2=round_2,
        round_4=round_4,
    )

    # ============================================================
    # CÁLCULO
    # ============================================================

    start = perf_counter()

    result = composition_calculator.calculate(
        composition_tree,
    )

    calculation_time = (
        perf_counter() - start
    )

    # ============================================================
    # RESULTADO
    # ============================================================

    expected_value = Decimal(
        "105890.00"
    )

    print()
    print("=" * 70)
    print(
        "CÁLCULO OTIMIZADO — "
        f"COMPOSIÇÃO {COMPOSITION_CODE}"
    )
    print("=" * 70)

    print()
    print("ETAPAS DO MOTOR")
    print("-" * 70)

    print(
        f"Resolução da árvore:       "
        f"{tree_resolution_time:>8.3f} s"
    )

    print(
        f"Descoberta dos códigos:    "
        f"{code_discovery_time:>8.3f} s"
    )

    print(
        f"Carregamento do cache:     "
        f"{cache_load_time:>8.3f} s"
    )

    print(
        f"Cálculo da composição:     "
        f"{calculation_time:>8.3f} s"
    )

    print()
    print("CÓDIGOS MONETÁRIOS")
    print("-" * 70)

    for group, codes in codes_by_group.items():
        print(
            f"{group}: {len(codes):>3} códigos"
        )

    print(
        f"Total de códigos únicos:    "
        f"{len(composition_tree.monetary_item_codes):>3}"
    )

    print()
    print("ÁRVORE")
    print("-" * 70)

    print(
        f"Quantidade de nós:          "
        f"{len(composition_tree):>3}"
    )

    print()
    print("RESULTADO")
    print("-" * 70)

    print(
        f"Custo unitário calculado:  "
        f"R$ {result.composition_unit_cost}"
    )

    print()
    print("REQUISIÇÕES HTTP")
    print("-" * 70)

    metrics.print_report()

    print()
    print("=" * 70)

    # ============================================================
    # VALIDAÇÕES
    # ============================================================

    assert result.composition_code == (
        COMPOSITION_CODE
    )

    assert result.composition_unit_cost == (
        expected_value
    )