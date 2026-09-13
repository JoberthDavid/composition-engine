from datetime import date
from decimal import Decimal, ROUND_HALF_UP

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

def round_2(
    value: Decimal,
    ) -> Decimal:
    """Arredonda um valor para duas casas decimais."""

    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

def round_4(
    value: Decimal,
    ) -> Decimal:
    """Arredonda um valor para quatro casas decimais."""

    return value.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )

def print_composition_tree(
    tree,
    ) -> None:
    """
    Imprime a árvore resolvida de composições.
    """

    print()
    print("=" * 80)
    print("ÁRVORE RESOLVIDA")
    print("-" * 80)

    def print_node(
        node,
        level: int = 0,
    ) -> None:

        indentation = "    " * level

        print(
            f"{indentation}- "
            f"{node.composition.code} | "
            f"{node.composition.generic_description}"
        )

        for child in node.children:
            print_node(
                child,
                level + 1,
            )

    print_node(
        tree.root
    )

def print_monetary_codes(
    codes_by_group: dict[str, set[str]],
    ) -> None:
    """
    Imprime os códigos monetários necessários,
    separados por grupo.
    """

    print()
    print("=" * 80)
    print("CÓDIGOS MONETÁRIOS NECESSÁRIOS")
    print("-" * 80)

    total_codes: set[str] = set()

    for group in ("EQ", "MO", "MA"):

        codes = codes_by_group.get(
            group,
            set(),
        )

        total_codes.update(
            codes
        )

        print(
            f"{group}: {len(codes)} códigos"
        )

        for code in sorted(codes):
            print(
                f"    {code}"
            )

    print("-" * 80)
    print(
        "Total de códigos monetários únicos:",
        len(total_codes),
    )

def print_result(
    result,
    ) -> None:
    """
    Imprime o resultado do cálculo da composição.
    """

    print()
    print("=" * 80)
    print("RESULTADO DO CÁLCULO")
    print("=" * 80)

    print(
        f"Código: "
        f"{result.composition_code}"
    )

    print(
        f"Descrição: "
        f"{result.node.composition.generic_description}"
    )

    print(
        f"Produção: "
        f"{result.production}"
    )

    print(
        f"Custo de equipamentos: "
        f"{result.equipment_cost}"
    )

    print(
        f"Custo de mão de obra: "
        f"{result.labor_cost}"
    )

    print(
        f"Custo operacional total: "
        f"{result.operational_total}"
    )

    print(
        f"Custo operacional unitário: "
        f"{result.operational_unit}"
    )

    print(
        f"Custo FIC: "
        f"{result.fic_cost}"
    )

    print(
        f"Custo de materiais: "
        f"{result.materials_cost}"
    )

    print(
        f"Custo de atividades auxiliares: "
        f"{result.auxiliary_cost}"
    )

    print(
        f"Custo de tempos fixos: "
        f"{result.fixed_time_cost}"
    )

    print(
        f"Custo total bruto: "
        f"{result.composition_total_raw}"
    )

    print(
        f"Custo unitário final: "
        f"{result.composition_unit_cost}"
    )

