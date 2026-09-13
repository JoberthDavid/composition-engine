from decimal import Decimal

from app.services.composition_explosion import (
    CompositionExplosion,
)
from app.infrastructure.monetary_value_api_client import (
    MonetaryValueApiClient,
)


COMPOSITION_CODE = "0919013"
OFFICIAL_VALUE = Decimal("105890.00")


class DetailedCostCalculator:
    """
    Serviço auxiliar de teste para calcular o custo detalhado
    de cada recurso consolidado da composição.

    Este serviço existe apenas para diagnóstico e validação
    do motor de composição.
    """

    ON = "ON"
    NA = "NA"

    def __init__(
        self,
        monetary_value_client: MonetaryValueApiClient | None = None,
    ) -> None:
        self.monetary_value_client = (
            monetary_value_client
            if monetary_value_client is not None
            else MonetaryValueApiClient()
        )

    def calculate_resource_cost(self, resource) -> dict:
        """
        Calcula o custo individual de um recurso consolidado.
        """

        values = self.monetary_value_client.get_values_by_code(
            resource.code
        )

        if not values:
            raise ValueError(
                f"Nenhum valor monetário encontrado para "
                f"o recurso {resource.code}."
            )

        if resource.is_equipment():
            return self._calculate_equipment_cost(
                resource=resource,
                values=values,
            )

        if resource.is_workman():
            return self._calculate_workman_cost(
                resource=resource,
                values=values,
            )

        if resource.is_material():
            return self._calculate_material_cost(
                resource=resource,
                values=values,
            )

        raise ValueError(
            f"Grupo de recurso não suportado: "
            f"{resource.group}"
        )

    def _calculate_equipment_cost(
        self,
        resource,
        values: list[dict],
    ) -> dict:
        """
        Calcula o custo de equipamento.

        O recurso já possui as quantidades produtiva
        e improdutiva agregadas.
        """

        official_value = self._find_value(
            values=values,
            type_system=self.ON,
            classification="",
            group="",
            preferred_classifications={"PR", "IM"},
        )

        productive_price = self._find_equipment_price(
            values=values,
            classification="PR",
        )

        unproductive_price = self._find_equipment_price(
            values=values,
            classification="IM",
        )

        productive_cost = (
            resource.productive_quantity
            * productive_price
        )

        unproductive_cost = (
            resource.unproductive_quantity
            * unproductive_price
        )

        total_cost = (
            productive_cost
            + unproductive_cost
        )

        return {
            "code": resource.code,
            "group": resource.group,
            "description": resource.description,
            "unit": resource.unit,
            "quantity": (
                resource.productive_quantity
                + resource.unproductive_quantity
            ),
            "productive_quantity": resource.productive_quantity,
            "unproductive_quantity": resource.unproductive_quantity,
            "productive_price": productive_price,
            "unproductive_price": unproductive_price,
            "productive_cost": productive_cost,
            "unproductive_cost": unproductive_cost,
            "total_cost": total_cost,
        }

    def _calculate_workman_cost(
        self,
        resource,
        values: list[dict],
    ) -> dict:
        """
        Calcula o custo de mão de obra.
        """

        price = self._find_labor_material_price(
            values=values,
            resource_group="MO",
        )

        total_cost = resource.quantity * price

        return {
            "code": resource.code,
            "group": resource.group,
            "description": resource.description,
            "unit": resource.unit,
            "quantity": resource.quantity,
            "price": price,
            "total_cost": total_cost,
        }

    def _calculate_material_cost(
        self,
        resource,
        values: list[dict],
    ) -> dict:
        """
        Calcula o custo de material.
        """

        price = self._find_labor_material_price(
            values=values,
            resource_group="MA",
        )

        total_cost = resource.quantity * price

        return {
            "code": resource.code,
            "group": resource.group,
            "description": resource.description,
            "unit": resource.unit,
            "quantity": resource.quantity,
            "price": price,
            "total_cost": total_cost,
        }

    def _find_equipment_price(
        self,
        values: list[dict],
        classification: str,
    ) -> Decimal:
        """
        Localiza o preço produtivo ou improdutivo
        do equipamento no sistema ON.
        """

        for item in values:
            if (
                item.get("type_system") == self.ON
                and item.get("classification") == classification
            ):
                return Decimal(
                    item["monetary_value"]
                )

        raise ValueError(
            f"Valor {classification} não encontrado "
            f"para equipamento."
        )

    def _find_labor_material_price(
        self,
        values: list[dict],
        resource_group: str,
    ) -> Decimal:
        """
        Localiza o custo horário de mão de obra
        ou o custo do material.

        Mão de obra utiliza ON / CT.
        Materiais utilizam NA / CT.
        """

        if resource_group == "MO":
            preferred_type_system = self.ON
        elif resource_group == "MA":
            preferred_type_system = self.NA
        else:
            raise ValueError(
                f"Grupo inválido: {resource_group}"
            )

        for item in values:
            if (
                item.get("type_system")
                == preferred_type_system
                and item.get("classification") == "CT"
            ):
                return Decimal(
                    item["monetary_value"]
                )

        raise ValueError(
            f"Valor CT não encontrado para "
            f"o recurso do grupo {resource_group}."
        )

    def _find_value(
        self,
        values: list[dict],
        type_system: str,
        classification: str,
        group: str,
        preferred_classifications: set[str],
    ) -> Decimal:
        """
        Método auxiliar genérico para localizar
        um valor monetário.
        """

        for item in values:
            if item.get("type_system") != type_system:
                continue

            if classification:
                if item.get("classification") != classification:
                    continue

            if group:
                if item.get("group") != group:
                    continue

            if (
                item.get("classification")
                not in preferred_classifications
            ):
                continue

            return Decimal(
                item["monetary_value"]
            )

        raise ValueError(
            "Valor monetário não encontrado."
        )


