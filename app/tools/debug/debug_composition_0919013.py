
#PYTHONPATH=. python app/tools/debug/debug_composition_0919013.py

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.domain.calculation_context import CalculationContext
from app.domain.composition_calculation_result import (
    CompositionCalculationResult,
)
from app.infrastructure.composition_api_client import (
    CompositionApiClient,
)
from app.infrastructure.monetary_value_api_client import (
    MonetaryValueApiClient,
)
from app.repositories.composition_repository import (
    CompositionRepository,
)
from app.repositories.monetary_value_repository import (
    MonetaryValueRepository,
)
from app.repositories.optimized_composition_repository import (
    OptimizedCompositionRepository,
)
from app.services.composition_calculator import (
    CompositionCalculator,
)
from app.services.composition_resolver import (
    CompositionResolver,
)
from app.services.equipment_calculator import (
    EquipmentCalculator,
)
from app.services.fic_calculator import (
    FicCalculator,
)
from app.services.labor_calculator import (
    LaborCalculator,
)
from app.services.material_calculator import (
    MaterialCalculator,
)
from app.services.monetary_value_resolver import (
    MonetaryValueResolver,
)
from app.services.operational_cost_calculator import (
    OperationalCostCalculator,
)

from app.tools.debug.debug_query_metrics import (
    round_2,
    round_4,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

COMPOSITION_CODE = "0919013"

COMPOSITION_DATA_BASE = "2021-10-01"

MONETARY_DATA_BASE = date(
    2021,
    10,
    1,
)

SOURCE_FILE_UF = "DF"

TYPE_SYSTEM = "ON"

REPORT_DIRECTORY = (
    Path(__file__).resolve().parent
)

JSON_REPORT_PATH = (
    REPORT_DIRECTORY
    / "debug_composition_0919013_report.json"
)

MARKDOWN_REPORT_PATH = (
    REPORT_DIRECTORY
    / "debug_composition_0919013_report.md"
)


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def serialize_value(
    value: Any,
) -> Any:
    """
    Converte objetos utilizados pelo motor para estruturas
    serializáveis em JSON.
    """

    if isinstance(
        value,
        Decimal,
    ):
        return str(value)

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            serialize_value(item)
            for item in value
        ]

    return value


# ============================================================
# ESTRUTURAS DE DIAGNÓSTICO
# ============================================================

@dataclass
class HttpRequestEvent:
    """
    Registra uma chamada HTTP realizada pelo cliente
    de valores monetários.
    """

    sequence: int
    method: str
    operation: str
    kwargs: dict[str, Any]
    result_count: int
    result_records: list[dict[str, Any]]


@dataclass
class MonetaryResolutionEvent:
    """
    Registra uma resolução de MonetaryValue.
    """

    sequence: int
    node_id: int | None
    composition_code: str | None

    code: str

    criteria: dict[str, Any]

    candidate_count_before_filter: int

    candidate_ids_before_filter: list[Any]

    candidate_count_after_filter: int

    candidate_ids_after_filter: list[Any]

    selected_id: Any | None

    selected_value: Any | None

    selected_unit: Any | None

    selected_classification: Any | None

    selected_group: Any | None

    selected_type_system: Any | None

    selected_source_file_uf: Any | None

    selected_source_file_data_base: Any | None


@dataclass
class MonetaryLineEvent:
    """
    Registra a utilização efetiva de um valor monetário
    por uma linha de cálculo.
    """

    sequence: int

    node_id: int | None
    composition_code: str | None

    calculator: str

    input_group: str | None

    generic_item: str

    input_quantity: Any

    input_use: Any | None

    line_cost: Any

    monetary_values_resolved: list[int]
    monetary_values_used: list[int]


@dataclass
class CompositionNodeEvent:
    """
    Representa uma ocorrência específica de CompositionNode.
    """

    sequence: int

    node_id: int

    parent_node_id: int | None

    depth: int

    composition_code: str

    generic_item: str
    description: str

    production: Any

    reference_code: str | None
    reference_group: str | None
    reference_quantity: Any

    effective_quantity: Any
    accumulated_quantity: Any

    input_count: int
    child_count: int

    inputs: list[dict[str, Any]]


@dataclass
class CompositionCalculationEvent:
    """
    Resultado completo do cálculo de uma ocorrência.
    """

    sequence: int

    node_id: int

    composition_code: str

    production: Any

    fic_percentage: Any

    equipment_cost: Any
    labor_cost: Any

    fic_cost: Any

    operational_total: Any
    operational_unit: Any

    materials_cost: Any

    auxiliary_cost: Any
    fixed_time_cost: Any

    composition_total_raw: Any
    composition_unit_cost: Any

    own_cost: Any
    children_cost: Any


# ============================================================
# COLETOR CENTRAL
# ============================================================

