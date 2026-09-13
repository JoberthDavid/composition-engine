from decimal import Decimal

from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput


class CompositionNode:
    """
    Representa uma composição dentro da árvore de composições.

    Cada nó possui:

    - uma composição;
    - uma referência ao nó pai;
    - o CompositionInput que originou a referência;
    - zero ou mais nós filhos.

    Os filhos representam composições referenciadas por:

    - AX: Atividade Auxiliar;
    - TF: Tempo Fixo.

    O atributo reference_input é especialmente importante porque
    identifica exatamente qual insumo da composição pai originou
    aquele nó.

    Dessa forma, o nó filho consegue identificar diretamente:

    - o código da referência;
    - a quantidade utilizada;
    - o grupo do insumo;
    - se a referência é AX;
    - se a referência é TF.

    Isso evita a necessidade de procurar novamente o insumo dentro
    da composição pai durante o cálculo.
    """

    def __init__(
        self,
        composition: Composition,
        reference_input: CompositionInput | None = None,
        parent: "CompositionNode | None" = None,
    ) -> None:
        """
        Inicializa um nó da árvore de composições.

        Parameters
        ----------
        composition:
            A composição representada pelo nó.

        reference_input:
            O CompositionInput da composição pai que originou
            esta composição filha.

            Para o nó raiz, o valor deve ser None.

        parent:
            O nó pai da árvore.

            Para o nó raiz, o valor deve ser None.
        """

        self.composition = composition
        self.reference_input = reference_input
        self.parent = parent

        self.children: list["CompositionNode"] = []

    # ============================================================
    # REFERÊNCIA
    # ============================================================

    @property
    def reference_quantity(self) -> Decimal | None:
        """
        Retorna a quantidade utilizada para referenciar
        esta composição dentro da composição pai.

        A quantidade é obtida diretamente do CompositionInput
        que originou o nó.

        Para o nó raiz, retorna None.
        """

        if self.reference_input is None:
            return None

        return self.reference_input.input_quantity

    @property
    def reference_code(self) -> str | None:
        """
        Retorna o código da referência que originou o nó.

        Para o nó raiz, retorna None.
        """

        if self.reference_input is None:
            return None

        return self.reference_input.generic_item

    @property
    def reference_group(self) -> str | None:
        """
        Retorna o grupo do insumo que originou a referência.

        Exemplos:

        - AX
        - TF

        Para o nó raiz, retorna None.
        """

        if self.reference_input is None:
            return None

        return self.reference_input.input_group

    # ============================================================
    # IDENTIFICAÇÃO DO NÓ
    # ============================================================

    def is_root(self) -> bool:
        """
        Verifica se o nó é a raiz da árvore.
        """

        return self.parent is None

    def is_auxiliary_activity(self) -> bool:
        """
        Verifica se o nó foi originado por uma
        atividade auxiliar (AX).

        O nó raiz nunca é uma atividade auxiliar.
        """

        if self.reference_input is None:
            return False

        return (
            self.reference_input.is_auxiliary_activity()
        )

    def is_fixed_time(self) -> bool:
        """
        Verifica se o nó foi originado por
        uma referência de tempo fixo (TF).

        O nó raiz nunca é um tempo fixo.
        """

        if self.reference_input is None:
            return False

        return (
            self.reference_input.is_fixed_time()
        )

    def is_composition_reference(self) -> bool:
        """
        Verifica se o nó foi originado por uma referência
        para outra composição.

        Atualmente isso significa:

        - AX
        - TF
        """

        if self.reference_input is None:
            return False

        return (
            self.reference_input.is_composition_reference()
        )

    # ============================================================
    # ÁRVORE
    # ============================================================

    def add_child(
        self,
        child: "CompositionNode",
    ) -> None:
        """
        Adiciona um nó filho ao nó atual.

        O nó atual passa automaticamente a ser definido
        como pai do filho.
        """

        child.parent = self

        self.children.append(
            child
        )

    def has_children(self) -> bool:
        """
        Verifica se o nó possui filhos.
        """

        return bool(
            self.children
        )

    def get_children_count(self) -> int:
        """
        Retorna a quantidade de nós filhos.
        """

        return len(
            self.children
        )

    # ============================================================
    # QUANTIDADES NA ÁRVORE
    # ============================================================

    @property
    def effective_quantity(self) -> Decimal:
        """
        Calcula a quantidade efetiva da composição
        dentro da árvore.

        Para o nó raiz:

            effective_quantity = 1

        Para os demais nós:

            quantidade efetiva do pai
            × quantidade da referência
            ÷ produção da composição atual

        Observação:

        Este cálculo representa a propagação de quantidade
        considerando a produção da composição filha.
        """

        if self.is_root():
            return Decimal("1")

        reference_quantity = self.reference_quantity

        if reference_quantity is None:

            if self.parent is None:
                return Decimal("1")

            return self.parent.effective_quantity

        if self.composition.production == Decimal("0"):

            raise ValueError(
                "Composition production cannot be zero: "
                f"{self.composition.code}"
            )

        if self.parent is None:
            return Decimal("1")

        return (
            self.parent.effective_quantity
            * reference_quantity
            / self.composition.production
        )

    @property
    def accumulated_quantity(self) -> Decimal:
        """
        Calcula a quantidade acumulada ao longo
        do caminho da árvore.

        A produção NÃO é aplicada neste cálculo.

        Para o nó raiz:

            accumulated_quantity = 1

        Para os demais nós:

            quantidade acumulada do pai
            × quantidade da referência

        Exemplo:

        Raiz
            quantidade = 1

        AX 1
            quantidade = 10

        AX 2
            quantidade = 5

        Quantidade acumulada do AX 2:

            1 × 10 × 5 = 50
        """

        if self.is_root():
            return Decimal("1")

        reference_quantity = self.reference_quantity

        if reference_quantity is None:

            if self.parent is None:
                return Decimal("1")

            return self.parent.accumulated_quantity

        if self.parent is None:
            return Decimal("1")

        return (
            self.parent.accumulated_quantity
            * reference_quantity
        )

    # ============================================================
    # REPRESENTAÇÃO
    # ============================================================

    def __repr__(self) -> str:
        """
        Retorna uma representação textual do nó.
        """

        return (
            "CompositionNode("
            f"code='{self.composition.code}', "
            f"reference_code={self.reference_code!r}, "
            f"reference_group={self.reference_group!r}, "
            f"reference_quantity={self.reference_quantity!r}, "
            f"effective_quantity={self.effective_quantity}"
            ")"
        )