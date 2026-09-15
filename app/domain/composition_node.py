from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.composition import Composition
    from app.domain.composition_input import CompositionInput


class CompositionNode:
    """
    Representa uma ocorrência de uma composição dentro da árvore.

    Cada nó representa uma ocorrência específica de uma composição.
    A estrutura é uma árvore de ocorrências, portanto cada nó possui
    no máximo um pai.

    O nó concentra apenas:
    - seu estado;
    - sua relação imediata com pai e filhos;
    - regras de negócio próprias da ocorrência;
    - cálculos de quantidade derivados de sua posição na árvore.
    """

    def __init__(
        self,
        composition: Composition,
        reference_input: CompositionInput | None = None,
        parent: CompositionNode | None = None,
    ) -> None:
        """
        Inicializa uma ocorrência de composição.

        Args:
            composition: Composição representada pela ocorrência.
            reference_input: Insumo de composição que originou esta
                ocorrência, quando aplicável.
            parent: Pai da ocorrência, quando aplicável.
        """
        self._validate_production(composition)

        self.composition = composition
        self.reference_input = reference_input
        self.parent = parent
        self.children: list[CompositionNode] = []

    @staticmethod
    def _validate_production(composition: Composition) -> None:
        if composition.production <= Decimal("0"):
            raise ValueError(
                "Composition production must be greater than zero: "
                f"{composition.code}"
            )

    @property
    def reference_quantity(self) -> Decimal:
        """
        Retorna a quantidade da referência que originou o nó.

        Para a raiz, que não possui uma referência de origem,
        a quantidade considerada é 1.
        """
        if self.reference_input is None:
            return Decimal("1")

        return self.reference_input.input_quantity

    @property
    def reference_code(self) -> str | None:
        """
        Retorna o código da referência que originou o nó.
        """
        if self.reference_input is None:
            return None

        return self.reference_input.generic_item

    @property
    def reference_group(self) -> str | None:
        """
        Retorna o grupo da referência que originou o nó.
        """
        if self.reference_input is None:
            return None

        return self.reference_input.input_group

    def is_root(self) -> bool:
        """
        Verifica se o nó é a raiz da árvore.
        """
        return self.parent is None

    def is_auxiliary_activity(self) -> bool:
        """
        Verifica se o nó foi originado por uma atividade auxiliar.
        """
        return (
            self.reference_input is not None
            and self.reference_input.is_auxiliary_activity()
        )

    def is_fixed_time(self) -> bool:
        """
        Verifica se o nó foi originado por um tempo fixo.
        """
        return (
            self.reference_input is not None
            and self.reference_input.is_fixed_time()
        )

    def is_composition_reference(self) -> bool:
        """
        Verifica se o nó representa uma referência de composição.
        """
        return (
            self.reference_input is not None
            and self.reference_input.is_composition_reference()
        )

    def add_child(self, child: CompositionNode) -> None:
        """
        Adiciona uma ocorrência filha ao nó.

        Como a estrutura do domínio é uma árvore de ocorrências,
        um nó não pode:
        - ser filho de si mesmo;
        - possuir outro pai;
        - ser adicionado duas vezes ao mesmo pai;
        - criar um ciclo na estrutura hierárquica.

        Args:
            child: Ocorrência que será adicionada como filha.

        Raises:
            ValueError: Quando a operação violar a estrutura de árvore.
        """
        if child is self:
            raise ValueError(
                "O nó não pode ser seu próprio filho"
            )

        if child.parent is not None and child.parent is not self:
            raise ValueError(
                "O nó não pode ter mais de um nó pai."
            )

        if child in self.children:
            raise ValueError(
                "O nó já é filho deste nó pai."
            )

        ancestor = self

        while ancestor is not None:
            if ancestor is child:
                raise ValueError(
                    "O nó não pode ser adicionado abaixo de seu descendente"
                )

            ancestor = ancestor.parent

        child.parent = self
        self.children.append(child)

    def has_children(self) -> bool:
        """
        Verifica se o nó possui ocorrências filhas.
        """
        return bool(self.children)

    def get_children_count(self) -> int:
        """
        Retorna a quantidade de ocorrências filhas.
        """
        return len(self.children)

    @property
    def effective_quantity(self) -> Decimal:
        """
        Calcula a quantidade efetiva da ocorrência.

        Para a raiz:

            1

        Para os demais nós:

            quantidade efetiva do pai
            × quantidade da referência
            ÷ produção da composição

        A regra de negócio existente é preservada.
        """
        if self.is_root():
            return Decimal("1")

        production = self.composition.production

        return (
            self.parent.effective_quantity
            * self.reference_quantity
            / production
        )

    @property
    def accumulated_quantity(self) -> Decimal:
        """
        Calcula a quantidade acumulada ao longo do caminho da árvore.

        Para a raiz:

            1

        Para os demais nós:

            quantidade acumulada do pai
            × quantidade da referência

        A quantidade acumulada não incorpora a produção da composição.
        """
        if self.is_root():
            return Decimal("1")

        return (
            self.parent.accumulated_quantity
            * self.reference_quantity
        )

    def __repr__(self) -> str:
        """
        Retorna uma representação textual do nó.
        """
        return (
            f"CompositionNode("
            f"composition_code={self.composition.code!r}, "
            f"reference_code={self.reference_code!r})"
        )