from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from app.domain.composition_node import CompositionNode
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver


FOUR_PLACES = Decimal("0.0001")
TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")

ROOT_CODE = "0919013"
OFFICIAL_TOTAL = Decimal("105890.00")


def round_sicro(value: Decimal, places: Decimal = FOUR_PLACES) -> Decimal:
    """Arredonda com ROUND_HALF_UP na precisão informada."""
    return value.quantize(places, rounding=ROUND_HALF_UP)


class MonetaryValueResolver:
    """Resolve valores monetários e mantém cache local."""

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
        """Obtém um valor monetário da API."""
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
            "Valor monetário não encontrado: "
            f"{code} / {type_system} / {classification}"
        )

    def equipment_prices(self, code: str) -> tuple[Decimal, Decimal]:
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
class EdgeComparison:
    """Compara uma aresta pai-filho nas árvores A e B."""

    parent: str
    child: str
    reference_quantity: Decimal

    child_a: Decimal
    child_b_exposed: Decimal

    line_a: Decimal
    line_b: Decimal

    edge_delta: Decimal


@dataclass
class NodeComparison:
    """Armazena o resultado dos modelos A e B para um nó."""

    node_id: int
    code: str
    depth: int
    path: str

    own_cost: Decimal
    children_a: Decimal
    children_b: Decimal

    total_a: Decimal
    total_b: Decimal

    exposed_b: Decimal

    edges: list[EdgeComparison] = field(default_factory=list)

    @property
    def node_delta(self) -> Decimal:
        """Retorna a diferença entre os totais A e B no nó."""
        return round_sicro(self.total_b - self.total_a)


class TreeBValidator:
    """
    Valida a hipótese da árvore B.

    Árvore A:
        cada pai utiliza o custo interno completo da filha.

    Árvore B:
        cada composição calcula seu custo normalmente;
        quando essa composição é usada pelo pai como AX/TF,
        o pai recebe o custo unitário total da filha arredondado
        para duas casas.

    EQ/MO/MA permanecem exatamente com o cálculo atual.
    """

    def __init__(
        self,
        monetary_values: MonetaryValueResolver,
    ) -> None:
        self.monetary_values = monetary_values
        self.cache_a: dict[int, NodeComparison] = {}
        self.cache_b: dict[int, NodeComparison] = {}

    def calculate(
        self,
        node: CompositionNode,
        depth: int = 0,
    ) -> NodeComparison:
        """Calcula A e B recursivamente para todo o nó."""
        node_id = id(node)

        if node_id in self.cache_a:
            return self.cache_a[node_id]

        own_cost = self._calculate_own_cost(node)

        children_a = ZERO
        children_b = ZERO
        edges: list[EdgeComparison] = []

        for child in node.children:
            child_result = self.calculate(
                child,
                depth=depth + 1,
            )

            reference_quantity = round_sicro(
                child.reference_quantity or ZERO
            )

            line_a = round_sicro(
                reference_quantity * child_result.total_a
            )

            child_b_exposed = round_sicro(
                child_result.total_b,
                TWO_PLACES,
            )

            line_b = round_sicro(
                reference_quantity * child_b_exposed
            )

            children_a += line_a
            children_b += line_b

            edges.append(
                EdgeComparison(
                    parent=node.composition.code,
                    child=child.composition.code,
                    reference_quantity=reference_quantity,
                    child_a=child_result.total_a,
                    child_b_exposed=child_b_exposed,
                    line_a=line_a,
                    line_b=line_b,
                    edge_delta=round_sicro(
                        line_b - line_a
                    ),
                )
            )

        children_a = round_sicro(children_a)
        children_b = round_sicro(children_b)

        total_a = round_sicro(
            own_cost + children_a
        )

        total_b = round_sicro(
            own_cost + children_b
        )

        comparison = NodeComparison(
            node_id=node_id,
            code=node.composition.code,
            depth=depth,
            path=self._build_path(node),
            own_cost=own_cost,
            children_a=children_a,
            children_b=children_b,
            total_a=total_a,
            total_b=total_b,
            exposed_b=round_sicro(
                total_b,
                TWO_PLACES,
            ),
            edges=edges,
        )

        self.cache_a[node_id] = comparison
        self.cache_b[node_id] = comparison

        return comparison

    def _calculate_own_cost(
        self,
        node: CompositionNode,
    ) -> Decimal:
        """Calcula EQ, MO, MA e FIC exatamente como no cálculo-base."""
        composition = node.composition

        if composition.production == ZERO:
            raise ValueError(
                f"Production cannot be zero: {composition.code}"
            )

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

        return round_sicro(
            equipment_cost
            + workman_cost
            + material_cost
            + fic_cost
        )

    def _equipment_line(
        self,
        composition,
        composition_input,
    ) -> Decimal:
        """Calcula uma linha EQ exatamente como no cálculo-base."""
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
            unproductive_quantity * unproductive_price
        )

        return productive_cost + unproductive_cost

    def _workman_line(
        self,
        composition,
        composition_input,
    ) -> Decimal:
        """Calcula uma linha MO exatamente como no cálculo-base."""
        quantity = round_sicro(
            composition_input.quantity
            / composition.production
        )

        price = self.monetary_values.workman_cost(
            composition_input.code
        )

        return round_sicro(
            quantity * price
        )

    def _material_line(
        self,
        composition_input,
    ) -> Decimal:
        """Calcula uma linha MA exatamente como no cálculo-base."""
        quantity = round_sicro(
            composition_input.quantity
        )

        price = self.monetary_values.material_cost(
            composition_input.code
        )

        return round_sicro(
            quantity * price
        )

    @staticmethod
    def _build_path(node: CompositionNode) -> str:
        """Monta o caminho da ocorrência até a raiz."""
        codes: list[str] = []
        current = node

        while current is not None:
            codes.append(current.composition.code)
            current = current.parent

        return " -> ".join(reversed(codes))

    def all_comparisons(self) -> list[NodeComparison]:
        """Retorna todas as comparações em ordem de profundidade."""
        values = list(self.cache_a.values())
        return sorted(
            values,
            key=lambda item: (
                item.depth,
                item.path,
                item.node_id,
            ),
        )

    def top_edges(self, limit: int = 30) -> list[EdgeComparison]:
        """Retorna as arestas com maior impacto absoluto."""
        edges: list[EdgeComparison] = []

        for result in self.cache_a.values():
            edges.extend(result.edges)

        return sorted(
            edges,
            key=lambda item: abs(item.edge_delta),
            reverse=True,
        )[:limit]


