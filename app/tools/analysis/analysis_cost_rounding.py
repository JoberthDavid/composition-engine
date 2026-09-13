from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from app.services.composition_explosion import (
    CompositionExplosion,
)


COMPOSITION_CODE = "0919013"
ROUNDING_PLACES = 4

OUTPUT_FILE = Path(
    "tests/test_cost_rounding_output.txt"
)


def round_decimal(
    value: Decimal,
) -> Decimal:
    """
    Arredonda um valor decimal para 4 casas utilizando
    arredondamento comercial.
    """

    return value.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


def calculate_line_quantity(
    node,
    composition_input,
    accumulated_quantity: Decimal,
) -> Decimal:
    """
    Calcula a quantidade da linha antes do arredondamento.

    EQ e MO:
        quantidade acumulada × quantidade da linha ÷ produção

    MA:
        quantidade acumulada × quantidade da linha

    AX e TF:
        quantidade acumulada × quantidade da referência

    Transportes:
        quantidade acumulada × quantidade da linha

    O transporte é apenas registrado neste teste.
    """

    composition = node.composition
    production = composition.production

    if composition_input.is_composition_reference():

        return (
            accumulated_quantity
            * composition_input.quantity
        )

    if composition_input.group in {
        "EQ",
        "MO",
    }:

        if production == Decimal("0"):
            raise ValueError(
                f"Composition production cannot be zero: "
                f"{composition.code}"
            )

        return (
            accumulated_quantity
            * composition_input.quantity
            / production
        )

    return (
        accumulated_quantity
        * composition_input.quantity
    )


def write_line(
    output,
    line_number: int,
    composition_input,
    raw_quantity: Decimal,
    rounded_quantity: Decimal,
) -> None:
    """
    Escreve uma linha completa no arquivo de saída.
    """

    output.write(
        f"  LINHA {line_number}\n"
    )

    output.write(
        f"    Grupo: {composition_input.group}\n"
    )

    output.write(
        f"    Código: {composition_input.code}\n"
    )

    output.write(
        f"    Identificador: "
        f"{composition_input.identifier}\n"
    )

    output.write(
        f"    Descrição: "
        f"{composition_input.description}\n"
    )

    output.write(
        f"    Unidade: "
        f"{composition_input.unit}\n"
    )

    output.write(
        f"    Quantidade original: "
        f"{composition_input.quantity}\n"
    )

    output.write(
        f"    Quantidade calculada: "
        f"{raw_quantity}\n"
    )

    output.write(
        f"    Quantidade arredondada: "
        f"{rounded_quantity}\n"
    )

    output.write(
        f"    Diferença arredondamento: "
        f"{rounded_quantity - raw_quantity}\n"
    )

    output.write(
        f"    Use: "
        f"{composition_input.use}\n"
    )

    output.write(
        f"    Proprietary item: "
        f"{composition_input.proprietary_item}\n"
    )

    output.write("\n")


def write_node(
    output,
    node,
    accumulated_quantity: Decimal,
    path: str,
) -> None:
    """
    Escreve uma composição completa e todos os seus filhos.

    As referências AX e TF são associadas aos nós filhos
    pela ordem em que aparecem na composição.
    """

    composition = node.composition

    output.write("\n")
    output.write("=" * 140 + "\n")

    output.write(
        f"CAMINHO: {path}\n"
    )

    output.write(
        f"COMPOSIÇÃO: {composition.code}\n"
    )

    output.write(
        f"ID: {composition.identifier}\n"
    )

    output.write(
        f"DESCRIÇÃO: {composition.description}\n"
    )

    output.write(
        f"GRUPO: {composition.group}\n"
    )

    output.write(
        f"UNIDADE: {composition.unit}\n"
    )

    output.write(
        f"PRODUÇÃO: {composition.production}\n"
    )

    output.write(
        f"FIC: {composition.fic}\n"
    )

    output.write(
        f"QUANTIDADE ACUMULADA: "
        f"{accumulated_quantity}\n"
    )

    output.write(
        f"QUANTIDADE DE LINHAS: "
        f"{len(composition.inputs)}\n"
    )

    output.write(
        f"QUANTIDADE DE FILHOS: "
        f"{len(node.children)}\n"
    )

    output.write(
        "=" * 140 + "\n\n"
    )

    # ------------------------------------------------------
    # Calcula e escreve todas as linhas
    # ------------------------------------------------------

    for line_number, composition_input in enumerate(
        composition.inputs,
        start=1,
    ):

        raw_quantity = calculate_line_quantity(
            node=node,
            composition_input=composition_input,
            accumulated_quantity=accumulated_quantity,
        )

        rounded_quantity = round_decimal(
            raw_quantity
        )

        write_line(
            output=output,
            line_number=line_number,
            composition_input=composition_input,
            raw_quantity=raw_quantity,
            rounded_quantity=rounded_quantity,
        )

    # ------------------------------------------------------
    # Percorre os filhos.
    #
    # A correspondência é feita pela ordem das referências
    # AX/TF, e não apenas pelo código.
    # ------------------------------------------------------

    child_index = 0

    for composition_input in composition.inputs:

        if not composition_input.is_composition_reference():
            continue

        if child_index >= len(node.children):
            raise ValueError(
                f"Child node not found for reference "
                f"{composition_input.code} in "
                f"composition {composition.code}"
            )

        child = node.children[child_index]

        raw_child_quantity = (
            accumulated_quantity
            * composition_input.quantity
        )

        rounded_child_quantity = round_decimal(
            raw_child_quantity
        )

        child_index += 1

        output.write(
            "-" * 140 + "\n"
        )

        output.write(
            f"REFERÊNCIA PARA FILHO #{child_index}\n"
        )

        output.write(
            f"Grupo: {composition_input.group}\n"
        )

        output.write(
            f"Código referência: "
            f"{composition_input.code}\n"
        )

        output.write(
            f"Código filho: "
            f"{child.composition.code}\n"
        )

        output.write(
            f"Quantidade referência: "
            f"{composition_input.quantity}\n"
        )

        output.write(
            f"Quantidade filha sem arredondamento: "
            f"{raw_child_quantity}\n"
        )

        output.write(
            f"Quantidade filha arredondada: "
            f"{rounded_child_quantity}\n"
        )

        output.write(
            "-" * 140 + "\n"
        )

        child_path = (
            f"{path}"
            f" -> "
            f"{child.composition.code}"
            f"[{child_index}]"
        )

        write_node(
            output=output,
            node=child,
            accumulated_quantity=(
                rounded_child_quantity
            ),
            path=child_path,
        )

    if child_index != len(node.children):
        raise ValueError(
            f"Mismatch between composition references "
            f"and child nodes in composition "
            f"{composition.code}: "
            f"{child_index} references processed, "
            f"{len(node.children)} children found."
        )


