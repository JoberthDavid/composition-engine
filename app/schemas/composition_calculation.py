from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class CompositionCalculationRequest(BaseModel):
    composition_id: str
    source_file_uf: str
    methodology: Literal["SC", "SN"]
    type_system: str
    monetary_base_date: date
    reference_base_date: date

class EquipmentLineResponse(BaseModel):
    code: str
    description: str
    unit: str
    quantity: Decimal
    input_use: Decimal
    productive_value: Decimal
    unproductive_value: Decimal
    line_cost: Decimal


class LaborLineResponse(BaseModel):
    code: str
    description: str
    unit: str
    quantity: Decimal
    monetary_value: Decimal
    line_cost: Decimal


class MaterialLineResponse(BaseModel):
    code: str
    description: str
    unit: str
    quantity: Decimal
    monetary_value: Decimal
    line_cost: Decimal


class CompositionCalculationLinesResponse(BaseModel):
    equipment: list[EquipmentLineResponse]
    labor: list[LaborLineResponse]
    materials: list[MaterialLineResponse]


class CompositionCalculationDetailResponse(BaseModel):
    composition_id: str
    reference_base_date: date
    unit_cost: Decimal
    detail: CompositionCalculationLinesResponse


class CompositionCalculationResponse(BaseModel):
    composition_id: str
    reference_base_date: date
    unit_cost: Decimal