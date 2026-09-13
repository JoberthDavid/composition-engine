from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from app.domain.composition_node import CompositionNode
from app.infrastructure.monetary_value_api_client import MonetaryValueApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver


FOUR_PLACES = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

ROOT_CODE = "0919013"
OUTPUT_PATH = "tests/test_recursive_fic_unit_output.txt"


def round_sicro(value: Decimal) -> Decimal:
    """
    Arredonda um valor para quatro casas decimais.
    """
    return value.quantize(
        FOUR_PLACES,
        rounding=ROUND_HALF_UP,
    )


class MonetaryValueResolver:
    """
    Resolve os valores monetários dos insumos.

    Sistemas utilizados:

        ON:
            equipamentos e mão de obra

        NA:
            materiais

    Classificações:

        EQ:
            PR = preço produtivo
            IM = preço improdutivo

        MO:
            CT = custo

        MA:
            CT = custo
    """

    def __init__(
        self,
        client: MonetaryValueApiClient | None = None,
    ) -> None:
        self.client = client or MonetaryValueApiClient()

        self.cache: dict[
            tuple[str, str, str],
            Decimal,
        ] = {}

    def get_value(
        self,
        code: str,
        type_system: str,
        classification: str,
    ) -> Decimal:
        """
        Retorna o valor monetário correspondente ao sistema
        e à classificação solicitados.
        """

        cache_key = (
            code,
            type_system,
            classification,
        )

        if cache_key in self.cache:
            return self.cache[cache_key]

        values = self.client.get_values_by_code(code)

        for item in values:

            if (
                item.get("type_system") == type_system
                and item.get("classification") == classification
            ):
                value = Decimal(
                    item["monetary_value"]
                )

                self.cache[cache_key] = value

                return value

        raise ValueError(
            "Valor monetário não encontrado: "
            f"código={code}, "
            f"sistema={type_system}, "
            f"classificação={classification}"
        )

    def get_equipment_prices(
        self,
        code: str,
    ) -> tuple[Decimal, Decimal]:
        """
        Retorna preço produtivo e improdutivo de equipamento.
        """

        productive_price = self.get_value(
            code=code,
            type_system="ON",
            classification="PR",
        )

        unproductive_price = self.get_value(
            code=code,
            type_system="ON",
            classification="IM",
        )

        return (
            productive_price,
            unproductive_price,
        )

    def get_workman_cost(
        self,
        code: str,
    ) -> Decimal:
        """
        Retorna o custo de mão de obra.
        """

        return self.get_value(
            code=code,
            type_system="ON",
            classification="CT",
        )

    def get_material_cost(
        self,
        code: str,
    ) -> Decimal:
        """
        Retorna o custo de material.
        """

        return self.get_value(
            code=code,
            type_system="NA",
            classification="CT",
        )

@dataclass
class NodeCostResult:
    """
    Resultado do cálculo de uma composição.

    O total representa o custo unitário completo da composição,
    incluindo recursos próprios, FIC próprio e composições filhas.
    """

    code: str

    equipment_cost: Decimal = ZERO
    workman_cost: Decimal = ZERO
    material_cost: Decimal = ZERO

    fic_base: Decimal = ZERO
    fic_cost: Decimal = ZERO

    own_cost: Decimal = ZERO
    children_cost: Decimal = ZERO

    total_cost: Decimal = ZERO

    children: list[dict] = field(
        default_factory=list
    )


