from pprint import pprint

from app.services.composition_explosion import CompositionExplosion


COMPOSITION_CODE = "0919013"


def print_object(obj, title="OBJETO"):
    print("\n" + "=" * 120)
    print(title)
    print("=" * 120)

    if hasattr(obj, "__dict__"):
        pprint(vars(obj))
    else:
        pprint(obj)


def get_attr(obj, *names, default=None):
    """
    Tenta encontrar um atributo usando diferentes nomes possíveis.
    Isso permite que o script funcione mesmo se os nomes internos
    das classes forem diferentes do esperado.
    """
    for name in names:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
        else:
            if hasattr(obj, name):
                return getattr(obj, name)

    return default


def inspect_node(node, level=0, path=""):
    indent = "    " * level

    code = get_attr(
        node,
        "code",
        "generic_item",
        "item_code",
        default="?"
    )

    description = get_attr(
        node,
        "description",
        "name",
        "descricao",
        default=""
    )

    group = get_attr(
        node,
        "group",
        "classification_group",
        "tipo",
        default=""
    )

    quantity = get_attr(
        node,
        "quantity",
        "quantidade",
        "coefficient",
        "coeficiente",
        default=""
    )

    production = get_attr(
        node,
        "production",
        "produtividade",
        "output",
        "production_quantity",
        default=""
    )

    use = get_attr(
        node,
        "use",
        "utilization",
        "utilization_factor",
        "fator_utilizacao",
        default=""
    )

    unit = get_attr(
        node,
        "unit",
        "unidade",
        default=""
    )

    current_path = f"{path} -> {code}" if path else str(code)

    print()
    print(f"{indent}{'-' * 100}")
    print(f"{indent}NÍVEL: {level}")
    print(f"{indent}CAMINHO: {current_path}")
    print(f"{indent}CÓDIGO: {code}")
    print(f"{indent}DESCRIÇÃO: {description}")
    print(f"{indent}GRUPO: {group}")
    print(f"{indent}QUANTIDADE: {quantity}")
    print(f"{indent}UNIDADE: {unit}")
    print(f"{indent}PRODUÇÃO: {production}")
    print(f"{indent}USE: {use}")

    # Mostra todos os atributos do nó
    print(f"{indent}ATRIBUTOS DISPONÍVEIS:")

    if hasattr(node, "__dict__"):
        for key, value in vars(node).items():

            # Evita imprimir filhos aqui porque serão tratados recursivamente
            if key in ("children", "items", "components", "resources"):
                continue

            print(f"{indent}  {key} = {value}")

    # Procura possíveis listas de filhos
    children = get_attr(
        node,
        "children",
        "items",
        "components",
        "resources",
        default=[]
    )

    if children is None:
        children = []

    try:
        children_list = list(children)
    except TypeError:
        children_list = []

    if children_list:
        print()
        print(f"{indent}TOTAL DE FILHOS: {len(children_list)}")

        for child in children_list:
            inspect_node(
                child,
                level=level + 1,
                path=current_path
            )


def main():

    print("=" * 120)
    print("DIAGNÓSTICO DA ÁRVORE DE COMPOSIÇÃO")
    print("=" * 120)
    print(f"COMPOSIÇÃO RAIZ: {COMPOSITION_CODE}")

    explosion = CompositionExplosion()

    print("\nExecutando explosão da composição...")

    result = explosion.explode(COMPOSITION_CODE)

    print_object(
        result,
        "RESULTADO DA EXPLOSÃO - ESTRUTURA PRINCIPAL"
    )

    print("\n")

    # Tentamos localizar a raiz em diferentes nomes possíveis
    root_node = get_attr(
        result,
        "root_node",
        "root",
        "tree",
        default=None
    )

    if root_node is None:
        print("=" * 120)
        print("NÃO FOI POSSÍVEL IDENTIFICAR AUTOMATICAMENTE O ROOT NODE")
        print("=" * 120)

        print("\nResultado completo:")
        pprint(result)

        return

    print()
    print("=" * 120)
    print("ÁRVORE HIERÁRQUICA")
    print("=" * 120)

    inspect_node(root_node)


if __name__ == "__main__":
    main()
