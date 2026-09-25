from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    create_composition_calculation_service,
    get_composition_explosion,
    get_composition_operation_context,
)
from app.api.schemas import CompositionExplosionResponse
from app.schemas.composition_calculation import (
    CompositionCalculationResponse,
)
from app.schemas.composition_operation import (
    CompositionOperationContextRequest,
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
    "/{composition_code}/calculate",
    response_model=CompositionCalculationResponse,
    dependencies=[Depends(require_api_key)],
)
def calculate(
    composition_code: str,
    context: CompositionOperationContextRequest = Depends(
        get_composition_operation_context,
    ),
    service: CompositionCalculationService = Depends(
        create_composition_calculation_service,
    ),
) -> CompositionCalculationResponse:

    result = service.calculate(
        composition_id=composition_code,
    )

    return CompositionCalculationResponse(
        composition_id=result.composition_code,
        reference_base_date=context.reference_base_date,
        unit_cost=result.composition_unit_cost,
    )


@router.get(
    "/{composition_code}/explosion",
    response_model=CompositionExplosionResponse,
    dependencies=[Depends(require_api_key)],
)
def explode_composition(
    composition_code: str,
    explosion: CompositionExplosion = Depends(
        get_composition_explosion,
    ),
):
    try:
        result = explosion.explode(composition_code)

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
                "unproductive_quantity": str(
                    item.unproductive_quantity
                ),
                "proprietary_item": item.proprietary_item,
            }
            for item in result.inputs
        ],
    }