from datetime import date

from app.domain.calculation_context import (
CalculationContext,
)
from app.domain.monetary_value import (
MonetaryValue,
)
from app.repositories.monetary_value_repository import (
MonetaryValueRepository,
)

class MonetaryValueResolver:
    """
    Responsável por localizar e selecionar o valor monetário
    correto de um insumo para um determinado contexto de cálculo.

    ```
    Os critérios principais são definidos pelo usuário através
    do CalculationContext:

    - UF;
    - data-base;
    - classificação;
    - grupo;
    - sistema.

    Além disso, os calculadores específicos podem sobrescrever
    temporariamente algum critério durante uma resolução.

    Exemplo para equipamentos:

        resolve(
            code="E9155",
            context=context,
            classification="PR",
        )

        resolve(
            code="E9155",
            context=context,
            classification="IM",
        )

    Essas sobrescritas não modificam o CalculationContext original.
    """

    def __init__(
        self,
        repository: MonetaryValueRepository,
    ) -> None:
        """
        Inicializa o resolver.

        O repositório deve ser fornecido explicitamente pelo
        CompositionRoot.
        """

        self.repository = repository

    # ============================================================
    # MÉTODO PÚBLICO
    # ============================================================

    def resolve(
        self,
        code: str,
        context: CalculationContext,
        source_file_uf: str | None = None,
        source_file_data_base: date | None = None,
        classification: str | None = None,
        group: str | None = None,
        type_system: str | None = None,
    ) -> MonetaryValue:
        """
        Resolve o valor monetário correto para um insumo.

        Os critérios opcionais informados diretamente neste método
        possuem prioridade sobre os valores definidos no
        CalculationContext.

        Parameters
        ----------
        code:
            Código do insumo.

        context:
            Contexto principal definido pelo usuário.

        source_file_uf:
            UF específica para esta resolução.

        source_file_data_base:
            Data-base específica para esta resolução.

        classification:
            Classificação específica para esta resolução.

            Exemplo:

                PR
                IM

            Utilizado principalmente pelo EquipmentCalculator.

        group:
            Grupo específico para esta resolução.

        type_system:
            Sistema específico para esta resolução.

        Returns
        -------
        MonetaryValue
            Valor monetário selecionado.

        Raises
        ------
        ValueError
            Caso nenhum valor monetário seja encontrado.

        ValueError
            Caso nenhum valor seja compatível com os critérios.

        ValueError
            Caso mais de um valor continue compatível após
            a aplicação dos filtros.
        """

        # ========================================================
        # OBTÉM OS VALORES DISPONÍVEIS
        # ========================================================

        monetary_values = (
            self.repository.get_by_code(
                code
            )
        )

        if not monetary_values:

            raise ValueError(
                "No monetary values found for input: "
                f"{code}"
            )

        # ========================================================
        # RESOLVE OS CRITÉRIOS FINAIS
        # ========================================================

        criteria = self._build_criteria(
            context=context,
            source_file_uf=source_file_uf,
            source_file_data_base=(
                source_file_data_base
            ),
            classification=classification,
            group=group,
            type_system=type_system,
        )

        # ========================================================
        # FILTRA OS VALORES
        # ========================================================

        filtered_values = (
            self._filter_values(
                values=monetary_values,
                criteria=criteria,
            )
        )

        # ========================================================
        # VALIDA RESULTADO
        # ========================================================

        if not filtered_values:

            raise ValueError(
                self._build_not_found_message(
                    code=code,
                    criteria=criteria,
                )
            )

        if len(filtered_values) > 1:

            raise ValueError(
                self._build_ambiguous_message(
                    code=code,
                    values=filtered_values,
                    criteria=criteria,
                )
            )

        return filtered_values[0]

    # ============================================================
    # CONSTRUÇÃO DOS CRITÉRIOS
    # ============================================================

    def _build_criteria(
        self,
        context: CalculationContext,
        source_file_uf: str | None,
        source_file_data_base: date | None,
        classification: str | None,
        group: str | None,
        type_system: str | None,
    ) -> dict[str, object | None]:
        """
        Constrói os critérios finais utilizados na resolução.

        A prioridade é:

            1. Critério informado diretamente em resolve()
            2. Critério existente no CalculationContext
            3. None

        Isso permite sobrescrever temporariamente qualquer
        critério sem modificar o contexto original.
        """

        return {
            "source_file_uf": (
                source_file_uf
                if source_file_uf is not None
                else context.source_file_uf
            ),
            "source_file_data_base": (
                source_file_data_base
                if source_file_data_base is not None
                else context.source_file_data_base
            ),
            "classification": (
                classification
                if classification is not None
                else context.classification
            ),
            "group": (
                group
                if group is not None
                else context.group
            ),
            "type_system": (
                type_system
                if type_system is not None
                else context.type_system
            ),
        }

    # ============================================================
    # FILTRAGEM PRINCIPAL
    # ============================================================

    def _filter_values(
        self,
        values: list[MonetaryValue],
        criteria: dict[str, object | None],
    ) -> list[MonetaryValue]:
        """
        Aplica todos os filtros cumulativamente.

        Ordem:

            valores disponíveis
                ↓
            UF
                ↓
            data-base
                ↓
            classificação
                ↓
            grupo
                ↓
            sistema
        """

        filtered_values = values

        filtered_values = (
            self._filter_by_uf(
                values=filtered_values,
                source_file_uf=(
                    criteria["source_file_uf"]
                ),
            )
        )

        filtered_values = (
            self._filter_by_data_base(
                values=filtered_values,
                source_file_data_base=(
                    criteria["source_file_data_base"]
                ),
            )
        )

        filtered_values = (
            self._filter_by_classification(
                values=filtered_values,
                classification=(
                    criteria["classification"]
                ),
            )
        )

        filtered_values = (
            self._filter_by_group(
                values=filtered_values,
                group=criteria["group"],
            )
        )

        filtered_values = (
            self._filter_by_type_system(
                values=filtered_values,
                type_system=(
                    criteria["type_system"]
                ),
            )
        )

        return filtered_values

    # ============================================================
    # UF
    # ============================================================

    def _filter_by_uf(
        self,
        values: list[MonetaryValue],
        source_file_uf: object | None,
    ) -> list[MonetaryValue]:
        """
        Filtra os valores monetários pela UF.
        """

        if source_file_uf is None:

            return values

        return [
            value
            for value in values
            if (
                value.source_file_uf
                == source_file_uf
            )
        ]

    # ============================================================
    # DATA-BASE
    # ============================================================

    def _filter_by_data_base(
        self,
        values: list[MonetaryValue],
        source_file_data_base: object | None,
    ) -> list[MonetaryValue]:
        """
        Filtra os valores monetários pela data-base.
        """

        if source_file_data_base is None:

            return values

        return [
            value
            for value in values
            if (
                value.source_file_data_base
                == source_file_data_base
            )
        ]

    # ============================================================
    # CLASSIFICAÇÃO
    # ============================================================

    def _filter_by_classification(
        self,
        values: list[MonetaryValue],
        classification: object | None,
    ) -> list[MonetaryValue]:
        """
        Filtra os valores pela classificação.

        Exemplos:

            PR
            IM
            PC
        """

        if classification is None:

            return values

        return [
            value
            for value in values
            if (
                value.classification
                == classification
            )
        ]

    # ============================================================
    # GRUPO
    # ============================================================

    def _filter_by_group(
        self,
        values: list[MonetaryValue],
        group: object | None,
    ) -> list[MonetaryValue]:
        """
        Filtra os valores pelo grupo.
        """

        if group is None:

            return values

        return [
            value
            for value in values
            if value.group == group
        ]

    # ============================================================
    # SISTEMA
    # ============================================================

    def _filter_by_type_system(
        self,
        values: list[MonetaryValue],
        type_system: object | None,
    ) -> list[MonetaryValue]:
        """
        Filtra os valores pelo sistema.
        """

        if type_system is None:

            return values

        return [
            value
            for value in values
            if (
                value.type_system
                == type_system
            )
        ]

    # ============================================================
    # MENSAGENS DE ERRO
    # ============================================================

    def _build_not_found_message(
        self,
        code: str,
        criteria: dict[str, object | None],
    ) -> str:
        """
        Constrói uma mensagem detalhada quando nenhum valor
        monetário compatível é encontrado.
        """

        return (
            "No monetary value matches the calculation "
            "criteria. "
            f"Input: {code}. "
            f"UF: "
            f"{criteria['source_file_uf']}. "
            f"Data base: "
            f"{criteria['source_file_data_base']}. "
            f"Classification: "
            f"{criteria['classification']}. "
            f"Group: "
            f"{criteria['group']}. "
            f"Type system: "
            f"{criteria['type_system']}."
        )

    def _build_ambiguous_message(
        self,
        code: str,
        values: list[MonetaryValue],
        criteria: dict[str, object | None],
    ) -> str:
        """
        Constrói uma mensagem quando mais de um valor monetário
        continua compatível com os critérios.

        Isso normalmente indica que:

            - o CalculationContext possui poucos filtros; ou
            - os critérios específicos informados em resolve()
            não são suficientes para selecionar um único valor.
        """

        values_description = (
            ", ".join(
                str(value.id)
                for value in values
            )
        )

        return (
            "More than one monetary value matches the "
            "calculation criteria. "
            f"Input: {code}. "
            f"Matching IDs: "
            f"{values_description}. "
            f"Criteria: "
            f"UF={criteria['source_file_uf']}, "
            f"DataBase="
            f"{criteria['source_file_data_base']}, "
            f"Classification="
            f"{criteria['classification']}, "
            f"Group="
            f"{criteria['group']}, "
            f"TypeSystem="
            f"{criteria['type_system']}."
        )