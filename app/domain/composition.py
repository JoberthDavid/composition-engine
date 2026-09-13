from decimal import Decimal

from app.domain.composition_input import CompositionInput

class Composition:
    """
    Representa uma composição de custos utilizada pelo motor.


    A composição recebe os insumos agrupados pela API e mantém
    separadamente equipamentos, mão de obra, materiais, atividades
    auxiliares e transportes.

    O campo 'transports' retornado pela API pode conter diferentes
    grupos de insumos:

        TF -> Tempo Fixo
        LN -> Transporte
        RP -> Transporte
        PV -> Transporte
        FR -> Transporte

    Por isso, os filtros são disponibilizados através das propriedades
    fixed_time_inputs e transport_inputs.
    """

    def __init__(
        self,
        id: int,
        composition_group: str,
        generic_item: str,
        generic_description: str,
        unit: str,
        fic: Decimal,
        production: Decimal,
        equipments: list[CompositionInput],
        workmen: list[CompositionInput],
        materials: list[CompositionInput],
        activities: list[CompositionInput],
        transports: list[CompositionInput],
    ) -> None:
        """
        Inicializa uma composição.
        """

        self.id = id
        self.composition_group = composition_group
        self.generic_item = generic_item
        self.generic_description = generic_description
        self.unit = unit
        self.fic = fic
        self.production = production

        self.equipments = equipments
        self.workmen = workmen
        self.materials = materials
        self.activities = activities
        self.transports = transports

    # ============================================================
    # CONSTRUÇÃO A PARTIR DA API
    # ============================================================

    @classmethod
    def from_api_data(
        cls,
        data: dict,
    ) -> "Composition":
        """
        Cria uma composição a partir dos dados retornados pela API Django.
        """

        return cls(
            id=data["id"],
            composition_group=data["composition_group"],
            generic_item=data["generic_item"],
            generic_description=data["generic_description"],
            unit=data["unit"],
            fic=Decimal(str(data["fic"])),
            production=Decimal(str(data["production"])),
            equipments=cls._create_inputs(
                data.get("equipments", [])
            ),
            workmen=cls._create_inputs(
                data.get("workmen", [])
            ),
            materials=cls._create_inputs(
                data.get("materials", [])
            ),
            activities=cls._create_inputs(
                data.get("activities", [])
            ),
            transports=cls._create_inputs(
                data.get("transports", [])
            ),
        )

    @staticmethod
    def _create_inputs(
        inputs: list[dict],
    ) -> list[CompositionInput]:
        """
        Converte os dicionários retornados pela API em objetos
        CompositionInput.
        """

        return [
            CompositionInput.from_api_data(
                input_data
            )
            for input_data in inputs
        ]

    # ============================================================
    # CÓDIGO DA COMPOSIÇÃO
    # ============================================================

    @property
    def code(self) -> str:
        """
        Retorna o código da composição.

        generic_item é o campo utilizado pela API Django para
        identificar a composição.
        """

        return self.generic_item

    # ============================================================
    # ATIVIDADES AUXILIARES
    # ============================================================

    @property
    def auxiliary_inputs(
        self,
    ) -> list[CompositionInput]:
        """
        Retorna as atividades auxiliares da composição.

        As atividades auxiliares possuem input_group = AX.
        """

        return [
            composition_input
            for composition_input in self.activities
            if composition_input.is_auxiliary_activity()
        ]

    # ============================================================
    # TEMPOS FIXOS
    # ============================================================

    @property
    def fixed_time_inputs(
        self,
    ) -> list[CompositionInput]:
        """
        Retorna somente os tempos fixos.

        A chave 'transports' da API Django pode conter diversos
        grupos de transporte. Apenas os itens com:

            input_group = TF

        representam referências a composições de tempo fixo.
        """

        return [
            composition_input
            for composition_input in self.transports
            if composition_input.is_fixed_time()
        ]

    # ============================================================
    # TRANSPORTES
    # ============================================================

    @property
    def transport_inputs(
        self,
    ) -> list[CompositionInput]:
        """
        Retorna somente os insumos de transporte.

        A lista 'transports' retornada pela API Django contém:

            TF -> Tempo Fixo
            LN -> Transporte
            RP -> Transporte
            PV -> Transporte
            FR -> Transporte

        O grupo TF é excluído desta propriedade porque representa
        uma referência recursiva para outra composição.

        Esta propriedade retorna somente:

            LN
            RP
            PV
            FR
        """

        return [
            composition_input
            for composition_input in self.transports
            if composition_input.is_transport()
        ]

    # ============================================================
    # REFERÊNCIAS RECURSIVAS
    # ============================================================

    @property
    def composition_references(
        self,
    ) -> list[CompositionInput]:
        """
        Retorna todas as referências para outras composições.

        Atualmente são consideradas referências recursivas:

            AX -> Atividade Auxiliar
            TF -> Tempo Fixo
        """

        return (
            self.auxiliary_inputs
            + self.fixed_time_inputs
        )

    # ============================================================
    # TODOS OS INSUMOS
    # ============================================================

    @property
    def inputs(
        self,
    ) -> list[CompositionInput]:
        """
        Retorna todos os insumos da composição em uma única lista.

        Inclui todos os transportes retornados pela API, inclusive TF.
        """

        return (
            self.equipments
            + self.workmen
            + self.materials
            + self.activities
            + self.transports
        )

    # ============================================================
    # CONTADORES
    # ============================================================

    def get_inputs_count(
        self,
    ) -> int:
        """
        Retorna a quantidade total de insumos da composição.
        """

        return len(
            self.inputs
        )

    def get_auxiliary_inputs_count(
        self,
    ) -> int:
        """
        Retorna a quantidade de atividades auxiliares.
        """

        return len(
            self.auxiliary_inputs
        )

    def get_fixed_time_inputs_count(
        self,
    ) -> int:
        """
        Retorna a quantidade de tempos fixos.
        """

        return len(
            self.fixed_time_inputs
        )

    def get_transport_inputs_count(
        self,
    ) -> int:
        """
        Retorna a quantidade de transportes propriamente ditos.

        Não inclui TF.
        """

        return len(
            self.transport_inputs
        )

    # ============================================================
    # REPRESENTAÇÃO
    # ============================================================

    def __repr__(
        self,
    ) -> str:
        """
        Retorna uma representação textual da composição.
        """

        return (
            "Composition("
            f"generic_item='{self.generic_item}', "
            f"generic_description="
            f"'{self.generic_description}'"
            ")"
        )