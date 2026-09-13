from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from app.infrastructure.composition_api_client import (
    CompositionApiClient,
)
from app.infrastructure.monetary_value_api_client import (
    MonetaryValueApiClient,
)
from app.repositories.composition_repository import (
    CompositionRepository,
)
from app.services.composition_resolver import (
    CompositionResolver,
)


ROOT_COMPOSITION_CODE = "0919013"

ROUNDING_PLACES = Decimal("0.0001")

OUTPUT_FILE = Path(
    "tests/test_recursive_fic_output.txt"
)


def round_sicro(
    value: Decimal,
) -> Decimal:
    """
    Arredonda um valor decimal para 4 casas decimais.

    O arredondamento é aplicado individualmente
    ao resultado de cada linha.
    """

    return value.quantize(
        ROUNDING_PLACES,
        rounding=ROUND_HALF_UP,
    )


def format_decimal(
    value: Decimal,
) -> str:
    """
    Formata um Decimal para diagnóstico.
    """

    return f"{value:.10f}"


def format_money(
    value: Decimal,
) -> str:
    """
    Formata um valor monetário.
    """

    return f"R$ {value:.4f}"


def get_monetary_value(
    values: list[dict],
    type_system: str,
    classification: str,
) -> Decimal:
    """
    Localiza um valor monetário específico.
    """

    for value in values:

        if value.get("type_system") != type_system:
            continue

        if value.get("classification") != classification:
            continue

        return Decimal(
            str(
                value["monetary_value"]
            )
        )

    raise ValueError(
        "Valor monetário não encontrado: "
        f"type_system={type_system}, "
        f"classification={classification}"
    )


class MonetaryValueResolver:
    """
    Resolve e armazena em cache os valores monetários
    dos recursos.
    """

    def __init__(
        self,
        client: MonetaryValueApiClient,
    ) -> None:
        self.client = client

        self.cache: dict[
            str,
            list[dict],
        ] = {}

    def get_values(
        self,
        code: str,
    ) -> list[dict]:
        """
        Obtém os valores monetários de um recurso.
        """

        if code not in self.cache:

            self.cache[code] = (
                self.client.get_values_by_code(
                    code
                )
            )

        return self.cache[code]


class NodeCostResult:
    """
    Armazena o resultado completo do cálculo
    de uma ocorrência de composição.
    """

    def __init__(
        self,
        code: str,
    ) -> None:

        self.code = code

        self.equipment_cost = Decimal("0")

        self.workman_cost = Decimal("0")

        self.material_cost = Decimal("0")

        self.fic_base = Decimal("0")

        self.fic_cost = Decimal("0")

        self.children_cost = Decimal("0")

        self.total_cost = Decimal("0")

        self.children: list[
            NodeCostResult
        ] = []


