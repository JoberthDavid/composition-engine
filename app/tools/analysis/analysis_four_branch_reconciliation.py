from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from app.domain.composition_node import CompositionNode
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver


FOUR_PLACES = Decimal("0.0001")
TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")

ROOT_CODE = "0919013"
TARGET_CODES = {
    "0919079",
    "1619003",
    "0909617",
    "0407819",
}


def round_sicro(value: Decimal, places: Decimal = FOUR_PLACES) -> Decimal:
    """Arredonda conforme a precisão solicitada no diagnóstico."""
    return value.quantize(places, rounding=ROUND_HALF_UP)


class MonetaryValueResolver:
    """Resolve e armazena em cache os valores monetários dos insumos."""

    def __init__(
        self,
        client: MonetaryValueApiClient | None = None,
    ) -> None:
        self.client = client or MonetaryValueApiClient()
        self.cache: dict[tuple[str, str, str], Decimal] = {}

    def get_value(
        self,
        code: str,
        type_system: str,
        classification: str,
    ) -> Decimal:
        """Obtém um valor monetário filtrando sistema e classificação."""
        key = (code, type_system, classification)

        if key in self.cache:
            return self.cache[key]

        values = self.client.get_values_by_code(code)

        for item in values:
            if (
                item.get("type_system") == type_system
                and item.get("classification") == classification
            ):
                value = Decimal(item["monetary_value"])
                self.cache[key] = value
                return value

        raise ValueError(
            f"Valor monetário não encontrado: "
            f"code={code}, type_system={type_system}, "
            f"classification={classification}"
        )

    def equipment_prices(
        self,
        code: str,
    ) -> tuple[Decimal, Decimal]:
        """Retorna preço produtivo e improdutivo."""
        return (
            self.get_value(code, "ON", "PR"),
            self.get_value(code, "ON", "IM"),
        )

    def workman_cost(self, code: str) -> Decimal:
        """Retorna custo de mão de obra."""
        return self.get_value(code, "ON", "CT")

    def material_cost(self, code: str) -> Decimal:
        """Retorna custo de material."""
        return self.get_value(code, "NA", "CT")


@dataclass
class NodeResult:
    """Armazena os custos interno, propagado e os detalhes da composição."""

    code: str
    internal_cost: Decimal = ZERO
    internal_cost_2: Decimal = ZERO
    own_cost: Decimal = ZERO
    children_cost: Decimal = ZERO
    children: list["ChildResult"] = field(default_factory=list)


@dataclass
class ChildResult:
    """Representa o impacto da filha em seu pai."""

    code: str
    reference_quantity: Decimal
    internal_cost: Decimal
    rounded_cost: Decimal
    internal_line: Decimal
    rounded_line: Decimal
    local_delta: Decimal
    parent: str
    grandchildren_delta: Decimal = ZERO

    @property
    def effective_delta(self) -> Decimal:
        """Retorna o impacto da redução do custo da filha na linha do pai."""
        return self.rounded_line - self.internal_line


