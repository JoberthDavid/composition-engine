from unittest.mock import Mock, patch

import pytest
import requests

from app.infrastructure.manifold_api_client import (
    ManifoldApiClient,
    ManifoldApiError,
)


def test_get_sends_bearer_token_and_params():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "results": [{"id": 1}],
    }

    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        return_value=response,
    ) as mock_request:
        client = ManifoldApiClient(
            base_url="http://manifold.test/",
            token="test-token",
            timeout=15,
        )

        result = client.get(
            "/api/test/",
            params={"code": "123"},
        )

    assert result == {
        "results": [{"id": 1}],
    }

    mock_request.assert_called_once_with(
        "GET",
        "http://manifold.test/api/test/",
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer test-token",
        },
        params={"code": "123"},
        timeout=15,
    )


def test_get_without_token_does_not_send_authorization_header():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"ok": True}

    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        return_value=response,
    ) as mock_request:
        client = ManifoldApiClient(
            base_url="http://manifold.test",
            token="",
        )

        result = client.get("/api/test/")

    assert result == {"ok": True}

    mock_request.assert_called_once_with(
        "GET",
        "http://manifold.test/api/test/",
        headers={
            "Accept": "application/json",
        },
        params=None,
        timeout=30,
    )


def test_post_sends_json_body():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "created": True,
    }

    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        return_value=response,
    ) as mock_request:
        client = ManifoldApiClient(
            base_url="http://manifold.test",
            token="test-token",
        )

        result = client.post(
            "/api/test/",
            json={"code": "123"},
            params={"dry_run": "true"},
        )

    assert result == {
        "created": True,
    }

    mock_request.assert_called_once_with(
        "POST",
        "http://manifold.test/api/test/",
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer test-token",
        },
        params={"dry_run": "true"},
        json={"code": "123"},
        timeout=30,
    )


def test_empty_response_returns_none():
    response = Mock()
    response.status_code = 204
    response.content = b""

    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        return_value=response,
    ):
        client = ManifoldApiClient(
            base_url="http://manifold.test",
        )

        result = client.get("/api/test/")

    assert result is None


@pytest.mark.parametrize(
    "status_code",
    [401, 403],
)
def test_authentication_errors_raise_manifold_api_error(
    status_code,
):
    response = Mock()
    response.status_code = status_code
    response.text = "Unauthorized"

    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        return_value=response,
    ):
        client = ManifoldApiClient(
            base_url="http://manifold.test",
            token="invalid-token",
        )

        with pytest.raises(
            ManifoldApiError,
            match="autenticação",
        ):
            client.get("/api/test/")


def test_http_error_raises_manifold_api_error():
    response = Mock()
    response.status_code = 500
    response.text = "Internal Server Error"

    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        return_value=response,
    ):
        client = ManifoldApiClient(
            base_url="http://manifold.test",
        )

        with pytest.raises(
            ManifoldApiError,
            match="HTTP 500",
        ):
            client.get("/api/test/")


def test_connection_error_raises_manifold_api_error():
    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        side_effect=requests.RequestException(
            "connection error"
        ),
    ):
        client = ManifoldApiClient(
            base_url="http://manifold.test",
        )

        with pytest.raises(
            ManifoldApiError,
            match="comunicar com o Manifold",
        ):
            client.get("/api/test/")


def test_invalid_json_raises_manifold_api_error():
    response = Mock()
    response.status_code = 200
    response.content = b"not-json"
    response.json.side_effect = ValueError(
        "invalid json"
    )

    with patch(
        "app.infrastructure.manifold_api_client.requests.request",
        return_value=response,
    ):
        client = ManifoldApiClient(
            base_url="http://manifold.test",
        )

        with pytest.raises(
            ManifoldApiError,
            match="JSON",
        ):
            client.get("/api/test/")