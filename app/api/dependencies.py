from __future__ import annotations
from datetime import date
from typing import Literal
from fastapi import Depends

from app.composition_root import CompositionRoot
from app.domain.calculation_context import CalculationContext

from app.services.composition_calculation_service import (
    CompositionCalculationService,
)
from app.services.composition_explosion import CompositionExplosion

from app.schemas.composition_operation import (
    CompositionOperationContextRequest,
)
from app.domain.composition_operation_context import (
    CompositionOperationContext,
)

def get_composition_operation_context(
    source_file_uf: str,
    type_system: Literal["ON", "DS", "NA"],
    methodology: Literal["SC", "SN"],
    monetary_base_date: date,
    reference_base_date: date,
) -> CompositionOperationContext:
    """
    Constrói o contexto da operação a partir dos parâmetros
    recebidos pela API.

    Os cinco parâmetros são recebidos pelo FastAPI como
    query parameters.
    """
    return CompositionOperationContext(
        source_file_uf=source_file_uf,
        type_system=type_system,
        methodology=methodology,
        monetary_base_date=monetary_base_date,
        reference_base_date=reference_base_date,
    )

def get_composition_explosion(
    context: CompositionOperationContext = Depends(
        get_composition_operation_context,
    ),
    ) -> CompositionExplosion:
    """
    Constrói o serviço de explosão a partir do contexto
    recebido pela API.

    A referência estrutural da composição é definida por
    reference_base_date.
    """
    root = CompositionRoot(
        composition_data_base=(
            context.reference_base_date.isoformat()
        ),
    )

    return root.create_composition_explosion(
        context=context,
    )


def create_composition_calculation_service(
    context: CompositionOperationContext = Depends(
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
        methodology=context.methodology,
    )

    root = CompositionRoot(
        composition_data_base=(
            context.reference_base_date.isoformat()
        ),
    )

    return root.create_composition_calculation(
        calculation_context=calculation_context,
    )
