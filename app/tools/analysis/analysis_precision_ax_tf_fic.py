from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from itertools import product
from pathlib import Path

from app.domain.composition_node import CompositionNode
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver

# Reutiliza exatamente os métodos atuais de EQ/MO/MA do teste que já foi validado.
from app.tools.analysis.analysis_recursive_fic_unit import (
    MonetaryValueResolver,
    NodeCostResult,
    UnitRecursiveFicCalculator,
)

FOUR_PLACES = Decimal("0.0001")
ZERO = Decimal("0")
ROOT_CODE = "0919013"
OFFICIAL_TOTAL = Decimal("105890.00")


def round_sicro(value: Decimal) -> Decimal:
    """Arredonda no padrão usado no experimento: quatro casas decimais."""
    return value.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PrecisionMode:
    """Define apenas onde o arredondamento AX/TF e FIC será aplicado."""

    edge_quantity_round: bool
    edge_cost_round: bool
    children_sum_round: bool
    fic_cost_round: bool
    total_round: bool

    @property
    def name(self) -> str:
        return (
            f"Q={'4' if self.edge_quantity_round else 'raw'} "
            f"L={'4' if self.edge_cost_round else 'raw'} "
            f"S={'4' if self.children_sum_round else 'raw'} "
            f"F={'4' if self.fic_cost_round else 'raw'} "
            f"T={'4' if self.total_round else 'raw'}"
        )


class PrecisionOnlyCalculator(UnitRecursiveFicCalculator):
    """
    Calcula a árvore alterando exclusivamente a precisão de AX/TF e FIC.

    Os métodos herdados _calculate_equipment_line(), _calculate_workman_line()
    e _calculate_material_line() permanecem exatamente os do cálculo atual.
    """

    def __init__(
        self,
        monetary_values: MonetaryValueResolver,
        mode: PrecisionMode,
    ) -> None:
        super().__init__(monetary_values=monetary_values)
        self.mode = mode

    def calculate(self, node: CompositionNode) -> NodeCostResult:
        """Calcula um nó mantendo EQ/MO/MA e variando só AX/TF/FIC."""
        self.processed_nodes += 1
        composition = node.composition

        # ---------------------------------------------------------------
        # EQ / MO / MA: exatamente os métodos atuais.
        # ---------------------------------------------------------------
        equipment_cost = ZERO
        workman_cost = ZERO
        material_cost = ZERO

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

        # Estes três arredondamentos também permanecem exatamente como no teste atual.
        equipment_cost = round_sicro(equipment_cost)
        workman_cost = round_sicro(workman_cost)
        material_cost = round_sicro(material_cost)

        # ---------------------------------------------------------------
        # FIC: única parte de FIC que será experimental.
        # A base já é soma de valores de 4 casas; portanto, retirar o
        # arredondamento da base não muda matematicamente o resultado.
        # ---------------------------------------------------------------
        fic_base = round_sicro(equipment_cost + workman_cost)
        fic_value = fic_base * composition.fic
        fic_cost = (
            round_sicro(fic_value)
            if self.mode.fic_cost_round
            else fic_value
        )

        # Próprio permanece arredondado como no cálculo atual.
        own_cost = round_sicro(
            equipment_cost
            + workman_cost
            + material_cost
            + fic_cost
        )

        # ---------------------------------------------------------------
        # AX / TF: experimentamos somente a precisão da propagação.
        # ---------------------------------------------------------------
        children_cost = ZERO
        children_details: list[tuple[str, Decimal, Decimal]] = []

        for child in node.children:
            child_result = self.calculate(child)

            reference_quantity = child.reference_quantity or ZERO
            if self.mode.edge_quantity_round:
                reference_quantity = round_sicro(reference_quantity)

            child_line_cost = reference_quantity * child_result.total_cost
            if self.mode.edge_cost_round:
                child_line_cost = round_sicro(child_line_cost)

            children_cost += child_line_cost
            children_details.append(
                (
                    child.composition.code,
                    reference_quantity,
                    child_line_cost,
                )
            )

        if self.mode.children_sum_round:
            children_cost = round_sicro(children_cost)

        total_cost = own_cost + children_cost
        if self.mode.total_round:
            total_cost = round_sicro(total_cost)

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
            children=children_details,
        )


