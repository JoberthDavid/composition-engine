from pprint import pprint

from app.services.composition_explosion import CompositionExplosion


COMPOSITION_CODE = "0919013"


def inspect_object(obj, name, level=0, visited=None):
    """
    Inspeciona recursivamente objetos e mostra apenas a estrutura
    necessária para entendermos CompositionNode, Composition e seus filhos.
    """

    if visited is None:
        visited = set()

    indent = "    " * level

    if obj is None:
        print(f"{indent}{name}: None")
        return

    obj_id = id(obj)

    # Evita loops circulares (parent <-> child)
    if obj_id in visited:
        print(f"{indent}{name}: <REFERÊNCIA JÁ VISITADA>")
        return

    visited.add(obj_id)

    print()
    print(f"{indent}{'=' * 100}")
    print(f"{indent}{name}")
    print(f"{indent}{'=' * 100}")
    print(f"{indent}TIPO: {type(obj)}")

    # Dicionário
    if isinstance(obj, dict):

        for key, value in obj.items():

            print(f"{indent}{key}: {value}")

        return

    # Lista
    if isinstance(obj, (list, tuple, set)):

        print(f"{indent}TOTAL DE ITENS: {len(obj)}")

        for i, item in enumerate(obj):

            print(f"{indent}[{i}] {type(item)}")

            if i < 5:
                inspect_object(
                    item,
                    f"{name}[{i}]",
                    level + 1,
                    visited
                )

        return

    # Objeto normal
    if hasattr(obj, "__dict__"):

        attributes = vars(obj)

        print(f"{indent}ATRIBUTOS:")

        for key, value in attributes.items():

            # Não seguir parent automaticamente
            if key == "parent":

                print(
                    f"{indent}  {key} = "
                    f"{type(value)}"
                )

                continue

            # Listas de filhos: apenas identificar
            if isinstance(value, (list, tuple, set)):

                print()
                print(
                    f"{indent}  {key} -> "
                    f"{type(value)} "
                    f"(TOTAL={len(value)})"
                )

                # Inspeciona até os 3 primeiros
                for i, item in enumerate(list(value)[:3]):

                    inspect_object(
                        item,
                        f"{name}.{key}[{i}]",
                        level + 1,
                        visited
                    )

                continue

            # Objetos internos importantes
            if hasattr(value, "__dict__"):

                print()
                print(
                    f"{indent}  {key} -> "
                    f"{type(value)}"
                )

                inspect_object(
                    value,
                    f"{name}.{key}",
                    level + 1,
                    visited
                )

                continue

            print(
                f"{indent}  {key} = {repr(value)}"
            )

        return

    # Valor simples
    print(f"{indent}VALOR: {repr(obj)}")


def main():

    print("=" * 120)
    print("DIAGNÓSTICO ESTRUTURAL DO COMPOSITION NODE")
    print("=" * 120)

    explosion = CompositionExplosion()

    result = explosion.explode(COMPOSITION_CODE)

    root_node = result.root_node

    print()
    print("RESULTADO:")
    print(result)

    print()
    print()
    print("=" * 120)
    print("ROOT NODE")
    print("=" * 120)

    inspect_object(
        root_node,
        "root_node"
    )


if __name__ == "__main__":
    main()
