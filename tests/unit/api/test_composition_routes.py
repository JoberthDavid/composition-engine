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
from app.domain.composition_line_result import (
    CompositionReferenceLineResult,
)


def create_test_app(
    service: Mock,
) -> FastAPI:
    app = FastAPI()

    app.include_router(router)

    app.dependency_overrides[
        create_composition_calculation_service
    ] = lambda: service

    return app


def test_calculate_returns_public_contract(jwt_headers) -> None:
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
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "composition_id": "0919013",
        "reference_base_date": "2023-01-01",
        "unit_cost": "105890.00",
    }

    service.calculate.assert_called_once_with(
        composition_id="0919013",
    )

def test_calculate_rejects_missing_source_file_uf(jwt_headers) -> None:
    service = Mock()

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 422

    service.calculate.assert_not_called()


def test_calculate_rejects_invalid_monetary_base_date(jwt_headers) -> None:
    service = Mock()

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "invalid",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 422

    service.calculate.assert_not_called()

def test_calculate_rejects_missing_type_system(jwt_headers) -> None:
    service = Mock()

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 422

    service.calculate.assert_not_called()

def test_calculate_rejects_missing_source_file_uf(jwt_headers) -> None:
    service = Mock()

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
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


def test_calculate_calls_service_with_composition_id(jwt_headers) -> None:
    service = FakeCompositionCalculationService()

    app = _build_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 200

    assert (
        service.received_composition_id
        == "0919013"
    )


def test_calculate_returns_expected_response(jwt_headers) -> None:
    service = FakeCompositionCalculationService()

    app = _build_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "composition_id": "0919013",
        "reference_base_date": "2023-01-01",
        "unit_cost": "800.00",
    }

def test_calculate_rejects_missing_reference_base_date(jwt_headers) -> None:
    service = FakeCompositionCalculationService()

    app = _build_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 422

def test_calculate_rejects_missing_methodology(jwt_headers) -> None:
    service = Mock()

    app = create_test_app(service)
    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "type_system": "ON",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 422
    service.calculate.assert_not_called()


def test_calculate_detail_returns_complete_cost_breakdown(
    jwt_headers,
) -> None:
    service = Mock()

    service.calculate.return_value = SimpleNamespace(
        composition_code="0919013",
        composition_unit_cost=Decimal("105890.123456"),
        equipment_items=[
            SimpleNamespace(
                code="E001",
                description="Equipment 1",
                unit="h",
                quantity=Decimal("2.5000"),
                input_use=Decimal("0.8000"),
                productive_value=Decimal("100.1234"),
                unproductive_value=Decimal("50.5678"),
                line_cost=Decimal("225.4150"),
            ),
            SimpleNamespace(
                code="E002",
                description="Equipment 2",
                unit="h",
                quantity=Decimal("1.0000"),
                input_use=Decimal("0.5000"),
                productive_value=Decimal("80.0000"),
                unproductive_value=Decimal("40.0000"),
                line_cost=Decimal("60.0000"),
            ),
        ],
        labor_items=[
            SimpleNamespace(
                code="MO001",
                description="Labor 1",
                unit="h",
                quantity=Decimal("3.0000"),
                monetary_value=Decimal("25.123456"),
                line_cost=Decimal("75.370368"),
            ),
        ],
        material_items=[
            SimpleNamespace(
                code="MA001",
                description="Material 1",
                unit="kg",
                quantity=Decimal("10.0000"),
                monetary_value=Decimal("12.345678"),
                line_cost=Decimal("123.456780"),
            ),
        ],
        composition_reference_items=[],
    )

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate-detail",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["composition_id"] == "0919013"
    assert data["reference_base_date"] == "2023-01-01"
    assert data["unit_cost"] == "105890.123456"

    assert len(data["detail"]["equipment"]) == 2
    assert len(data["detail"]["labor"]) == 1
    assert len(data["detail"]["materials"]) == 1

    assert data["detail"]["equipment"][0] == {
        "code": "E001",
        "description": "Equipment 1",
        "unit": "h",
        "quantity": "2.5000",
        "input_use": "0.8000",
        "productive_value": "100.1234",
        "unproductive_value": "50.5678",
        "line_cost": "225.4150",
    }

    assert data["detail"]["equipment"][1] == {
        "code": "E002",
        "description": "Equipment 2",
        "unit": "h",
        "quantity": "1.0000",
        "input_use": "0.5000",
        "productive_value": "80.0000",
        "unproductive_value": "40.0000",
        "line_cost": "60.0000",
    }

    assert data["detail"]["labor"][0] == {
        "code": "MO001",
        "description": "Labor 1",
        "unit": "h",
        "quantity": "3.0000",
        "monetary_value": "25.123456",
        "line_cost": "75.370368",
    }

    assert data["detail"]["materials"][0] == {
        "code": "MA001",
        "description": "Material 1",
        "unit": "kg",
        "quantity": "10.0000",
        "monetary_value": "12.345678",
        "line_cost": "123.456780",
    }

    service.calculate.assert_called_once_with(
        composition_id="0919013",
    )

def test_calculate_detail_returns_composition_references(
    jwt_headers,
) -> None:
    service = Mock()

    service.calculate.return_value = SimpleNamespace(
        composition_code="0919013",
        composition_unit_cost=Decimal("20.00"),
        equipment_items=[],
        labor_items=[],
        material_items=[],
        composition_reference_items=[
            CompositionReferenceLineResult(
                group="AX",
                code="0919002",
                description="Insumo de teste",
                unit="UN",
                quantity=Decimal("2"),
                child_unit_cost=Decimal("10"),
                line_cost=Decimal("20"),
            ),
            CompositionReferenceLineResult(
                group="TF",
                code="0900001",
                description="Tempo fixo",
                unit="UN",
                quantity=Decimal("3"),
                child_unit_cost=Decimal("10"),
                line_cost=Decimal("30"),
            ),
        ],
    )

    app = create_test_app(service)

    client = TestClient(app)

    response = client.post(
        "/compositions/0919013/calculate-detail",
        headers=jwt_headers(["composition:calculate"]),
        params={
            "source_file_uf": "DF",
            "type_system": "ON",
            "methodology": "SC",
            "monetary_base_date": "2023-01-01",
            "reference_base_date": "2023-01-01",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["composition_id"] == "0919013"
    assert data["reference_base_date"] == "2023-01-01"
    assert data["unit_cost"] == "20.00"

    references = data["detail"]["composition_references"]

    assert len(references) == 2

    assert references[0] == {
        "group": "AX",
        "code": "0919002",
        "description": "Insumo de teste",
        "unit": "UN",
        "quantity": "2",
        "child_unit_cost": "10",
        "line_cost": "20",
    }

    assert references[1] == {
        "group": "TF",
        "code": "0900001",
        "description": "Tempo fixo",
        "unit": "UN",
        "quantity": "3",
        "child_unit_cost": "10",
        "line_cost": "30",
    }

    service.calculate.assert_called_once_with(
        composition_id="0919013",
    )
