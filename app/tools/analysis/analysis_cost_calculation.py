from decimal import Decimal, getcontext

from app.infrastructure.composition_api_client import CompositionApiClient
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient

from app.repositories.composition_repository import CompositionRepository

from app.services.composition_resolver import CompositionResolver
from app.services.composition_aggregator import CompositionAggregator
from app.services.composition_explosion import CompositionExplosion
from app.services.input_aggregator import InputAggregator


# Precisão elevada para evitar perda durante a explosão
getcontext().prec = 50


def decimal(value) -> Decimal:
    """
    Converte qualquer valor numérico para Decimal
    preservando a precisão.
    """
    if value is None:
        return Decimal("0")

    return Decimal(str(value))


def get_monetary_value(
    values: list[dict],
    classification: str,
    type_system: str = "ON",
) -> Decimal | None:
    """
    Localiza um valor monetário específico.

    Exemplo:

    Equipamento:
        classification = PR
        classification = IM

    Mão de obra:
        classification = CT

    Material:
        classification = CT
    """

    for item in values:

        if (
            item.get("classification") == classification
            and item.get("type_system") == type_system
        ):
            return decimal(item.get("monetary_value"))

    return None


def calculate_equipment_cost(
    resource,
    monetary_values: list[dict],
) -> dict:
    """
    Calcula o custo de um equipamento.

    Fórmula:

    Custo =
        Quantidade produtiva × Valor produtivo
        +
        Quantidade improdutiva × Valor improdutivo
    """

    productive_quantity = decimal(
        resource.productive_quantity
    )

    unproductive_quantity = decimal(
        resource.unproductive_quantity
    )

    productive_value = get_monetary_value(
        monetary_values,
        classification="PR",
        type_system="ON",
    )

    unproductive_value = get_monetary_value(
        monetary_values,
        classification="IM",
        type_system="ON",
    )

    if productive_value is None:
        raise ValueError(
            f"Valor produtivo não encontrado "
            f"para equipamento {resource.code}"
        )

    if unproductive_value is None:
        raise ValueError(
            f"Valor improdutivo não encontrado "
            f"para equipamento {resource.code}"
        )

    productive_cost = (
        productive_quantity
        * productive_value
    )

    unproductive_cost = (
        unproductive_quantity
        * unproductive_value
    )

    total_cost = (
        productive_cost
        + unproductive_cost
    )

    return {
        "productive_quantity": productive_quantity,
        "unproductive_quantity": unproductive_quantity,
        "productive_value": productive_value,
        "unproductive_value": unproductive_value,
        "productive_cost": productive_cost,
        "unproductive_cost": unproductive_cost,
        "total_cost": total_cost,
    }


def calculate_labor_cost(
    resource,
    monetary_values: list[dict],
) -> dict:
    """
    Calcula o custo de mão de obra.

    Fórmula:

        Custo = Quantidade × Valor
    """

    quantity = decimal(
        resource.quantity
    )

    value = get_monetary_value(
        monetary_values,
        classification="CT",
        type_system="ON",
    )

    if value is None:
        raise ValueError(
            f"Valor de mão de obra não encontrado "
            f"para {resource.code}"
        )

    total_cost = quantity * value

    return {
        "quantity": quantity,
        "value": value,
        "total_cost": total_cost,
    }


def calculate_material_cost(
    resource,
    monetary_values: list[dict],
) -> dict:
    """
    Calcula o custo de material.

    Fórmula:

        Custo = Quantidade × Valor
    """

    quantity = decimal(
        resource.quantity
    )

    value = None

    # Materiais normalmente possuem
    # sistema NA e classificação CT
    for item in monetary_values:

        if item.get("classification") == "CT":

            value = decimal(
                item.get("monetary_value")
            )

            break

    if value is None:
        raise ValueError(
            f"Valor de material não encontrado "
            f"para {resource.code}"
        )

    total_cost = quantity * value

    return {
        "quantity": quantity,
        "value": value,
        "total_cost": total_cost,
    }


def print_equipment_result(
    resource,
    result,
):
    print()
    print(
        f"{resource.code} | {resource.group} | "
        f"{resource.unit}"
    )

    print(
        f"Descrição: {resource.description}"
    )

    print(
        f"Quantidade produtiva: "
        f"{result['productive_quantity']}"
    )

    print(
        f"Quantidade improdutiva: "
        f"{result['unproductive_quantity']}"
    )

    print(
        f"Valor produtivo: "
        f"{result['productive_value']}"
    )

    print(
        f"Valor improdutivo: "
        f"{result['unproductive_value']}"
    )

    print(
        f"Custo produtivo: "
        f"{result['productive_cost']}"
    )

    print(
        f"Custo improdutivo: "
        f"{result['unproductive_cost']}"
    )

    print(
        f"CUSTO TOTAL: "
        f"{result['total_cost']}"
    )

    print(
        "-" * 100
    )


def print_labor_result(
    resource,
    result,
):
    print()
    print(
        f"{resource.code} | {resource.group} | "
        f"{resource.unit}"
    )

    print(
        f"Descrição: {resource.description}"
    )

    print(
        f"Quantidade: "
        f"{result['quantity']}"
    )

    print(
        f"Valor unitário: "
        f"{result['value']}"
    )

    print(
        f"CUSTO TOTAL: "
        f"{result['total_cost']}"
    )

    print(
        "-" * 100
    )


