from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

class CompositionCalculationRequest(BaseModel):
    """
    Contrato HTTP para solicitação do cálculo de uma composição.
    """
    composition_id: str
    source_file_uf: str
    methodology: Literal["SC", "SN"]
    type_system: str
    monetary_base_date: date
    reference_base_date: date



class CompositionCalculationResponse(BaseModel):
    """
    Contrato HTTP público do resultado do cálculo.
    """

    composition_id: str
    reference_base_date: date
    unit_cost: Decimal