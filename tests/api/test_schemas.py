from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.api.schemas import (
    BudgetCalculationRequestSchema,
    BudgetCalculationResponse,
    CalculatedBudgetResponse,
)


def make_valid_request() -> dict:
    return {
        "project_id": "PROJ-001",
        "budget_id": "ORC-001",
        "type_system": "SICRO",
        "monetary_base_date": "2026-01",
        "services": [
            {
                "id": "SERV-001",
                "code": "4011209",
                "description": "Execução de serviço",
                "unit": "m3",
                "quantity": "100.00",
                "compositions": [
                    {
                        "composition_id": "4011209",
                        "reference_base_date": "2026-01",
                        "factor": "1.00",
                    }
                ],
            }
        ],
        "overrides": {},
    }


def test_budget_calculation_request_accepts_valid_payload():
    request = BudgetCalculationRequestSchema.model_validate(
        make_valid_request()
    )

    assert request.project_id == "PROJ-001"
    assert request.budget_id == "ORC-001"
    assert request.type_system == "SICRO"
    assert request.monetary_base_date == "2026-01"

    assert len(request.services) == 1
    assert request.services[0].id == "SERV-001"
    assert len(request.services[0].compositions) == 1


def test_budget_calculation_request_preserves_decimal_types():
    request = BudgetCalculationRequestSchema.model_validate(
        make_valid_request()
    )

    service = request.services[0]
    composition = service.compositions[0]

    assert isinstance(service.quantity, Decimal)
    assert service.quantity == Decimal("100.00")

    assert isinstance(composition.factor, Decimal)
    assert composition.factor == Decimal("1.00")


def test_budget_id_is_optional():
    payload = make_valid_request()
    payload.pop("budget_id")

    request = BudgetCalculationRequestSchema.model_validate(payload)

    assert request.budget_id is None


def test_overrides_is_optional():
    payload = make_valid_request()
    payload.pop("overrides")

    request = BudgetCalculationRequestSchema.model_validate(payload)

    assert request.overrides == {}


@pytest.mark.parametrize(
    "field",
    [
        "project_id",
        "type_system",
        "monetary_base_date",
        "services",
    ],
)
def test_required_request_fields_are_required(field):
    payload = make_valid_request()
    payload.pop(field)

    with pytest.raises(ValidationError):
        BudgetCalculationRequestSchema.model_validate(payload)


def test_budget_calculation_response_with_budget():
    payload = {
        "calculation_id": "CALC-001",
        "budget": {
            "id": "ORC-001",
            "project_id": "PROJ-001",
            "type_system": "SICRO",
            "monetary_base_date": "2026-01",
            "total_cost": "123456.78",
            "services": [
                {
                    "id": "SERV-001",
                    "code": "4011209",
                    "description": "Execução de serviço",
                    "unit": "m3",
                    "quantity": "100.00",
                    "unit_cost": "1234.57",
                    "total_cost": "123456.78",
                    "compositions": [
                        {
                            "composition_id": "4011209",
                            "reference_base_date": "2026-01",
                            "factor": "1.00",
                            "unit_cost": "1234.57",
                            "total_cost": "123456.78",
                        }
                    ],
                }
            ],
        },
        "issues": [],
    }

    response = BudgetCalculationResponse.model_validate(payload)

    assert response.calculation_id == "CALC-001"
    assert response.budget is not None
    assert response.budget.id == "ORC-001"
    assert response.budget.total_cost == Decimal("123456.78")
    assert response.issues == []


def test_budget_calculation_response_with_null_budget_and_issues():
    payload = {
        "calculation_id": "CALC-002",
        "budget": None,
        "issues": [
            {
                "code": "SERVICE_ITEM_ZERO_QUANTITY",
                "severity": "CRITICAL",
                "entity": "ServiceItem",
                "entity_id": "SERV-001",
                "message": (
                    "Informe uma quantidade maior que zero "
                    "ou remova o ServiceItem."
                ),
            }
        ],
    }

    response = BudgetCalculationResponse.model_validate(payload)

    assert response.calculation_id == "CALC-002"
    assert response.budget is None

    assert len(response.issues) == 1
    assert response.issues[0].code == "SERVICE_ITEM_ZERO_QUANTITY"
    assert response.issues[0].severity == "CRITICAL"


def test_missing_required_field_returns_http_422():
    app = FastAPI()

    @app.post("/budgets/calculate")
    def calculate(request: BudgetCalculationRequestSchema):
        return request

    client = TestClient(app)

    payload = make_valid_request()
    payload.pop("project_id")

    response = client.post(
        "/budgets/calculate",
        json=payload,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["detail"]
    assert any(
        error["loc"][-1] == "project_id"
        for error in body["detail"]
    )