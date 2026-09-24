from fastapi.testclient import TestClient

from app.main import app


def test_calculate_composition_0919013() -> None:
    client = TestClient(app)

    response = client.post(
        "/compositions/calculate",
        headers={
            "X-API-Key": "test-api-key",
        },
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