def write_summary(
    output,
    root_node,
) -> None:
    """
    Escreve um resumo da árvore no final do arquivo.
    """

    nodes = root_node.walk()

    output.write("\n\n")
    output.write("#" * 140 + "\n")
    output.write("RESUMO DA ÁRVORE\n")
    output.write("#" * 140 + "\n\n")

    output.write(
        f"Nós totais: {len(nodes)}\n"
    )

    composition_codes: dict[str, int] = {}

    for node in nodes:

        code = node.composition.code

        composition_codes[code] = (
            composition_codes.get(code, 0)
            + 1
        )

    output.write(
        f"Códigos de composição distintos: "
        f"{len(composition_codes)}\n\n"
    )

    output.write(
        "OCORRÊNCIAS POR COMPOSIÇÃO\n"
    )

    output.write(
        "-" * 140 + "\n"
    )

    for code in sorted(composition_codes):

        output.write(
            f"{code}: "
            f"{composition_codes[code]} ocorrência(s)\n"
        )

    output.write("\n")

    output.write(
        "REGRA DE ARREDONDAMENTO\n"
    )

    output.write(
        "-" * 140 + "\n"
    )

    output.write(
        "Cada linha de EQ, MO, MA, AX, TF e transporte "
        "é calculada individualmente.\n"
    )

    output.write(
        f"O resultado calculado é arredondado para "
        f"{ROUNDING_PLACES} casas decimais.\n"
    )

    output.write(
        "Nas referências AX/TF, a quantidade arredondada "
        "é propagada para a composição filha.\n"
    )

    output.write("\n")


def main() -> None:
    """
    Executa o teste detalhado e grava toda a saída
    em arquivo TXT.
    """

    explosion = CompositionExplosion()

    result = explosion.explode(
        COMPOSITION_CODE
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as output:

        output.write(
            f"TESTE DETALHADO DE ARREDONDAMENTO SICRO\n"
        )

        output.write(
            f"Composição raiz: "
            f"{COMPOSITION_CODE}\n"
        )

        output.write(
            f"Casas decimais: "
            f"{ROUNDING_PLACES}\n"
        )

        output.write(
            f"Nós na árvore: "
            f"{len(result.root_node.walk())}\n"
        )

        output.write(
            f"Recursos consolidados atuais: "
            f"{len(result.inputs)}\n"
        )

        output.write("\n")

        output.write(
            "Objetivo: registrar todas as linhas de todas "
            "as ocorrências da árvore, incluindo EQ, MO, "
            "MA, AX, TF e transportes.\n"
        )

        output.write(
            "O arquivo preserva quantidade original, "
            "quantidade calculada, quantidade arredondada "
            "e diferença de arredondamento.\n"
        )

        write_node(
            output=output,
            node=result.root_node,
            accumulated_quantity=Decimal("1"),
            path=COMPOSITION_CODE,
        )

        write_summary(
            output=output,
            root_node=result.root_node,
        )

    print()
    print("=" * 100)
    print("TESTE CONCLUÍDO")
    print("=" * 100)
    print()
    print(
        f"Arquivo gerado:"
    )
    print(
        f"  {OUTPUT_FILE}"
    )
    print()
    print(
        f"Nós processados: "
        f"{len(result.root_node.walk())}"
    )
    print(
        f"Linhas escritas no arquivo: "
        f"todas as linhas das composições."
    )


if __name__ == "__main__":
    main()