class FourBranchAnalyzer:
    """
    Analisa somente quatro ramos prioritários da árvore.

    EQ/MO/MA permanecem com a lógica do cálculo atual:
    - EQ e MO divididos pela produção;
    - MA sem divisão;
    - quantidades e custos de linha arredondados a quatro casas.

    A hipótese B é aplicada somente ao custo unitário total da filha:
    - custo interno completo;
    - custo unitário propagado arredondado a duas casas.
    """

    def __init__(
        self,
        monetary_values: MonetaryValueResolver,
    ) -> None:
        self.monetary_values = monetary_values
        self.cache: dict[int, NodeResult] = {}

    def calculate(
        self,
        node: CompositionNode,
    ) -> NodeResult:
        """Calcula recursivamente um nó uma única vez."""
        node_id = id(node)

        if node_id in self.cache:
            return self.cache[node_id]

        composition = node.composition

        equipment_cost = ZERO
        workman_cost = ZERO
        material_cost = ZERO

        for composition_input in composition.inputs:
            if composition_input.is_composition_reference():
                continue

            if composition_input.is_transport():
                continue

            if composition_input.group == "EQ":
                equipment_cost += self._equipment_line(
                    composition,
                    composition_input,
                )
                continue

            if composition_input.group == "MO":
                workman_cost += self._workman_line(
                    composition,
                    composition_input,
                )
                continue

            if composition_input.group == "MA":
                material_cost += self._material_line(
                    composition_input,
                )

        equipment_cost = round_sicro(equipment_cost)
        workman_cost = round_sicro(workman_cost)
        material_cost = round_sicro(material_cost)

        fic_base = round_sicro(
            equipment_cost + workman_cost
        )
        fic_cost = round_sicro(
            fic_base * composition.fic
        )
        own_cost = round_sicro(
            equipment_cost
            + workman_cost
            + material_cost
            + fic_cost
        )

        children_cost = ZERO
        children: list[ChildResult] = []

        for child in node.children:
            child_result = self.calculate(child)

            reference_quantity = round_sicro(
                child.reference_quantity or ZERO
            )

            internal_line = round_sicro(
                reference_quantity * child_result.internal_cost
            )

            rounded_cost = round_sicro(
                child_result.internal_cost,
                TWO_PLACES,
            )

            rounded_line = round_sicro(
                reference_quantity * rounded_cost
            )

            local_delta = (
                round_sicro(
                    reference_quantity
                    * (
                        rounded_cost
                        - child_result.internal_cost
                    )
                )
            )

            children_cost += rounded_line

            children.append(
                ChildResult(
                    code=child.composition.code,
                    reference_quantity=reference_quantity,
                    internal_cost=child_result.internal_cost,
                    rounded_cost=rounded_cost,
                    internal_line=internal_line,
                    rounded_line=rounded_line,
                    local_delta=local_delta,
                    parent=composition.code,
                    grandchildren_delta=(
                        child_result.children_cost
                        - (
                            child_result.internal_cost
                            - child_result.own_cost
                        )
                    ),
                )
            )

        children_cost = round_sicro(children_cost)

        internal_cost = round_sicro(
            own_cost + children_cost
        )

        result = NodeResult(
            code=composition.code,
            internal_cost=internal_cost,
            internal_cost_2=round_sicro(
                internal_cost,
                TWO_PLACES,
            ),
            own_cost=own_cost,
            children_cost=children_cost,
            children=children,
        )

        self.cache[node_id] = result
        return result

    def _equipment_line(self, composition, composition_input) -> Decimal:
        """Calcula exatamente uma linha de equipamento."""
        base_quantity = (
            composition_input.quantity
            / composition.production
        )

        use = (
            composition_input.use
            if composition_input.use is not None
            else ONE
        )

        productive_quantity = round_sicro(
            base_quantity * use
        )
        unproductive_quantity = round_sicro(
            base_quantity * (ONE - use)
        )

        productive_price, unproductive_price = (
            self.monetary_values.equipment_prices(
                composition_input.code
            )
        )

        productive_cost = round_sicro(
            productive_quantity * productive_price
        )
        unproductive_cost = round_sicro(
            unproductive_quantity
            * unproductive_price
        )

        return productive_cost + unproductive_cost

    def _workman_line(self, composition, composition_input) -> Decimal:
        """Calcula exatamente uma linha de mão de obra."""
        quantity = round_sicro(
            composition_input.quantity
            / composition.production
        )

        price = self.monetary_values.workman_cost(
            composition_input.code
        )

        return round_sicro(quantity * price)

    def _material_line(self, composition_input) -> Decimal:
        """Calcula exatamente uma linha de material."""
        quantity = round_sicro(
            composition_input.quantity
        )

        price = self.monetary_values.material_cost(
            composition_input.code
        )

        return round_sicro(quantity * price)

    def branch_report(
        self,
        root: CompositionNode,
        target_code: str,
    ) -> list[tuple[int, CompositionNode, list[ChildResult]]]:
        """Extrai todas as ocorrências do código-alvo e seus descendentes."""
        matches: list[
            tuple[int, CompositionNode, list[ChildResult]]
        ] = []

        counter = 0

        def walk(
            node: CompositionNode,
            depth: int,
        ) -> None:
            nonlocal counter
            counter += 1

            if node.composition.code == target_code:
                result = self.calculate(node)
                matches.append(
                    (
                        depth,
                        node,
                        result.children,
                    )
                )

            for child in node.children:
                walk(child, depth + 1)

        walk(root, 0)
        return matches


def format_money(value: Decimal) -> str:
    """Formata um valor monetário com quatro casas."""
    return f"R$ {value:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")


