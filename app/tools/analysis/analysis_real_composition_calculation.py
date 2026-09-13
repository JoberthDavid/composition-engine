from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver


# COMPOSITION_CODE = "4915757"

COMPOSITION_CODE = "0919013"

def round_4(value: float) -> float:
    """Arredonda o valor para quatro casas decimais."""
    return round(value, 4)


def round_2(value: float) -> float:
    """Arredonda o valor para duas casas decimais."""
    return round(value, 2)


def get_monetary_value(
    client: MonetaryValueApiClient,
    code: str,
    type_system: str,
    classification: str,
) -> float:
    """Obtém o valor monetário aplicável ao insumo."""
    values = client.get_values_by_code(code)

    for value in values:
        if (
            value.get("type_system") == type_system
            and value.get("classification") == classification
        ):
            return float(value["monetary_value"])

    raise ValueError(
        f"Valor monetário não encontrado para {code}: "
        f"type_system={type_system}, "
        f"classification={classification}"
    )


def calculate_composition(
    node,
    monetary_client: MonetaryValueApiClient,
    disable_fic: bool = False,
) -> float:
    """
    Calcula uma composição seguindo exatamente a marcha definida.

    O custo unitário calculado é retornado com duas casas decimais
    para ser utilizado pela composição pai.
    """
    composition = node.composition
    production = float(composition.production)

    if disable_fic:
        # FIC desligado temporariamente para experimento controlado.
        fic_percentage = 0.0
    else:
        fic_percentage = float(composition.fic)

    print()
    print("=" * 100)
    print(f"COMPOSIÇÃO: {composition.generic_item}")
    print(f"DESCRIÇÃO:  {composition.generic_description}")
    print(f"PRODUÇÃO:   {production:.5f}")
    print(f"FIC:        {fic_percentage:.5f}")
    print("=" * 100)

    equipment_cost = 0.0
    labor_cost = 0.0
    materials_cost = 0.0
    auxiliary_cost = 0.0
    fixed_time_cost = 0.0

    # ------------------------------------------------------------------
    # 1. EQUIPAMENTOS
    # ------------------------------------------------------------------

    print("\nEQUIPAMENTOS")

    for composition_input in composition.inputs:
        if composition_input.input_group != "EQ":
            continue

        quantity = round_4(float(composition_input.input_quantity))

        values = monetary_client.get_values_by_code(
            composition_input.generic_item
        )


        productive_value = None
        improductive_value = None

        for value in values:
            if (
                value.get("type_system") == "ON"
                and value.get("classification") == "PR"
            ):
                productive_value = float(value["monetary_value"])

            if (
                value.get("type_system") == "ON"
                and value.get("classification") == "IM"
            ):
                improductive_value = float(value["monetary_value"])

        if productive_value is None:
            raise ValueError(
                f"Valor PR não encontrado para equipamento "
                f"{composition_input.generic_item}"
            )

        if improductive_value is None:
            raise ValueError(
                f"Valor IM não encontrado para equipamento "
                f"{composition_input.generic_item}"
            )

        use_percentage = float(
            composition_input.input_use
        )

        productive_quantity = round_4(
            quantity * use_percentage
        )

        improductive_quantity = round_4(
            quantity * (1.0 - use_percentage)
        )

        line_cost = round_4(
            productive_quantity * productive_value
            + improductive_quantity * improductive_value
        )

        equipment_cost += line_cost

        print(
            f"  {composition_input.generic_item} | "
            f"qtd={quantity:.4f} | "
            f"uso={use_percentage:.4f} | "
            f"custo={line_cost:.4f}"
        )

    equipment_cost = round_4(equipment_cost)

    # ------------------------------------------------------------------
    # 2. MÃO DE OBRA
    # ------------------------------------------------------------------

    print("\nMÃO DE OBRA")

    for composition_input in composition.inputs:
        if composition_input.input_group != "MO":
            continue

        quantity = round_4(float(composition_input.input_quantity))

        cost_value = get_monetary_value(
            monetary_client,
            composition_input.generic_item,
            "ON",
            "CT",
        )

        line_cost = round_4(
            quantity * cost_value
        )

        labor_cost += line_cost

        print(
            f"  {composition_input.generic_item} | "
            f"qtd={quantity:.4f} | "
            f"custo={line_cost:.4f}"
        )

    labor_cost = round_4(labor_cost)

    # ------------------------------------------------------------------
    # 3. FIC
    # ------------------------------------------------------------------

    fic_cost = round_4(
        ((equipment_cost + labor_cost) / production)
        * fic_percentage
    )

    operational_total = round_4(
        equipment_cost
        + labor_cost
    )

    operational_unit = round_4(
        ( operational_total / production )
        + fic_cost
    )

    print("\nCUSTO OPERACIONAL")
    print(f"  Equipamentos : {equipment_cost:.4f}")
    print(f"  Mão de obra  : {labor_cost:.4f}")
    print(f"  FIC          : {fic_cost:.4f}")
    print(f"  Total        : {operational_total:.4f}")
    print(f"  Unitário     : {operational_unit:.4f}")

    # ------------------------------------------------------------------
    # 4. MATERIAIS
    # ------------------------------------------------------------------

    print("\nMATERIAIS")

    for composition_input in composition.inputs:
        if composition_input.input_group != "MA":
            continue

        quantity = round_4(float(composition_input.input_quantity))

        cost_value = get_monetary_value(
            monetary_client,
            composition_input.generic_item,
            "NA",
            "CT",
        )

        line_cost = round_4(
            quantity * cost_value
        )

        materials_cost += line_cost

        print(
            f"  {composition_input.generic_item} | "
            f"qtd={quantity:.4f} | "
            f"custo={line_cost:.4f}"
        )

    materials_cost = round_4(materials_cost)

    # ------------------------------------------------------------------
    # 5. AX / TF
    # ------------------------------------------------------------------

    print("\nREFERÊNCIAS DE COMPOSIÇÃO")

    for child in node.children:
        child_unit_cost = calculate_composition(
            child,
            monetary_client,
            disable_fic=disable_fic,
        )

        child_unit_cost = round_2(child_unit_cost)

        line_cost = round_4(
            float(child.reference_quantity)
            * child_unit_cost
        )

        if child.is_auxiliary_activity():
            auxiliary_cost += line_cost

            reference_type = "AX"

        elif child.is_fixed_time():
            fixed_time_cost += line_cost

            reference_type = "TF"

        else:
            raise ValueError(
                f"Referência desconhecida: "
                f"{child.reference_group}"
            )

        print(
            f"\n  {reference_type} → "
            f"{child.composition.generic_item}"
        )
        print(
            f"    quantidade     = "
            f"{float(child.reference_quantity):.4f}"
        )
        print(
            f"    custo filho    = "
            f"{child_unit_cost:.2f}"
        )
        print(
            f"    custo da linha = "
            f"{line_cost:.4f}"
        )

    auxiliary_cost = round_4(auxiliary_cost)
    fixed_time_cost = round_4(fixed_time_cost)

    # ------------------------------------------------------------------
    # 6. TOTAL DA COMPOSIÇÃO
    # ------------------------------------------------------------------

    composition_total_raw = round_4(
        operational_unit
        + materials_cost
        + auxiliary_cost
        + fixed_time_cost
    )

    composition_unit_cost = round_2(
        composition_total_raw
    )

    print("\nRESULTADO DA COMPOSIÇÃO")
    print(f"  Operacional : {operational_unit:.4f}")
    print(f"  Materiais   : {materials_cost:.4f}")
    print(f"  AX          : {auxiliary_cost:.4f}")
    print(f"  TF          : {fixed_time_cost:.4f}")
    print(f"  Total bruto : {composition_total_raw:.4f}")
    print(f"  Unitário    : {composition_unit_cost:.2f}")

    return composition_unit_cost


