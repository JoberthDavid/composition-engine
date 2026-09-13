from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.domain.composition_node import CompositionNode
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver


FOUR = Decimal("0.0001")
TWO = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")

ROOT_CODE = "0919013"
OFFICIAL = Decimal("105890.00")


def round_sicro(value: Decimal, places: Decimal) -> Decimal:
    """Arredonda com ROUND_HALF_UP."""
    return value.quantize(places, rounding=ROUND_HALF_UP)


class MonetaryValueResolver:
    """Resolve valores monetários com cache."""

    def __init__(
        self,
        client: MonetaryValueApiClient | None = None,
    ) -> None:
        self.client = client or MonetaryValueApiClient()
        self.cache: dict[tuple[str, str, str], Decimal] = {}

    def get(
        self,
        code: str,
        type_system: str,
        classification: str,
    ) -> Decimal:
        """Obtém um valor monetário filtrado."""
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
            f"Valor não encontrado: {code} / "
            f"{type_system} / {classification}"
        )

    def eq_prices(self, code: str) -> tuple[Decimal, Decimal]:
        """Obtém preços produtivo e improdutivo."""
        return (
            self.get(code, "ON", "PR"),
            self.get(code, "ON", "IM"),
        )

    def mo_price(self, code: str) -> Decimal:
        """Obtém custo de mão de obra."""
        return self.get(code, "ON", "CT")

    def ma_price(self, code: str) -> Decimal:
        """Obtém custo de material."""
        return self.get(code, "NA", "CT")


@dataclass
class Result:
    """Armazena o resultado de uma variante."""

    name: str
    total: Decimal
    children_cost: Decimal


class AxTfPrecisionTester:
    """
    Testa somente a precisão entre custo unitário e linha AX/TF.

    Todas as variantes preservam:
    - cálculo de EQ/MO/MA;
    - FIC;
    - quantidade AX/TF em quatro casas.

    Variantes:
    1. B1: custo filha em 2 casas; linha AX/TF em 4 casas.
    2. B2: custo filha em 2 casas; linha AX/TF sem arredondamento.
    3. B3: custo filha em 2 casas; linha AX/TF em 2 casas.
    4. B4: custo filha interno; linha AX/TF em 4 casas
       (controle equivalente à propagação sem corte do custo unitário).
    """

    def __init__(
        self,
        monetary_values: MonetaryValueResolver,
    ) -> None:
        self.monetary_values = monetary_values
        self.total_nodes = 0

    def calculate(
        self,
        node: CompositionNode,
        variant: str,
    ) -> Decimal:
        """Calcula o custo total da composição em uma variante."""
        self.total_nodes += 1
        composition = node.composition

        own_cost = self._own_cost(composition)
        children_cost = ZERO

        for child in node.children:
            child_internal = self.calculate(
                child,
                variant,
            )

            reference_quantity = round_sicro(
                child.reference_quantity or ZERO,
                FOUR,
            )

            if variant == "B1":
                child_unit = round_sicro(
                    child_internal,
                    TWO,
                )
                line = round_sicro(
                    reference_quantity * child_unit,
                    FOUR,
                )

            elif variant == "B2":
                child_unit = round_sicro(
                    child_internal,
                    TWO,
                )
                line = reference_quantity * child_unit

            elif variant == "B3":
                child_unit = round_sicro(
                    child_internal,
                    TWO,
                )
                line = round_sicro(
                    reference_quantity * child_unit,
                    TWO,
                )

            elif variant == "B4":
                child_unit = child_internal
                line = round_sicro(
                    reference_quantity * child_unit,
                    FOUR,
                )

            else:
                raise ValueError(f"Variante desconhecida: {variant}")

            children_cost += line

        children_cost = round_sicro(
            children_cost,
            FOUR,
        )

        return round_sicro(
            own_cost + children_cost,
            FOUR,
        )

    def inspect_root_edges(
        self,
        root: CompositionNode,
    ) -> list[tuple[str, Decimal, Decimal, Decimal, Decimal]]:
        """Compara as linhas AX/TF diretas da raiz nas variantes."""
        rows = []

        for child in root.children:
            internal = self.calculate(child, "B4")

            quantity = round_sicro(
                child.reference_quantity or ZERO,
                FOUR,
            )

            b1_unit = round_sicro(internal, TWO)
            b1_line = round_sicro(
                quantity * b1_unit,
                FOUR,
            )

            b2_line = quantity * b1_unit
            b3_line = round_sicro(
                quantity * b1_unit,
                TWO,
            )

            b4_line = round_sicro(
                quantity * internal,
                FOUR,
            )

            rows.append(
                (
                    child.composition.code,
                    quantity,
                    b4_line,
                    b1_line,
                    b3_line,
                )
            )

        return rows

    def _own_cost(self, composition) -> Decimal:
        """Calcula EQ, MO, MA e FIC com a lógica atual."""
        if composition.production == ZERO:
            raise ValueError(
                f"Production cannot be zero: {composition.code}"
            )

        equipment = ZERO
        workman = ZERO
        material = ZERO

        for item in composition.inputs:
            if item.is_composition_reference():
                continue

            if item.is_transport():
                continue

            if item.group == "EQ":
                equipment += self._equipment_line(
                    composition,
                    item,
                )
            elif item.group == "MO":
                workman += self._workman_line(
                    composition,
                    item,
                )
            elif item.group == "MA":
                material += self._material_line(item)

        equipment = round_sicro(equipment, FOUR)
        workman = round_sicro(workman, FOUR)
        material = round_sicro(material, FOUR)

        fic_base = round_sicro(
            equipment + workman,
            FOUR,
        )

        fic = round_sicro(
            fic_base * composition.fic,
            FOUR,
        )

        return round_sicro(
            equipment + workman + material + fic,
            FOUR,
        )

    def _equipment_line(self, composition, item) -> Decimal:
        """Calcula uma linha EQ exatamente como no cálculo-base."""
        base = item.quantity / composition.production

        use = (
            item.use
            if item.use is not None
            else ONE
        )

        productive_quantity = round_sicro(
            base * use,
            FOUR,
        )

        unproductive_quantity = round_sicro(
            base * (ONE - use),
            FOUR,
        )

        productive_price, unproductive_price = (
            self.monetary_values.eq_prices(item.code)
        )

        productive_cost = round_sicro(
            productive_quantity * productive_price,
            FOUR,
        )

        unproductive_cost = round_sicro(
            unproductive_quantity * unproductive_price,
            FOUR,
        )

        return productive_cost + unproductive_cost

    def _workman_line(self, composition, item) -> Decimal:
        """Calcula uma linha MO exatamente como no cálculo-base."""
        quantity = round_sicro(
            item.quantity / composition.production,
            FOUR,
        )

        return round_sicro(
            quantity * self.monetary_values.mo_price(item.code),
            FOUR,
        )

    def _material_line(self, item) -> Decimal:
        """Calcula uma linha MA exatamente como no cálculo-base."""
        quantity = round_sicro(
            item.quantity,
            FOUR,
        )

        return round_sicro(
            quantity * self.monetary_values.ma_price(item.code),
            FOUR,
        )