class DebugCollector:
    """
    Coleta as duas trilhas da execução.

    TRILHA A:
        árvore
        nós
        inputs
        referências
        quantidades
        resultados

    TRILHA B:
        chamadas HTTP
        registros retornados
        filtros
        valores selecionados
        utilização efetiva
        parcelas de cálculo
    """

    def __init__(self) -> None:
        self.http_requests: list[
            HttpRequestEvent
        ] = []

        self.monetary_resolutions: list[
            MonetaryResolutionEvent
        ] = []

        self.monetary_lines: list[
            MonetaryLineEvent
        ] = []

        self.composition_nodes: list[
            CompositionNodeEvent
        ] = []

        self.composition_calculations: list[
            CompositionCalculationEvent
        ] = []

        self.current_node_id: int | None = None
        self.current_composition_code: str | None = None

        self._http_sequence = 0
        self._monetary_resolution_sequence = 0
        self._monetary_line_sequence = 0
        self._node_sequence = 0
        self._calculation_sequence = 0

    # ========================================================
    # CONTEXTO DO NÓ
    # ========================================================

    def set_current_node(
        self,
        node,
    ) -> None:
        self.current_node_id = id(node)

        self.current_composition_code = (
            str(
                node.composition.code
            )
        )

    # ========================================================
    # HTTP
    # ========================================================

    def record_http_request(
        self,
        operation: str,
        kwargs: dict[str, Any],
        result_records: list[dict],
    ) -> None:

        self._http_sequence += 1

        self.http_requests.append(
            HttpRequestEvent(
                sequence=self._http_sequence,
                method="GET",
                operation=operation,
                kwargs=serialize_value(
                    kwargs
                ),
                result_count=len(
                    result_records
                ),
                result_records=serialize_value(
                    result_records
                ),
            )
        )

    # ========================================================
    # RESOLUÇÃO MONETÁRIA
    # ========================================================

    def record_monetary_resolution(
        self,
        code: str,
        criteria: dict[str, Any],
        before: list,
        after: list,
        selected,
    ) -> None:

        self._monetary_resolution_sequence += 1

        selected_id = None
        selected_value = None
        selected_unit = None
        selected_classification = None
        selected_group = None
        selected_type_system = None
        selected_uf = None
        selected_data_base = None

        if selected is not None:

            selected_id = selected.id
            selected_value = (
                selected.monetary_value
            )
            selected_unit = selected.unit
            selected_classification = (
                selected.classification
            )
            selected_group = selected.group
            selected_type_system = (
                selected.type_system
            )
            selected_uf = (
                selected.source_file_uf
            )
            selected_data_base = (
                selected.source_file_data_base
            )

        self.monetary_resolutions.append(
            MonetaryResolutionEvent(
                sequence=(
                    self._monetary_resolution_sequence
                ),
                node_id=self.current_node_id,
                composition_code=(
                    self.current_composition_code
                ),
                code=str(code),
                criteria=serialize_value(
                    criteria
                ),
                candidate_count_before_filter=(
                    len(before)
                ),
                candidate_ids_before_filter=[
                    value.id
                    for value in before
                ],
                candidate_count_after_filter=(
                    len(after)
                ),
                candidate_ids_after_filter=[
                    value.id
                    for value in after
                ],
                selected_id=selected_id,
                selected_value=serialize_value(
                    selected_value
                ),
                selected_unit=serialize_value(
                    selected_unit
                ),
                selected_classification=(
                    serialize_value(
                        selected_classification
                    )
                ),
                selected_group=serialize_value(
                    selected_group
                ),
                selected_type_system=(
                    serialize_value(
                        selected_type_system
                    )
                ),
                selected_source_file_uf=(
                    serialize_value(
                        selected_uf
                    )
                ),
                selected_source_file_data_base=(
                    serialize_value(
                        selected_data_base
                    )
                ),
            )
        )

    # ========================================================
    # LINHA MONETÁRIA
    # ========================================================

    def record_monetary_line(
        self,
        calculator: str,
        composition_input,
        line_cost: Decimal,
        resolution_start_sequence: int,
    ) -> None:
        """
        Registra os valores monetários resolvidos e os que
        efetivamente participaram do cálculo da linha.

        A correlação usa o intervalo de sequência das resoluções
        produzidas pela chamada específica do calculador, evitando
        associar resoluções anteriores do mesmo nó e item.
        """

        self._monetary_line_sequence += 1

        generic_item = str(
            composition_input.generic_item
        )

        resolution_end_sequence = (
            self._monetary_resolution_sequence
        )

        line_resolutions = [
            event
            for event in self.monetary_resolutions
            if (
                resolution_start_sequence
                < event.sequence
                <= resolution_end_sequence
                and event.node_id
                == self.current_node_id
                and event.code
                == generic_item
            )
        ]

        resolved_values = [
            event.selected_id
            for event in line_resolutions
            if event.selected_id is not None
        ]

        input_use = getattr(
            composition_input,
            "input_use",
            None,
        )

        effective_values = (
            self._get_effective_monetary_value_ids(
                calculator=calculator,
                line_resolutions=line_resolutions,
                input_use=input_use,
            )
        )

        self.monetary_lines.append(
            MonetaryLineEvent(
                sequence=(
                    self._monetary_line_sequence
                ),
                node_id=self.current_node_id,
                composition_code=(
                    self.current_composition_code
                ),
                calculator=calculator,
                input_group=(
                    composition_input.input_group
                ),
                generic_item=generic_item,
                input_quantity=(
                    serialize_value(
                        composition_input.input_quantity
                    )
                ),
                input_use=serialize_value(
                    input_use
                ),
                line_cost=serialize_value(
                    line_cost
                ),
                monetary_values_resolved=(
                    resolved_values
                ),
                monetary_values_used=(
                    effective_values
                ),
            )
        )

    @staticmethod
    def _get_effective_monetary_value_ids(
        calculator: str,
        line_resolutions: list[MonetaryResolutionEvent],
        input_use: Any | None,
    ) -> list[int]:
        """
        Identifica os valores que efetivamente participaram
        da fórmula do calculador.

        Para equipamentos:
            input_use = 1 -> PR
            input_use = 0 -> IM
            0 < input_use < 1 -> PR + IM

        Para mão de obra e materiais, o valor selecionado pelo
        resolver é o valor efetivamente utilizado.
        """

        if not line_resolutions:
            return []

        if calculator != "EquipmentCalculator":
            return [
                event.selected_id
                for event in line_resolutions
                if event.selected_id is not None
            ]

        use = (
            Decimal(str(input_use))
            if input_use is not None
            else Decimal("0")
        )

        effective_ids: list[int] = []

        for event in line_resolutions:
            if event.selected_id is None:
                continue

            classification = (
                str(event.selected_classification).upper()
                if event.selected_classification is not None
                else ""
            )

            if classification == "PR" and use > 0:
                effective_ids.append(event.selected_id)
            elif classification == "IM" and use < 1:
                effective_ids.append(event.selected_id)

        return effective_ids

    # ========================================================
    # NÓ DA ÁRVORE
    # ========================================================

    def record_node(
        self,
        node,
        depth: int,
    ) -> None:

        self._node_sequence += 1

        inputs = []

        for composition_input in (
            node.composition.inputs
        ):
            inputs.append(
                {
                    "code": str(
                        composition_input.code
                    ),
                    "generic_item": str(
                        composition_input.generic_item
                    ),
                    "description": serialize_value(
                        getattr(
                            composition_input,
                            "generic_description",
                            None,
                        )
                    ),
                    "input_group": serialize_value(
                        composition_input.input_group
                    ),
                    "input_quantity": serialize_value(
                        composition_input.input_quantity
                    ),
                    "input_use": serialize_value(
                        getattr(
                            composition_input,
                            "input_use",
                            None,
                        )
                    ),
                    "unit": serialize_value(
                        getattr(
                            composition_input,
                            "unit",
                            None,
                        )
                    ),
                }
            )

        self.composition_nodes.append(
            CompositionNodeEvent(
                sequence=self._node_sequence,
                node_id=id(node),
                parent_node_id=(
                    id(node.parent)
                    if node.parent is not None
                    else None
                ),
                depth=depth,
                composition_code=str(
                    node.composition.code
                ),
                generic_item=str(
                    node.composition.generic_item
                ),
                description=str(
                    node.composition.generic_description
                ),
                production=serialize_value(
                    node.composition.production
                ),
                reference_code=(
                    serialize_value(
                        node.reference_code
                    )
                ),
                reference_group=(
                    serialize_value(
                        node.reference_group
                    )
                ),
                reference_quantity=(
                    serialize_value(
                        node.reference_quantity
                    )
                ),
                effective_quantity=(
                    serialize_value(
                        node.effective_quantity
                    )
                ),
                accumulated_quantity=(
                    serialize_value(
                        node.accumulated_quantity
                    )
                ),
                input_count=len(
                    node.composition.inputs
                ),
                child_count=len(
                    node.children
                ),
                inputs=inputs,
            )
        )

    # ========================================================
    # RESULTADO DA COMPOSIÇÃO
    # ========================================================

    def record_calculation(
        self,
        result: CompositionCalculationResult,
    ) -> None:

        self._calculation_sequence += 1

        self.composition_calculations.append(
            CompositionCalculationEvent(
                sequence=self._calculation_sequence,
                node_id=id(result.node),
                composition_code=str(
                    result.composition_code
                ),
                production=serialize_value(
                    result.production
                ),
                fic_percentage=serialize_value(
                    result.fic_percentage
                ),
                equipment_cost=serialize_value(
                    result.equipment_cost
                ),
                labor_cost=serialize_value(
                    result.labor_cost
                ),
                fic_cost=serialize_value(
                    result.fic_cost
                ),
                operational_total=serialize_value(
                    result.operational_total
                ),
                operational_unit=serialize_value(
                    result.operational_unit
                ),
                materials_cost=serialize_value(
                    result.materials_cost
                ),
                auxiliary_cost=serialize_value(
                    result.auxiliary_cost
                ),
                fixed_time_cost=serialize_value(
                    result.fixed_time_cost
                ),
                composition_total_raw=serialize_value(
                    result.composition_total_raw
                ),
                composition_unit_cost=serialize_value(
                    result.composition_unit_cost
                ),
                own_cost=serialize_value(
                    result.own_cost
                ),
                children_cost=serialize_value(
                    result.children_cost
                ),
            )
        )

    # ========================================================
    # RELATÓRIO
    # ========================================================

    def build_report(
        self,
        tree,
        root_result,
        started_at: datetime,
        finished_at: datetime,
    ) -> dict[str, Any]:

        resolution_by_code = Counter(
            event.code
            for event in self.monetary_resolutions
        )

        selected_by_code = Counter(
            event.code
            for event in self.monetary_resolutions
            if event.selected_id is not None
        )

        http_records_by_operation = Counter(
            event.operation
            for event in self.http_requests
        )

        report = {
            "metadata": {
                "composition_code": COMPOSITION_CODE,
                "composition_data_base": (
                    COMPOSITION_DATA_BASE
                ),
                "monetary_data_base": (
                    MONETARY_DATA_BASE.isoformat()
                ),
                "source_file_uf": SOURCE_FILE_UF,
                "type_system": TYPE_SYSTEM,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_seconds": (
                    finished_at - started_at
                ).total_seconds(),
            },

            "summary": {
                "tree_node_count": len(
                    self.composition_nodes
                ),
                "tree_leaf_count": len(
                    tree.get_leaves()
                ),
                "composition_calculation_count": len(
                    self.composition_calculations
                ),
                "http_request_count": len(
                    self.http_requests
                ),
                "monetary_resolution_count": len(
                    self.monetary_resolutions
                ),
                "monetary_line_count": len(
                    self.monetary_lines
                ),
                "unique_monetary_codes": len(
                    resolution_by_code
                ),
                "root_result": (
                    serialize_value(
                        root_result.composition_unit_cost
                    )
                ),
                "http_requests_by_operation": dict(
                    http_records_by_operation
                ),
                "resolutions_by_code": dict(
                    resolution_by_code
                ),
                "selected_values_by_code": dict(
                    selected_by_code
                ),
            },

            "composition": {
                "nodes": [
                    asdict(node)
                    for node in self.composition_nodes
                ],
                "calculations": [
                    asdict(calculation)
                    for calculation
                    in self.composition_calculations
                ],
            },

            "monetary": {
                "http_requests": [
                    asdict(event)
                    for event in self.http_requests
                ],
                "resolutions": [
                    asdict(event)
                    for event
                    in self.monetary_resolutions
                ],
                "lines": [
                    asdict(event)
                    for event in self.monetary_lines
                ],
            },
        }

        return serialize_value(
            report
        )


