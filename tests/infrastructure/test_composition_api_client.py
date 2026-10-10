from unittest.mock import Mock

import pytest

from app.infrastructure.composition_api_client import (
    CompositionApiClient,
)
from app.infrastructure.manifold_api_client import (
    ManifoldApiError,
)


COMPOSITION_DATA_BASE = "2021-10-01"

ACTIVITIES_PATH = (
    "/api/integrations/"
    "scraper/buscar-atividades-composicao/"
)


def test_get_composition_activities_by_codes_returns_empty_for_empty_codes():
    manifold_client = Mock()

    client = CompositionApiClient(
        manifold_client=manifold_client,
    )

    result = client.get_composition_activities_by_codes([])

    assert result == []

    manifold_client.get.assert_not_called()


def test_get_composition_activities_by_codes_sends_codes():
    manifold_client = Mock()

    manifold_client.get.return_value = {
        "results": [
            {
                "composition_code": "0919013",
                "generic_item": "0407819",
                "input_quantity": "1.00000",
            }
        ],
        "next": None,
    }

    client = CompositionApiClient(
        manifold_client=manifold_client,
    )

    result = client.get_composition_activities_by_codes(
        ["0919013", "0919013", "0407819"]
    )

    assert result == [
        {
            "composition_code": "0919013",
            "generic_item": "0407819",
            "input_quantity": "1.00000",
        }
    ]

    manifold_client.get.assert_called_once_with(
        ACTIVITIES_PATH,
        params={
            "composition_code__in": "0919013,0919013,0407819",
            "limit": 1000,
        },
    )


def test_get_composition_activities_by_codes_sends_data_base():
    manifold_client = Mock()

    manifold_client.get.return_value = {
        "results": [],
        "next": None,
    }

    client = CompositionApiClient(
        manifold_client=manifold_client,
    )

    client.get_composition_activities_by_codes(
        ["0919013"],
        data_base=COMPOSITION_DATA_BASE,
    )

    manifold_client.get.assert_called_once_with(
        ACTIVITIES_PATH,
        params={
            "composition_code__in": "0919013",
            "limit": 1000,
            "data_base": COMPOSITION_DATA_BASE,
        },
    )


def test_get_composition_activities_by_codes_follows_pagination():
    manifold_client = Mock()

    first_response = {
        "results": [
            {"generic_item": "A"},
        ],
        "next": "https://example.com/page-2",
    }

    second_response = {
        "results": [
            {"generic_item": "B"},
        ],
        "next": None,
    }

    manifold_client.get.side_effect = [
        first_response,
        second_response,
    ]

    client = CompositionApiClient(
        manifold_client=manifold_client,
    )

    result = client.get_composition_activities_by_codes(
        ["0919013"]
    )

    assert result == [
        {"generic_item": "A"},
        {"generic_item": "B"},
    ]

    assert manifold_client.get.call_count == 2

    first_call = manifold_client.get.call_args_list[0]
    second_call = manifold_client.get.call_args_list[1]

    assert first_call.args == (
        ACTIVITIES_PATH,
    )

    assert first_call.kwargs == {
        "params": {
            "composition_code__in": "0919013",
            "limit": 1000,
        },
    }

    assert second_call.args == (
        "https://example.com/page-2",
    )

    assert second_call.kwargs == {}


def test_get_composition_activities_by_codes_propagates_manifold_api_error():
    manifold_client = Mock()

    manifold_client.get.side_effect = ManifoldApiError(
        "connection error"
    )

    client = CompositionApiClient(
        manifold_client=manifold_client,
    )

    with pytest.raises(ManifoldApiError):
        client.get_composition_activities_by_codes(
            ["0919013"]
        )