def format_decimal(value: Decimal) -> str:
    """
    Formata um Decimal para exibição no terminal.
    """

    return f"{value:.10f}"


def print_equipment_result(result: dict) -> None:
    """
    Imprime o detalhamento específico de equipamento.
    """

    print(
        f"{result['code']} | "
        f"{result['description']}"
    )

    print(
        f"  Produtiva:   "
        f"{format_decimal(result['productive_quantity'])}"
        f" × "
        f"{format_decimal(result['productive_price'])}"
        f" = "
        f"R$ {format_decimal(result['productive_cost'])}"
    )

    print(
        f"  Improdutiva: "
        f"{format_decimal(result['unproductive_quantity'])}"
        f" × "
        f"{format_decimal(result['unproductive_price'])}"
        f" = "
        f"R$ {format_decimal(result['unproductive_cost'])}"
    )

    print(
        f"  TOTAL: "
        f"R$ {format_decimal(result['total_cost'])}"
    )


def print_resource_result(result: dict) -> None:
    """
    Imprime o detalhamento de mão de obra ou material.
    """

    print(
        f"{result['code']} | "
        f"{result['description']}"
    )

    print(
        f"  Quantidade: "
        f"{format_decimal(result['quantity'])}"
        f" × "
        f"{format_decimal(result['price'])}"
        f" = "
        f"R$ {format_decimal(result['total_cost'])}"
    )


def main() -> None:
    """
    Executa o cálculo detalhado da composição.
    """

    explosion = CompositionExplosion()
    monetary_value_client = MonetaryValueApiClient()

    result = explosion.explode(
        COMPOSITION_CODE
    )

    calculator = DetailedCostCalculator(
        monetary_value_client=monetary_value_client
    )

    equipment_total = Decimal("0")
    workman_total = Decimal("0")
    material_total = Decimal("0")

    calculated_results = []

    print()
    print("=" * 120)
    print(
        f"CUSTO DETALHADO DA COMPOSIÇÃO {COMPOSITION_CODE}"
    )
    print("=" * 120)

    print(
        f"Recursos consolidados: "
        f"{len(result.inputs)}"
    )

    print()

    for resource in result.inputs:

        resource_result = (
            calculator.calculate_resource_cost(
                resource
            )
        )

        calculated_results.append(
            resource_result
        )

        print("-" * 120)

        if resource.is_equipment():

            print(
                f"[EQ] {resource.code}"
            )

            print_equipment_result(
                resource_result
            )

            equipment_total += (
                resource_result["total_cost"]
            )

        elif resource.is_workman():

            print(
                f"[MO] {resource.code}"
            )

            print_resource_result(
                resource_result
            )

            workman_total += (
                resource_result["total_cost"]
            )

        elif resource.is_material():

            print(
                f"[MA] {resource.code}"
            )

            print_resource_result(
                resource_result
            )

            material_total += (
                resource_result["total_cost"]
            )

    total_cost = (
        equipment_total
        + workman_total
        + material_total
    )

    difference = (
        total_cost
        - OFFICIAL_VALUE
    )

    difference_percentage = (
        difference
        / OFFICIAL_VALUE
        * Decimal("100")
    )

    print()
    print("=" * 120)
    print("ACUMULADO POR GRUPO")
    print("=" * 120)

    print(
        f"Equipamentos: "
        f"R$ {format_decimal(equipment_total)}"
    )

    print(
        f"Mão de obra:  "
        f"R$ {format_decimal(workman_total)}"
    )

    print(
        f"Materiais:    "
        f"R$ {format_decimal(material_total)}"
    )

    print(
        "-" * 120
    )

    print(
        f"TOTAL CALCULADO: "
        f"R$ {format_decimal(total_cost)}"
    )

    print(
        f"VALOR OFICIAL:   "
        f"R$ {format_decimal(OFFICIAL_VALUE)}"
    )

    print(
        f"DIFERENÇA:       "
        f"R$ {format_decimal(difference)}"
    )

    print(
        f"DIFERENÇA (%):   "
        f"{difference_percentage:.6f}%"
    )

    print()
    print("=" * 120)

    if total_cost == OFFICIAL_VALUE:
        print("STATUS: VALOR EXATO")
    else:
        print("STATUS: EXISTE DIFERENÇA A INVESTIGAR")

    print("=" * 120)


if __name__ == "__main__":
    main()