def format_money(value: Decimal) -> str:
    """Formata valores monetários com quatro casas decimais."""
    return (
        f"R$ {value:,.4f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def write_report(
    validator: TreeBValidator,
    root_result: NodeComparison,
) -> None:
    """Escreve o relatório completo da validação da árvore B."""
    output_path = (
        "tests/test_validate_tree_b_output.txt"
    )

    comparisons = validator.all_comparisons()
    edges = validator.top_edges()

    with open(output_path, "w", encoding="utf-8") as output:
        output.write(
            "VALIDAÇÃO DA HIPÓTESE DA ÁRVORE B\n"
        )
        output.write("=" * 130 + "\n")
        output.write(
            "A = filha propagada com custo interno completo\n"
        )
        output.write(
            "B = filha propagada ao pai com custo unitário total "
            "arredondado a 2 casas\n"
        )
        output.write(
            "EQ/MO/MA preservados exatamente no cálculo-base\n"
        )
        output.write("=" * 130 + "\n\n")

        output.write(
            "RESULTADO DA RAIZ\n"
        )
        output.write("-" * 130 + "\n")
        output.write(
            f"Árvore A: {format_money(root_result.total_a)}\n"
        )
        output.write(
            f"Árvore B: {format_money(root_result.total_b)}\n"
        )
        output.write(
            f"Oficial:  {format_money(OFFICIAL_TOTAL)}\n"
        )
        output.write(
            f"Delta A:  "
            f"{format_money(root_result.total_a - OFFICIAL_TOTAL)}\n"
        )
        output.write(
            f"Delta B:  "
            f"{format_money(root_result.total_b - OFFICIAL_TOTAL)}\n"
        )
        output.write(
            f"Melhora:  "
            f"{format_money(root_result.total_b - root_result.total_a)}\n"
        )
        output.write("\n")

        output.write(
            "MAIORES IMPACTOS NAS ARESTAS PAI → FILHA\n"
        )
        output.write("-" * 130 + "\n")
        output.write(
            f"{'#':>3} {'pai':>10} {'filha':>10} "
            f"{'Q':>10} {'A':>12} {'B usado':>12} "
            f"{'linha A':>12} {'linha B':>12} {'delta':>12}\n"
        )

        for index, edge in enumerate(edges, start=1):
            output.write(
                f"{index:>3} "
                f"{edge.parent:>10} "
                f"{edge.child:>10} "
                f"{edge.reference_quantity:>10.4f} "
                f"{edge.child_a:>12.4f} "
                f"{edge.child_b_exposed:>12.2f} "
                f"{edge.line_a:>12.4f} "
                f"{edge.line_b:>12.4f} "
                f"{edge.edge_delta:>12.4f}\n"
            )

        output.write("\n")
        output.write(
            "TODOS OS NÓS — EFEITO RECURSIVO\n"
        )
        output.write("-" * 130 + "\n")
        output.write(
            f"{'#':>4} {'nível':>5} {'código':>10} "
            f"{'próprio':>12} {'filhas A':>12} "
            f"{'filhas B':>12} {'total A':>12} "
            f"{'total B':>12} {'delta':>12} {'B exposto':>12}\n"
        )

        for index, result in enumerate(
            comparisons,
            start=1,
        ):
            output.write(
                f"{index:>4} "
                f"{result.depth:>5} "
                f"{result.code:>10} "
                f"{result.own_cost:>12.4f} "
                f"{result.children_a:>12.4f} "
                f"{result.children_b:>12.4f} "
                f"{result.total_a:>12.4f} "
                f"{result.total_b:>12.4f} "
                f"{result.node_delta:>12.4f} "
                f"{result.exposed_b:>12.2f}\n"
            )

            output.write(
                f"      caminho: {result.path}\n"
            )

        output.write("\n")
        output.write(
            "INTERPRETAÇÃO\n"
        )
        output.write("-" * 130 + "\n")
        output.write(
            "A diferença entre A e B em um nó é reincorporada "
            "pelos seus ancestrais quando o custo B do nó é "
            "novamente exposto em duas casas.\n"
        )


