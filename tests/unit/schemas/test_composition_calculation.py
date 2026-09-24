from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.composition_calculation import (
    CompositionCalculationRequest,
    CompositionCalculationResponse,
)


def test_request_accepts_valid_data() -> None:
    request = CompositionCalculationRequest(
        composition_id="0919013",
        source_file_uf="DF",
        type_system="ON",
        monetary_base_date="2021-10-01",
        reference_base_date="2021-10-01",
    )

    assert request.composition_id == "0919013"
    assert request.source_file_uf == "DF"
    assert request.type_system == "ON"

    assert request.monetary_base_date == date(
        2021,
        10,
        1,
    )

    assert request.reference_base_date == date(
        2021,
        10,
        1,
    )


def test_request_rejects_missing_composition_id() -> None:
    with pytest.raises(ValidationError):
        CompositionCalculationRequest(
            source_file_uf="DF",
            type_system="ON",
            monetary_base_date="2021-10-01",
            reference_base_date="2021-10-01",
        )


def test_request_rejects_missing_source_file_uf() -> None:
    with pytest.raises(ValidationError):
        CompositionCalculationRequest(
            composition_id="0919013",
            type_system="ON",
            monetary_base_date="2021-10-01",
            reference_base_date="2021-10-01",
        )


def test_request_rejects_invalid_monetary_base_date() -> None:
    with pytest.raises(ValidationError):
        CompositionCalculationRequest(
            composition_id="0919013",
            source_file_uf="DF",
            type_system="ON",
            monetary_base_date="data-invalida",
            reference_base_date="2021-10-01",
        )


def test_request_rejects_invalid_reference_base_date() -> None:
    with pytest.raises(ValidationError):
        CompositionCalculationRequest(
            composition_id="0919013",
            source_file_uf="DF",
            type_system="ON",
            monetary_base_date="2021-10-01",
            reference_base_date="data-invalida",
        )


def test_response_accepts_decimal_unit_cost() -> None:
    response = CompositionCalculationResponse(
        composition_id="0919013",
        reference_base_date="2021-10-01",
        unit_cost=Decimal("105890.00"),
    )

    assert response.unit_cost == Decimal("105890.00")


def test_response_serializes_decimal_without_float_conversion() -> None:
    response = CompositionCalculationResponse(
        composition_id="0919013",
        reference_base_date="2021-10-01",
        unit_cost=Decimal("105890.00"),
    )

    data = response.model_dump()

    assert data["unit_cost"] == Decimal("105890.00")