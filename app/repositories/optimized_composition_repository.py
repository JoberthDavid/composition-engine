from app.infrastructure.composition_api_client import CompositionApiClient


class OptimizedCompositionRepository:
    """
    Repositório otimizado para descoberta da estrutura
    das composições.

    A data-base utilizada neste repositório é exclusivamente
    a data-base da estrutura das composições.
    """

    def __init__(
        self,
        api_client: CompositionApiClient | None = None,
        composition_data_base: str | None = None,
    ) -> None:
        self.api_client = (
            api_client
            if api_client is not None
            else CompositionApiClient()
        )

        self.composition_data_base = (
            composition_data_base
        )

    def get_child_codes_by_composition_codes(
        self,
        composition_codes: list[str],
    ) -> dict[str, list[str]]:
        """
        Obtém os códigos dos filhos diretos de várias composições.

        As relações estruturais podem estar presentes tanto nas
        atividades quanto nos transportes do tipo TF (tempo fixo).

        Os transportes LN, RP, PV e FR não participam desta
        descoberta estrutural e serão tratados separadamente.
        """
        normalized_codes = list(
            dict.fromkeys(
                str(code)
                for code in composition_codes
                if str(code)
            )
        )

        if not normalized_codes:
            return {}

        activities = (
        self.api_client.get_composition_activities_by_codes(
                normalized_codes,
                data_base=self.composition_data_base,
            )
        )

        transports = (
            self.api_client.get_composition_transports_by_codes(
                normalized_codes,
                data_base=self.composition_data_base,
            )
        )

        children_by_composition: dict[str, list[str]] = {}

        for activity in activities:
            composition_code = str(
                activity["composition_code"]
            )
            child_code = str(
                activity["generic_item"]
            )

            children = children_by_composition.setdefault(
                composition_code,
                [],
            )

            if child_code not in children:
                children.append(child_code)

        for transport in transports:
            if str(transport["input_group"]) != "TF":
                continue

            composition_code = str(
                transport["composition_code"]
            )
            child_code = str(
                transport["generic_item"]
            )

            children = children_by_composition.setdefault(
                composition_code,
                [],
            )

            if child_code not in children:
                children.append(child_code)

        return children_by_composition