from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree
from app.repositories.composition_repository import CompositionRepository
from app.repositories.optimized_composition_repository import (
    OptimizedCompositionRepository,
)


class CompositionResolver:
    """
    Responsável por resolver composições e construir
    a árvore de referências entre composições.

    Existem dois caminhos de resolução:

    - resolve_tree():
        utiliza o CompositionRepository tradicional e funciona
        como baseline de referência.

    - resolve_tree_optimized():
        utiliza o OptimizedCompositionRepository para descobrir
        a estrutura em lotes por nível.

    Em ambos os caminhos, os CompositionInput originais são
    preservados para a criação dos CompositionNode.

    A árvore considera como referências recursivas:

    - AX: Atividade Auxiliar
    - TF: Tempo Fixo
    """

    def __init__(
        self,
        repository: CompositionRepository | None = None,
        optimized_repository: OptimizedCompositionRepository | None = None,
    ) -> None:

        self.repository = (
            repository
            if repository is not None
            else CompositionRepository()
        )

        self.optimized_repository = optimized_repository

    # ============================================================
    # RESOLUÇÃO TRADICIONAL — BASELINE
    # ============================================================

    def resolve_tree(
        self,
        composition_code: str,
    ) -> CompositionTree:
        """
        Resolve uma composição utilizando o caminho tradicional.

        Este método é mantido como baseline de referência.

        A expansão utiliza diretamente os CompositionInput
        de cada composição.
        """

        root_node = self._create_root_node(
            composition_code=composition_code,
        )

        self._expand_level(
            nodes=[root_node],
            current_paths=[set()],
        )

        return CompositionTree(
            root=root_node,
        )

    # ============================================================
    # RESOLUÇÃO OTIMIZADA
    # ============================================================

    def resolve_tree_optimized(
        self,
        composition_code: str,
    ) -> CompositionTree:
        """
        Resolve uma composição utilizando a descoberta estrutural
        otimizada por níveis.

        O OptimizedCompositionRepository informa quais códigos
        de composição estão ligados a cada composição da fronteira.

        Depois disso, o CompositionRepository carrega as
        composições completas.

        Os CompositionInput originais continuam sendo utilizados
        para construir cada ocorrência do CompositionNode.

        Dessa forma, a otimização reduz as requisições à API sem
        alterar a semântica da árvore.
        """

        if self.optimized_repository is None:
            raise ValueError(
                "An OptimizedCompositionRepository is required "
                "to resolve the composition tree using the "
                "optimized strategy."
            )

        root_node = self._create_root_node(
            composition_code=composition_code,
        )

        self._expand_levels_optimized(
            root_node=root_node,
        )

        return CompositionTree(
            root=root_node,
        )

    # ============================================================
    # CRIAÇÃO DA RAIZ
    # ============================================================

    def _create_root_node(
        self,
        composition_code: str,
    ) -> CompositionNode:
        """
        Obtém a composição raiz e cria seu CompositionNode.
        """

        root_composition = self.repository.get_by_code(
            composition_code
        )

        if root_composition is None:
            raise ValueError(
                "Composition not found: "
                f"{composition_code}"
            )

        return CompositionNode(
            composition=root_composition,
        )

    # ============================================================
    # EXPANSÃO TRADICIONAL
    # ============================================================

    def _expand_level(
        self,
        nodes: list[CompositionNode],
        current_paths: list[set[str]],
    ) -> None:
        """
        Expande um nível da árvore pelo caminho tradicional.

        Todas as referências do nível atual são coletadas
        antes de consultar o repositório.

        As composições são carregadas em lote.
        """

        references: list[
            tuple[
                CompositionNode,
                CompositionInput,
                set[str],
            ]
        ] = []

        for node, current_path in zip(
            nodes,
            current_paths,
        ):
            composition_code = (
                node.composition.generic_item
            )

            if composition_code in current_path:
                cycle_path = " -> ".join(
                    list(current_path)
                    + [composition_code]
                )

                raise ValueError(
                    "Composition cycle detected: "
                    f"{cycle_path}"
                )

            next_path = current_path | {
                composition_code
            }

            for composition_input in (
                node.composition.composition_references
            ):
                references.append(
                    (
                        node,
                        composition_input,
                        next_path,
                    )
                )

        if not references:
            return

        child_codes = [
            composition_input.generic_item
            for _, composition_input, _ in references
        ]

        child_compositions = self.repository.get_by_codes(
            child_codes
        )

        compositions_by_code = {
            str(composition.code): composition
            for composition in child_compositions
        }

        next_nodes: list[CompositionNode] = []
        next_paths: list[set[str]] = []

        for (
            parent_node,
            composition_input,
            current_path,
        ) in references:

            child_composition_code = (
                composition_input.generic_item
            )

            child_composition = (
                compositions_by_code.get(
                    child_composition_code
                )
            )

            if child_composition is None:
                raise ValueError(
                    self._build_missing_composition_message(
                        parent_node=parent_node,
                        composition_input=composition_input,
                    )
                )

            child_node = CompositionNode(
                composition=child_composition,
                reference_input=composition_input,
                parent=parent_node,
            )

            parent_node.add_child(
                child_node
            )

            next_nodes.append(
                child_node
            )

            next_paths.append(
                current_path
            )

        self._expand_level(
            nodes=next_nodes,
            current_paths=next_paths,
        )

    # ============================================================
    # EXPANSÃO OTIMIZADA POR NÍVEIS
    # ============================================================

    def _expand_levels_optimized(
        self,
        root_node: CompositionNode,
    ) -> None:
        """
        Expande a árvore utilizando consultas agrupadas por nível.

        A estrutura de uma composição é consultada uma única vez,
        mas cada ocorrência da composição na árvore continua sendo
        expandida individualmente.

        Dessa forma:

            consulta da composição
                ≠
            ocorrência da composição

        Uma mesma composição pode aparecer diversas vezes na árvore.
        Nesse caso, a estrutura é reutilizada, mas cada ocorrência
        continua recebendo seu próprio conjunto de CompositionNode.

        Para cada nível:

            1. identifica os códigos de composição da fronteira;
            2. consulta somente os códigos cuja estrutura ainda não
            foi obtida;
            3. armazena a estrutura em cache;
            4. carrega as composições candidatas em lote;
            5. cria todas as ocorrências dos filhos;
            6. monta a próxima fronteira.

        O controle de ciclos continua sendo feito por caminho.
        """

        frontier: list[
            tuple[
                CompositionNode,
                set[str],
            ]
        ] = [
            (
                root_node,
                set(),
            )
        ]

        # Cache da estrutura:
        #
        # código da composição
        #        ↓
        # códigos dos filhos estruturais
        #
        # O valor [] também é armazenado para composição folha,
        # evitando nova consulta à API.
        structural_children_cache: dict[
            str,
            list[str],
        ] = {}

        while frontier:

            # ========================================================
            # CÓDIGOS DA FRONTEIRA ATUAL
            # ========================================================

            current_codes = list(
                dict.fromkeys(
                    str(node.composition.code)
                    for node, _ in frontier
                )
            )

            # ========================================================
            # DESCOBERTA ESTRUTURAL
            # ========================================================

            codes_to_query = [
                code
                for code in current_codes
                if code not in structural_children_cache
            ]

            if codes_to_query:

                discovered_children = (
                    self.optimized_repository
                    .get_child_codes_by_composition_codes(
                        codes_to_query
                    )
                )

                for code in codes_to_query:

                    structural_children_cache[code] = [
                        str(child_code)
                        for child_code in (
                            discovered_children.get(
                                code,
                                [],
                            )
                        )
                    ]

            # ========================================================
            # CANDIDATOS DE TODA A FRONTEIRA
            # ========================================================

            candidate_codes: list[str] = []

            for parent_code in current_codes:

                for child_code in (
                    structural_children_cache.get(
                        parent_code,
                        [],
                    )
                ):

                    if child_code not in candidate_codes:
                        candidate_codes.append(
                            child_code
                        )

            # ========================================================
            # NÃO HÁ MAIS FILHOS
            # ========================================================

            if not candidate_codes:
                break

            # ========================================================
            # CARREGA COMPOSIÇÕES EM LOTE
            # ========================================================

            child_compositions = (
                self.repository.get_by_codes(
                    candidate_codes
                )
            )

            compositions_by_code = {
                str(composition.code): composition
                for composition in child_compositions
            }

            # ========================================================
            # CONSTRÓI TODAS AS OCORRÊNCIAS
            # ========================================================

            next_frontier: list[
                tuple[
                    CompositionNode,
                    set[str],
                ]
            ] = []

            for (
                parent_node,
                current_path,
            ) in frontier:

                parent_code = str(
                    parent_node.composition.code
                )

                # ====================================================
                # DETECÇÃO DE CICLO
                # ====================================================

                if parent_code in current_path:

                    cycle_path = " -> ".join(
                        list(current_path)
                        + [parent_code]
                    )

                    raise ValueError(
                        "Composition cycle detected: "
                        f"{cycle_path}"
                    )

                next_path = (
                    current_path
                    | {parent_code}
                )

                structural_child_codes = set(
                    structural_children_cache.get(
                        parent_code,
                        [],
                    )
                )

                if not structural_child_codes:
                    continue

                # ====================================================
                # REFERÊNCIAS REAIS DA COMPOSIÇÃO
                # ====================================================

                for composition_input in (
                    parent_node.composition.composition_references
                ):

                    child_code = str(
                        composition_input.generic_item
                    )

                    if child_code not in (
                        structural_child_codes
                    ):
                        continue

                    # ================================================
                    # DETECÇÃO DE CICLO NO FILHO
                    # ================================================

                    if child_code in next_path:

                        cycle_path = " -> ".join(
                            list(next_path)
                            + [child_code]
                        )

                        raise ValueError(
                            "Composition cycle detected: "
                            f"{cycle_path}"
                        )

                    # ================================================
                    # COMPOSIÇÃO FILHA
                    # ================================================

                    child_composition = (
                        compositions_by_code.get(
                            child_code
                        )
                    )

                    if child_composition is None:

                        raise ValueError(
                            self._build_missing_composition_message(
                                parent_node=parent_node,
                                composition_input=composition_input,
                            )
                        )

                    # ================================================
                    # NOVA OCORRÊNCIA DO NÓ
                    # ================================================

                    child_node = CompositionNode(
                        composition=child_composition,
                        reference_input=composition_input,
                        parent=parent_node,
                    )

                    parent_node.add_child(
                        child_node
                    )

                    # ================================================
                    # PRÓXIMO NÍVEL
                    #
                    # IMPORTANTE:
                    #
                    # não eliminamos child_code porque ele já apareceu
                    # anteriormente. Cada ocorrência precisa continuar
                    # sendo expandida.
                    # ================================================

                    next_frontier.append(
                        (
                            child_node,
                            next_path,
                        )
                    )

            frontier = next_frontier

    # ============================================================
    # CANDIDATOS ESTRUTURAIS
    # ============================================================

    @staticmethod
    def _get_candidate_codes(
        children_by_parent: dict[str, list[str]],
    ) -> list[str]:
        """
        Constrói a lista única de códigos candidatos
        retornados pela descoberta estrutural.
        """

        candidate_codes: list[str] = []

        for children in children_by_parent.values():
            for child_code in children:

                child_code = str(
                    child_code
                )

                if child_code not in candidate_codes:
                    candidate_codes.append(
                        child_code
                    )

        return candidate_codes

    # ============================================================
    # MENSAGENS DE ERRO
    # ============================================================

    @staticmethod
    def _build_missing_composition_message(
        parent_node: CompositionNode,
        composition_input: CompositionInput,
    ) -> str:
        """
        Constrói a mensagem utilizada quando uma composição
        referenciada não é encontrada.
        """

        return (
            "Referenced composition not found: "
            f"{composition_input.generic_item}. "
            f"Parent composition: "
            f"{parent_node.composition.generic_item}. "
            f"Input group: "
            f"{composition_input.input_group}."
        )