class RecursiveFicCalculator:
    """
    Calcula recursivamente o custo de cada composição.

    Regras:

    EQ:
        quantidade da linha × quantidade acumulada
        ÷ produção.

    MO:
        quantidade da linha × quantidade acumulada
        ÷ produção.

    MA:
        quantidade da linha × quantidade acumulada.

    FIC:
        (custo de equipamentos + custo de mão de obra)
        × FIC.

    AX e TF:
        são processados recursivamente.

    O custo calculado da composição filha já contém
    o seu próprio FIC e é acumulado no pai.
    """

    def __init__(
        self,
        monetary_value_resolver: MonetaryValueResolver,
        output,
    ) -> None:

        self.monetary_value_resolver = (
            monetary_value_resolver
        )

        self.output = output

        self.node_counter = 0

    def write(
        self,
        text: str = "",
    ) -> None:
        """
        Escreve uma linha no arquivo de diagnóstico.
        """

        self.output.write(
            text + "\n"
        )

    def calculate_node(
        self,
        node,
        depth: int = 0,
    ) -> NodeCostResult:
        """
        Calcula uma ocorrência de composição
        e todas as suas composições filhas.
        """

        self.node_counter += 1

        node_number = self.node_counter

        composition = node.composition

        production = composition.production

        fic_rate = composition.fic

        accumulated_quantity = (
            node.accumulated_quantity
        )

        result = NodeCostResult(
            code=composition.code
        )

        indent = "    " * depth

        # ==================================================================
        # CABEÇALHO DO NÓ
        # ==================================================================

        self.write()
        self.write(
            "=" * 140
        )

        self.write(
            f"{indent}NÓ #{node_number}"
        )

        self.write(
            f"{indent}NÍVEL: {depth}"
        )

        self.write(
            f"{indent}CAMINHO: "
            f"{self._build_path(node)}"
        )

        self.write(
            f"{indent}COMPOSIÇÃO: "
            f"{composition.code}"
        )

        self.write(
            f"{indent}ID: "
            f"{composition.identifier}"
        )

        self.write(
            f"{indent}DESCRIÇÃO: "
            f"{composition.description}"
        )

        self.write(
            f"{indent}UNIDADE: "
            f"{composition.unit}"
        )

        self.write(
            f"{indent}PRODUÇÃO: "
            f"{production}"
        )

        self.write(
            f"{indent}FIC: "
            f"{fic_rate}"
        )

        self.write(
            f"{indent}QUANTIDADE ACUMULADA: "
            f"{accumulated_quantity}"
        )

        self.write(
            f"{indent}QUANTIDADE DE LINHAS: "
            f"{len(composition.inputs)}"
        )

        self.write(
            f"{indent}QUANTIDADE DE FILHOS: "
            f"{len(node.children)}"
        )

        self.write(
            "-" * 140
        )

        # ==================================================================
        # RECURSOS PRÓPRIOS
        # ==================================================================

        self._calculate_own_resources(
            node=node,
            result=result,
            indent=indent,
        )

        # ==================================================================
        # FIC
        # ==================================================================

        result.fic_base = (
            result.equipment_cost
            + result.workman_cost
        )

        result.fic_cost = round_sicro(
            result.fic_base
            * fic_rate
        )

        self.write()
        self.write(
            f"{indent}CÁLCULO DO FIC"
        )

        self.write(
            f"{indent}  Equipamentos: "
            f"{format_money(result.equipment_cost)}"
        )

        self.write(
            f"{indent}  Mão de obra: "
            f"{format_money(result.workman_cost)}"
        )

        self.write(
            f"{indent}  Base FIC: "
            f"{format_money(result.fic_base)}"
        )

        self.write(
            f"{indent}  FIC decimal: "
            f"{format_decimal(fic_rate)}"
        )

        self.write(
            f"{indent}  FIC calculado: "
            f"{format_money(result.fic_cost)}"
        )

        # ==================================================================
        # FILHAS
        # ==================================================================

        self.write()
        self.write(
            f"{indent}COMPOSIÇÕES FILHAS"
        )

        if not node.children:

            self.write(
                f"{indent}  Nenhuma."
            )

        for child in node.children:

            child_result = (
                self.calculate_node(
                    node=child,
                    depth=depth + 1,
                )
            )

            result.children.append(
                child_result
            )

            result.children_cost += (
                child_result.total_cost
            )

        # ==================================================================
        # TOTAL
        # ==================================================================

        own_cost = (
            result.equipment_cost
            + result.workman_cost
            + result.material_cost
            + result.fic_cost
        )

        result.total_cost = round_sicro(
            own_cost
            + result.children_cost
        )

        self.write()
        self.write(
            f"{indent}RESUMO DO NÓ"
        )

        self.write(
            f"{indent}  Custo equipamentos: "
            f"{format_money(result.equipment_cost)}"
        )

        self.write(
            f"{indent}  Custo mão de obra: "
            f"{format_money(result.workman_cost)}"
        )

        self.write(
            f"{indent}  Custo materiais: "
            f"{format_money(result.material_cost)}"
        )

        self.write(
            f"{indent}  Custo FIC: "
            f"{format_money(result.fic_cost)}"
        )

        self.write(
            f"{indent}  Custo próprio: "
            f"{format_money(own_cost)}"
        )

        self.write(
            f"{indent}  Custo das filhas: "
            f"{format_money(result.children_cost)}"
        )

        self.write()

        self.write(
            f"{indent}>>> TOTAL DA COMPOSIÇÃO "
            f"{composition.code}: "
            f"{format_money(result.total_cost)}"
        )

        self.write(
            "=" * 140
        )

        return result

    def _calculate_own_resources(
        self,
        node,
        result: NodeCostResult,
        indent: str,
    ) -> None:
        """
        Calcula equipamentos, mão de obra e materiais
        pertencentes diretamente à composição.
        """

        composition = node.composition

        production = composition.production

        accumulated_quantity = (
            node.accumulated_quantity
        )

        # ==============================================================
        # EQUIPAMENTOS
        # ==============================================================

        self.write()
        self.write(
            f"{indent}EQUIPAMENTOS"
        )

        equipment_found = False

        for composition_input in (
            composition.equipments
        ):

            equipment_found = True

            values = (
                self.monetary_value_resolver.get_values(
                    composition_input.code
                )
            )

            productive_price = (
                get_monetary_value(
                    values=values,
                    type_system="ON",
                    classification="PR",
                )
            )

            unproductive_price = (
                get_monetary_value(
                    values=values,
                    type_system="ON",
                    classification="IM",
                )
            )

            use = (
                composition_input.use
                if composition_input.use
                is not None
                else Decimal("1")
            )

            productive_quantity = (
                composition_input.quantity
                * use
                * accumulated_quantity
                / production
            )

            unproductive_quantity = (
                composition_input.quantity
                * (
                    Decimal("1")
                    - use
                )
                * accumulated_quantity
                / production
            )

            productive_quantity_rounded = (
                round_sicro(
                    productive_quantity
                )
            )

            unproductive_quantity_rounded = (
                round_sicro(
                    unproductive_quantity
                )
            )

            productive_cost = (
                productive_quantity_rounded
                * productive_price
            )

            unproductive_cost = (
                unproductive_quantity_rounded
                * unproductive_price
            )

            line_cost = (
                productive_cost
                + unproductive_cost
            )

            result.equipment_cost += (
                line_cost
            )

            self.write()
            self.write(
                f"{indent}  [EQ] "
                f"{composition_input.code}"
            )

            self.write(
                f"{indent}    "
                f"{composition_input.description}"
            )

            self.write(
                f"{indent}    Quantidade original: "
                f"{composition_input.quantity}"
            )

            self.write(
                f"{indent}    Use: "
                f"{use}"
            )

            self.write(
                f"{indent}    Quantidade produtiva "
                f"antes arredondamento: "
                f"{productive_quantity}"
            )

            self.write(
                f"{indent}    Quantidade produtiva "
                f"arredondada: "
                f"{productive_quantity_rounded}"
            )

            self.write(
                f"{indent}    Quantidade improdutiva "
                f"antes arredondamento: "
                f"{unproductive_quantity}"
            )

            self.write(
                f"{indent}    Quantidade improdutiva "
                f"arredondada: "
                f"{unproductive_quantity_rounded}"
            )

            self.write(
                f"{indent}    Preço produtivo: "
                f"{productive_price}"
            )

            self.write(
                f"{indent}    Preço improdutivo: "
                f"{unproductive_price}"
            )

            self.write(
                f"{indent}    Custo produtivo: "
                f"{format_money(productive_cost)}"
            )

            self.write(
                f"{indent}    Custo improdutivo: "
                f"{format_money(unproductive_cost)}"
            )

            self.write(
                f"{indent}    "
                f"CUSTO DA LINHA EQ: "
                f"{format_money(line_cost)}"
            )

        if not equipment_found:

            self.write(
                f"{indent}  Nenhum equipamento."
            )

        # ==============================================================
        # MÃO DE OBRA
        # ==============================================================

        self.write()
        self.write(
            f"{indent}MÃO DE OBRA"
        )

        workman_found = False

        for composition_input in (
            composition.workmen
        ):

            workman_found = True

            values = (
                self.monetary_value_resolver.get_values(
                    composition_input.code
                )
            )

            price = get_monetary_value(
                values=values,
                type_system="ON",
                classification="CT",
            )

            quantity = (
                composition_input.quantity
                * accumulated_quantity
                / production
            )

            quantity_rounded = round_sicro(
                quantity
            )

            line_cost = (
                quantity_rounded
                * price
            )

            result.workman_cost += (
                line_cost
            )

            self.write()
            self.write(
                f"{indent}  [MO] "
                f"{composition_input.code}"
            )

            self.write(
                f"{indent}    "
                f"{composition_input.description}"
            )

            self.write(
                f"{indent}    Quantidade original: "
                f"{composition_input.quantity}"
            )

            self.write(
                f"{indent}    Quantidade calculada: "
                f"{quantity}"
            )

            self.write(
                f"{indent}    Quantidade arredondada: "
                f"{quantity_rounded}"
            )

            self.write(
                f"{indent}    Preço: "
                f"{price}"
            )

            self.write(
                f"{indent}    "
                f"CUSTO DA LINHA MO: "
                f"{format_money(line_cost)}"
            )

        if not workman_found:

            self.write(
                f"{indent}  Nenhuma mão de obra."
            )

        # ==============================================================
        # MATERIAIS
        # ==============================================================

        self.write()
        self.write(
            f"{indent}MATERIAIS"
        )

        material_found = False

        for composition_input in (
            composition.materials
        ):

            material_found = True

            values = (
                self.monetary_value_resolver.get_values(
                    composition_input.code
                )
            )

            price = get_monetary_value(
                values=values,
                type_system="NA",
                classification="CT",
            )

            quantity = (
                composition_input.quantity
                * accumulated_quantity
            )

            quantity_rounded = round_sicro(
                quantity
            )

            line_cost = (
                quantity_rounded
                * price
            )

            result.material_cost += (
                line_cost
            )

            self.write()
            self.write(
                f"{indent}  [MA] "
                f"{composition_input.code}"
            )

            self.write(
                f"{indent}    "
                f"{composition_input.description}"
            )

            self.write(
                f"{indent}    Quantidade original: "
                f"{composition_input.quantity}"
            )

            self.write(
                f"{indent}    Quantidade calculada: "
                f"{quantity}"
            )

            self.write(
                f"{indent}    Quantidade arredondada: "
                f"{quantity_rounded}"
            )

            self.write(
                f"{indent}    Preço: "
                f"{price}"
            )

            self.write(
                f"{indent}    "
                f"CUSTO DA LINHA MA: "
                f"{format_money(line_cost)}"
            )

        if not material_found:

            self.write(
                f"{indent}  Nenhum material."
            )

        # ==============================================================
        # TRANSPORTES
        # ==============================================================

        self._write_transport_lines(
            node=node,
            indent=indent,
        )

    def _write_transport_lines(
        self,
        node,
        indent: str,
    ) -> None:
        """
        Registra as linhas de transporte.

        Os transportes ainda não entram no custo total.
        """

        composition = node.composition

        transport_inputs = [
            item
            for item in composition.transports
        ]

        self.write()
        self.write(
            f"{indent}TRANSPORTES"
        )

        if not transport_inputs:

            self.write(
                f"{indent}  Nenhum transporte."
            )

            return

        for composition_input in (
            transport_inputs
        ):

            quantity = (
                composition_input.quantity
                * node.accumulated_quantity
            )

            quantity_rounded = round_sicro(
                quantity
            )

            self.write()
            self.write(
                f"{indent}  "
                f"[{composition_input.group}] "
                f"{composition_input.code}"
            )

            self.write(
                f"{indent}    "
                f"{composition_input.description}"
            )

            self.write(
                f"{indent}    Quantidade original: "
                f"{composition_input.quantity}"
            )

            self.write(
                f"{indent}    Quantidade calculada: "
                f"{quantity}"
            )

            self.write(
                f"{indent}    Quantidade arredondada: "
                f"{quantity_rounded}"
            )

            self.write(
                f"{indent}    "
                f"Item proprietário: "
                f"{composition_input.proprietary_item}"
            )

            self.write(
                f"{indent}    "
                f"OBSERVAÇÃO: transporte ainda "
                f"não incorporado ao custo."
            )

    def _build_path(
        self,
        node,
    ) -> str:
        """
        Constrói o caminho completo da ocorrência
        dentro da árvore.
        """

        path = []

        current = node

        while current is not None:

            if current.parent is None:

                path.append(
                    current.composition.code
                )

            else:

                siblings = [
                    child
                    for child in current.parent.children
                    if child.composition.code
                    == current.composition.code
                ]

                occurrence = (
                    siblings.index(current)
                    + 1
                )

                path.append(
                    f"{current.composition.code}"
                    f"[{occurrence}]"
                )

            current = current.parent

        path.reverse()

        return " -> ".join(path)


