from decimal import Decimal

from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput


def _build_composition(
    *,
    identifier: int = 1,
    code: str = "4915757",
    description: str = "Composição de teste",
    unit: str = "m³",
    production: str = "1",
    equipments: list[CompositionInput] | None = None,
    workmen: list[CompositionInput] | None = None,
    materials: list[CompositionInput] | None = None,
    activities: list[CompositionInput] | None = None,
    transports: list[CompositionInput] | None = None,
) -> Composition:
    """
    Cria uma composição mínima para os testes.
    """

    return Composition(
        id=identifier,
        composition_group=code[:2],
        generic_item=code,
        generic_description=description,
        unit=unit,
        fic=Decimal("0"),
        production=Decimal(production),
        equipments=equipments or [],
        workmen=workmen or [],
        materials=materials or [],
        activities=activities or [],
        transports=transports or [],
    )


def _build_input(
    *,
    identifier: int = 1,
    code: str,
    group: str,
    quantity: str = "1",
) -> CompositionInput:
    """
    Cria um insumo mínimo para os testes.
    """

    return CompositionInput(
        id=identifier,
        input_group=group,
        generic_item=code,
        generic_description=f"Insumo {code}",
        unit="un",
        input_quantity=Decimal(quantity),
    )


def test_composition_stores_basic_attributes() -> None:
    """
    Verifica os atributos básicos da entidade Composition.
    """

    composition = _build_composition(
        identifier=7,
        code="4915757",
        description="Composição de teste",
        unit="m³",
        production="2.5",
    )

    assert composition.id == 7
    assert composition.composition_group == "49"
    assert composition.generic_item == "4915757"
    assert composition.generic_description == "Composição de teste"
    assert composition.code == "4915757"
    assert composition.unit == "m³"
    assert composition.fic == Decimal("0")
    assert composition.production == Decimal("2.5")


def test_composition_starts_with_empty_input_collections() -> None:
    """
    Verifica que uma composição pode ser criada sem insumos.
    """

    composition = _build_composition()

    assert composition.equipments == []
    assert composition.workmen == []
    assert composition.materials == []
    assert composition.activities == []
    assert composition.transports == []
    assert composition.inputs == []
    assert composition.get_inputs_count() == 0


def test_composition_get_inputs_count_counts_all_input_groups() -> None:
    """
    Verifica que get_inputs_count() contabiliza os insumos
    de todos os grupos da composição.
    """

    equipment = _build_input(
        identifier=1,
        code="E0001",
        group="EQ",
    )

    workman = _build_input(
        identifier=2,
        code="P0001",
        group="MO",
    )

    material = _build_input(
        identifier=3,
        code="M0001",
        group="MA",
    )

    activity = _build_input(
        identifier=4,
        code="A0001",
        group="AX",
    )

    transport = _build_input(
        identifier=5,
        code="T0001",
        group="TF",
    )

    composition = _build_composition(
        equipments=[equipment],
        workmen=[workman],
        materials=[material],
        activities=[activity],
        transports=[transport],
    )

    assert composition.get_inputs_count() == 5
    assert len(composition.inputs) == 5


def test_composition_preserves_input_objects() -> None:
    """
    Verifica que a composição mantém as referências aos objetos
    de entrada recebidos na construção.
    """

    equipment = _build_input(
        code="E0001",
        group="EQ",
        quantity="2.5",
    )

    material = _build_input(
        code="M0001",
        group="MA",
        quantity="3.75",
    )

    composition = _build_composition(
        equipments=[equipment],
        materials=[material],
    )

    assert composition.equipments[0] is equipment
    assert composition.materials[0] is material

    assert composition.equipments[0].quantity == Decimal("2.5")
    assert composition.materials[0].quantity == Decimal("3.75")