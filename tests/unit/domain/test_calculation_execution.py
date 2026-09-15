from decimal import Decimal

import pytest

from app.domain.calculation_execution import CalculationExecution
from app.domain.composition import Composition
from app.domain.composition_calculation_result import (
    CompositionCalculationResult,
)
from app.domain.composition_node import CompositionNode


def _build_node(
    *,
    identifier: int = 1,
    code: str = "COMP-001",
) -> CompositionNode:
    """
    Cria uma ocorrência mínima de composição para os testes.
    """
    composition = Composition(
        id=identifier,
        composition_group="XX",
        generic_item=code,
        generic_description=f"Composição {code}",
        unit="un",
        fic=Decimal("0"),
        production=Decimal("1"),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[],
        transports=[],
    )

    return CompositionNode(
        composition=composition,
    )


def _build_result(
    node: CompositionNode,
    unit_cost: str,
) -> CompositionCalculationResult:
    """
    Cria um resultado de cálculo identificável pelo custo unitário.
    """
    return CompositionCalculationResult(
        node=node,
        composition_unit_cost=Decimal(unit_cost),
    )


def test_execution_stores_and_returns_result_for_node():
    """
    CalculationExecution deve armazenar um resultado e
    recuperá-lo pela ocorrência correspondente.
    """
    execution = CalculationExecution()
    node = _build_node()
    result = _build_result(
        node=node,
        unit_cost="100.00",
    )

    execution.add_result(
        node=node,
        result=result,
    )

    returned_result = execution.get_result(
        node=node,
    )

    assert returned_result is result


def test_execution_keeps_distinct_results_for_same_composition_code():
    """
    Duas ocorrências com o mesmo código devem possuir
    resultados independentes.

    O código da composição não pode ser utilizado como
    identidade da ocorrência.
    """
    execution = CalculationExecution()

    first_node = _build_node(
        identifier=1,
        code="COMP-001",
    )

    second_node = _build_node(
        identifier=2,
        code="COMP-001",
    )

    first_result = _build_result(
        node=first_node,
        unit_cost="100.00",
    )

    second_result = _build_result(
        node=second_node,
        unit_cost="200.00",
    )

    execution.add_result(
        node=first_node,
        result=first_result,
    )

    execution.add_result(
        node=second_node,
        result=second_result,
    )

    assert execution.get_result(
        node=first_node,
    ) is first_result

    assert execution.get_result(
        node=second_node,
    ) is second_result

    assert first_result is not second_result

    assert first_result.node is first_node
    assert second_result.node is second_node


def test_execution_does_not_overwrite_result_for_distinct_occurrences():
    """
    Adicionar um resultado para uma ocorrência não deve
    sobrescrever o resultado de outra ocorrência, mesmo
    quando ambas possuem o mesmo código.
    """
    execution = CalculationExecution()

    first_node = _build_node(
        identifier=1,
        code="COMP-001",
    )

    second_node = _build_node(
        identifier=2,
        code="COMP-001",
    )

    first_result = _build_result(
        node=first_node,
        unit_cost="100.00",
    )

    second_result = _build_result(
        node=second_node,
        unit_cost="200.00",
    )

    execution.add_result(
        node=first_node,
        result=first_result,
    )

    execution.add_result(
        node=second_node,
        result=second_result,
    )

    assert execution.get_result(
        node=first_node,
    ) is first_result

    assert execution.get_result(
        node=second_node,
    ) is second_result


def test_execution_returns_results_in_calculation_order():
    """
    get_all_results() deve preservar a ordem em que os
    resultados foram adicionados.

    O CompositionCalculator adiciona os resultados em
    pós-ordem; portanto, essa ordem deve ser preservada.
    """
    execution = CalculationExecution()

    first_node = _build_node(
        identifier=1,
        code="CHILD-A",
    )

    second_node = _build_node(
        identifier=2,
        code="CHILD-B",
    )

    root_node = _build_node(
        identifier=3,
        code="ROOT",
    )

    first_result = _build_result(
        node=first_node,
        unit_cost="10.00",
    )

    second_result = _build_result(
        node=second_node,
        unit_cost="20.00",
    )

    root_result = _build_result(
        node=root_node,
        unit_cost="30.00",
    )

    execution.add_result(
        node=first_node,
        result=first_result,
    )

    execution.add_result(
        node=second_node,
        result=second_result,
    )

    execution.add_result(
        node=root_node,
        result=root_result,
    )

    results = execution.get_all_results()

    assert results == [
        first_result,
        second_result,
        root_result,
    ]


def test_execution_get_all_results_preserves_distinct_occurrences():
    """
    get_all_results() deve retornar resultados distintos para
    ocorrências distintas da mesma composição.
    """
    execution = CalculationExecution()

    first_node = _build_node(
        identifier=1,
        code="COMP-001",
    )

    second_node = _build_node(
        identifier=2,
        code="COMP-001",
    )

    first_result = _build_result(
        node=first_node,
        unit_cost="100.00",
    )

    second_result = _build_result(
        node=second_node,
        unit_cost="200.00",
    )

    execution.add_result(
        node=first_node,
        result=first_result,
    )

    execution.add_result(
        node=second_node,
        result=second_result,
    )

    results = execution.get_all_results()

    assert len(results) == 2
    assert results[0] is first_result
    assert results[1] is second_result

    assert results[0].node is first_node
    assert results[1].node is second_node


def test_execution_raises_error_when_result_does_not_exist():
    """
    Solicitar o resultado de uma ocorrência que ainda não
    foi calculada deve gerar ValueError.
    """
    execution = CalculationExecution()
    node = _build_node(
        identifier=1,
        code="COMP-001",
    )

    with pytest.raises(
        ValueError,
        match="Composition result not found for node",
    ):
        execution.get_result(
            node=node,
        )


def test_execution_isolated_between_instances():
    """
    Cada CalculationExecution deve possuir seu próprio estado.
    """
    first_execution = CalculationExecution()
    second_execution = CalculationExecution()

    node = _build_node(
        identifier=1,
        code="COMP-001",
    )

    result = _build_result(
        node=node,
        unit_cost="100.00",
    )

    first_execution.add_result(
        node=node,
        result=result,
    )

    assert first_execution.get_result(
        node=node,
    ) is result

    with pytest.raises(ValueError):
        second_execution.get_result(
            node=node,
        )

    assert second_execution.get_all_results() == []
