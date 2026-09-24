from __future__ import annotations
from datetime import date

from fastapi import Depends

from app.composition_root import CompositionRoot
from app.domain.calculation_context import CalculationContext
from app.schemas.composition_calculation import (
    CompositionCalculationRequest,
)
from app.services.composition_calculation_service import (
    CompositionCalculationService,
)
from app.services.composition_explosion import CompositionExplosion

from app.schemas.composition_operation import (
    CompositionOperationContextRequest,
)


def get_composition_explosion() -> CompositionExplosion:
    """
    Dependency responsável por construir o serviço de
    explosão de composições.
    """

    root = CompositionRoot()

    return root.create_composition_explosion()


def get_composition_operation_context(
    source_file_uf: str,
    type_system: str,
    monetary_base_date: date,
    reference_base_date: date,
) -> CompositionOperationContextRequest:
    """
    Constrói o contexto da operação a partir dos parâmetros
    recebidos pela API.

    Os quatro parâmetros são recebidos pelo FastAPI como
    query parameters.
    """

    return CompositionOperationContextRequest(
        source_file_uf=source_file_uf,
        type_system=type_system,
        monetary_base_date=monetary_base_date,
        reference_base_date=reference_base_date,
    )

def create_composition_calculation_service(
    context: CompositionOperationContextRequest = Depends(
        get_composition_operation_context,
    ),
) -> CompositionCalculationService:
    """
    Constrói o serviço de cálculo a partir do contexto
    recebido pela API.
    """

    calculation_context = CalculationContext(
        source_file_uf=context.source_file_uf,
        source_file_data_base=context.monetary_base_date,
        type_system=context.type_system,
    )

    root = CompositionRoot(
        composition_data_base=(
            context.reference_base_date.isoformat()
        ),
    )

    return root.create_composition_calculation(
        calculation_context=calculation_context,
    )