class UnitRecursiveFicCalculator:
    """
    Calcula o custo unitário de uma composição de forma recursiva.

    Regras:

    EQ:
        quantidade / produção

    MO:
        quantidade / produção

    MA:
        quantidade

    FIC:
        (equipamentos + mão de obra) × FIC

    AX/TF:
        são referências para composições filhas.

    A composição filha é calculada primeiro como uma composição
    independente. Depois sua quantidade de referência é aplicada:

        custo_filha =
            quantidade_referencia × custo_unitario_filha
    """

    def __init__(
        self,
        monetary_values: MonetaryValueResolver,
    ) -> None:

        self.monetary_values = monetary_values

        self.processed_nodes = 0

    def calculate(
        self,
        node: CompositionNode,
    ) -> NodeCostResult:
        """
        Calcula o custo unitário completo de uma composição.
        """

        self.processed_nodes += 1

        composition = node.composition

        if composition.production == ZERO:
            raise ValueError(
                "Produção da composição igual a zero: "
                f"{composition.code}"
            )

        equipment_cost = ZERO
        workman_cost = ZERO
        material_cost = ZERO

        # ==============================================================
        # RECURSOS PRÓPRIOS
        # ==============================================================

        for composition_input in composition.inputs:

            # AX e TF são referências para outras composições.
            if composition_input.is_composition_reference():
                continue

            # Transportes serão tratados posteriormente.
            if composition_input.is_transport():
                continue

            if composition_input.group == "EQ":

                line_cost = self._calculate_equipment_line(
                    composition=composition,
                    composition_input=composition_input,
                )

                equipment_cost += line_cost

            elif composition_input.group == "MO":

                line_cost = self._calculate_workman_line(
                    composition=composition,
                    composition_input=composition_input,
                )

                workman_cost += line_cost

            elif composition_input.group == "MA":

                line_cost = self._calculate_material_line(
                    composition_input=composition_input,
                )

                material_cost += line_cost

        # Arredondamento da consolidação dos recursos.
        equipment_cost = round_sicro(
            equipment_cost
        )

        workman_cost = round_sicro(
            workman_cost
        )

        material_cost = round_sicro(
            material_cost
        )

        # ==============================================================
        # FIC
        # ==============================================================

        fic_base = round_sicro(
            equipment_cost + workman_cost
        )

        fic_cost = round_sicro(
            fic_base * composition.fic
        )

        # ==============================================================
        # CUSTO PRÓPRIO
        # ==============================================================

        own_cost = round_sicro(
            equipment_cost
            + workman_cost
            + material_cost
            + fic_cost
        )

        # ==============================================================
        # COMPOSIÇÕES FILHAS
        # ==============================================================

        children_cost = ZERO

        children_details = []

        for child in node.children:

            # ----------------------------------------------------------
            # Primeiro calcula a filha como custo unitário independente.
            # ----------------------------------------------------------

            child_result = self.calculate(
                child
            )

            # ----------------------------------------------------------
            # A quantidade da referência pertence ao pai.
            # ----------------------------------------------------------

            reference_quantity = round_sicro(
                child.reference_quantity
                if child.reference_quantity is not None
                else ZERO
            )

            # ----------------------------------------------------------
            # Aplica a quantidade da referência ao custo unitário.
            # ----------------------------------------------------------

            child_line_cost = round_sicro(
                reference_quantity
                * child_result.total_cost
            )

            children_cost += child_line_cost

            children_details.append(
                {
                    "code": child.composition.code,
                    "reference_quantity": reference_quantity,
                    "unit_cost": child_result.total_cost,
                    "accumulated_cost": child_line_cost,
                }
            )

        children_cost = round_sicro(
            children_cost
        )

        # ==============================================================
        # TOTAL
        # ==============================================================

        total_cost = round_sicro(
            own_cost + children_cost
        )

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

    def _calculate_equipment_line(
        self,
        composition,
        composition_input,
    ) -> Decimal:
        """
        Calcula uma linha de equipamento.

        A quantidade é dividida pela produção da composição.

        Depois é separada em:
            produtiva
            improdutiva

        Cada quantidade é arredondada individualmente.
        """

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
            self.monetary_values.get_equipment_prices(
                composition_input.code
            )
        )

        productive_cost = round_sicro(
            productive_quantity
            * productive_price
        )

        unproductive_cost = round_sicro(
            unproductive_quantity
            * unproductive_price
        )

        return round_sicro(
            productive_cost
            + unproductive_cost
        )

    def _calculate_workman_line(
        self,
        composition,
        composition_input,
    ) -> Decimal:
        """
        Calcula uma linha de mão de obra.

        A quantidade é dividida pela produção.
        """

        quantity = round_sicro(
            composition_input.quantity
            / composition.production
        )

        price = self.monetary_values.get_workman_cost(
            composition_input.code
        )

        return round_sicro(
            quantity * price
        )

    def _calculate_material_line(
        self,
        composition_input,
    ) -> Decimal:
        """
        Calcula uma linha de material.

        A quantidade de material NÃO é dividida pela produção.
        """

        quantity = round_sicro(
            composition_input.quantity
        )

        price = self.monetary_values.get_material_cost(
            composition_input.code
        )

        return round_sicro(
            quantity * price
        )


