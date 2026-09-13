from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.domain.calculation_context import CalculationContext
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.repositories.monetary_value_repository import MonetaryValueRepository
from app.services.composition_calculator import CompositionCalculator
from app.services.composition_resolver import CompositionResolver
from app.services.equipment_calculator import EquipmentCalculator
from app.services.fic_calculator import FicCalculator
from app.services.labor_calculator import LaborCalculator
from app.services.material_calculator import MaterialCalculator
from app.services.monetary_value_resolver import MonetaryValueResolver
from app.services.operational_cost_calculator import OperationalCostCalculator


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


def test_composition_0919013_matches_api_value():
    composition_code = "0919013"

    context = CalculationContext(
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
        type_system="ON",
    )

    # Resolve a árvore da composição.
    composition_repository = CompositionRepository()
    composition_resolver = CompositionResolver(
        repository=composition_repository,
    )


    root = composition_resolver.resolve_tree(
        composition_code=composition_code,
    )

    # Carrega somente os valores monetários necessários
    # para a árvore da composição.
    monetary_value_repository = MonetaryValueRepository()

    monetary_value_repository.load_cache(
        codes_by_group=root.monetary_item_codes_by_group,
        type_system=context.type_system,
        source_file_uf=context.source_file_uf,
        source_file_data_base=context.source_file_data_base,
    )

    monetary_value_resolver = MonetaryValueResolver(
        repository=monetary_value_repository,
    )

    equipment_calculator = EquipmentCalculator(
        monetary_value_resolver=monetary_value_resolver,
        calculation_context=context,
    )

    labor_calculator = LaborCalculator(
        monetary_value_resolver=monetary_value_resolver,
        calculation_context=context,
    )

    material_calculator = MaterialCalculator(
        monetary_value_resolver=monetary_value_resolver,
        calculation_context=context,
    )

    calculator = CompositionCalculator(
        calculation_context=context,
        equipment_calculator=equipment_calculator,
        labor_calculator=labor_calculator,
        material_calculator=material_calculator,
        operational_cost_calculator=OperationalCostCalculator(),
        fic_calculator=FicCalculator(),
        round_2=round_2,
        round_4=round_4,
    )

    # Executa o cálculo completo da composição.
    result = calculator.calculate(root)

    # Consulta o endpoint:
    #
    # /valores-monetarios/
    #     ?generic_item=0919013
    #
    # Os demais filtros são aplicados abaixo para identificar
    # exatamente o valor correspondente ao contexto do cálculo.
    monetary_value_api_client = MonetaryValueApiClient()

    api_values = monetary_value_api_client.get_values(
        generic_item=composition_code,
    )

    matching_values = [
        value
        for value in api_values
        if value["type_system"] == context.type_system
        and value["source_file"]["uf"] == context.source_file_uf
        and value["source_file"]["data_base"]
        == context.source_file_data_base.isoformat()
    ]

    assert len(matching_values) == 1

    api_value = Decimal(
        str(matching_values[0]["monetary_value"])
    )

    # O valor calculado pelo motor deve ser igual
    # ao valor oficial disponibilizado pela API Django.
    print()
    print("=" * 60)
    print(f"Composição: {composition_code}")
    print(f"Valor calculado pelo motor: R$ {result.composition_unit_cost}")
    print(f"Valor retornado pela API Django: R$ {api_value}")
    print(f"Diferença: R$ {result.composition_unit_cost - api_value}")
    print("=" * 60)

    assert result.composition_unit_cost == api_value