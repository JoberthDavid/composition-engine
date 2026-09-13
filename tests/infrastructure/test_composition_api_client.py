from unittest.mock import Mock, patch

import pytest
import requests

from app.infrastructure.composition_api_client import (
    CompositionApiClient,
    CompositionApiError,
)

COMPOSITION_DATA_BASE = "2021-10-01"


def test_get_composition_activities_by_codes_returns_empty_for_empty_codes():
    client = CompositionApiClient()

    with patch("app.infrastructure.composition_api_client.requests.get") as mock_get:
        result = client.get_composition_activities_by_codes([])

    assert result == []
    mock_get.assert_not_called()

def test_get_composition_activities_by_codes_deduplicates_codes():
    client = CompositionApiClient()

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "results": [
            {
                "composition_code": "0919013",
                "generic_item": "0407819",
                "input_quantity": "1.00000",
            }
        ],
        "next": None,
    }

    with patch(
        "app.infrastructure.composition_api_client.requests.get",
        return_value=response,
    ) as mock_get:
        result = client.get_composition_activities_by_codes(
            ["0919013", "0919013", "0407819"]
        )

    assert result == response.json.return_value["results"]

    mock_get.assert_called_once()

    _, kwargs = mock_get.call_args

    assert kwargs["params"] == {
        "composition_code__in": "0919013,0407819",
        "limit": 1000,
    }

def test_get_composition_activities_by_codes_sends_data_base():
    client = CompositionApiClient()

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "results": [],
        "next": None,
    }

    with patch(
        "app.infrastructure.composition_api_client.requests.get",
        return_value=response,
    ) as mock_get:
        client.get_composition_activities_by_codes(
            ["0919013"],
            data_base=COMPOSITION_DATA_BASE,
        )

    _, kwargs = mock_get.call_args

    assert kwargs["params"] == {
        "composition_code__in": "0919013",
        "limit": 1000,
        "data_base": COMPOSITION_DATA_BASE,
    }

def test_get_composition_activities_by_codes_follows_pagination():
    client = CompositionApiClient()

    first_response = Mock()
    first_response.raise_for_status.return_value = None
    first_response.json.return_value = {
        "results": [{"generic_item": "A"}],
        "next": "https://example.com/compositions/activities/?page=2",
    }

    second_response = Mock()
    second_response.raise_for_status.return_value = None
    second_response.json.return_value = {
        "results": [{"generic_item": "B"}],
        "next": None,
    }

    with patch(
        "app.infrastructure.composition_api_client.requests.get",
        side_effect=[first_response, second_response],
    ) as mock_get:
        result = client.get_composition_activities_by_codes(
            ["0919013"]
        )

    assert result == [
        {"generic_item": "A"},
        {"generic_item": "B"},
    ]

    assert mock_get.call_count == 2

    first_call = mock_get.call_args_list[0]
    second_call = mock_get.call_args_list[1]

    assert first_call.kwargs["params"] == {
        "composition_code__in": "0919013",
        "limit": 1000,
    }

    assert second_call.args[0] == (
        "https://example.com/compositions/activities/?page=2"
    )
    assert second_call.kwargs["params"] is None


def test_get_composition_activities_by_codes_raises_composition_api_error():
    client = CompositionApiClient()

    with patch(
        "app.infrastructure.composition_api_client.requests.get",
        side_effect=requests.RequestException("connection error"),
    ):
        with pytest.raises(CompositionApiError):
            client.get_composition_activities_by_codes(
                ["0919013"]
            )