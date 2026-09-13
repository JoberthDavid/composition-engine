from app.services.composition_explosion import CompositionExplosion


def inspect_node(node, level=0, max_level=3):
    indent = "    " * level

    print("=" * 120)
    print(f"{indent}NÓ: {node.composition.code}")
    print(f"{indent}Descrição: {node.composition.description}")
    print(f"{indent}Produção: {node.composition.production}")

    print()

    print(f"{indent}ATRIBUTOS DO NODE:")

    for attr in dir(node):
        if attr.startswith("_"):
            continue

        try:
            value = getattr(node, attr)

            if callable(value):
                continue

            print(
                f"{indent}  {attr} = {value!r}"
            )

        except Exception as e:
            print(
                f"{indent}  {attr} = <ERRO: {e}>"
            )

    print()

    if node.parent is None:
        print(f"{indent}PAI: None")
    else:
        print(
            f"{indent}PAI: "
            f"{node.parent.composition.code}"
        )

    print()

    if level >= max_level:
        return

    print(f"{indent}FILHOS: {len(node.children)}")
    print()

    for child in node.children:
        inspect_node(
            child,
            level=level + 1,
            max_level=max_level
        )


def main():

    composition_code = "0919013"

    explosion = CompositionExplosion()

    result = explosion.explode(
        composition_code
    )

    root = result.root_node

    print()
    print("=" * 120)
    print("DIAGNÓSTICO DE QUANTIDADE EFETIVA")
    print("=" * 120)
    print()

    inspect_node(
        root,
        level=0,
        max_level=3
    )


if __name__ == "__main__":
    main()
