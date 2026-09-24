from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.compositions import router

from app.api.dependencies import (
    create_composition_calculation_service,
)
API_HEADERS = {
    "X-API-Key": "test-api-key",
}

def create_test_app(
    service: Mock,
) -> FastAPI:
    app = FastAPI()

    app.include_router(router)

    app.dependency_overrides[
        create_composition_calculation_service
    ] = lambda: service

    return app


def test_calculate_returns_public_contract() -> None:
    service = Mock()

    service.calculate.return_value = Mock(
        composition_code="0919013",
        composition_unit_cost=Decimal(
            "105890.00"
        ),
    )

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers=API_HEADERS,
        json={
            "composition_id": "0919013",
            "source_file_uf": "DF",
            "type_system": "ON",
            "monetary_base_date": "2021-10-01",
            "reference_base_date": "2021-10-01",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "composition_id": "0919013",
        "reference_base_date": "2021-10-01",
        "unit_cost": "105890.00",
    }

    service.calculate.assert_called_once_with(
        composition_id="0919013",
    )


def test_calculate_rejects_missing_composition_id() -> None:
    service = Mock()

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers=API_HEADERS,
        json={
            "source_file_uf": "DF",
            "type_system": "ON",
            "monetary_base_date": "2021-10-01",
            "reference_base_date": "2021-10-01",
        },
    )

    assert response.status_code == 422

    service.calculate.assert_not_called()


def test_calculate_rejects_invalid_monetary_base_date() -> None:
    service = Mock()

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers=API_HEADERS,
        json={
            "composition_id": "0919013",
            "source_file_uf": "DF",
            "type_system": "ON",
            "monetary_base_date": "invalid",
            "reference_base_date": "2021-10-01",
        },
    )

    assert response.status_code == 422

    service.calculate.assert_not_called()


def test_calculate_rejects_missing_source_file_uf() -> None:
    service = Mock()

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers=API_HEADERS,
        json={
            "composition_id": "0919013",
            "type_system": "ON",
            "monetary_base_date": "2021-10-01",
            "reference_base_date": "2021-10-01",
        },
    )

    assert response.status_code == 422

    service.calculate.assert_not_called()


def _build_app(
    service,
) -> FastAPI:

    app = FastAPI()

    app.include_router(router)

    app.dependency_overrides[
        create_composition_calculation_service
    ] = lambda: service

    return app


class FakeCompositionCalculationService:

    def __init__(self) -> None:
        self.received_composition_id = None

    def calculate(
        self,
        *,
        composition_id: str,
    ):
        self.received_composition_id = composition_id

        return SimpleNamespace(
            composition_code="0919013",
            composition_unit_cost=Decimal("800.00"),
        )


def test_calculate_calls_service_with_composition_id() -> None:
    service = FakeCompositionCalculationService()

    app = _build_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers=API_HEADERS,
        json={
            "composition_id": "0919013",
            "source_file_uf": "DF",
            "type_system": "ON",
            "monetary_base_date": "2021-10-01",
            "reference_base_date": "2021-10-01",
        },
    )

    assert response.status_code == 200

    assert (
        service.received_composition_id
        == "0919013"
    )


def test_calculate_returns_expected_response() -> None:
    service = FakeCompositionCalculationService()

    app = _build_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers=API_HEADERS,
        json={
            "composition_id": "0919013",
            "source_file_uf": "DF",
            "type_system": "ON",
            "monetary_base_date": "2021-10-01",
            "reference_base_date": "2021-10-01",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "composition_id": "0919013",
        "reference_base_date": "2021-10-01",
        "unit_cost": "800.00",
    }


def test_calculate_rejects_invalid_request() -> None:
    service = FakeCompositionCalculationService()

    app = _build_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers=API_HEADERS,
        json={
            "composition_id": "0919013",
            "source_file_uf": "DF",
            "type_system": "ON",
            "monetary_base_date": "2021-10-01",
        },
    )

    assert response.status_code == 422