# ============================================================
# CLIENTE MONETÁRIO INSTRUMENTADO
# ============================================================

class DebugMonetaryValueApiClient:
    """
    Proxy do MonetaryValueApiClient.

    Não modifica o cliente original.

    Apenas registra as chamadas e delega para ele.
    """

    def __init__(
        self,
        collector: DebugCollector,
        client: MonetaryValueApiClient | None = None,
    ) -> None:

        self.collector = collector

        self.client = (
            client
            if client is not None
            else MonetaryValueApiClient()
        )

    def get_values_by_code(
        self,
        code: str,
    ) -> list[dict]:

        result = self.client.get_values_by_code(
            code
        )

        self.collector.record_http_request(
            operation="get_values_by_code",
            kwargs={
                "code": code,
            },
            result_records=result,
        )

        return result

    def get_values(
        self,
        **kwargs,
    ) -> list[dict]:

        result = self.client.get_values(
            **kwargs
        )

        self.collector.record_http_request(
            operation="get_values",
            kwargs=kwargs,
            result_records=result,
        )

        return result


# ============================================================
# REPOSITÓRIO MONETÁRIO INSTRUMENTADO
# ============================================================

class DebugMonetaryValueRepository(
    MonetaryValueRepository
):
    """
    Mantém o comportamento do MonetaryValueRepository
    e adiciona observabilidade.
    """

    def __init__(
        self,
        collector: DebugCollector,
        api_client: MonetaryValueApiClient | None = None,
    ) -> None:

        super().__init__(
            api_client=DebugMonetaryValueApiClient(
                collector=collector,
                client=api_client,
            )
        )


