from app.services.composition_explosion import (
    CompositionExplosion,
)


def main():

    explosion = CompositionExplosion()

    result = explosion.explode(
        code="0919013"
    )

    print()

    print("Resultado da explosão")
    print("=" * 80)

    print()

    total_nodes = sum(
        1
        for _ in result.root_node.walk()
    )

    print(
        f"Quantidade total de nós: "
        f"{total_nodes}"
    )

    print(
        f"Quantidade de composições únicas: "
        f"{len(result.compositions)}"
    )

    print(
        f"Quantidade de insumos únicos: "
        f"{len(result.inputs)}"
    )

    print()

    print(result)


if __name__ == "__main__":
    main()