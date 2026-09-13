from decimal import Decimal


class CompositionInput:
    """
    Representa um insumo pertencente a uma composição.

    A classe é genérica e pode representar:

    - EQ: Equipamento
    - MO: Mão de obra
    - MA: Material
    - AX: Atividade auxiliar
    - TF: Tempo fixo
    - LN: Transporte
    - RP: Transporte
    - PV: Transporte
    - FR: Transporte

    O campo `input_group` define a natureza do insumo.
    """

    EQUIPMENT_GROUP = "EQ"
    WORKMAN_GROUP = "MO"
    MATERIAL_GROUP = "MA"
    AUXILIARY_ACTIVITY_GROUP = "AX"
    FIXED_TIME_GROUP = "TF"

    TRANSPORT_GROUPS = {
        "LN",
        "RP",
        "PV",
        "FR",
    }

    COMPOSITION_REFERENCE_GROUPS = {
        AUXILIARY_ACTIVITY_GROUP,
        FIXED_TIME_GROUP,
    }

    def __init__(
        self,
        id: int,
        input_group: str,
        generic_item: str,
        generic_description: str,
        unit: str,
        input_quantity: Decimal,
        input_use: Decimal | None = None,
        proprietary_item: str | None = None,
    ) -> None:

        self.id = id

        self.input_group = input_group

        self.generic_item = generic_item
        self.generic_description = generic_description

        self.unit = unit

        self.input_quantity = input_quantity

        self.input_use = input_use

        self.proprietary_item = proprietary_item

    # ============================================================
    # CONSTRUÇÃO A PARTIR DA API
    # ============================================================

    @classmethod
    def from_api_data(
        cls,
        data: dict,
    ) -> "CompositionInput":
        """
        Cria um CompositionInput a partir dos dados
        retornados pela API Django.

        Os valores monetários e quantidades são convertidos
        diretamente para Decimal para evitar perda de precisão.
        """

        return cls(
            id=data["id"],

            input_group=data["input_group"],

            generic_item=data["generic_item"],

            generic_description=data[
                "generic_description"
            ],

            unit=data["unit"],

            input_quantity=Decimal(
                str(data["input_quantity"])
            ),

            input_use=(
                Decimal(
                    str(data["input_use"])
                )
                if data.get("input_use") is not None
                else None
            ),

            proprietary_item=data.get(
                "proprietary_item"
            ),
        )

    # ============================================================
    # PROPRIEDADES DE IDENTIFICAÇÃO
    # ============================================================

    @property
    def code(self) -> str:
        """
        Retorna o código genérico do insumo.

        Exemplo:

        E9785
        P9801
        M0004
        0919079
        """

        return self.generic_item

    @property
    def description(self) -> str:
        """
        Retorna a descrição genérica do insumo.
        """

        return self.generic_description

    @property
    def quantity(self) -> Decimal:
        """
        Retorna a quantidade do insumo.

        Este é um alias para `input_quantity`.

        O objetivo é facilitar o uso no motor de cálculo,
        permitindo expressões como:

            input.quantity

        em vez de:

            input.input_quantity
        """

        return self.input_quantity

    # ============================================================
    # CAMPOS OPCIONAIS
    # ============================================================

    def has_use(self) -> bool:
        """
        Verifica se o insumo possui utilização informada.
        """

        return self.input_use is not None

    def has_proprietary_item(self) -> bool:
        """
        Verifica se existe um item proprietário associado.
        """

        return (
            self.proprietary_item is not None
        )

    # ============================================================
    # CLASSIFICAÇÃO DO INSUMO
    # ============================================================

    def is_equipment(self) -> bool:
        """
        Verifica se o insumo representa um equipamento.
        """

        return (
            self.input_group
            == self.EQUIPMENT_GROUP
        )

    def is_workman(self) -> bool:
        """
        Verifica se o insumo representa mão de obra.
        """

        return (
            self.input_group
            == self.WORKMAN_GROUP
        )

    def is_material(self) -> bool:
        """
        Verifica se o insumo representa um material.
        """

        return (
            self.input_group
            == self.MATERIAL_GROUP
        )

    def is_auxiliary_activity(self) -> bool:
        """
        Verifica se o insumo representa
        uma atividade auxiliar (AX).
        """

        return (
            self.input_group
            == self.AUXILIARY_ACTIVITY_GROUP
        )

    def is_fixed_time(self) -> bool:
        """
        Verifica se o insumo representa
        um tempo fixo (TF).
        """

        return (
            self.input_group
            == self.FIXED_TIME_GROUP
        )

    # ============================================================
    # REFERÊNCIAS PARA OUTRAS COMPOSIÇÕES
    # ============================================================

    def is_composition_reference(self) -> bool:
        """
        Verifica se o insumo referencia outra composição.

        Atualmente, as referências recursivas utilizadas
        pela árvore de composições são:

        AX - Atividade auxiliar
        TF - Tempo fixo
        """

        return (
            self.input_group
            in self.COMPOSITION_REFERENCE_GROUPS
        )

    # ============================================================
    # TRANSPORTES
    # ============================================================

    def is_transport(self) -> bool:
        """
        Verifica se o insumo representa uma operação
        de transporte.

        Os grupos de transporte considerados são:

        LN
        RP
        PV
        FR

        O grupo TF NÃO é considerado transporte nesta
        classificação porque, no motor de composição,
        TF representa uma referência recursiva para
        outra composição.
        """

        return (
            self.input_group
            in self.TRANSPORT_GROUPS
        )

    # ============================================================
    # REPRESENTAÇÃO
    # ============================================================

    def __repr__(self) -> str:

        return (
            "CompositionInput("
            f"id={self.id}, "
            f"generic_item='{self.generic_item}', "
            f"input_group='{self.input_group}', "
            f"input_quantity={self.input_quantity}, "
            f"unit='{self.unit}', "
            f"generic_description="
            f"'{self.generic_description}'"
            ")"
        )