def count_nodes(
    node: CompositionNode,
) -> int:
    """
    Conta os nós existentes na árvore.
    """

    return len(
        node.walk()
    )


def write_node_tree(
    output,
    node: CompositionNode,
    result: NodeCostResult,
    level: int,
    calculator: UnitRecursiveFicCalculator,
) -> None:
    """
    Escreve o resultado da composição e de suas filhas no diagnóstico.
    """

    indent = "    " * level

    composition = node.composition

    output.write(
        "\n"
        + indent
        + "=" * 100
        + "\n"
    )

    output.write(
        f"{indent}COMPOSIÇÃO: {composition.code}\n"
    )

    output.write(
        f"{indent}ID: {composition.identifier}\n"
    )

    output.write(
        f"{indent}DESCRIÇÃO: {composition.description}\n"
    )

    output.write(
        f"{indent}UNIDADE: {composition.unit}\n"
    )

    output.write(
        f"{indent}PRODUÇÃO: {composition.production}\n"
    )

    output.write(
        f"{indent}FIC: {composition.fic}\n"
    )

    output.write(
        f"{indent}QUANTIDADE DE REFERÊNCIA NO PAI: "
        f"{node.reference_quantity}\n"
    )

    output.write(
        f"{indent}QUANTIDADE ACUMULADA NA ÁRVORE: "
        f"{node.accumulated_quantity}\n"
    )

    output.write(
        "\n"
        f"{indent}CUSTO UNITÁRIO DA COMPOSIÇÃO\n"
    )

    output.write(
        f"{indent}  Equipamentos: "
        f"R$ {result.equipment_cost}\n"
    )

    output.write(
        f"{indent}  Mão de obra: "
        f"R$ {result.workman_cost}\n"
    )

    output.write(
        f"{indent}  Materiais: "
        f"R$ {result.material_cost}\n"
    )

    output.write(
        f"{indent}  Base FIC: "
        f"R$ {result.fic_base}\n"
    )

    output.write(
        f"{indent}  FIC: "
        f"R$ {result.fic_cost}\n"
    )

    output.write(
        f"{indent}  Custo próprio: "
        f"R$ {result.own_cost}\n"
    )

    output.write(
        f"{indent}  Custo das filhas: "
        f"R$ {result.children_cost}\n"
    )

    output.write(
        f"{indent}  TOTAL UNITÁRIO: "
        f"R$ {result.total_cost}\n"
    )

    if result.children:

        output.write(
            f"\n{indent}FILHAS\n"
        )

        for child in result.children:

            output.write(
                f"{indent}  "
                f"{child['code']} | "
                f"referência={child['reference_quantity']} | "
                f"custo_unitário={child['unit_cost']} | "
                f"custo_acumulado={child['accumulated_cost']}\n"
            )

    for child in node.children:

        # Calcula novamente somente para gerar o diagnóstico
        # detalhado da subárvore.
        child_result = calculator.calculate(
            child
        )

        write_node_tree(
            output=output,
            node=child,
            result=child_result,
            level=level + 1,
            calculator=calculator,
        )


