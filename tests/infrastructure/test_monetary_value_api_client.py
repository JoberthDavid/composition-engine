from unittest.mock import Mock

import pytest

from app.infrastructure.manifold_api_client import (
    ManifoldApiError,
)
from app.infrastructure.monetary_value_api_client import (
    MonetaryValueApiClient,
    MonetaryValueApiError,
)


VALUES_PATH = (
    "/api/integrations/"
    "scraper/buscar-valores-monetarios/"
)


def test_get_values_by_code_sends_generic_item():
    manifold_client = Mock()

    manifold_client.get.return_value = {
        "results": [
            {
                "generic_item": "0919013",
                "monetary_value": "124841.9800",
            }
        ],
        "next": None,
    }

    client = MonetaryValueApiClient(
        manifold_client=manifold_client,
    )

    result = client.get_values_by_code("0919013")

    assert result == [
        {
            "generic_item": "0919013",
            "monetary_value": "124841.9800",
        }
    ]

    manifold_client.get.assert_called_once_with(
        VALUES_PATH,
        params={
            "generic_item": "0919013",
        },
    )


def test_get_values_sends_all_filters():
    manifold_client = Mock()

    manifold_client.get.return_value = {
        "results": [],
        "next": None,
    }

    client = MonetaryValueApiClient(
        manifold_client=manifold_client,
    )

    client.get_values(
        generic_item="0919013",
        generic_item_in=["0919013", "0919014"],
        type_system="ON",
        source_file="2",
        classification="PC",
        group="CO",
        unit="un",
    )

    manifold_client.get.assert_called_once_with(
        VALUES_PATH,
        params={
            "generic_item": "0919013",
            "generic_item__in": "0919013,0919014",
            "type_system": "ON",
            "source_file": "2",
            "classification": "PC",
            "group": "CO",
            "unit": "un",
        },
    )


def test_get_values_ignores_empty_filters():
    manifold_client = Mock()

    manifold_client.get.return_value = {
        "results": [],
        "next": None,
    }

    client = MonetaryValueApiClient(
        manifold_client=manifold_client,
    )

    client.get_values(
        generic_item="0919013",
        generic_item_in=[],
        type_system="",
        source_file=None,
        classification="",
        group=None,
        unit="",
    )

    manifold_client.get.assert_called_once_with(
        VALUES_PATH,
        params={
            "generic_item": "0919013",
        },
    )


def test_get_values_follows_pagination():
    manifold_client = Mock()

    manifold_client.get.side_effect = [
        {
            "results": [
                {"generic_item": "A"},
            ],
            "next": "https://example.com/page-2",
        },
        {
            "results": [
                {"generic_item": "B"},
            ],
            "next": None,
        },
    ]

    client = MonetaryValueApiClient(
        manifold_client=manifold_client,
    )

    result = client.get_values(
        generic_item="0919013",
    )

    assert result == [
        {"generic_item": "A"},
        {"generic_item": "B"},
    ]

    assert manifold_client.get.call_count == 2

    first_call = manifold_client.get.call_args_list[0]
    second_call = manifold_client.get.call_args_list[1]

    assert first_call.args == (
        VALUES_PATH,
    )

    assert first_call.kwargs == {
        "params": {
            "generic_item": "0919013",
        },
    }

    assert second_call.args == (
        "https://example.com/page-2",
    )

    assert second_call.kwargs == {}


def test_get_values_wraps_manifold_api_error():
    manifold_client = Mock()

    manifold_client.get.side_effect = ManifoldApiError(
        "connection error"
    )

    client = MonetaryValueApiClient(
        manifold_client=manifold_client,
    )

    with pytest.raises(MonetaryValueApiError):
        client.get_values(
            generic_item="0919013",
        )


def test_get_values_by_code_returns_empty_when_no_results():
    manifold_client = Mock()

    manifold_client.get.return_value = {
        "results": [],
        "next": None,
    }

    client = MonetaryValueApiClient(
        manifold_client=manifold_client,
    )

    result = client.get_values_by_code("0919013")

    assert result == []