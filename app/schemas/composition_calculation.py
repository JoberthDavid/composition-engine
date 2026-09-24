from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CompositionCalculationRequest(BaseModel):
    """
    Contrato HTTP para solicitação do cálculo de uma composição.

    reference_base_date:
        Base de dados estrutural da composição.

    monetary_base_date:
        Data-base utilizada para seleção dos valores monetários.

    source_file_uf:
        UF da base de valores monetários.
    """

    composition_id: str
    source_file_uf: str
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