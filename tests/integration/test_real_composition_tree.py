from app.domain.composition_tree import CompositionTree
from app.infrastructure.composition_api_client import CompositionApiClient
from app.repositories.composition_repository import CompositionRepository
from app.services.composition_resolver import CompositionResolver


COMPOSITION_CODE = "4915757"


def print_tree(
    node,
    prefix: str = "",
    is_last: bool = True,
) -> None:
    """
    Imprime a árvore de composição de forma hierárquica.
    """

    connector = "└── " if is_last else "├── "

    if node.is_root():
        print(
            f"{node.composition.generic_item} "
            f"[ROOT]"
        )
    else:
        print(
            f"{prefix}"
            f"{connector}"
            f"{node.reference_group} → "
            f"{node.composition.generic_item} "
            f"(qtd={node.reference_quantity})"
        )

    children = node.children

    for index, child in enumerate(children):

        child_is_last = (
            index == len(children) - 1
        )

        if node.is_root():
            child_prefix = ""
        else:
            child_prefix = (
                prefix
                + ("    " if is_last else "│   ")
            )

        print_tree(
            node=child,
            prefix=child_prefix,
            is_last=child_is_last,
        )


def test_real_composition_tree() -> None:
    """
    Testa a construção de uma árvore utilizando
    uma composição real obtida da API Django.
    """

    print()
    print("=" * 100)
    print("TESTE DE INTEGRAÇÃO - COMPOSIÇÃO REAL DA API")
    print("=" * 100)

    print()
    print(f"Composição raiz: {COMPOSITION_CODE}")

    # ============================================================
    # RESOLVER
    # ============================================================

    api_client = CompositionApiClient()

    composition_repository = CompositionRepository(
        api_client=api_client,
    )

    resolver = CompositionResolver(
        repository=composition_repository,
    )

    # ============================================================
    # CONSTRUÇÃO DA ÁRVORE
    # ============================================================

    tree: CompositionTree = (
        resolver.resolve_tree(
            COMPOSITION_CODE
        )
    )

    # ============================================================
    # INFORMAÇÕES DA RAIZ
    # ============================================================

    root = tree.root
    composition = root.composition

    print()
    print("-" * 100)
    print("COMPOSIÇÃO RAIZ")
    print("-" * 100)

    print()
    print(
        f"Código:      {composition.generic_item}"
    )

    print(
        f"Descrição:   {composition.generic_description}"
    )

    print(
        f"Unidade:     {composition.unit}"
    )

    print(
        f"Produção:    {composition.production}"
    )

    print(
        f"FIC:         {composition.fic}"
    )

    # ============================================================
    # QUANTIDADES DE INSUMOS
    # ============================================================

    print()
    print("-" * 100)
    print("INSUMOS DA COMPOSIÇÃO RAIZ")
    print("-" * 100)

    print()

    for composition_input in composition.inputs:

        print(
            f"{composition_input.input_group:>4} | "
            f"{composition_input.generic_item:<12} | "
            f"qtd={composition_input.input_quantity}"
        )

    # ============================================================
    # ÁRVORE
    # ============================================================

    print()
    print("-" * 100)
    print("ÁRVORE DE COMPOSIÇÕES")
    print("-" * 100)

    print()

    print_tree(
        tree.root
    )

    # ============================================================
    # ESTATÍSTICAS
    # ============================================================

    nodes = tree.walk()

    post_order_nodes = (
        tree.walk_post_order()
    )

    print()
    print("-" * 100)
    print("ESTATÍSTICAS DA ÁRVORE")
    print("-" * 100)

    print()

    print(
        f"Nós em pré-ordem:  "
        f"{len(nodes)}"
    )

    print(
        f"Nós em pós-ordem:  "
        f"{len(post_order_nodes)}"
    )

    print(
        f"Nós folha:         "
        f"{len(tree.get_leaves())}"
    )

    # ============================================================
    # PÓS-ORDEM
    # ============================================================

    print()
    print("-" * 100)
    print("ORDEM DE CÁLCULO - PÓS-ORDEM")
    print("-" * 100)

    print()

    for index, node in enumerate(
        post_order_nodes,
        start=1,
    ):

        print(
            f"{index:>3}. "
            f"{node.composition.generic_item}"
        )

    # ============================================================
    # VALIDAÇÕES
    # ============================================================

    print()
    print("-" * 100)
    print("VALIDAÇÕES")
    print("-" * 100)

    print()

    print(
        f"Código da raiz: "
        f"{composition.generic_item}"
    )

    assert (
        composition.generic_item
        == COMPOSITION_CODE
    )

    print(
        "Resultado: OK"
    )

    print()

    print(
        "Árvore construída:"
    )

    assert (
        tree.root
        is root
    )

    print(
        "Resultado: OK"
    )

    print()

    print(
        "Pós-ordem executada:"
    )

    assert (
        post_order_nodes
    )

    print(
        "Resultado: OK"
    )

    print()
    print("=" * 100)
    print("TESTE DE INTEGRAÇÃO APROVADO")
    print("=" * 100)


if __name__ == "__main__":
    test_real_composition_tree()