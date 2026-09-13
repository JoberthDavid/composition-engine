from decimal import Decimal

from app.domain.composition_node import CompositionNode


class CompositionCalculationResult:
    """
    Representa o resultado completo do cálculo de uma composição
    dentro da árvore.

    Cada resultado pertence a uma ocorrência específica de
    CompositionNode.

    Isso é importante porque a mesma composição pode aparecer
    mais de uma vez na árvore, em caminhos diferentes.
    """

    def __init__(
        self,
        node: CompositionNode,
        equipment_cost: Decimal = Decimal("0"),
        labor_cost: Decimal = Decimal("0"),
        fic_cost: Decimal = Decimal("0"),
        operational_total: Decimal = Decimal("0"),
        operational_unit: Decimal = Decimal("0"),
        materials_cost: Decimal = Decimal("0"),
        auxiliary_cost: Decimal = Decimal("0"),
        fixed_time_cost: Decimal = Decimal("0"),
        composition_total_raw: Decimal = Decimal("0"),
        composition_unit_cost: Decimal = Decimal("0"),
    ) -> None:
        """
        Inicializa o resultado do cálculo da composição.

        Parameters
        ----------
        node:
            Nó específico da árvore ao qual este resultado pertence.

        equipment_cost:
            Soma dos custos de equipamentos.

        labor_cost:
            Soma dos custos de mão de obra.

        fic_cost:
            Custo calculado do FIC.

        operational_total:
            Soma de:

                equipamentos
                + mão de obra
                + FIC

        operational_unit:
            Custo operacional dividido pela produção.

        materials_cost:
            Soma dos custos de materiais.

        auxiliary_cost:
            Soma das linhas das atividades auxiliares (AX).

        fixed_time_cost:
            Soma das linhas dos tempos fixos (TF).

        composition_total_raw:
            Soma antes do arredondamento final:

                operational_unit
                + materials_cost
                + auxiliary_cost
                + fixed_time_cost

        composition_unit_cost:
            Custo unitário final da composição.

            Este é o valor arredondado em 2 casas decimais que
            sobe para a composição pai quando esta composição
            for utilizada como AX ou TF.
        """

        self.node = node

        # ========================================================
        # 1. EQUIPAMENTOS
        # ========================================================

        self.equipment_cost = equipment_cost

        # ========================================================
        # 2. MÃO DE OBRA
        # ========================================================

        self.labor_cost = labor_cost

        # ========================================================
        # 3. FIC
        # ========================================================

        self.fic_cost = fic_cost

        # ========================================================
        # 4. CUSTO OPERACIONAL
        # ========================================================

        self.operational_total = operational_total

        self.operational_unit = operational_unit

        # ========================================================
        # 5. MATERIAIS
        # ========================================================

        self.materials_cost = materials_cost

        # ========================================================
        # 6. ATIVIDADES AUXILIARES
        # ========================================================

        self.auxiliary_cost = auxiliary_cost

        # ========================================================
        # 6B. TEMPOS FIXOS
        # ========================================================

        self.fixed_time_cost = fixed_time_cost

        # ========================================================
        # 7. TOTAL ANTES DO ARREDONDAMENTO FINAL
        # ========================================================

        self.composition_total_raw = (
            composition_total_raw
        )

        # ========================================================
        # 8. CUSTO UNITÁRIO FINAL
        # ========================================================

        self.composition_unit_cost = (
            composition_unit_cost
        )

    # ============================================================
    # PROPRIEDADES DE ACESSO À COMPOSIÇÃO
    # ============================================================

    @property
    def composition_code(self) -> str:
        """
        Retorna o código da composição calculada.
        """

        return self.node.composition.code

    @property
    def composition_description(self) -> str:
        """
        Retorna a descrição da composição calculada.
        """

        return self.node.composition.generic_description

    @property
    def production(self) -> Decimal:
        """
        Retorna a produção da composição.
        """

        return self.node.composition.production

    @property
    def fic_percentage(self) -> Decimal:
        """
        Retorna o percentual de FIC da composição.
        """

        return self.node.composition.fic

    # ============================================================
    # CUSTO PRÓPRIO DA COMPOSIÇÃO
    # ============================================================

    @property
    def own_cost(self) -> Decimal:
        """
        Retorna o custo próprio da composição.

        Considera os custos calculados diretamente pela própria
        composição, sem incluir atividades auxiliares e tempos fixos.

        Fórmula:

            custo operacional unitário
            + materiais
        """

        return (
            self.operational_unit
            + self.materials_cost
        )

    # ============================================================
    # CUSTO DAS COMPOSIÇÕES FILHAS
    # ============================================================

    @property
    def children_cost(self) -> Decimal:
        """
        Retorna o custo proveniente das composições filhas.

        Fórmula:

            atividades auxiliares
            + tempos fixos
        """

        return (
            self.auxiliary_cost
            + self.fixed_time_cost
        )

    # ============================================================
    # CUSTO OPERACIONAL
    # ============================================================

    @property
    def operational_cost(self) -> Decimal:
        """
        Retorna o custo operacional unitário.

        Mantido como alias de operational_unit para facilitar
        a leitura do código de relatórios e testes.
        """

        return self.operational_unit

    # ============================================================
    # VERIFICAÇÕES
    # ============================================================

    def has_auxiliary_cost(self) -> bool:
        """
        Verifica se a composição possui custo de atividades
        auxiliares.
        """

        return self.auxiliary_cost != Decimal("0")

    def has_fixed_time_cost(self) -> bool:
        """
        Verifica se a composição possui custo de tempos fixos.
        """

        return self.fixed_time_cost != Decimal("0")

    def has_children_cost(self) -> bool:
        """
        Verifica se a composição possui custos provenientes
        de outras composições.
        """

        return self.children_cost != Decimal("0")

    # ============================================================
    # REPRESENTAÇÃO
    # ============================================================

    def __repr__(self) -> str:
        """
        Retorna uma representação resumida do resultado.
        """

        return (
            "CompositionCalculationResult("
            f"code='{self.composition_code}', "
            f"own_cost={self.own_cost}, "
            f"children_cost={self.children_cost}, "
            f"unit_cost={self.composition_unit_cost}"
            ")"
        )