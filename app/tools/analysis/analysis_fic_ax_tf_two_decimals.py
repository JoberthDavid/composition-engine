from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from app.domain.composition_node import CompositionNode
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver

from app.tools.analysis.analysis_recursive_fic_unit import (
    MonetaryValueResolver,
    NodeCostResult,
    UnitRecursiveFicCalculator,
    round_sicro,
)

ROOT_CODE = "0919013"
OFFICIAL_TOTAL = Decimal("105890.00")
TWO_PLACES = Decimal("0.01")


def round_two(value: Decimal) -> Decimal:
    """Arredonda o custo unitário total da composição para duas casas."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class TwoDecimalChildCostCalculator(UnitRecursiveFicCalculator):
    """
    Testa exclusivamente a hipótese de propagação do custo unitário da filha
    com duas casas decimais.

    EQ/MO/MA permanecem exatamente nos métodos herdados do cálculo atual.
    FIC da composição é calculado normalmente em quatro casas.
    A única alteração experimental ocorre quando o custo total da filha
    é incorporado à composição pai: o custo unitário da filha é reduzido
    para duas casas antes da multiplicação pela quantidade AX/TF.
    """

    def calculate(self, node: CompositionNode) -> NodeCostResult:
        """Calcula o nó mantendo o cálculo atual e altera só a propagação da filha."""
        self.processed_nodes += 1
        composition = node.composition

        equipment_cost = Decimal("0")
        workman_cost = Decimal("0")
        material_cost = Decimal("0")

        # EQ/MO/MA: exatamente os métodos atuais.
        for composition_input in composition.inputs:
            if composition_input.is_composition_reference():
                continue

            if composition_input.is_transport():
                continue

            if composition_input.group == "EQ":
                equipment_cost += self._calculate_equipment_line(
                    composition=composition,
                    composition_input=composition_input,
                )
                continue

            if composition_input.group == "MO":
                workman_cost += self._calculate_workman_line(
                    composition=composition,
                    composition_input=composition_input,
                )
                continue

            if composition_input.group == "MA":
                material_cost += self._calculate_material_line(
                    composition_input=composition_input,
                )

        equipment_cost = round_sicro(equipment_cost)
        workman_cost = round_sicro(workman_cost)
        material_cost = round_sicro(material_cost)

        # FIC: mantido exatamente como no cálculo atual.
        fic_base = round_sicro(equipment_cost + workman_cost)
        fic_cost = round_sicro(fic_base * composition.fic)

        own_cost = round_sicro(
            equipment_cost
            + workman_cost
            + material_cost
            + fic_cost
        )

        children_cost = Decimal("0")
        children_details: list[tuple[str, Decimal, Decimal, Decimal]] = []

        for child in node.children:
            child_result = self.calculate(child)

            # HIPÓTESE:
            # o custo unitário total da filha aparece com duas casas e é esse
            # valor apresentado que será usado na composição pai.
            child_unit_cost_internal = child_result.total_cost
            child_unit_cost_two_decimals = round_two(child_unit_cost_internal)

            # AX/TF continua com a quantidade arredondada para quatro casas,
            # exatamente como no cálculo-base.
            reference_quantity = round_sicro(
                child.reference_quantity or Decimal("0")
            )

            child_line_cost = round_sicro(
                reference_quantity * child_unit_cost_two_decimals
            )

            children_cost += child_line_cost
            children_details.append(
                (
                    child.composition.code,
                    reference_quantity,
                    child_unit_cost_two_decimals,
                    child_line_cost,
                )
            )

        children_cost = round_sicro(children_cost)
        total_cost = round_sicro(own_cost + children_cost)

        return NodeCostResult(
            code=composition.code,
            equipment_cost=equipment_cost,
            workman_cost=workman_cost,
            material_cost=material_cost,
            fic_base=fic_base,
            fic_cost=fic_cost,
            own_cost=own_cost,
            children_cost=children_cost,
            total_cost=total_cost,
            # Mantemos apenas o formato esperado pelo resultado-base.
            children=[
                (code, quantity, line_cost)
                for code, quantity, _, line_cost in children_details
            ],
        )


def build_root() -> CompositionNode:
    """Constrói uma única árvore para o experimento."""
    resolver = CompositionResolver(
        repository=CompositionRepository()
    )
    return resolver.resolve_tree(ROOT_CODE)


def run_baseline(
    root: CompositionNode,
    monetary_values: MonetaryValueResolver,
) -> NodeCostResult:
    """Executa o cálculo-base já validado para comparação."""
    calculator = UnitRecursiveFicCalculator(
        monetary_values=monetary_values,
    )
    return calculator.calculate(root)


def run_hypothesis_b(
    root: CompositionNode,
    monetary_values: MonetaryValueResolver,
) -> TwoDecimalChildCostCalculator:
    """Executa a hipótese e retorna o calculador usado."""
    calculator = TwoDecimalChildCostCalculator(
        monetary_values=monetary_values,
    )
    calculator.calculate(root)
    return calculator


def print_direct_children(
    root: CompositionNode,
    result: NodeCostResult,
) -> None:
    """Exibe os custos das filhas diretas da raiz sob a hipótese."""
    print("\nFILHAS DIRETAS DA RAIZ — HIPÓTESE")
    print("-" * 110)
    print(
        f"{'código':10} {'Q AX/TF':>12} {'custo interno':>16} "
        f"{'custo 2 casas':>16} {'custo linha':>16}"
    )

    result_by_code = {
        child[0]: child
        for child in result.children
    }

    # O resultado guarda somente o custo de linha. Para obter também o custo
    # interno e o custo com duas casas, recalculamos cada filha isoladamente.
    # Como o resolvedor monetário está em cache, isso não gera novas consultas.
    monetary_values = getattr(print_direct_children, "monetary_values", None)
    if monetary_values is None:
        return

    for child in root.children:
        child_calc = TwoDecimalChildCostCalculator(
            monetary_values=monetary_values,
        )
        child_result = child_calc.calculate(child)
        quantity = round_sicro(child.reference_quantity or Decimal("0"))
        internal = child_result.total_cost
        two_places = round_two(internal)
        line_cost = round_sicro(quantity * two_places)
        print(
            f"{child.composition.code:10} "
            f"{quantity:12.4f} "
            f"R$ {internal:13.4f} "
            f"R$ {two_places:13.2f} "
            f"R$ {line_cost:13.4f}"
        )


def main() -> None:
    """Executa a comparação entre o cálculo-base e a hipótese."""
    root = build_root()
    monetary_values = MonetaryValueResolver(
        client=MonetaryValueApiClient()
    )

    baseline = run_baseline(root, monetary_values)

    calculator_b = TwoDecimalChildCostCalculator(
        monetary_values=monetary_values,
    )
    result_b = calculator_b.calculate(root)

    baseline_difference = baseline.total_cost - OFFICIAL_TOTAL
    hypothesis_difference = result_b.total_cost - OFFICIAL_TOTAL
    improvement = abs(baseline_difference) - abs(hypothesis_difference)

    print()
    print("=" * 120)
    print("TESTE HIPÓTESE — CUSTO UNITÁRIO DA FILHA COM 2 CASAS")
    print("=" * 120)
    print(f"Composição raiz: {ROOT_CODE}")
    print("EQ/MO/MA: preservados exatamente pelos métodos atuais")
    print("FIC interno: preservado exatamente em 4 casas")
    print("AX/TF: quantidade preservada em 4 casas")
    print("Hipótese: custo unitário total da filha arredondado para 2 casas")
    print(f"Referência oficial: R$ {OFFICIAL_TOTAL:.2f}")

    print("\nCOMPARAÇÃO")
    print("-" * 120)
    print(f"Base atual                  : R$ {baseline.total_cost:12.4f} | diferença = R$ {baseline_difference:10.4f}")
    print(f"Hipótese                    : R$ {result_b.total_cost:12.4f} | diferença = R$ {hypothesis_difference:10.4f}")
    print(f"Melhora absoluta            : R$ {improvement:12.4f}")
    print(f"Custo próprio da raiz       : R$ {result_b.own_cost:12.4f}")
    print(f"Custo das filhas            : R$ {result_b.children_cost:12.4f}")
    print(f"Nós processados             : {calculator_b.processed_nodes}")

    print("\nFILHAS DIRETAS DA RAIZ — HIPÓTESE")
    print("-" * 120)
    print(
        f"{'código':10} {'Q AX/TF':>12} {'interno':>14} "
        f"{'2 casas':>14} {'linha':>14}"
    )

    for child in root.children:
        child_calculator = TwoDecimalChildCostCalculator(
            monetary_values=monetary_values,
        )
        child_result = child_calculator.calculate(child)
        quantity = round_sicro(child.reference_quantity or Decimal("0"))
        internal = child_result.total_cost
        two_places = round_two(internal)
        line_cost = round_sicro(quantity * two_places)
        print(
            f"{child.composition.code:10} "
            f"{quantity:12.4f} "
            f"R$ {internal:10.4f} "
            f"R$ {two_places:10.2f} "
            f"R$ {line_cost:10.4f}"
        )

    output_path = Path("tests/test_fic_ax_tf_two_decimals_output.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output:
        output.write("TESTE HIPÓTESE — CUSTO UNITÁRIO DA FILHA COM 2 CASAS\n")
        output.write("=" * 120 + "\n")
        output.write(f"Base atual: {baseline.total_cost:.8f}\n")
        output.write(f"Hipótese: {result_b.total_cost:.8f}\n")
        output.write(f"Oficial: {OFFICIAL_TOTAL:.2f}\n")
        output.write(f"Diferença base: {baseline_difference:.8f}\n")
        output.write(f"Diferença hipótese: {hypothesis_difference:.8f}\n")
        output.write(f"Melhora absoluta: {improvement:.8f}\n")
        output.write(f"Custo próprio raiz: {result_b.own_cost:.8f}\n")
        output.write(f"Custo filhas raiz: {result_b.children_cost:.8f}\n")

    print(f"\nArquivo: {output_path}")


if __name__ == "__main__":
    main()