from __future__ import annotations

from app.composition_root import CompositionRoot
from app.domain.calculation_context import CalculationContext
from app.schemas.composition_calculation import (
    CompositionCalculationRequest,
)
from app.services.composition_calculation_service import (
    CompositionCalculationService,
)
from app.services.composition_explosion import CompositionExplosion


def get_composition_explosion() -> CompositionExplosion:
    """
    Dependency responsável por construir o serviço de
    explosão de composições.
    """

    root = CompositionRoot()

    return root.create_composition_explosion()


def create_composition_calculation_service(
    request: CompositionCalculationRequest,
) -> CompositionCalculationService:
    """
    Constrói o serviço de cálculo de composição a partir
    dos parâmetros recebidos pela API.

    Mapeamento:

        reference_base_date
            -> CompositionRoot.composition_data_base

        monetary_base_date
            -> CalculationContext.source_file_data_base
    """

    context = CalculationContext(
        source_file_uf=request.source_file_uf,
        source_file_data_base=request.monetary_base_date,
        type_system=request.type_system,
    )

    root = CompositionRoot(
        composition_data_base=(
            request.reference_base_date.isoformat()
        ),
    )

    return root.create_composition_calculation(
        calculation_context=context,
    )