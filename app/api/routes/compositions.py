from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    create_composition_calculation_service,
    get_composition_explosion,
)
from app.schemas.composition_calculation import (
    CompositionCalculationRequest,
    CompositionCalculationResponse,
)
from app.services.composition_calculation_service import (
    CompositionCalculationService,
)
from app.services.composition_explosion import CompositionExplosion

from app.api.security import require_api_key

router = APIRouter(
    prefix="/compositions",
    tags=["compositions"],
)


def _count_nodes(node) -> int:
    return 1 + sum(
        _count_nodes(child)
        for child in node.children
    )

@router.post(
    "/calculate",
    response_model=CompositionCalculationResponse,
    dependencies=[Depends(require_api_key)],
)
def calculate(
    request: CompositionCalculationRequest,
    service: CompositionCalculationService = Depends(
        create_composition_calculation_service,
    ),
) -> CompositionCalculationResponse:

    result = service.calculate(
        composition_id=request.composition_id,
    )

    return CompositionCalculationResponse(
        composition_id=result.composition_code,
        reference_base_date=request.reference_base_date,
        unit_cost=result.composition_unit_cost,
    )


@router.get(
    "/{composition_id}/explosion",
    dependencies=[Depends(require_api_key)],
)
def explode_composition(
    composition_id: str,
    explosion: CompositionExplosion = Depends(
        get_composition_explosion,
    ),
):
    try:
        result = explosion.explode(composition_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "composition": {
            "code": result.root_node.root.composition.generic_item,
            "nodes": _count_nodes(result.root_node.root),
        },
        "compositions": [
            {
                "identifier": item.identifier,
                "group": item.group,
                "code": item.code,
                "description": item.description,
                "unit": item.unit,
                "quantity": str(item.quantity),
            }
            for item in result.compositions
        ],
        "inputs": [
            {
                "identifier": item.identifier,
                "group": item.group,
                "code": item.code,
                "description": item.description,
                "unit": item.unit,
                "quantity": str(item.quantity),
                "productive_quantity": str(item.productive_quantity),
                "unproductive_quantity": str(item.unproductive_quantity),
                "proprietary_item": item.proprietary_item,
            }
            for item in result.inputs
        ],
    }