def build_root() -> CompositionNode:
    """Monta uma árvore nova para cada variante."""
    resolver = CompositionResolver(
        repository=CompositionRepository()
    )
    return resolver.resolve_tree(ROOT_CODE)


def main() -> None:
    """Executa uma varredura sistemática de 32 combinações de precisão."""
    modes = [
        PrecisionMode(*flags)
        for flags in product([False, True], repeat=5)
    ]

    # A árvore e o resolvedor monetário são construídos uma única vez.
    # Assim, as 32 variantes não repetem chamadas à API.
    root = build_root()
    monetary_values = MonetaryValueResolver(
        client=MonetaryValueApiClient()
    )

    rows = []
    for mode in modes:
        calculator = PrecisionOnlyCalculator(
            monetary_values=monetary_values,
            mode=mode,
        )
        result = calculator.calculate(root)
        processed_nodes = calculator.processed_nodes
        difference = result.total_cost - OFFICIAL_TOTAL
        rows.append(
            (
                abs(difference),
                difference,
                mode,
                result,
                processed_nodes,
            )
        )

    rows.sort(key=lambda item: item[0])

    print()
    print("=" * 120)
    print("TESTE EXCLUSIVO DE PRECISÃO — AX/TF + FIC")
    print("=" * 120)
    print(f"Composição raiz: {ROOT_CODE}")
    print("EQ/MO/MA: preservados exatamente pelos métodos atuais")
    print(f"Referência oficial: R$ {OFFICIAL_TOTAL:.2f}")
    print("Combinações testadas: 32")
    print("")
    print("Legenda: Q=quantidade AX/TF | L=custo da linha AX/TF | S=subtotal das filhas")
    print("         F=arredondamento do FIC | T=arredondamento do total da composição")
    print("")
    print("TOP 10 MAIS PRÓXIMAS")
    print("-" * 120)
    print(
        f"{'modo':32} {'total':>14} {'diferença':>14} "
        f"{'filhas':>14} {'FIC raiz':>12} {'nós':>6}"
    )

    for _, difference, mode, result, processed_nodes in rows[:10]:
        print(
            f"{mode.name:32} "
            f"R$ {result.total_cost:>10.4f} "
            f"R$ {difference:>10.4f} "
            f"R$ {result.children_cost:>10.4f} "
            f"R$ {result.fic_cost:>8.4f} "
            f"{processed_nodes:>6}"
        )

    print("")
    print("BASE ATUAL ESPERADA: Q=4 L=4 S=4 F=4 T=4")
    baseline = next(
        item for item in rows
        if item[2] == PrecisionMode(True, True, True, True, True)
    )
    baseline_result = baseline[3]
    print(
        f"Total = R$ {baseline_result.total_cost:.4f} | "
        f"diferença = R$ {baseline[1]:.4f}"
    )

    # Gera arquivo somente para a auditoria local do experimento.
    output_path = Path("tests/test_precision_ax_tf_fic_output.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output:
        output.write("TESTE EXCLUSIVO DE PRECISÃO — AX/TF + FIC\n")
        output.write("=" * 120 + "\n")
        output.write(f"Referência oficial: R$ {OFFICIAL_TOTAL:.2f}\n")
        output.write("EQ/MO/MA preservados pelos métodos atuais.\n\n")
        for _, difference, mode, result, processed_nodes in rows:
            output.write(
                f"{mode.name} | total={result.total_cost:.8f} | "
                f"dif={difference:.8f} | filhas={result.children_cost:.8f} | "
                f"fic_raiz={result.fic_cost:.8f} | nos={processed_nodes}\n"
            )

    print("")
    print(f"Arquivo: {output_path}")


if __name__ == "__main__":
    main()
