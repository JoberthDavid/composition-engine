from decimal import Decimal

from app.domain.aggregated_input import AggregatedInput
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree


class InputAggregator:
    """
    Agrega equipamentos, mão de obra e materiais
    presentes em uma CompositionTree.
    """

    def aggregate(
        self,
        tree: CompositionTree,
    ) -> list[AggregatedInput]:
        """
        Agrega os insumos monetários da árvore.

        Insumos de composição (AX e TF) e transportes
        (LN, RP, PV e FR) não são agregados nesta etapa.
        """

        aggregated_by_code: dict[
            str,
            AggregatedInput,
        ] = {}

        for node in tree.walk():

            composition = node.composition

            for composition_input in composition.inputs:

                if composition_input.is_composition_reference():
                    continue

                if composition_input.is_transport():
                    continue

                if composition_input.is_equipment():

                    self._aggregate_equipment(
                        aggregated_by_code=aggregated_by_code,
                        node=node,
                        composition_input=composition_input,
                    )

                elif composition_input.is_workman():

                    self._aggregate_workman(
                        aggregated_by_code=aggregated_by_code,
                        node=node,
                        composition_input=composition_input,
                    )

                elif composition_input.is_material():

                    self._aggregate_material(
                        aggregated_by_code=aggregated_by_code,
                        node=node,
                        composition_input=composition_input,
                    )

        return list(aggregated_by_code.values())

    def _aggregate_equipment(
        self,
        aggregated_by_code: dict[str, AggregatedInput],
        node: CompositionNode,
        composition_input: CompositionInput,
    ) -> None:
        """
        Agrega um equipamento considerando suas parcelas
        produtiva e improdutiva.

        A quantidade base é determinada pela quantidade
        acumulada na árvore e normalizada pela produção
        da composição.
        """

        production = node.composition.production

        base_quantity = (
            composition_input.input_quantity
            * node.accumulated_quantity
            / production
        )

        use = (
            composition_input.input_use
            if composition_input.input_use is not None
            else Decimal("1")
        )

        productive_quantity = base_quantity * use

        unproductive_quantity = (
            base_quantity * (Decimal("1") - use)
        )

        aggregated = aggregated_by_code.get(
            composition_input.code
        )

        if aggregated is None:

            aggregated_by_code[composition_input.code] = (
                AggregatedInput(
                    identifier=composition_input.id,
                    group=composition_input.input_group,
                    code=composition_input.code,
                    description=composition_input.description,
                    unit=composition_input.unit,
                    productive_quantity=productive_quantity,
                    unproductive_quantity=unproductive_quantity,
                    proprietary_item=composition_input.proprietary_item,
                )
            )

        else:

            aggregated.add_equipment_quantity(
                productive_quantity=productive_quantity,
                unproductive_quantity=unproductive_quantity,
            )

    def _aggregate_workman(
        self,
        aggregated_by_code: dict[str, AggregatedInput],
        node: CompositionNode,
        composition_input: CompositionInput,
    ) -> None:
        """
        Agrega mão de obra considerando a produção
        da composição e a quantidade acumulada na árvore.
        """

        production = node.composition.production

        quantity = (
            composition_input.input_quantity
            * node.accumulated_quantity
            / production
        )

        self._add_standard_quantity(
            aggregated_by_code=aggregated_by_code,
            composition_input=composition_input,
            quantity=quantity,
        )

    def _aggregate_material(
        self,
        aggregated_by_code: dict[str, AggregatedInput],
        node: CompositionNode,
        composition_input: CompositionInput,
    ) -> None:
        """
        Agrega material utilizando a quantidade acumulada
        na árvore.

        Materiais não são normalizados pela produção da
        composição nesta etapa.
        """

        quantity = (
            composition_input.input_quantity
            * node.accumulated_quantity
        )

        self._add_standard_quantity(
            aggregated_by_code=aggregated_by_code,
            composition_input=composition_input,
            quantity=quantity,
        )

    def _add_standard_quantity(
        self,
        aggregated_by_code: dict[str, AggregatedInput],
        composition_input: CompositionInput,
        quantity: Decimal,
    ) -> None:
        """
        Adiciona uma quantidade de mão de obra ou material
        ao resultado agregado.
        """

        aggregated = aggregated_by_code.get(
            composition_input.code
        )

        if aggregated is None:

            aggregated_by_code[composition_input.code] = (
                AggregatedInput(
                    identifier=composition_input.id,
                    group=composition_input.input_group,
                    code=composition_input.code,
                    description=composition_input.description,
                    unit=composition_input.unit,
                    quantity=quantity,
                    proprietary_item=composition_input.proprietary_item,
                )
            )

        else:

            aggregated.add_quantity(quantity)