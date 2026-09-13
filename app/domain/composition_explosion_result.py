from app.domain.aggregated_composition import (
    AggregatedComposition,
)
from app.domain.aggregated_input import (
    AggregatedInput,
)
from app.domain.composition_node import (
    CompositionNode,
)


class CompositionExplosionResult:
    """
    Representa o resultado completo da explosão
    de uma composição.
    """

    def __init__(
        self,
        root_node: CompositionNode,
        compositions: list[
            AggregatedComposition
        ],
        inputs: list[
            AggregatedInput
        ],
    ) -> None:

        self.root_node = root_node
        self.compositions = compositions
        self.inputs = inputs

    def __repr__(self) -> str:

        return (
            f"CompositionExplosionResult("
            f"nodes={sum(1 for _ in self.root_node.walk())}, "
            f"compositions={len(self.compositions)}, "
            f"inputs={len(self.inputs)}"
            f")"
        )