def write_report(
    root: CompositionNode,
    analyzer: FourBranchAnalyzer,
    root_result: NodeResult,
) -> None:
    """Grava o diagnóstico completo dos quatro ramos prioritários."""
    output_path = "tests/test_four_branch_reconciliation_output.txt"

    with open(output_path, "w", encoding="utf-8") as output:
        output.write(
            "RECONCILIAÇÃO DOS QUATRO RAMOS PRIORITÁRIOS\n"
        )
        output.write("=" * 120 + "\n")
        output.write(
            "Hipótese B: custo unitário da filha arredondado para 2 casas\n"
        )
        output.write(
            "EQ/MO/MA: cálculo atual preservado\n"
        )
        output.write(
            f"Raiz: {ROOT_CODE}\n"
        )
        output.write(
            f"Custo raiz com hipótese B: "
            f"{format_money(root_result.internal_cost)}\n"
        )
        output.write("=" * 120 + "\n\n")

        for target in (
            "0919079",
            "1619003",
            "0909617",
            "0407819",
        ):
            matches = analyzer.branch_report(
                root,
                target,
            )

            output.write(
                f"RAMO {target} — {len(matches)} ocorrência(s)\n"
            )
            output.write("-" * 120 + "\n")

            for occurrence, (depth, node, _) in enumerate(
                matches,
                start=1,
            ):
                result = analyzer.calculate(node)

                output.write(
                    f"Ocorrência #{occurrence} | "
                    f"nível={depth} | "
                    f"caminho={_build_path(node)}\n"
                )
                output.write(
                    f"  próprio: "
                    f"{format_money(result.own_cost)}\n"
                )
                output.write(
                    f"  filhas: "
                    f"{format_money(result.children_cost)}\n"
                )
                output.write(
                    f"  custo interno: "
                    f"{format_money(result.internal_cost)}\n"
                )
                output.write(
                    f"  custo 2 casas: "
                    f"{format_money(result.internal_cost_2)}\n"
                )

                for child in result.children:
                    output.write(
                        "  FILHA\n"
                    )
                    output.write(
                        f"    código: {child.code}\n"
                    )
                    output.write(
                        f"    Q AX/TF: "
                        f"{child.reference_quantity:.4f}\n"
                    )
                    output.write(
                        f"    custo interno: "
                        f"{format_money(child.internal_cost)}\n"
                    )
                    output.write(
                        f"    custo 2 casas: "
                        f"{format_money(child.rounded_cost)}\n"
                    )
                    output.write(
                        f"    linha interna: "
                        f"{format_money(child.internal_line)}\n"
                    )
                    output.write(
                        f"    linha 2 casas: "
                        f"{format_money(child.rounded_line)}\n"
                    )
                    output.write(
                        f"    impacto local: "
                        f"{format_money(child.effective_delta)}\n"
                    )

                output.write("\n")

            output.write("\n")

        output.write(
            "RESUMO FINAL\n"
        )
        output.write("=" * 120 + "\n")
        output.write(
            f"Custo interno da raiz: "
            f"{format_money(root_result.internal_cost)}\n"
        )
        output.write(
            "Observação: o impacto total na raiz não é a soma dos "
            "impactos locais de cada ocorrência, pois uma alteração "
            "em um nível é reincorporada nas composições ancestrais.\n"
        )


def _build_path(node: CompositionNode) -> str:
    """Monta o caminho da ocorrência desde a raiz."""
    codes: list[str] = []
    current = node

    while current is not None:
        codes.append(current.composition.code)
        current = current.parent

    return " -> ".join(reversed(codes))


def main() -> None:
    """Executa o diagnóstico dos quatro ramos prioritários."""
    resolver = CompositionResolver(
        repository=CompositionRepository()
    )

    root = resolver.resolve_tree(
        composition_code=ROOT_CODE
    )

    monetary_values = MonetaryValueResolver(
        client=MonetaryValueApiClient()
    )

    analyzer = FourBranchAnalyzer(
        monetary_values=monetary_values
    )

    root_result = analyzer.calculate(root)

    write_report(
        root=root,
        analyzer=analyzer,
        root_result=root_result,
    )

    print()
    print("=" * 120)
    print("RECONCILIAÇÃO DOS QUATRO RAMOS PRIORITÁRIOS")
    print("=" * 120)
    print(
        f"Custo hipótese B: "
        f"{format_money(root_result.internal_cost)}"
    )
    print(
        f"Meta oficial: R$ 105.890,0000"
    )
    print(
        f"Diferença: "
        f"{format_money(root_result.internal_cost - Decimal('105890.00'))}"
    )

    for target in (
        "0919079",
        "1619003",
        "0909617",
        "0407819",
    ):
        matches = analyzer.branch_report(
            root,
            target,
        )

        print()
        print(
            f"{target}: {len(matches)} ocorrência(s)"
        )

        for occurrence, (_, node, _) in enumerate(
            matches,
            start=1,
        ):
            result = analyzer.calculate(node)

            print(
                f"  #{occurrence} "
                f"{_build_path(node)}"
            )
            print(
                f"     próprio: "
                f"{format_money(result.own_cost)}"
            )
            print(
                f"     filhas: "
                f"{format_money(result.children_cost)}"
            )
            print(
                f"     interno: "
                f"{format_money(result.internal_cost)}"
            )
            print(
                f"     2 casas: "
                f"{format_money(result.internal_cost_2)}"
            )

    print()
    print(
        "Arquivo: "
        "tests/test_four_branch_reconciliation_output.txt"
    )


if __name__ == "__main__":
    main()