def print_material_result(
    resource,
    result,
):
    print()
    print(
        f"{resource.code} | {resource.group} | "
        f"{resource.unit}"
    )

    print(
        f"Descrição: {resource.description}"
    )

    print(
        f"Quantidade: "
        f"{result['quantity']}"
    )

    print(
        f"Valor unitário: "
        f"{result['value']}"
    )

    print(
        f"CUSTO TOTAL: "
        f"{result['total_cost']}"
    )

    print(
        "-" * 100
    )


def main():

    composition_code = "0919013"

    print()
    print("=" * 120)
    print(
        "TESTE DE CÁLCULO DE CUSTO"
    )
    print("=" * 120)

    print(
        f"Composição raiz: "
        f"{composition_code}"
    )

    print()

    # ================================================================
    # CLIENTE DA API DE COMPOSIÇÕES
    # ================================================================

    composition_api_client = (
        CompositionApiClient()
    )

    # ================================================================
    # REPOSITÓRIO
    # ================================================================

    composition_repository = (
        CompositionRepository(
            composition_api_client
        )
    )

    # ================================================================
    # SERVIÇOS DE EXPLOSÃO
    # ================================================================

    composition_resolver = (
        CompositionResolver(
            composition_repository
        )
    )

    composition_explosion = (
        CompositionExplosion(
            resolver=composition_resolver,
        )
    )

    # ================================================================
    # EXPLOSÃO DA COMPOSIÇÃO
    # ================================================================

    print(
        "Executando explosão da composição..."
    )

    explosion_result = (
        composition_explosion.explode(
            composition_code
        )
    )

    # ================================================================
    # AGREGAÇÃO DOS RECURSOS
    # ================================================================

    print(
        "Agregando recursos..."
    )

    input_aggregator = (
        InputAggregator()
    )

    resources = (
        input_aggregator.aggregate(
            explosion_result.root_node
        )
    )

    print(
        f"Recursos encontrados: "
        f"{len(resources)}"
    )

    # ================================================================
    # CLIENTE DE VALORES MONETÁRIOS
    # ================================================================

    monetary_value_client = (
        MonetaryValueApiClient()
    )

    # ================================================================
    # TOTAIS
    # ================================================================

    total_equipment_cost = Decimal("0")

    total_labor_cost = Decimal("0")

    total_material_cost = Decimal("0")

    # ================================================================
    # EQUIPAMENTOS
    # ================================================================

    print()
    print("=" * 120)
    print(
        "EQUIPAMENTOS"
    )
    print("=" * 120)

    equipment_resources = [
        resource
        for resource in resources
        if resource.group == "EQ"
    ]

    for resource in equipment_resources:

        monetary_values = (
            monetary_value_client
            .get_values_by_code(
                resource.code
            )
        )

        result = (
            calculate_equipment_cost(
                resource,
                monetary_values,
            )
        )

        total_equipment_cost += (
            result["total_cost"]
        )

        print_equipment_result(
            resource,
            result,
        )

    # ================================================================
    # MÃO DE OBRA
    # ================================================================

    print()
    print("=" * 120)
    print(
        "MÃO DE OBRA"
    )
    print("=" * 120)

    labor_resources = [
        resource
        for resource in resources
        if resource.group == "MO"
    ]

    for resource in labor_resources:

        monetary_values = (
            monetary_value_client
            .get_values_by_code(
                resource.code
            )
        )

        result = (
            calculate_labor_cost(
                resource,
                monetary_values,
            )
        )

        total_labor_cost += (
            result["total_cost"]
        )

        print_labor_result(
            resource,
            result,
        )

    # ================================================================
    # MATERIAIS
    # ================================================================

    print()
    print("=" * 120)
    print(
        "MATERIAIS"
    )
    print("=" * 120)

    material_resources = [
        resource
        for resource in resources
        if resource.group == "MA"
    ]

    for resource in material_resources:

        monetary_values = (
            monetary_value_client
            .get_values_by_code(
                resource.code
            )
        )

        result = (
            calculate_material_cost(
                resource,
                monetary_values,
            )
        )

        total_material_cost += (
            result["total_cost"]
        )

        print_material_result(
            resource,
            result,
        )

    # ================================================================
    # RESUMO FINAL
    # ================================================================

    total_cost = (
        total_equipment_cost
        + total_labor_cost
        + total_material_cost
    )

    print()
    print()
    print("=" * 120)
    print(
        "RESUMO FINAL DO CUSTO"
    )
    print("=" * 120)

    print()

    print(
        f"Equipamentos: "
        f"R$ {total_equipment_cost}"
    )

    print(
        f"Mão de obra: "
        f"R$ {total_labor_cost}"
    )

    print(
        f"Materiais: "
        f"R$ {total_material_cost}"
    )

    print()

    print(
        f"CUSTO TOTAL DA COMPOSIÇÃO: "
        f"R$ {total_cost}"
    )

    print()
    print("=" * 120)


if __name__ == "__main__":
    main()