from app.domain.composition_calculation_result import (
    CompositionCalculationResult,
)
from app.domain.composition_node import CompositionNode


class CalculationExecution:
    """
    Representa o estado de uma execução de cálculo.

    Os resultados armazenados pertencem exclusivamente
    à execução atual e não ao CompositionCalculator.
    """

    def __init__(self) -> None:
        self._results: dict[
            CompositionNode,
            CompositionCalculationResult,
        ] = {}

    def add_result(
        self,
        node: CompositionNode,
        result: CompositionCalculationResult,
    ) -> None:
        """
        Armazena o resultado calculado de um nó.
        """

        self._results[node] = result

    def get_result(
        self,
        node: CompositionNode,
    ) -> CompositionCalculationResult:
        """
        Retorna o resultado calculado de um nó.
        """

        if node not in self._results:
            raise ValueError(
                "Composition result not found for node: "
                f"{node.composition.generic_item}"
            )

        return self._results[node]

    def get_all_results(
        self,
    ) -> list[CompositionCalculationResult]:
        """
        Retorna todos os resultados da execução.

        A ordem corresponde à ordem em que os nós
        foram calculados em pós-ordem.
        """

        return list(
            self._results.values()
        )