# ============================================================
# RESOLVER MONETÁRIO INSTRUMENTADO
# ============================================================

class DebugMonetaryValueResolver(
    MonetaryValueResolver
):
    """
    Instrumenta o processo de resolução.

    Captura:

        valores antes do filtro
        ↓
        critérios
        ↓
        valores depois dos filtros
        ↓
        valor selecionado
    """

    def __init__(
        self,
        collector: DebugCollector,
        repository: MonetaryValueRepository,
    ) -> None:

        super().__init__(
            repository=repository
        )

        self.collector = collector

    def _filter_values(
        self,
        values,
        criteria,
    ):

        filtered_values = super()._filter_values(
            values=values,
            criteria=criteria,
        )

        self._last_filter_values = (
            values,
            filtered_values,
            criteria,
        )

        return filtered_values

    def resolve(
        self,
        code: str,
        context: CalculationContext,
        source_file_uf: str | None = None,
        source_file_data_base: date | None = None,
        classification: str | None = None,
        group: str | None = None,
        type_system: str | None = None,
    ):

        self._last_filter_values = (
            [],
            [],
            {},
        )

        result = super().resolve(
            code=code,
            context=context,
            source_file_uf=source_file_uf,
            source_file_data_base=source_file_data_base,
            classification=classification,
            group=group,
            type_system=type_system,
        )

        (
            before,
            after,
            criteria,
        ) = self._last_filter_values

        self.collector.record_monetary_resolution(
            code=code,
            criteria=criteria,
            before=before,
            after=after,
            selected=result,
        )

        return result


# ============================================================
# CALCULADORES DE LINHA INSTRUMENTADOS
# ============================================================

class DebugEquipmentCalculator(
    EquipmentCalculator
):

    def __init__(
        self,
        collector: DebugCollector,
        **kwargs,
    ) -> None:

        super().__init__(**kwargs)

        self.collector = collector

    def calculate(
        self,
        equipment,
    ):

        resolution_start_sequence = (
            self.collector._monetary_resolution_sequence
        )

        result = super().calculate(
            equipment
        )

        self.collector.record_monetary_line(
            calculator="EquipmentCalculator",
            composition_input=equipment,
            line_cost=result,
            resolution_start_sequence=(
                resolution_start_sequence
            ),
        )

        return result


class DebugLaborCalculator(
    LaborCalculator
):

    def __init__(
        self,
        collector: DebugCollector,
        **kwargs,
    ) -> None:

        super().__init__(**kwargs)

        self.collector = collector

    def calculate(
        self,
        labor,
    ):

        resolution_start_sequence = (
            self.collector._monetary_resolution_sequence
        )

        result = super().calculate(
            labor
        )

        self.collector.record_monetary_line(
            calculator="LaborCalculator",
            composition_input=labor,
            line_cost=result,
            resolution_start_sequence=(
                resolution_start_sequence
            ),
        )

        return result


class DebugMaterialCalculator(
    MaterialCalculator
):

    def __init__(
        self,
        collector: DebugCollector,
        **kwargs,
    ) -> None:

        super().__init__(**kwargs)

        self.collector = collector

    def calculate(
        self,
        material,
    ):

        resolution_start_sequence = (
            self.collector._monetary_resolution_sequence
        )

        result = super().calculate(
            material
        )

        self.collector.record_monetary_line(
            calculator="MaterialCalculator",
            composition_input=material,
            line_cost=result,
            resolution_start_sequence=(
                resolution_start_sequence
            ),
        )

        return result


# ============================================================
# CALCULADOR DE COMPOSIÇÃO INSTRUMENTADO
# ============================================================

class DebugCompositionCalculator(
    CompositionCalculator
):
    """
    Instrumenta cada ocorrência de CompositionNode.

    O cálculo real continua sendo executado pela classe original.
    """

    def __init__(
        self,
        collector: DebugCollector,
        **kwargs,
    ) -> None:

        super().__init__(**kwargs)

        self.collector = collector

    def _calculate_node(
        self,
        node,
        execution,
    ):

        self.collector.set_current_node(
            node
        )

        result = super()._calculate_node(
            node=node,
            execution=execution,
        )

        self.collector.record_calculation(
            result
        )

        return result


# ============================================================
# CONSTRUÇÃO DO CONTEXTO
# ============================================================

def build_calculation_context() -> CalculationContext:
    """
    Contexto usado pela regressão histórica da 0919013.
    """

    return CalculationContext(
        source_file_uf=SOURCE_FILE_UF,
        source_file_data_base=MONETARY_DATA_BASE,
        type_system=TYPE_SYSTEM,
    )


# ============================================================
# REGISTRO DA ÁRVORE
# ============================================================

def record_tree(
    tree,
    collector: DebugCollector,
) -> None:
    """
    Percorre a árvore em pré-ordem e registra cada ocorrência.

    A ordem é útil para reconstruir visualmente a árvore.
    """

    def visit(
        node,
        depth: int,
    ) -> None:

        collector.record_node(
            node=node,
            depth=depth,
        )

        for child in node.children:
            visit(
                child,
                depth + 1,
            )

    visit(
        tree.root,
        0,
    )


# ============================================================
# CONSTRUÇÃO DO CALCULADOR
# ============================================================

def build_calculator(
    context: CalculationContext,
    monetary_repository: MonetaryValueRepository,
    collector: DebugCollector,
) -> DebugCompositionCalculator:

    monetary_resolver = (
        DebugMonetaryValueResolver(
            collector=collector,
            repository=monetary_repository,
        )
    )

    equipment_calculator = (
        DebugEquipmentCalculator(
            collector=collector,
            monetary_value_resolver=(
                monetary_resolver
            ),
            calculation_context=context,
        )
    )

    labor_calculator = (
        DebugLaborCalculator(
            collector=collector,
            monetary_value_resolver=(
                monetary_resolver
            ),
            calculation_context=context,
        )
    )

    material_calculator = (
        DebugMaterialCalculator(
            collector=collector,
            monetary_value_resolver=(
                monetary_resolver
            ),
            calculation_context=context,
        )
    )

    operational_cost_calculator = (
        OperationalCostCalculator()
    )

    fic_calculator = FicCalculator()

    return DebugCompositionCalculator(
        collector=collector,
        calculation_context=context,
        equipment_calculator=equipment_calculator,
        labor_calculator=labor_calculator,
        material_calculator=material_calculator,
        operational_cost_calculator=(
            operational_cost_calculator
        ),
        fic_calculator=fic_calculator,
        round_2=round_2,
        round_4=round_4,
    )


# ============================================================
# GERAÇÃO DO MARKDOWN
# ============================================================

def format_money(
    value: Any,
) -> str:

    if value is None:
        return "-"

    return str(value)


def generate_markdown_report(
    report: dict[str, Any],
) -> str:

    metadata = report["metadata"]
    summary = report["summary"]

    lines: list[str] = []

    lines.append(
        "# Debug da composição 0919013"
    )

    lines.append("")

    lines.append(
        "## 1. Identificação da execução"
    )

    lines.append("")

    lines.append(
        f"- **Composição:** "
        f"{metadata['composition_code']}"
    )

    lines.append(
        f"- **Data-base da composição:** "
        f"{metadata['composition_data_base']}"
    )

    lines.append(
        f"- **UF monetária:** "
        f"{metadata['source_file_uf']}"
    )

    lines.append(
        f"- **Data-base monetária:** "
        f"{metadata['monetary_data_base']}"
    )

    lines.append(
        f"- **Sistema:** "
        f"{metadata['type_system']}"
    )

    lines.append(
        f"- **Duração:** "
        f"{metadata['duration_seconds']:.3f} s"
    )

    lines.append("")

    # ========================================================
    # RESUMO
    # ========================================================

    lines.append(
        "## 2. Resumo da execução"
    )

    lines.append("")

    lines.append(
        f"- Nós da árvore: "
        f"{summary['tree_node_count']}"
    )

    lines.append(
        f"- Nós folha: "
        f"{summary['tree_leaf_count']}"
    )

    lines.append(
        f"- Cálculos de composição: "
        f"{summary['composition_calculation_count']}"
    )

    lines.append(
        f"- Requisições HTTP monetárias: "
        f"{summary['http_request_count']}"
    )

    lines.append(
        f"- Resoluções monetárias: "
        f"{summary['monetary_resolution_count']}"
    )

    lines.append(
        f"- Linhas monetárias calculadas: "
        f"{summary['monetary_line_count']}"
    )

    lines.append(
        f"- Códigos monetários únicos: "
        f"{summary['unique_monetary_codes']}"
    )

    lines.append(
        f"- **Resultado final:** "
        f"R$ {summary['root_result']}"
    )

    lines.append("")

    # ========================================================
    # TRILHA A
    # ========================================================

    lines.append(
        "## 3. TRILHA A — Composição"
    )

    lines.append("")

    lines.append(
        "### 3.1 Árvore de ocorrências"
    )

    lines.append("")

    for node in report[
        "composition"
    ]["nodes"]:

        indentation = (
            "  "
            * node["depth"]
        )

        lines.append(
            f"{indentation}- "
            f"`{node['composition_code']}` "
            f"— "
            f"{node['description']} "
            f"(node_id={node['node_id']})"
        )

        lines.append(
            f"{indentation}  - "
            f"referência: "
            f"{node['reference_code'] or '-'}"
        )

        lines.append(
            f"{indentation}  - "
            f"grupo: "
            f"{node['reference_group'] or '-'}"
        )

        lines.append(
            f"{indentation}  - "
            f"quantidade referência: "
            f"{node['reference_quantity']}"
        )

        lines.append(
            f"{indentation}  - "
            f"quantidade efetiva: "
            f"{node['effective_quantity']}"
        )

        lines.append(
            f"{indentation}  - "
            f"quantidade acumulada: "
            f"{node['accumulated_quantity']}"
        )

    lines.append("")

    # ========================================================
    # INPUTS
    # ========================================================

    lines.append(
        "### 3.2 Inputs de cada ocorrência"
    )

    lines.append("")

    for node in report[
        "composition"
    ]["nodes"]:

        lines.append(
            f"#### Composição "
            f"`{node['composition_code']}` "
            f"(node_id={node['node_id']})"
        )

        lines.append("")

        lines.append(
            "| Código | Generic Item | Grupo | Quantidade | Uso | Unidade |"
        )

        lines.append(
            "|---|---|---|---:|---:|---|"
        )

        for item in node["inputs"]:

            lines.append(
                "| "
                f"{item['code']} | "
                f"{item['generic_item']} | "
                f"{item['input_group']} | "
                f"{item['input_quantity']} | "
                f"{item['input_use'] or '-'} | "
                f"{item['unit'] or '-'} |"
            )

        lines.append("")

    # ========================================================
    # RESULTADOS
    # ========================================================

    lines.append(
        "### 3.3 Resultado de cada composição"
    )

    lines.append("")

    lines.append(
        "| Seq. | Composição | Equip. | MO | FIC | "
        "Operacional | Materiais | AX | TF | "
        "Total bruto | Custo unitário |"
    )

    lines.append(
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for result in report[
        "composition"
    ]["calculations"]:

        lines.append(
            "| "
            f"{result['sequence']} | "
            f"{result['composition_code']} | "
            f"{result['equipment_cost']} | "
            f"{result['labor_cost']} | "
            f"{result['fic_cost']} | "
            f"{result['operational_unit']} | "
            f"{result['materials_cost']} | "
            f"{result['auxiliary_cost']} | "
            f"{result['fixed_time_cost']} | "
            f"{result['composition_total_raw']} | "
            f"**{result['composition_unit_cost']}** |"
        )

    lines.append("")

    # ========================================================
    # TRILHA B
    # ========================================================

    lines.append(
        "## 4. TRILHA B — Monetária"
    )

    lines.append("")

    # ========================================================
    # HTTP
    # ========================================================

    lines.append(
        "### 4.1 Consultas HTTP"
    )

    lines.append("")

    for request in report[
        "monetary"
    ]["http_requests"]:

        lines.append(
            f"#### Requisição #{request['sequence']}"
        )

        lines.append("")

        lines.append(
            f"- Operação: `{request['operation']}`"
        )

        lines.append(
            f"- Parâmetros: "
            f"`{json.dumps(request['kwargs'], ensure_ascii=False)}`"
        )

        lines.append(
            f"- Registros retornados: "
            f"**{request['result_count']}**"
        )

        lines.append("")

    # ========================================================
    # RESOLUÇÕES
    # ========================================================

    lines.append(
        "### 4.2 Resoluções de MonetaryValue"
    )

    lines.append("")

    lines.append(
        "| Seq. | Nó | Composição | Código | "
        "Candidatos | Após filtros | ID selecionado | Valor | "
        "Classificação | Grupo | Sistema |"
    )

    lines.append(
        "|---:|---:|---|---|---:|---:|---:|---:|---|---|---|"
    )

    for event in report[
        "monetary"
    ]["resolutions"]:

        lines.append(
            "| "
            f"{event['sequence']} | "
            f"{event['node_id'] or '-'} | "
            f"{event['composition_code'] or '-'} | "
            f"{event['code']} | "
            f"{event['candidate_count_before_filter']} | "
            f"{event['candidate_count_after_filter']} | "
            f"{event['selected_id'] or '-'} | "
            f"{event['selected_value'] or '-'} | "
            f"{event['selected_classification'] or '-'} | "
            f"{event['selected_group'] or '-'} | "
            f"{event['selected_type_system'] or '-'} |"
        )

    lines.append("")

    # ========================================================
    # CRITÉRIOS
    # ========================================================

    lines.append(
        "### 4.3 Critérios utilizados pelo Resolver"
    )

    lines.append("")

    for event in report[
        "monetary"
    ]["resolutions"]:

        lines.append(
            f"#### Resolução #{event['sequence']} "
            f"— `{event['code']}`"
        )

        lines.append("")

        criteria = event[
            "criteria"
        ]

        lines.append(
            f"- UF: `{criteria.get('source_file_uf')}`"
        )

        lines.append(
            f"- Data-base: "
            f"`{criteria.get('source_file_data_base')}`"
        )

        lines.append(
            f"- Classificação: "
            f"`{criteria.get('classification')}`"
        )

        lines.append(
            f"- Grupo: "
            f"`{criteria.get('group')}`"
        )

        lines.append(
            f"- Sistema: "
            f"`{criteria.get('type_system')}`"
        )

        lines.append(
            f"- IDs antes dos filtros: "
            f"`{event['candidate_ids_before_filter']}`"
        )

        lines.append(
            f"- IDs depois dos filtros: "
            f"`{event['candidate_ids_after_filter']}`"
        )

        lines.append(
            f"- ID selecionado: "
            f"`{event['selected_id']}`"
        )

        lines.append("")

    # ========================================================
    # PARCELAS
    # ========================================================

    lines.append(
        "### 4.4 Utilização dos valores monetários"
    )

    lines.append("")

    lines.append(
        "| Seq. | Nó | Composição | Calculador | "
        "Grupo | Generic Item | Quantidade | Uso | "
        "Custo da linha | Valores resolvidos | Valores efetivamente utilizados |"
    )

    lines.append(
        "|---:|---:|---|---|---|---|---:|---:|---:|---|"
    )

    for line in report[
        "monetary"
    ]["lines"]:

        lines.append(
            "| "
            f"{line['sequence']} | "
            f"{line['node_id'] or '-'} | "
            f"{line['composition_code'] or '-'} | "
            f"{line['calculator']} | "
            f"{line['input_group'] or '-'} | "
            f"{line['generic_item']} | "
            f"{line['input_quantity']} | "
            f"{line['input_use'] or '-'} | "
            f"{line['line_cost']} | "
            f"`{line['monetary_values_resolved']}` |"
            f"`{line['monetary_values_used']}` |"
        )

    lines.append("")

    # ========================================================
    # CONCLUSÃO AUTOMÁTICA
    # ========================================================

    lines.append(
        "## 5. Indicadores de diagnóstico"
    )

    lines.append("")

    resolutions = report[
        "monetary"
    ]["resolutions"]

    ambiguous = [
        event
        for event in resolutions
        if event[
            "candidate_count_after_filter"
        ] > 1
    ]

    unresolved = [
        event
        for event in resolutions
        if event[
            "selected_id"
        ] is None
    ]

    no_filter_reduction = [
        event
        for event in resolutions
        if (
            event[
                "candidate_count_before_filter"
            ]
            ==
            event[
                "candidate_count_after_filter"
            ]
        )
    ]

    lines.append(
        f"- Resoluções ambíguas: "
        f"**{len(ambiguous)}**"
    )

    lines.append(
        f"- Resoluções sem valor selecionado: "
        f"**{len(unresolved)}**"
    )

    lines.append(
        f"- Resoluções em que os filtros não reduziram "
        f"a quantidade de candidatos: "
        f"**{len(no_filter_reduction)}**"
    )

    lines.append("")

    if ambiguous:

        lines.append(
            "### Resoluções potencialmente ambíguas"
        )

        lines.append("")

        for event in ambiguous:

            lines.append(
                f"- `{event['code']}` "
                f"na composição "
                f"`{event['composition_code']}`: "
                f"{event['candidate_count_after_filter']} "
                f"candidatos."
            )

        lines.append("")

    if unresolved:

        lines.append(
            "### Resoluções sem valor"
        )

        lines.append("")

        for event in unresolved:

            lines.append(
                f"- `{event['code']}` "
                f"na composição "
                f"`{event['composition_code']}`."
            )

        lines.append("")

    lines.append(
        "## 6. Resultado final"
    )

    lines.append("")

    lines.append(
        f"**Composição:** `{COMPOSITION_CODE}`"
    )

    lines.append("")

    lines.append(
        f"**Custo unitário final:** "
        f"**R$ {summary['root_result']}**"
    )

    lines.append("")

    return "\n".join(lines)


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main() -> None:

    started_at = datetime.now()

    collector = DebugCollector()

    print("")
    print("=" * 72)
    print("DEBUG DA COMPOSIÇÃO 0919013")
    print("=" * 72)
    print("")

    print(
        "[1/7] Criando clientes e repositórios..."
    )

    composition_api_client = (
        CompositionApiClient()
    )

    optimized_repository = (
        OptimizedCompositionRepository(
            api_client=composition_api_client,
            composition_data_base=(
                COMPOSITION_DATA_BASE
            ),
        )
    )

    composition_repository = (
        CompositionRepository(
            api_client=composition_api_client,
        )
    )

    monetary_repository = (
        DebugMonetaryValueRepository(
            collector=collector,
        )
    )

    print(
        "[2/7] Construindo resolver..."
    )

    resolver = CompositionResolver(
        repository=composition_repository,
        optimized_repository=optimized_repository,
    )

    print(
        "[3/7] Resolvendo árvore..."
    )

    tree = resolver.resolve_tree_optimized(
        COMPOSITION_CODE
    )

    print(
        f"      Nós encontrados: {len(tree)}"
    )

    print(
        "[4/7] Registrando TRILHA A — composição..."
    )

    record_tree(
        tree=tree,
        collector=collector,
    )

    print(
        f"      Nós registrados: "
        f"{len(collector.composition_nodes)}"
    )

    print(
        "[5/7] Carregando TRILHA B — valores monetários..."
    )

    context = build_calculation_context()

    monetary_repository.load_cache(
        codes_by_group=(
            tree.monetary_item_codes_by_group
        ),
        type_system=context.type_system,
        source_file_uf=context.source_file_uf,
        source_file_data_base=(
            context.source_file_data_base
        ),
    )

    print(
        f"      Códigos monetários únicos: "
        f"{len(tree.monetary_item_codes)}"
    )

    print(
        "[6/7] Executando cálculo instrumentado..."
    )

    calculator = build_calculator(
        context=context,
        monetary_repository=(
            monetary_repository
        ),
        collector=collector,
    )

    root_result = calculator.calculate(
        tree
    )

    print(
        f"      Resultado: "
        f"R$ {root_result.composition_unit_cost}"
    )

    print(
        "[7/7] Gerando relatórios..."
    )

    finished_at = datetime.now()

    report = collector.build_report(
        tree=tree,
        root_result=root_result,
        started_at=started_at,
        finished_at=finished_at,
    )

    markdown = generate_markdown_report(
        report
    )

    REPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with JSON_REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    with MARKDOWN_REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            markdown
        )

    print("")
    print("=" * 72)
    print("EXECUÇÃO CONCLUÍDA")
    print("=" * 72)
    print("")

    print(
        f"Resultado final: "
        f"R$ {root_result.composition_unit_cost}"
    )

    print(
        f"HTTP requests: "
        f"{len(collector.http_requests)}"
    )

    print(
        f"Resoluções monetárias: "
        f"{len(collector.monetary_resolutions)}"
    )

    print(
        f"Linhas monetárias: "
        f"{len(collector.monetary_lines)}"
    )

    print(
        f"Nós da árvore: "
        f"{len(collector.composition_nodes)}"
    )

    print("")
    print(
        f"JSON: {JSON_REPORT_PATH}"
    )

    print(
        f"Markdown: {MARKDOWN_REPORT_PATH}"
    )

    print("")


if __name__ == "__main__":
    main()