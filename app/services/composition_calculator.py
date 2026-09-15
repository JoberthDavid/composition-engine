from decimal import Decimal
from typing import Callable

from app.domain.calculation_context import (
    CalculationContext,
)
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

        self._results: dict[
            int,
            CompositionCalculationResult,
        ] = {}


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

        self._results.clear()

        for node in tree.walk_post_order():

            result = self._calculate_node(
                node=node,
            )

            self._results[
                id(node)
            ] = result

        return self._get_node_result(
            node=tree.root,
        )

    # ============================================================
    # CÁLCULO COMPLETO DE UM NÓ
    # ============================================================

    def _calculate_node(
        self,
        node: CompositionNode,
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

        equipment_cost = (
            self._calculate_equipment_cost(
                node=node,
            )
        )

        # ========================================================
        # 2. MÃO DE OBRA
        # ========================================================

        labor_cost = (
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

        materials_cost = (
            self._calculate_materials_cost(
                node=node,
            )
        )

        # ========================================================
        # 9. ATIVIDADES AUXILIARES
        # ========================================================

        auxiliary_cost = (
            self._calculate_children_cost(
                node=node,
                input_group="AX",
            )
        )

        # ========================================================
        # 10. TEMPOS FIXOS
        # ========================================================

        fixed_time_cost = (
            self._calculate_children_cost(
                node=node,
                input_group="TF",
            )
        )

        # ========================================================
        # 11. SOMA DA COMPOSIÇÃO
        # ========================================================

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
            composition_total_raw=(
                composition_total_raw
            ),
            composition_unit_cost=(
                composition_unit_cost
            ),
        )

    # ============================================================
    # 1. EQUIPAMENTOS
    # ============================================================

    def _calculate_equipment_cost(
        self,
        node: CompositionNode,
    ) -> Decimal:
        """
        Calcula o custo total dos equipamentos.

        Cada linha é delegada para EquipmentCalculator.
        """

        equipment_cost = DECIMAL_ZERO

        for equipment in node.composition.equipments:

            result_eq = (
                self.equipment_calculator.calculate(
                    equipment
                )
            )

            line_cost = self.round_4(
                result_eq
            )

            equipment_cost += line_cost

        return equipment_cost

    # ============================================================
    # 2. MÃO DE OBRA
    # ============================================================

    def _calculate_labor_cost(
        self,
        node: CompositionNode,
    ) -> Decimal:
        """
        Calcula o custo total da mão de obra.

        Cada linha é delegada para LaborCalculator.
        """

        labor_cost = DECIMAL_ZERO

        for labor in node.composition.workmen:

            result_mo = (
                self.labor_calculator.calculate(
                    labor
                )
            )

            line_cost = self.round_4(
                result_mo
            )

            labor_cost += line_cost

        return labor_cost

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
    ) -> Decimal:
        """
        Calcula o custo total dos materiais.

        Cada linha é delegada para MaterialCalculator.
        """

        materials_cost = DECIMAL_ZERO

        for material in node.composition.materials:

            result_ma = (
                self.material_calculator.calculate(
                    material
                )
            )

            line_cost = self.round_4(
                result_ma
            )

            materials_cost += line_cost

        return materials_cost

    # ============================================================
    # 5. ATIVIDADES AUXILIARES E TEMPOS FIXOS
    # ============================================================

    def _calculate_children_cost(
        self,
        node: CompositionNode,
        input_group: str,
    ) -> Decimal:
        """
        Calcula o custo das composições filhas AX ou TF.

        Para cada composição filha:

            quantidade da referência
                ×
            custo unitário final da filha

        A linha é arredondada para quatro casas.
        """

        children_cost = DECIMAL_ZERO

        for child in node.children:

            reference_input = (
                child.reference_input
            )

            if reference_input is None:
                continue

            if (
                reference_input.input_group
                != input_group
            ):
                continue

            child_result = (
                self._get_node_result(
                    node=child,
                )
            )

            child_unit = (
                self.round_2(
                    child_result.composition_unit_cost
                )
            )

            quantity = (
                reference_input.input_quantity
            )

            line_cost = (
                self.round_4(
                    quantity
                    * child_unit
                )
            )

            children_cost += line_cost

        return children_cost

    # ============================================================
    # RESULTADOS
    # ============================================================

    def _get_node_result(
        self,
        node: CompositionNode,
    ) -> CompositionCalculationResult:
        """
        Obtém o resultado calculado de um nó.

        Como o cálculo ocorre em pós-ordem, uma composição
        filha deve possuir resultado antes de sua composição pai.
        """

        node_id = id(node)

        if node_id not in self._results:

            raise ValueError(
                "Composition result not found for node: "
                f"{node.composition.generic_item}"
            )

        return self._results[
            node_id
        ]

    def get_result(
        self,
        node: CompositionNode,
    ) -> CompositionCalculationResult:
        """
        Retorna o resultado calculado de um nó.

        Deve ser utilizado após calculate().
        """

        return self._get_node_result(
            node=node,
        )

    def get_all_results(
        self,
    ) -> list[CompositionCalculationResult]:
        """
        Retorna todos os resultados calculados.

        A ordem corresponde à ordem em que os nós foram
        calculados em pós-ordem.
        """

        return list(
            self._results.values()
        )