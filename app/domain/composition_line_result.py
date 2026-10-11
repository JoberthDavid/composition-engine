from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EquipmentLineResult:
    """
    Resultado detalhado de uma linha de equipamento.
    """

    code: str
    description: str
    unit: str
    quantity: Decimal
    input_use: Decimal
    productive_value: Decimal
    unproductive_value: Decimal
    line_cost: Decimal


@dataclass(frozen=True)
class LaborLineResult:
    """
    Resultado detalhado de uma linha de mão de obra.
    """

    code: str
    description: str
    unit: str
    quantity: Decimal
    monetary_value: Decimal
    line_cost: Decimal


@dataclass(frozen=True)
class MaterialLineResult:
    """
    Resultado detalhado de uma linha de material.
    """

    code: str
    description: str
    unit: str
    quantity: Decimal
    monetary_value: Decimal
    line_cost: Decimal