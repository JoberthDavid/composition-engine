from __future__ import annotations

from dataclasses import dataclass
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
ZERO = Decimal("0")


def round_two(value: Decimal) -> Decimal:
    """Arredonda o custo unitário total para duas casas decimais."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass
class NodeRecord:
    """Armazena o custo unitário calculado uma única vez para cada ocorrência."""

    node: CompositionNode
    result: NodeCostResult


class SinglePassCostCalculator(UnitRecursiveFicCalculator):
    """
    Calcula toda a árvore em uma única passagem.

    EQ/MO/MA e FIC são mantidos exatamente como no cálculo-base atual.
    O objetivo é obter o custo interno de cada ocorrência sem recalcular
    repetidamente os mesmos ramos durante o diagnóstico.
    """

    def __init__(self, monetary_values: MonetaryValueResolver) -> None:
        super().__init__(monetary_values=monetary_values)
        self.records: dict[int, NodeRecord] = {}

    def calculate(self, node: CompositionNode) -> NodeCostResult:
        """Calcula o custo interno da ocorrência e registra o resultado."""
        result = super().calculate(node)
        self.records[id(node)] = NodeRecord(node=node, result=result)
        return result


def build_root() -> CompositionNode:
    """Constrói uma única árvore para o diagnóstico."""
    resolver = CompositionResolver(repository=CompositionRepository())
    return resolver.resolve_tree(ROOT_CODE)


def collect_nodes(root: CompositionNode) -> list[CompositionNode]:
    """Retorna todas as ocorrências da árvore na ordem de caminhada."""
    return list(root.walk())


def get_record(
    records: dict[int, NodeRecord],
    node: CompositionNode,
) -> NodeRecord:
    """Recupera o registro calculado para uma ocorrência."""
    return records[id(node)]


def format_impact(value: Decimal) -> str:
    """Formata impacto monetário com sinal explícito."""
    return f"{value:+.4f}"


def main() -> None:
    """Executa a reconciliação ocorrência por ocorrência."""
    root = build_root()
    monetary_values = MonetaryValueResolver(client=MonetaryValueApiClient())

    calculator = SinglePassCostCalculator(monetary_values=monetary_values)
    baseline_root = calculator.calculate(root)

    rows: list[dict[str, object]] = []

    nodes = collect_nodes(root)
    occurrence_number = 0

    for node in nodes:
        if node.parent is None:
            continue

        occurrence_number += 1
        parent = node.parent
        record = get_record(calculator.records, node)
        internal = record.result.total_cost
        two_decimals = round_two(internal)

        # A quantidade do filho no pai é exatamente a referência AX/TF
        # armazenada no nó filho.
        reference_quantity = round_sicro(
            node.reference_quantity or ZERO
        )

        direct_impact = (
            reference_quantity * (two_decimals - internal)
        )

        baseline_line = round_sicro(
            reference_quantity * internal
        )
        two_decimals_line = round_sicro(
            reference_quantity * two_decimals
        )
        effective_parent_impact = two_decimals_line - baseline_line

        rows.append(
            {
                "occurrence": occurrence_number,
                "depth": len(list(node.path)) - 1 if hasattr(node, "path") else "",
                "parent": parent.composition.code,
                "code": node.composition.code,
                "reference_quantity": reference_quantity,
                "internal_cost": internal,
                "two_decimals_cost": two_decimals,
                "cost_difference": two_decimals - internal,
                "direct_impact": direct_impact,
                "baseline_line": baseline_line,
                "two_decimals_line": two_decimals_line,
                "effective_parent_impact": effective_parent_impact,
            }
        )

    rows_by_impact = sorted(
        rows,
        key=lambda row: abs(row["effective_parent_impact"]),
        reverse=True,
    )

    sum_direct = sum(
        (row["direct_impact"] for row in rows),
        ZERO,
    )
    sum_effective = sum(
        (row["effective_parent_impact"] for row in rows),
        ZERO,
    )

    baseline_difference = baseline_root.total_cost - OFFICIAL_TOTAL
    target_delta = Decimal("105888.6770") - baseline_root.total_cost

    print()
    print("=" * 150)
    print("RECONCILIAÇÃO DA HIPÓTESE B — 121 OCORRÊNCIAS")
    print("=" * 150)
    print(f"Composição raiz: {ROOT_CODE}")
    print("EQ/MO/MA: cálculo-base preservado")
    print("Custo interno: custo unitário total da ocorrência")
    print("Custo 2 casas: custo interno arredondado a 2 casas")
    print("Impacto direto: Q AX/TF × (custo 2 casas − custo interno)")
    print("Impacto efetivo: diferença da linha AX/TF após arredondamento a 4 casas")
    print(f"Referência oficial: R$ {OFFICIAL_TOTAL:.2f}")
    print()
    print(f"Custo-base da raiz:       R$ {baseline_root.total_cost:.4f}")
    print(f"Diferença para oficial:   R$ {baseline_difference:+.4f}")
    print(f"Meta da hipótese B:       R$ 105888.6770")
    print(f"Delta observado da B:     R$ {target_delta:+.4f}")
    print(f"Soma impacto direto:       R$ {sum_direct:+.4f}")
    print(f"Soma impacto efetivo:      R$ {sum_effective:+.4f}")
    print(f"Ocorrências analisadas:    {len(rows)}")

    print()
    print("TOP 30 IMPACTOS EFETIVOS NO PAI")
    print("-" * 150)
    print(
        f"{'#':>4} {'pai':>10} {'filha':>10} {'Q AX/TF':>12} "
        f"{'interno':>12} {'2 casas':>10} {'dif. custo':>12} "
        f"{'impacto':>12}"
    )

    for row in rows_by_impact[:30]:
        print(
            f"{row['occurrence']:4d} "
            f"{row['parent']:>10} "
            f"{row['code']:>10} "
            f"{row['reference_quantity']:12.4f} "
            f"R$ {row['internal_cost']:9.4f} "
            f"R$ {row['two_decimals_cost']:7.2f} "
            f"{row['cost_difference']:+12.4f} "
            f"R$ {row['effective_parent_impact']:+9.4f}"
        )

    print()
    print("TODAS AS OCORRÊNCIAS")
    print("-" * 150)
    print(
        f"{'#':>4} {'pai':>10} {'filha':>10} {'Q AX/TF':>12} "
        f"{'interno':>12} {'2 casas':>10} {'dif. custo':>12} "
        f"{'impacto direto':>15} {'impacto efetivo':>16}"
    )

    for row in rows:
        print(
            f"{row['occurrence']:4d} "
            f"{row['parent']:>10} "
            f"{row['code']:>10} "
            f"{row['reference_quantity']:12.4f} "
            f"R$ {row['internal_cost']:9.4f} "
            f"R$ {row['two_decimals_cost']:7.2f} "
            f"{row['cost_difference']:+12.4f} "
            f"R$ {row['direct_impact']:+12.4f} "
            f"R$ {row['effective_parent_impact']:+13.4f}"
        )

    output_path = Path("tests/test_reconciliation_two_decimals_output.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output:
        output.write("RECONCILIAÇÃO DA HIPÓTESE B — 121 OCORRÊNCIAS\n")
        output.write("=" * 150 + "\n")
        output.write(f"Composição raiz: {ROOT_CODE}\n")
        output.write(f"Custo-base: {baseline_root.total_cost:.4f}\n")
        output.write(f"Diferença para oficial: {baseline_difference:+.4f}\n")
        output.write("Meta hipótese B: 105888.6770\n")
        output.write(f"Delta observado B: {target_delta:+.4f}\n")
        output.write(f"Soma impacto direto: {sum_direct:+.4f}\n")
        output.write(f"Soma impacto efetivo: {sum_effective:+.4f}\n")
        output.write(f"Ocorrências analisadas: {len(rows)}\n\n")

        output.write(
            "ocorrencia;parent;child;reference_quantity;internal_cost;"
            "two_decimals_cost;cost_difference;direct_impact;"
            "baseline_line;two_decimals_line;effective_parent_impact\n"
        )

        for row in rows:
            output.write(
                f"{row['occurrence']};"
                f"{row['parent']};"
                f"{row['code']};"
                f"{row['reference_quantity']};"
                f"{row['internal_cost']};"
                f"{row['two_decimals_cost']};"
                f"{row['cost_difference']};"
                f"{row['direct_impact']};"
                f"{row['baseline_line']};"
                f"{row['two_decimals_line']};"
                f"{row['effective_parent_impact']}\n"
            )

    print()
    print(f"Arquivo: {output_path}")


if __name__ == "__main__":
    main()