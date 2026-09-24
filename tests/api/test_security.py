from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.security import require_api_key


API_HEADERS = {
    "X-API-Key": "test-api-key",
}


def create_security_test_app() -> FastAPI:
    app = FastAPI()

    @app.get(
        "/protected",
        dependencies=[Depends(require_api_key)],
    )
    def protected():
        return {
            "status": "ok",
        }

    return app


def test_health_does_not_require_api_key():
    from app.main import app

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200


def test_protected_endpoint_requires_api_key():
    app = create_security_test_app()
    client = TestClient(app)

    response = client.get("/protected")

    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_api_key():
    app = create_security_test_app()
    client = TestClient(app)

    response = client.get(
        "/protected",
        headers={
            "X-API-Key": "invalid-key",
        },
    )

    assert response.status_code == 401


def test_protected_endpoint_accepts_valid_api_key():
    app = create_security_test_app()
    client = TestClient(app)

    response = client.get(
        "/protected",
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }