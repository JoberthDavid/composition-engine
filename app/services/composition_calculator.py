from decimal import Decimal
from typing import Callable

from app.domain.calculation_context import (
    CalculationContext,
)
from app.domain.calculation_execution import CalculationExecution
from app.domain.composition_calculation_result import (
    CompositionCalculationResult,
)
from app.domain.composition_node import (
    CompositionNode,
)
from app.domain.composition_tree import (
    CompositionTree,
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
from app.services.operational_cost_calculator import (
    OperationalCostCalculator,
)
from app.domain.composition_line_result import (
    CompositionReferenceLineResult,
    EquipmentLineResult,
    LaborLineResult,
    MaterialLineResult,
)

DECIMAL_ZERO = Decimal("0")


class CompositionCalculator:
    """
    Responsável por orquestrar o cálculo dos custos das
    composições presentes em uma CompositionTree.

    Os cálculos especializados são delegados para serviços
    específicos:

        EQ -> EquipmentCalculator
        MO -> LaborCalculator
        MA -> MaterialCalculator
        FIC -> FicCalculator
        Operacional -> OperationalCostCalculator

    A CompositionCalculator permanece responsável pela
    marcha de cálculo da composição e pela agregação das
    composições filhas AX e TF.

    A marcha de cálculo ocorre na seguinte ordem:

        1. Equipamentos
        2. Mão de obra
        3. Custo operacional
        4. FIC
        5. Materiais
        6. Atividades auxiliares
        7. Tempos fixos
        8. Soma da composição
        9. Arredondamento final

    O cálculo da árvore ocorre em pós-ordem:

        filhos
            ↓
        composição pai

    Dessa forma, quando uma composição pai é calculada,
    todas as composições referenciadas por AX e TF já
    possuem seus custos unitários calculados.
    """

    def __init__(
        self,
        calculation_context: CalculationContext,
        equipment_calculator: EquipmentCalculator,
        labor_calculator: LaborCalculator,
        material_calculator: MaterialCalculator,
        operational_cost_calculator: OperationalCostCalculator,
        fic_calculator: FicCalculator,
        round_2: Callable,
        round_4: Callable,
    ) -> None:
        """
        Inicializa o CompositionCalculator.

        Parameters
        ----------
        calculation_context:
            Contexto utilizado no cálculo da composição.

        equipment_calculator:
            Responsável pelo cálculo das linhas de
            equipamentos.

        labor_calculator:
            Responsável pelo cálculo das linhas de
            mão de obra.

        material_calculator:
            Responsável pelo cálculo das linhas de
            materiais.

        operational_cost_calculator:
            Responsável pelo cálculo do custo operacional
            total e unitário.

        fic_calculator:
            Responsável pelo cálculo do custo referente ao FIC.

        round_2:
            Função de arredondamento para duas casas.

        round_4:
            Função de arredondamento para quatro casas.
        """

        self.calculation_context = (
            calculation_context
        )

        self.equipment_calculator = (
            equipment_calculator
        )

        self.labor_calculator = (
            labor_calculator
        )

        self.material_calculator = (
            material_calculator
        )

        self.operational_cost_calculator = (
            operational_cost_calculator
        )

        self.fic_calculator = (
            fic_calculator
        )

        self.round_2 = round_2
        self.round_4 = round_4


    # ============================================================
    # MÉTODO PÚBLICO PRINCIPAL
    # ============================================================

    def calculate(
        self,
        tree: CompositionTree,
    ) -> CompositionCalculationResult:
        """
        Calcula toda a árvore de composições.

        O percurso ocorre em pós-ordem:

            folhas
                ↓
            composições intermediárias
                ↓
            composição raiz
        """

        execution = CalculationExecution()

        for node in tree.walk_post_order():

            result = self._calculate_node(
                node=node,
                execution=execution,
            )

            execution.add_result(
                node=node,
                result=result,
            )

        return execution.get_result(
            node=tree.root,
        )

    # ============================================================
    # CÁLCULO COMPLETO DE UM NÓ
    # ============================================================

    def _calculate_node(
        self,
        node: CompositionNode,
        execution: CalculationExecution,
    ) -> CompositionCalculationResult:
        """
        Calcula completamente uma composição.

        A composição é calculada utilizando os calculadores
        especializados e, ao final, seus custos são agregados
        em CompositionCalculationResult.
        """

        composition = node.composition

        # ========================================================
        # 1. EQUIPAMENTOS
        # ========================================================

        equipment_cost, equipment_items = (
            self._calculate_equipment_cost(
                node=node,
            )
        )

        # ========================================================
        # 2. MÃO DE OBRA
        # ========================================================

        labor_cost, labor_items = (
            self._calculate_labor_cost(
                node=node,
            )
        )

        # ========================================================
        # 3. CUSTO OPERACIONAL TOTAL
        # ========================================================

        operational_base = (
            self.operational_cost_calculator.calculate_total(
                equipment_cost=equipment_cost,
                labor_cost=labor_cost,
            )
        )

        # ========================================================
        # 4. CUSTO OPERACIONAL UNITÁRIO SEM FIC
        # ========================================================

        operational_unit_without_fic = (
            self.operational_cost_calculator.calculate_unit(
                operational_total=operational_base,
                production=composition.production,
            )
        )

        operational_unit_without_fic = (
            self.round_4(
                operational_unit_without_fic
            )
        )

        # ========================================================
        # 5. FIC
        # ========================================================

        fic_cost = (
            self._calculate_fic_cost(
                node=node,
                operational_unit=(
                    operational_unit_without_fic
                ),
            )
        )

        # ========================================================
        # 6. CUSTO OPERACIONAL UNITÁRIO COM FIC
        # ========================================================

        operational_unit = (
            self.round_4(
                operational_unit_without_fic
                + fic_cost
            )
        )

        # ========================================================
        # 7. CUSTO OPERACIONAL TOTAL
        # ========================================================

        operational_total = (
            self.round_4(
                operational_unit
                * composition.production
            )
        )

        # ========================================================
        # 8. MATERIAIS
        # ========================================================

        materials_cost, material_items = (
            self._calculate_materials_cost(
                node=node,
            )
        )

        # ========================================================
        # 9. ATIVIDADES AUXILIARES
        # ========================================================

        auxiliary_cost, auxiliary_items = (
            self._calculate_children_cost(
                node=node,
                input_group="AX",
                execution=execution,
            )
        )

        # ========================================================
        # 10. TEMPOS FIXOS
        # ========================================================

        fixed_time_cost, fixed_time_items = (
            self._calculate_children_cost(
                node=node,
                input_group="TF",
                execution=execution,
            )
        )


        # ========================================================
        # 11. SOMA DA COMPOSIÇÃO
        # ========================================================

        composition_reference_items = (
            auxiliary_items
            + fixed_time_items
        )

        composition_total_raw = (
            operational_unit
            + materials_cost
            + auxiliary_cost
            + fixed_time_cost
        )

        # ========================================================
        # 12. CUSTO UNITÁRIO FINAL
        # ========================================================

        composition_unit_cost = (
            self.round_2(
                composition_total_raw
            )
        )

        # ========================================================
        # RESULTADO
        # ========================================================

        return CompositionCalculationResult(
            node=node,
            equipment_cost=equipment_cost,
            labor_cost=labor_cost,
            fic_cost=fic_cost,
            operational_total=operational_total,
            operational_unit=operational_unit,
            materials_cost=materials_cost,
            auxiliary_cost=auxiliary_cost,
            fixed_time_cost=fixed_time_cost,
            composition_total_raw=composition_total_raw,
            composition_unit_cost=composition_unit_cost,
            equipment_items=equipment_items,
            labor_items=labor_items,
            material_items=material_items,
            composition_reference_items=composition_reference_items,
        )

    # ============================================================
    # 1. EQUIPAMENTOS
    # ============================================================

    def _calculate_equipment_cost(
        self,
        node: CompositionNode,
    ) -> tuple[
        Decimal,
        list[EquipmentLineResult],
    ]:
        """
        Calcula os equipamentos e preserva o resultado
        individual de cada linha.
        """

        equipment_cost = DECIMAL_ZERO
        equipment_items = []

        for equipment in node.composition.equipments:

            result = (
                self.equipment_calculator
                .calculate_detail(
                    equipment=equipment,
                )
            )

            line_cost = self.round_4(
                result.line_cost
            )

            equipment_cost += line_cost

            equipment_items.append(
                EquipmentLineResult(
                    code=result.code,
                    description=result.description,
                    unit=result.unit,
                    quantity=result.quantity,
                    input_use=result.input_use,
                    productive_value=result.productive_value,
                    unproductive_value=result.unproductive_value,
                    line_cost=line_cost,
                )
            )

        return equipment_cost, equipment_items

    # ============================================================
    # 2. MÃO DE OBRA
    # ============================================================

    def _calculate_labor_cost(
        self,
        node: CompositionNode,
    ) -> tuple[
        Decimal,
        list[LaborLineResult],
    ]:
        """
        Calcula a mão de obra e preserva o resultado
        individual de cada linha.
        """

        labor_cost = DECIMAL_ZERO
        labor_items = []

        for labor in node.composition.workmen:

            result = (
                self.labor_calculator
                .calculate_detail(
                    labor=labor,
                )
            )

            line_cost = self.round_4(
                result.line_cost
            )

            labor_cost += line_cost

            labor_items.append(
                LaborLineResult(
                    code=result.code,
                    description=result.description,
                    unit=result.unit,
                    quantity=result.quantity,
                    monetary_value=result.monetary_value,
                    line_cost=line_cost,
                )
            )

        return labor_cost, labor_items

    # ============================================================
    # 3. FIC
    # ============================================================

    def _calculate_fic_cost(
        self,
        node: CompositionNode,
        operational_unit: Decimal,
    ) -> Decimal:
        """
        Calcula o custo unitário referente ao FIC.

        O cálculo propriamente dito é delegado ao
        FicCalculator.

        O FIC é aplicado sobre o custo operacional
        unitário antes do FIC.
        """

        result_fic = (
            self.fic_calculator.calculate(
                operational_unit_cost=(
                    operational_unit
                ),
                fic_percentage=(
                    node.composition.fic
                ),
            )
        )

        return self.round_4(
            result_fic
        )

    # ============================================================
    # 4. MATERIAIS
    # ============================================================

    def _calculate_materials_cost(
        self,
        node: CompositionNode,
    ) -> tuple[
        Decimal,
        list[MaterialLineResult],
    ]:
        """
        Calcula os materiais e preserva o resultado
        individual de cada linha.
        """

        materials_cost = DECIMAL_ZERO
        material_items = []

        for material in node.composition.materials:

            result = (
                self.material_calculator
                .calculate_detail(
                    material=material,
                )
            )

            line_cost = self.round_4(
                result.line_cost
            )

            materials_cost += line_cost

            material_items.append(
                MaterialLineResult(
                    code=result.code,
                    description=result.description,
                    unit=result.unit,
                    quantity=result.quantity,
                    monetary_value=result.monetary_value,
                    line_cost=line_cost,
                )
            )

        return materials_cost, material_items

    # ============================================================
    # 5. ATIVIDADES AUXILIARES E TEMPOS FIXOS
    # ============================================================

    def _calculate_children_cost(
            self,
            node: CompositionNode,
            input_group: str,
            execution: CalculationExecution,
        ) -> tuple[
            Decimal,
            list[CompositionReferenceLineResult],
        ]:
            children_cost = DECIMAL_ZERO
            reference_items = []

            for child in node.children:
                reference_input = child.reference_input

                if reference_input is None:
                    continue

                if reference_input.input_group != input_group:
                    continue

                child_result = execution.get_result(
                    node=child,
                )

                child_unit = self.round_2(
                    child_result.composition_unit_cost
                )

                quantity = reference_input.input_quantity

                line_cost = self.round_4(
                    quantity * child_unit
                )

                children_cost += line_cost

                reference_items.append(
                    CompositionReferenceLineResult(
                        group=reference_input.input_group,
                        code=reference_input.generic_item,
                        description=reference_input.generic_description,
                        unit=reference_input.unit,
                        quantity=quantity,
                        child_unit_cost=child_unit,
                        line_cost=line_cost,
                    )
                )

            return children_cost, reference_items
