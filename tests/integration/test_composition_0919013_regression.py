from datetime import date
from decimal import Decimal

from app.domain.calculation_context import CalculationContext
from app.infrastructure.composition_api_client import CompositionApiClient
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.repositories.monetary_value_repository import MonetaryValueRepository
from app.repositories.optimized_composition_repository import OptimizedCompositionRepository
from app.services.composition_calculator import CompositionCalculator
from app.services.composition_resolver import CompositionResolver
from app.services.equipment_calculator import EquipmentCalculator
from app.services.fic_calculator import FicCalculator
from app.services.labor_calculator import LaborCalculator
from app.services.material_calculator import MaterialCalculator
from app.services.operational_cost_calculator import OperationalCostCalculator
from app.tools.debug.debug_query_metrics import round_2, round_4
from app.services.monetary_value_resolver import MonetaryValueResolver

COMPOSITION_CODE = "0919013"
COMPOSITION_DATA_BASE = "2021-10-01"
MONETARY_DATA_BASE = date(2021, 10, 1)

def _build_composition_calculator(
    calculation_context: CalculationContext,
    monetary_value_repository: MonetaryValueRepository,
) -> CompositionCalculator:
    """
    Cria um CompositionCalculator completo utilizando
    o contexto e o repositório monetário informados.
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

    operational_cost_calculator = (
        OperationalCostCalculator()
    )

    fic_calculator = FicCalculator()

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

def _build_calculation_context() -> CalculationContext:
    """
    Retorna o contexto utilizado na regressão da composição 0919013.
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
    Carrega no cache os valores monetários necessários
    para calcular a árvore.
    """

    monetary_value_repository.load_cache(
        codes_by_group=(
            tree.monetary_item_codes_by_group
        ),
        type_system=(
            calculation_context.type_system
        ),
        source_file_uf=(
            calculation_context.source_file_uf
        ),
        source_file_data_base=(
            calculation_context.source_file_data_base
        ),
    )

def test_composition_0919013_baseline_regression() -> None:
    """
    Garante que o caminho baseline continua produzindo
    o valor histórico conhecido da composição 0919013.
    """

    composition_api_client = CompositionApiClient()

    monetary_value_api_client = MonetaryValueApiClient()

    composition_repository = CompositionRepository(
        api_client=composition_api_client,
    )

    monetary_value_repository = MonetaryValueRepository(
        api_client=monetary_value_api_client,
    )

    calculation_context = _build_calculation_context()

    resolver = CompositionResolver(
        repository=composition_repository,
    )

    tree = resolver.resolve_tree(
        COMPOSITION_CODE,
    )

    _load_monetary_cache(
        tree=tree,
        calculation_context=calculation_context,
        monetary_value_repository=monetary_value_repository,
    )

    calculator = _build_composition_calculator(
        calculation_context=calculation_context,
        monetary_value_repository=monetary_value_repository,
    )

    result = calculator.calculate(
        tree,
    )

    assert result.composition_code == (
        COMPOSITION_CODE
    )

    assert result.composition_unit_cost == (
        Decimal("105890.00")
    )

def test_composition_0919013_optimized_regression() -> None:
    """
    Garante que o caminho otimizado continua produzindo
    o valor histórico conhecido da composição 0919013.
    """

    composition_api_client = CompositionApiClient()

    monetary_value_api_client = MonetaryValueApiClient()

    composition_repository = CompositionRepository(
        api_client=composition_api_client,
    )

    optimized_repository = (
        OptimizedCompositionRepository(
            api_client=composition_api_client,
            composition_data_base=COMPOSITION_DATA_BASE,
        )
    )

    monetary_value_repository = MonetaryValueRepository(
        api_client=monetary_value_api_client,
    )

    calculation_context = _build_calculation_context()

    resolver = CompositionResolver(
        repository=composition_repository,
        optimized_repository=optimized_repository,
    )

    tree = resolver.resolve_tree_optimized(
        COMPOSITION_CODE,
    )

    _load_monetary_cache(
        tree=tree,
        calculation_context=calculation_context,
        monetary_value_repository=monetary_value_repository,
    )

    calculator = _build_composition_calculator(
        calculation_context=calculation_context,
        monetary_value_repository=monetary_value_repository,
    )

    result = calculator.calculate(
        tree,
    )

    assert result.composition_code == (
        COMPOSITION_CODE
    )

    assert result.composition_unit_cost == (
        Decimal("105890.00")
    )

def _get_tree_result_data(
    result,
) -> tuple:
    """
    Retorna os componentes relevantes do resultado
    para comparação entre os resolvers.
    """

    return (
        result.composition_code,
        result.equipment_cost,
        result.labor_cost,
        result.fic_cost,
        result.operational_total,
        result.operational_unit,
        result.materials_cost,
        result.auxiliary_cost,
        result.fixed_time_cost,
        result.composition_total_raw,
        result.composition_unit_cost,
    )

def test_composition_0919013_baseline_and_optimized_are_identical() -> None:
    """
    Garante que o resolver otimizado produz exatamente
    o mesmo resultado econômico que o resolver baseline.
    """

    calculation_context = _build_calculation_context()

    # ============================================================
    # BASELINE
    # ============================================================

    baseline_composition_api_client = (
        CompositionApiClient()
    )

    baseline_monetary_value_api_client = (
        MonetaryValueApiClient()
    )

    baseline_composition_repository = (
        CompositionRepository(
            api_client=baseline_composition_api_client,
        )
    )

    baseline_monetary_value_repository = (
        MonetaryValueRepository(
            api_client=baseline_monetary_value_api_client,
        )
    )

    baseline_resolver = CompositionResolver(
        repository=baseline_composition_repository,
    )

    baseline_tree = (
        baseline_resolver.resolve_tree(
            COMPOSITION_CODE,
        )
    )

    _load_monetary_cache(
        tree=baseline_tree,
        calculation_context=calculation_context,
        monetary_value_repository=(
            baseline_monetary_value_repository
        ),
    )

    baseline_calculator = (
        _build_composition_calculator(
            calculation_context=calculation_context,
            monetary_value_repository=(
                baseline_monetary_value_repository
            ),
        )
    )

    baseline_result = (
        baseline_calculator.calculate(
            baseline_tree,
        )
    )

    # ============================================================
    # OTIMIZADO
    # ============================================================

    optimized_composition_api_client = (
        CompositionApiClient()
    )

    optimized_monetary_value_api_client = (
        MonetaryValueApiClient()
    )

    optimized_composition_repository = (
        CompositionRepository(
            api_client=optimized_composition_api_client,
        )
    )

    optimized_structure_repository = (
        OptimizedCompositionRepository(
            api_client=optimized_composition_api_client,
            composition_data_base=COMPOSITION_DATA_BASE,
        )
    )

    optimized_monetary_value_repository = (
        MonetaryValueRepository(
            api_client=optimized_monetary_value_api_client,
        )
    )

    optimized_resolver = CompositionResolver(
        repository=optimized_composition_repository,
        optimized_repository=optimized_structure_repository,
    )

    optimized_tree = (
        optimized_resolver.resolve_tree_optimized(
            COMPOSITION_CODE,
        )
    )

    _load_monetary_cache(
        tree=optimized_tree,
        calculation_context=calculation_context,
        monetary_value_repository=(
            optimized_monetary_value_repository
        ),
    )

    optimized_calculator = (
        _build_composition_calculator(
            calculation_context=calculation_context,
            monetary_value_repository=(
                optimized_monetary_value_repository
            ),
        )
    )

    optimized_result = (
        optimized_calculator.calculate(
            optimized_tree,
        )
    )

    # ============================================================
    # COMPARAÇÃO
    # ============================================================

    assert (
        _get_tree_result_data(
            baseline_result
        )
        ==
        _get_tree_result_data(
            optimized_result
        )
    )

    assert (
        optimized_result.composition_unit_cost
        == Decimal("105890.00")
    )