def fmt(value: Decimal) -> str:
    """Formata moeda com quatro casas."""
    return (
        f"R$ {value:,.4f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def main() -> None:
    """Executa as quatro variantes de precisão."""
    resolver = CompositionResolver(
        repository=CompositionRepository()
    )
    root = resolver.resolve_tree(ROOT_CODE)

    monetary = MonetaryValueResolver(
        client=MonetaryValueApiClient()
    )

    variants = [
        ("B1", "custo filha 2 casas + linha 4 casas"),
        ("B2", "custo filha 2 casas + linha sem arredondamento"),
        ("B3", "custo filha 2 casas + linha 2 casas"),
        ("B4", "custo filha interno + linha 4 casas"),
    ]

    results: list[Result] = []

    for code, name in variants:
        tester = AxTfPrecisionTester(monetary)
        total = tester.calculate(root, code)

        own_root = tester._own_cost(root.composition)

        results.append(
            Result(
                name=f"{code} — {name}",
                total=total,
                children_cost=round_sicro(
                    total - own_root,
                    FOUR,
                ),
            )
        )

    print()
    print("=" * 120)
    print("TESTE — CUSTO UNITÁRIO 2 CASAS × CUSTO DA LINHA AX/TF")
    print("=" * 120)
    print(f"Raiz: {ROOT_CODE}")
    print("EQ/MO/MA: preservados exatamente")
    print("Quantidade AX/TF: 4 casas")
    print(f"Oficial: {fmt(OFFICIAL)}")
    print()

    print("COMPARAÇÃO DAS VARIANTES")
    print("-" * 120)

    for result in results:
        delta = result.total - OFFICIAL

        print(
            f"{result.name:<62} "
            f"{fmt(result.total):>18} | "
            f"delta {fmt(delta):>14} | "
            f"filhas {fmt(result.children_cost):>16}"
        )

    print()
    print("LINHAS DIRETAS DA RAIZ")
    print("-" * 120)
    print(
        f"{'filha':>10} {'Q':>10} {'B4 interno':>16} "
        f"{'B1 linha 4c':>16} {'B3 linha 2c':>16}"
    )

    tester = AxTfPrecisionTester(monetary)

    # Evita recomputar desnecessariamente o mesmo diagnóstico
    for child in root.children:
        internal = tester.calculate(child, "B4")

        quantity = round_sicro(
            child.reference_quantity or ZERO,
            FOUR,
        )

        child_two = round_sicro(
            internal,
            TWO,
        )

        b1_line = round_sicro(
            quantity * child_two,
            FOUR,
        )

        b3_line = round_sicro(
            quantity * child_two,
            TWO,
        )

        print(
            f"{child.composition.code:>10} "
            f"{quantity:>10.4f} "
            f"{fmt(internal):>16} "
            f"{fmt(b1_line):>16} "
            f"{fmt(b3_line):>16}"
        )

    output_path = (
        "tests/test_ax_tf_unit_vs_line_precision_output.txt"
    )

    with open(output_path, "w", encoding="utf-8") as output:
        output.write(
            "TESTE — CUSTO UNITÁRIO 2 CASAS × LINHA AX/TF\n"
        )
        output.write("=" * 120 + "\n")
        output.write(
            "Somente a fronteira custo unitário -> linha AX/TF "
            "foi alterada.\n"
        )
        output.write(
            "EQ/MO/MA e FIC preservados.\n\n"
        )

        for result in results:
            delta = result.total - OFFICIAL
            output.write(
                f"{result.name}\n"
                f"  total: {result.total}\n"
                f"  delta: {delta}\n"
                f"  filhas: {result.children_cost}\n\n"
            )

        output.write(
            "Linhas diretas da raiz:\n"
        )

        for child in root.children:
            internal = tester.calculate(child, "B4")
            quantity = round_sicro(
                child.reference_quantity or ZERO,
                FOUR,
            )
            child_two = round_sicro(
                internal,
                TWO,
            )
            b1_line = round_sicro(
                quantity * child_two,
                FOUR,
            )
            b3_line = round_sicro(
                quantity * child_two,
                TWO,
            )

            output.write(
                f"{child.composition.code} | "
                f"Q={quantity} | "
                f"interno={internal} | "
                f"B1={b1_line} | "
                f"B3={b3_line}\n"
            )

    print()
    print(
        f"Arquivo: {output_path}"
    )


if __name__ == "__main__":
    main()