def write_final_summary(
    output,
    calculator: RecursiveFicCalculator,
    result: NodeCostResult,
) -> None:
    """
    Escreve o resumo final do cálculo.
    """

    output.write("\n\n")

    output.write(
        "#" * 140
        + "\n"
    )

    output.write(
        "RESULTADO FINAL"
        + "\n"
    )

    output.write(
        "#" * 140
        + "\n\n"
    )

    output.write(
        f"Nós processados: "
        f"{calculator.node_counter}\n"
    )

    output.write("\n")

    output.write(
        f"Equipamentos da raiz: "
        f"{format_money(result.equipment_cost)}\n"
    )

    output.write(
        f"Mão de obra da raiz: "
        f"{format_money(result.workman_cost)}\n"
    )

    output.write(
        f"Materiais da raiz: "
        f"{format_money(result.material_cost)}\n"
    )

    output.write(
        f"Base FIC da raiz: "
        f"{format_money(result.fic_base)}\n"
    )

    output.write(
        f"FIC da raiz: "
        f"{format_money(result.fic_cost)}\n"
    )

    output.write(
        f"Custo acumulado das filhas: "
        f"{format_money(result.children_cost)}\n"
    )

    output.write("\n")

    output.write(
        f"TOTAL CALCULADO DA COMPOSIÇÃO "
        f"{ROOT_COMPOSITION_CODE}: "
        f"{format_money(result.total_cost)}\n"
    )

    output.write("\n")

    output.write(
        "O custo das filhas já inclui o FIC "
        "próprio de cada composição filha.\n"
    )

    output.write(
        "Transportes foram apenas registrados "
        "e ainda não incorporados ao custo.\n"
    )

    output.write(
        "\n"
        + "#" * 140
        + "\n"
    )