def main() -> None:
    """Executa a validação completa da hipótese da árvore B."""
    resolver = CompositionResolver(
        repository=CompositionRepository()
    )

    root = resolver.resolve_tree(
        composition_code=ROOT_CODE
    )

    monetary_values = MonetaryValueResolver(
        client=MonetaryValueApiClient()
    )

    validator = TreeBValidator(
        monetary_values=monetary_values
    )

    root_result = validator.calculate(root)

    write_report(
        validator=validator,
        root_result=root_result,
    )

    comparisons = validator.all_comparisons()

    print()
    print("=" * 120)
    print("VALIDAÇÃO DA HIPÓTESE DA ÁRVORE B")
    print("=" * 120)
    print(
        f"Árvore A: R$ {root_result.total_a}"
    )
    print(
        f"Árvore B: R$ {root_result.total_b}"
    )
    print(
        f"Oficial:  R$ {OFFICIAL_TOTAL}"
    )
    print(
        f"Delta A:  R$ "
        f"{root_result.total_a - OFFICIAL_TOTAL}"
    )
    print(
        f"Delta B:  R$ "
        f"{root_result.total_b - OFFICIAL_TOTAL}"
    )
    print(
        f"Melhora:  R$ "
        f"{root_result.total_b - root_result.total_a}"
    )
    print(
        f"Nós:      {len(comparisons)}"
    )

    print()
    print("MAIORES IMPACTOS PAI → FILHA")
    print("-" * 120)

    for index, edge in enumerate(
        validator.top_edges(limit=15),
        start=1,
    ):
        print(
            f"{index:>2}. "
            f"{edge.parent} -> {edge.child} | "
            f"Q={edge.reference_quantity:.4f} | "
            f"A={edge.child_a:.4f} | "
            f"B={edge.child_b_exposed:.2f} | "
            f"delta linha={edge.edge_delta:+.4f}"
        )

    print()
    print(
        "Arquivo: "
        "tests/test_validate_tree_b_output.txt"
    )


if __name__ == "__main__":
    main()
