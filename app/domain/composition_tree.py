from collections.abc import Iterator

from app.domain.composition_node import CompositionNode


class CompositionTree:
    """
    Representa a árvore completa de ocorrências de composições.

    A árvore possui um único nó raiz e uma quantidade
    arbitrária de filhos por nó.
    """

    def __init__(
        self,
        root: CompositionNode,
    ) -> None:
        """
        Inicializa a árvore com seu nó raiz.
        """

        self.root = root

    def walk(self) -> list[CompositionNode]:
        """
        Percorre todos os nós da árvore em pré-ordem.

        A ordem é:

            pai
            depois filhos da esquerda para a direita.
        """

        nodes: list[CompositionNode] = []

        def visit(node: CompositionNode) -> None:
            nodes.append(node)

            for child in node.children:
                visit(child)

        visit(self.root)

        return nodes

    def walk_post_order(
        self,
    ) -> list[CompositionNode]:
        """
        Percorre todos os nós em pós-ordem.

        A ordem é:

            filhos
            depois pai.

        Cada CompositionNode é retornado apenas uma vez.

        O método também valida ciclos na estrutura,
        permitindo o uso da CompositionTree como
        um DAG acíclico direcionado.
        """

        nodes: list[CompositionNode] = []

        visiting: set[int] = set()

        def visit(
            node: CompositionNode,
        ) -> None:

            node_id = id(node)

            # ========================================================
            # CICLO DETECTADO
            # ========================================================

            if node_id in visiting:

                raise ValueError(
                    "Cycle detected in composition tree: "
                    f"{node.composition.generic_item}"
                )

            # ========================================================
            # INÍCIO DA VISITA
            # ========================================================

            visiting.add(
                node_id
            )

            # ========================================================
            # FILHOS
            # ========================================================

            for child in node.children:

                visit(
                    child
                )

            # ========================================================
            # FINALIZAÇÃO
            # ========================================================

            visiting.remove(
                node_id
            )

            nodes.append(
                node
            )

        visit(
            self.root
        )

        return nodes

    def __iter__(self) -> Iterator[CompositionNode]:
        """
        Permite percorrer a árvore diretamente com um for.
        """

        return iter(self.walk())

    def __len__(self) -> int:
        """
        Retorna a quantidade de nós da árvore.
        """

        return len(self.walk())

    def get_leaves(self) -> list[CompositionNode]:
        """
        Retorna os nós folha da árvore.
        """

        return [
            node
            for node in self.walk()
            if not node.has_children()
        ]

    def find_by_code(
        self,
        code: str,
    ) -> list[CompositionNode]:
        """
        Retorna todos os nós que possuem o código informado.

        O mesmo código pode aparecer várias vezes na árvore.
        """

        return [
            node
            for node in self.walk()
            if node.composition.code == code
        ]

    @property
    def monetary_item_codes_by_group(self) -> dict[str, set[str]]:
        codes_by_group = {
            "EQ": set(),
            "MO": set(),
            "MA": set(),
        }

        for node in self.walk():
            for composition_input in node.composition.inputs:

                if composition_input.is_equipment():
                    codes_by_group["EQ"].add(
                        composition_input.code
                    )

                elif composition_input.is_workman():
                    codes_by_group["MO"].add(
                        composition_input.code
                    )

                elif composition_input.is_material():
                    codes_by_group["MA"].add(
                        composition_input.code
                    )

        return codes_by_group


    @property
    def monetary_item_codes(self) -> set[str]:
        """
        Retorna todos os códigos monetários únicos da árvore.
        """

        return set().union(
            *self.monetary_item_codes_by_group.values()
        )