def main() -> None:
    """Executa o cálculo de uma composição real da API."""

    print("=" * 100)
    print("TESTE DE CÁLCULO - COMPOSIÇÃO REAL DA API")
    print("=" * 100)

    repository = CompositionRepository()
    resolver = CompositionResolver(repository=repository)
    monetary_client = MonetaryValueApiClient()

    tree = resolver.resolve_tree(COMPOSITION_CODE)

    print()
    print("ÁRVORE:")
    print()

    for node in tree.walk():
        level = 0
        current = node.parent

        while current is not None:
            level += 1
            current = current.parent

        if node.is_root():
            relation = "ROOT"
        else:
            relation = node.reference_group

        print(
            f"{'  ' * level}"
            f"{relation} → "
            f"{node.composition.generic_item}"
        )

    print()
    print("=" * 100)
    print("INICIANDO CÁLCULO")
    print("=" * 100)

    result = calculate_composition(
        tree.root,
        monetary_client,
    )

    print()
    print("=" * 100)
    print("RESULTADO FINAL")
    print("=" * 100)
    print()
    print(
        f"Composição: {COMPOSITION_CODE}"
    )
    print(
        f"Custo unitário calculado: R$ {result:.2f}"
    )
    print()
    print("=" * 100)


if __name__ == "__main__":
    main()