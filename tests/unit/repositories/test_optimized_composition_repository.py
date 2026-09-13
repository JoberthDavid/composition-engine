from unittest.mock import Mock

from app.repositories.optimized_composition_repository import (
    OptimizedCompositionRepository,
)

COMPOSITION_DATA_BASE = "2021-10-01"

def test_get_child_codes_by_composition_codes_returns_empty_for_empty_codes():
    api_client = Mock()

    repository = OptimizedCompositionRepository(
        api_client=api_client,
    )

    result = repository.get_child_codes_by_composition_codes([])

    assert result == {}

    api_client.get_composition_activities_by_codes.assert_not_called()
    api_client.get_composition_transports_by_codes.return_value = []

def test_get_child_codes_by_composition_codes_calls_api_client_once():
    api_client = Mock()

    api_client.get_composition_transports_by_codes.return_value = []

    api_client.get_composition_activities_by_codes.return_value = [
        {
            "composition_code": "0919013",
            "generic_item": "0407819",
            "input_quantity": "545.31643",
        },
        {
            "composition_code": "0919013",
            "generic_item": "3807864",
            "input_quantity": "140.00000",
        },
    ]

    repository = OptimizedCompositionRepository(
        api_client=api_client,
        composition_data_base=COMPOSITION_DATA_BASE,
    )

    result = repository.get_child_codes_by_composition_codes(
        ["0919013"]
    )

    assert result == {
        "0919013": [
            "0407819",
            "3807864",
        ]
    }

    api_client.get_composition_activities_by_codes.assert_called_once_with(
        ["0919013"],
        data_base=COMPOSITION_DATA_BASE,
    )

    api_client.get_composition_transports_by_codes.assert_called_once_with(
        ["0919013"],
        data_base=COMPOSITION_DATA_BASE,
    )

def test_get_child_codes_by_composition_codes_deduplicates_input_codes():
    api_client = Mock()

    api_client.get_composition_activities_by_codes.return_value = []
    api_client.get_composition_transports_by_codes.return_value = []

    repository = OptimizedCompositionRepository(
        api_client=api_client,
    )

    repository.get_child_codes_by_composition_codes(
        [
            "0919013",
            "0919013",
            "3807864",
            "3807864",
        ]
    )

    api_client.get_composition_activities_by_codes.assert_called_once_with(
        [
            "0919013",
            "3807864",
        ],
        data_base=None,
    )

def test_get_child_codes_by_composition_codes_groups_children_by_composition():
    api_client = Mock()

    api_client.get_composition_transports_by_codes.return_value = []
    api_client.get_composition_activities_by_codes.return_value = [
        {
            "composition_code": "0919013",
            "generic_item": "0407819",
            "input_quantity": "1.00000",
        },
        {
            "composition_code": "0919013",
            "generic_item": "3807864",
            "input_quantity": "2.00000",
        },
        {
            "composition_code": "3807864",
            "generic_item": "1107892",
            "input_quantity": "3.00000",
        },
    ]

    repository = OptimizedCompositionRepository(
        api_client=api_client,
    )

    result = repository.get_child_codes_by_composition_codes(
        [
            "0919013",
            "3807864",
        ]
    )

    assert result == {
        "0919013": [
            "0407819",
            "3807864",
        ],
        "3807864": [
            "1107892",
        ],
    }


def test_get_child_codes_by_composition_codes_removes_duplicate_relationships():
    api_client = Mock()

    api_client.get_composition_transports_by_codes.return_value = []
    api_client.get_composition_activities_by_codes.return_value = [
        {
            "composition_code": "0919013",
            "generic_item": "0407819",
            "input_quantity": "1.00000",
        },
        {
            "composition_code": "0919013",
            "generic_item": "0407819",
            "input_quantity": "1.00000",
        },
    ]

    repository = OptimizedCompositionRepository(
        api_client=api_client,
    )

    result = repository.get_child_codes_by_composition_codes(
        ["0919013"]
    )

    assert result == {
        "0919013": [
            "0407819",
        ]
    }

def test_get_child_codes_by_composition_codes_includes_tf_transports():
    api_client = Mock()

    api_client.get_composition_activities_by_codes.return_value = []

    api_client.get_composition_transports_by_codes.return_value = [
        {
            "composition_code": "0407819",
            "input_group": "TF",
            "generic_item": "5914655",
        },
        {
            "composition_code": "0407819",
            "input_group": "LN",
            "generic_item": "5914449",
        },
        {
            "composition_code": "0407819",
            "input_group": "RP",
            "generic_item": "5914464",
        },
        {
            "composition_code": "0407819",
            "input_group": "PV",
            "generic_item": "5914479",
        },
        {
            "composition_code": "0407819",
            "input_group": "FR",
            "generic_item": "algum_codigo",
        },
    ]

    repository = OptimizedCompositionRepository(
        api_client=api_client,
    )

    result = repository.get_child_codes_by_composition_codes(
        ["0407819"]
    )

    assert result == {
        "0407819": [
            "5914655",
        ]
    }