def main() -> None:
    """
    Executa o diagnóstico completo do cálculo da composição.
    """

    print()
    print("=" * 80)
    print(
        "DEBUG DO CÁLCULO COMPLETO - "
        f"COMPOSIÇÃO {COMPOSITION_CODE}"
    )
    print("=" * 80)

    # ============================================================
    # MÉTRICAS
    # ============================================================

    metrics = ApiQueryMetrics()

    # ============================================================
    # CLIENTES DE API
    # ============================================================

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

    monetary_value_repository = MonetaryValueRepository(
        api_client=monetary_value_api_client,
    )

    # ============================================================
    # CONTEXTO DO CÁLCULO
    # ============================================================

    calculation_context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(
            2021,
            10,
            1,
        ),
        type_system="ON",
    )

    # ============================================================
    # RESOLVER DE COMPOSIÇÕES
    # ============================================================

    composition_resolver = CompositionResolver(
        repository=composition_repository,
    )

    # ============================================================
    # RESOLUÇÃO DA ÁRVORE
    # ============================================================

    print()
    print(
        f"Resolvendo composição "
        f"{COMPOSITION_CODE}..."
    )

    composition_tree = composition_resolver.resolve_tree(
        COMPOSITION_CODE
    )

    print(
        "Árvore resolvida."
    )

    # ============================================================
    # CÓDIGOS MONETÁRIOS NECESSÁRIOS
    # ============================================================

    codes_by_group = (
        composition_tree.monetary_item_codes_by_group
    )

    print_monetary_codes(
        codes_by_group
    )

    # ============================================================
    # CARREGAMENTO SELETIVO DO CACHE
    # ============================================================

    print()
    print(
        "Carregando cache de valores monetários..."
    )

    monetary_value_repository.load_cache(
        codes_by_group=codes_by_group,
        type_system=calculation_context.type_system,
        source_file_uf=calculation_context.source_file_uf,
        source_file_data_base=(
            calculation_context.source_file_data_base
        ),
    )

    print(
        "Cache de valores monetários carregado."
    )

    print(
        "Códigos armazenados:",
        monetary_value_repository.cache_size,
    )

    print()
    print(
        "Contexto do cache:"
    )

    cache_context = (
        monetary_value_repository.cache_context
    )

    print(
        "UF:",
        cache_context["source_file_uf"],
    )

    print(
        "Data-base:",
        cache_context["source_file_data_base"],
    )

    print(
        "Type systems por grupo:"
    )

    for group in (
        "EQ",
        "MO",
        "MA",
    ):
        print(
            f"    {group}: "
            f"{MonetaryValueRepository.GROUP_TYPE_SYSTEMS[group]}"
        )

    # ============================================================
    # RESOLVER DE VALORES MONETÁRIOS
    # ============================================================

    monetary_value_resolver = MonetaryValueResolver(
        repository=monetary_value_repository,
    )

    # ============================================================
    # CALCULADORES ESPECIALIZADOS
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
    # CALCULADOR PRINCIPAL
    # ============================================================

    composition_calculator = CompositionCalculator(
        calculation_context=calculation_context,
        equipment_calculator=equipment_calculator,
        labor_calculator=labor_calculator,
        material_calculator=material_calculator,
        operational_cost_calculator=(
            operational_cost_calculator
        ),
        fic_calculator=fic_calculator,
        round_2=round_2,
        round_4=round_4,
    )

    # ============================================================
    # CÁLCULO
    # ============================================================

    print()
    print(
        f"Calculando composição "
        f"{COMPOSITION_CODE}..."
    )

    result = composition_calculator.calculate(
        composition_tree
    )

    print(
        "Cálculo concluído."
    )

    # ============================================================
    # RESULTADO
    # ============================================================

    print_result(
        result
    )

    # ============================================================
    # ÁRVORE
    # ============================================================

    print_composition_tree(
        composition_tree
    )

    # ============================================================
    # RELATÓRIO DE MÉTRICAS
    # ============================================================

    print()
    print("=" * 80)
    print("RELATÓRIO DE CONSULTAS À API")
    print("=" * 80)

    metrics.print_report()

    # ============================================================
    # RESUMO
    # ============================================================

    print()
    print("=" * 80)
    print("RESUMO DA EXECUÇÃO")
    print("=" * 80)

    print(
        f"Composição analisada: "
        f"{COMPOSITION_CODE}"
    )

    summary = metrics.summary()

    print(
        "Requisições de composições:",
        summary["composition_requests"],
    )

    print(
        "Requisições de valores monetários:",
        summary["monetary_value_requests"],
    )

    print(
        "Total de requisições HTTP:",
        summary["total_requests"],
    )

    print(
        "Códigos no cache:",
        monetary_value_repository.cache_size,
    )

    print(
        "Custo unitário final:",
        result.composition_unit_cost,
    )

    print("=" * 80)

if __name__ == "__main__":
    main()