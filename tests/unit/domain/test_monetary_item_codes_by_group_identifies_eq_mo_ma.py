from app.domain.composition import Composition
from app.domain.composition_input import CompositionInput
from app.domain.composition_node import CompositionNode
from app.domain.composition_tree import CompositionTree


def create_input(
    input_group: str,
    code: str,
) -> CompositionInput:
    """Cria um insumo simplificado para os testes."""
    return CompositionInput(
        id=1,
        input_group=input_group,
        generic_item=code,
        generic_description=f"Teste {code}",
        unit="UN",
        input_quantity=1,
        input_use=1,
        proprietary_item=False,
    )


def create_composition(inputs: list[CompositionInput]) -> Composition:
    """Cria uma composição simplificada para os testes."""
    return Composition(
        id=1,
        composition_group="TEST",
        generic_item="TEST001",
        generic_description="Composição de teste",
        unit="UN",
        fic=0,
        production=1,
        equipments=[
            item for item in inputs
            if item.is_equipment()
        ],
        workmen=[
            item for item in inputs
            if item.is_workman()
        ],
        materials=[
            item for item in inputs
            if item.is_material()
        ],
        activities=[
            item for item in inputs
            if item.is_auxiliary_activity()
            or item.is_fixed_time()
        ],
        transports=[
            item for item in inputs
            if item.is_transport()
        ],
    )


def test_monetary_item_codes_by_group_identifies_eq_mo_ma() -> None:
    """Verifica a identificação dos códigos por grupo."""
    inputs = [
        create_input("EQ", "E001"),
        create_input("EQ", "E002"),
        create_input("EQ", "E001"),
        create_input("MO", "P001"),
        create_input("MO", "P002"),
        create_input("MO", "P001"),
        create_input("MA", "M001"),
        create_input("MA", "M002"),
        create_input("MA", "M001"),
        create_input("AX", "A001"),
        create_input("TF", "T001"),
        create_input("LN", "L001"),
    ]

    composition = create_composition(inputs)
    root = CompositionNode(composition=composition)
    tree = CompositionTree(root)

    result = tree.monetary_item_codes_by_group

    assert result == {
        "EQ": {"E001", "E002"},
        "MO": {"P001", "P002"},
        "MA": {"M001", "M002"},
    }


def test_monetary_item_codes_returns_union_of_eq_mo_ma() -> None:
    """Verifica o conjunto geral de códigos monetários."""
    inputs = [
        create_input("EQ", "E001"),
        create_input("MO", "P001"),
        create_input("MA", "M001"),
        create_input("MA", "M002"),
    ]

    composition = create_composition(inputs)
    root = CompositionNode(composition=composition)
    tree = CompositionTree(root)

    assert tree.monetary_item_codes == {
        "E001",
        "P001",
        "M001",
        "M002",
    }