def main() -> None:
    """
    Executa o diagnóstico recursivo completo.
    """

    # ======================================================================
    # CLIENTES E REPOSITÓRIO
    # ======================================================================

    composition_api_client = (
        CompositionApiClient()
    )

    composition_repository = (
        CompositionRepository(
            composition_api_client
        )
    )

    composition_resolver = (
        CompositionResolver(
            composition_repository
        )
    )

    # ======================================================================
    # RESOLUÇÃO DA ÁRVORE
    # ======================================================================

    root_node = (
        composition_resolver.resolve_tree(
            composition_code=ROOT_COMPOSITION_CODE
        )
    )

    # ======================================================================
    # CLIENTE MONETÁRIO
    # ======================================================================

    monetary_client = (
        MonetaryValueApiClient()
    )

    monetary_value_resolver = (
        MonetaryValueResolver(
            monetary_client
        )
    )

    # ======================================================================
    # ARQUIVO DE SAÍDA
    # ======================================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as output:

        output.write(
            "DIAGNÓSTICO RECURSIVO DE CUSTO E FIC\n"
        )

        output.write(
            "=" * 140
            + "\n"
        )

        output.write(
            f"Composição raiz: "
            f"{ROOT_COMPOSITION_CODE}\n"
        )

        output.write(
            "Arredondamento por linha: "
            "4 casas decimais\n"
        )

        output.write(
            "EQ e MO: quantidade dividida pela produção\n"
        )

        output.write(
            "MA: quantidade não dividida pela produção\n"
        )

        output.write(
            "FIC: (EQ + MO) × FIC\n"
        )

        output.write(
            "AX e TF: custo da composição filha "
            "é acumulado no pai\n"
        )

        output.write(
            "Transportes: registrados, "
            "mas não incorporados ao custo\n"
        )

        output.write(
            "=" * 140
            + "\n\n"
        )

        # ==================================================================
        # CALCULADOR
        # ==================================================================

        calculator = (
            RecursiveFicCalculator(
                monetary_value_resolver=(
                    monetary_value_resolver
                ),
                output=output,
            )
        )

        # ==================================================================
        # CÁLCULO
        # ==================================================================

        final_result = (
            calculator.calculate_node(
                node=root_node
            )
        )

        # ==================================================================
        # RESUMO
        # ==================================================================

        write_final_summary(
            output=output,
            calculator=calculator,
            result=final_result,
        )

    # ======================================================================
    # SAÍDA NO TERMINAL
    # ======================================================================

    print()
    print(
        "=" * 100
    )

    print(
        "TESTE RECURSIVO CONCLUÍDO"
    )

    print(
        "=" * 100
    )

    print(
        f"Arquivo: "
        f"{OUTPUT_FILE.resolve()}"
    )

    print(
        f"Nós processados: "
        f"{calculator.node_counter}"
    )

    print(
        f"Total calculado: "
        f"{format_money(final_result.total_cost)}"
    )

    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()