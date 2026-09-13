from app.domain.composition_node import CompositionNode
from app.services.composition_resolver import (
CompositionResolver,
)

def print_tree(
    node,
    level: int = 0,
) -> None:

    indentation = "    " * level

    print(
        f"{indentation}→ "
        f"{node.composition.code}"
        f" | "
        f"{node.composition.description}"
    )

    if node.reference_quantity is not None:

        print(
            f"{indentation}  "
            f"Quantidade da referência: "
            f"{node.reference_quantity}"
        )

    print(
        f"{indentation}  "
        f"Quantidade efetiva: "
        f"{node.effective_quantity}"
    )

    for child in node.children:

        print_tree(
            node=child,
            level=level + 1,
        )


def count_nodes(
    node: CompositionNode,
    ) -> int:
    """
    Conta recursivamente todos os nós da árvore.
    """

    total = 1

    for child in node.children:

        total += count_nodes(
            child
        )

    return total


def main() -> None:

    resolver = CompositionResolver()

    root_node = resolver.resolve_tree(
        "0919013"
    )

    print()

    print(
        "Árvore de composições"
    )

    print(
        "=" * 80
    )

    print_tree(
        root_node
    )

    print()

    print(
        "=" * 80
    )

    print(
        f"Quantidade total de nós: "
        f"{count_nodes(root_node)}"
    )


if __name__ == "__main__":
    main()