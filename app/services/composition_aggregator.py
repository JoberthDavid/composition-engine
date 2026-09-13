from app.domain.aggregated_composition import AggregatedComposition
from app.domain.composition_tree import CompositionTree

class CompositionAggregator:
    """
    Agrega as composições presentes em uma CompositionTree.
    """

    def aggregate(
        self,
        tree: CompositionTree,
    ) -> list[AggregatedComposition]:
        """
        Agrega todas as composições da árvore por código.
        """

        aggregated_by_code: dict[
            str,
            AggregatedComposition,
        ] = {}

        for node in tree.walk():

            composition = node.composition
            code = composition.code

            if code not in aggregated_by_code:

                aggregated_by_code[code] = AggregatedComposition(
                    identifier=composition.id,
                    group=composition.composition_group,
                    code=composition.generic_item,
                    description=composition.generic_description,
                    unit=composition.unit,
                    quantity=node.effective_quantity,
                )

            else:

                aggregated_by_code[code].add_quantity(
                    node.effective_quantity
                )

        return list(
            aggregated_by_code.values()
        )