def write_result(
    root: CompositionNode,
    result: NodeCostResult,
    calculator: UnitRecursiveFicCalculator,
) -> None:
    """
    Grava o resultado principal e o diagnóstico no arquivo TXT.
    """

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as output:

        output.write(
            "DIAGNÓSTICO RECURSIVO POR CUSTO UNITÁRIO\n"
        )

        output.write(
            "=" * 100
            + "\n"
        )

        output.write(
            f"Composição raiz: "
            f"{root.composition.code}\n"
        )

        output.write(
            "Modelo: composição filha calculada como custo unitário "
            "independente antes de ser acumulada no pai.\n"
        )

        output.write(
            "EQ: quantidade / produção\n"
        )

        output.write(
            "MO: quantidade / produção\n"
        )

        output.write(
            "MA: quantidade sem divisão pela produção\n"
        )

        output.write(
            "FIC: (EQ + MO) × FIC\n"
        )

        output.write(
            "AX/TF: quantidade da referência × custo unitário da filha\n"
        )

        output.write(
            "Arredondamento: 4 casas decimais, ROUND_HALF_UP\n"
        )

        output.write(
            "Transportes: ainda não incorporados ao custo\n"
        )

        output.write(
            "=" * 100
            + "\n\n"
        )

        output.write(
            "RESULTADO FINAL\n"
        )

        output.write(
            f"Nós processados: "
            f"{calculator.processed_nodes}\n"
        )

        output.write(
            f"Equipamentos da raiz: "
            f"R$ {result.equipment_cost}\n"
        )

        output.write(
            f"Mão de obra da raiz: "
            f"R$ {result.workman_cost}\n"
        )

        output.write(
            f"Materiais da raiz: "
            f"R$ {result.material_cost}\n"
        )

        output.write(
            f"Base FIC da raiz: "
            f"R$ {result.fic_base}\n"
        )

        output.write(
            f"FIC da raiz: "
            f"R$ {result.fic_cost}\n"
        )

        output.write(
            f"Custo próprio da raiz: "
            f"R$ {result.own_cost}\n"
        )

        output.write(
            f"Custo das filhas: "
            f"R$ {result.children_cost}\n"
        )

        output.write(
            f"TOTAL CALCULADO: "
            f"R$ {result.total_cost}\n"
        )

        output.write(
            "\n"
        )

        output.write(
            "FILHAS DIRETAS DA RAIZ\n"
        )

        output.write(
            "-" * 100
            + "\n"
        )

        for child in result.children:

            output.write(
                f"{child['code']} | "
                f"referência={child['reference_quantity']} | "
                f"custo_unitário={child['unit_cost']} | "
                f"custo_acumulado={child['accumulated_cost']}\n"
            )


def print_root_children(
    root: CompositionNode,
    calculator: UnitRecursiveFicCalculator,
) -> None:
    """
    Imprime no terminal o custo unitário das filhas diretas da raiz.
    """

    print()
    print(
        "=== FILHAS DIRETAS DA RAIZ ==="
    )

    print(
        "-" * 100
    )

    for child in root.children:

        child_result = calculator.calculate(
            child
        )

        reference_quantity = round_sicro(
            child.reference_quantity
            if child.reference_quantity is not None
            else ZERO
        )

        accumulated_cost = round_sicro(
            reference_quantity
            * child_result.total_cost
        )

        print(
            f"{child.composition.code}: "
            f"ref={reference_quantity} | "
            f"custo_unit={child_result.total_cost} | "
            f"custo_acum={accumulated_cost}"
        )


def main() -> None:
    """
    Executa o teste integrado.
    """

    resolver = CompositionResolver(
        repository=CompositionRepository()
    )

    root = resolver.resolve_tree(
        ROOT_CODE
    )

    monetary_values = MonetaryValueResolver(
        client=MonetaryValueApiClient()
    )

    calculator = UnitRecursiveFicCalculator(
        monetary_values=monetary_values
    )

    # Primeiro cálculo oficial.
    result = calculator.calculate(
        root
    )

    # Impressão das filhas diretas.
    #
    # Esta chamada recalcula as filhas somente para diagnóstico.
    print_root_children(
        root=root,
        calculator=calculator,
    )

    # Grava o resultado do primeiro cálculo.
    #
    # Não utiliza os resultados recalculados acima.
    calculator.processed_nodes = 0

    calculator.calculate(root)

    calculator.processed_nodes = 0

    # Mantém o resultado original como resultado oficial.
    write_result(
        root=root,
        result=result,
        calculator=calculator,
    )

    print()
    print(
        "TESTE RECURSIVO POR CUSTO UNITÁRIO CONCLUÍDO"
    )

    print(
        f"Nós processados: "
        f"{count_nodes(root)}"
    )

    print(
        f"Custo próprio da raiz: "
        f"R$ {result.own_cost}"
    )

    print(
        f"Custo das filhas: "
        f"R$ {result.children_cost}"
    )

    print(
        f"Total calculado: "
        f"R$ {result.total_cost}"
    )

    print(
        f"Arquivo: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()