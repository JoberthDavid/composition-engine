from datetime import date
from unittest.mock import Mock


from app.repositories.monetary_value_repository import (
    MonetaryValueRepository,
)


def create_api_value(
    code: str,
    group: str,
    type_system: str,
) -> dict:
    """Cria um valor monetário simplificado para o teste."""
    return {
        "id": 1,
        "generic_item": code,
        "monetary_value": "100.0000",
        "type_system": type_system,
        "classification": "P",
        "group": group,
        "unit": {
            "unit": "UN",
        },
        "source_file": {
            "id": 1,
            "uf": "DF",
            "data_base": "2021-10-01",
        },
    }


def test_load_cache_queries_only_provided_codes() -> None:
    """Verifica que o cache consulta somente os códigos fornecidos."""
    api_client = Mock()

    def get_values(**kwargs):
        generic_item_in = kwargs["generic_item_in"]
        group = kwargs["group"]
        type_system = "NA" if group == "MA" else "ON"

        return [
            create_api_value(
                code=code,
                group=group,
                type_system=type_system,
            )
            for code in generic_item_in
        ]

    api_client.get_values.side_effect = get_values

    repository = MonetaryValueRepository(api_client=api_client)

    codes_by_group = {
        "EQ": {"E001", "E002"},
        "MO": {"P001"},
        "MA": {"M001", "M002"},
    }

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
    )

    assert api_client.get_values.call_count == 3

    calls = api_client.get_values.call_args_list

    requested_codes = {
        frozenset(call.kwargs["generic_item_in"])
        for call in calls
    }

    assert requested_codes == {
        frozenset({"E001", "E002"}),
        frozenset({"P001"}),
        frozenset({"M001", "M002"}),
    }


def test_load_cache_does_not_query_codes_outside_requested_groups() -> None:
    """Verifica que códigos não fornecidos não são consultados."""
    api_client = Mock()

    api_client.get_values.return_value = [
        create_api_value(
            code="E001",
            group="EQ",
            type_system="ON",
        )
    ]

    repository = MonetaryValueRepository(api_client=api_client)

    repository.load_cache(
        codes_by_group={
            "EQ": {"E001"},
            "MO": set(),
            "MA": set(),
        },
        type_system="ON",
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
    )

    api_client.get_values.assert_called_once()

    call = api_client.get_values.call_args

    assert call.kwargs["generic_item_in"] == ["E001"]
    assert call.kwargs["group"] == "EQ"
    assert call.kwargs["type_system"] == "ON"
    assert call.kwargs["source_file"] == "2021-10-01"


def test_load_cache_uses_na_for_materials() -> None:
    """Verifica que materiais utilizam o type system NA."""
    api_client = Mock()

    api_client.get_values.return_value = [
        create_api_value(
            code="M001",
            group="MA",
            type_system="NA",
        )
    ]

    repository = MonetaryValueRepository(api_client=api_client)

    repository.load_cache(
        codes_by_group={
            "EQ": set(),
            "MO": set(),
            "MA": {"M001"},
        },
        type_system="ON",
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
    )

    api_client.get_values.assert_called_once_with(
        generic_item_in=["M001"],
        type_system="NA",
        source_file="2021-10-01",
        group="MA",
    )

def test_load_cache_queries_only_new_codes_on_second_load() -> None:
    """Verifica o carregamento incremental do cache."""
    api_client = Mock()

    def get_values(**kwargs):
        generic_item_in = kwargs["generic_item_in"]
        group = kwargs["group"]
        type_system = "NA" if group == "MA" else "ON"

        return [
            create_api_value(
                code=code,
                group=group,
                type_system=type_system,
            )
            for code in generic_item_in
        ]

    api_client.get_values.side_effect = get_values

    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    context = {
        "type_system": "ON",
        "source_file_uf": "DF",
        "source_file_data_base": date(2021, 10, 1),
    }

    first_codes = {
        "EQ": {"E001", "E002"},
        "MO": {"P001"},
        "MA": {"M001"},
    }

    repository.load_cache(
        codes_by_group=first_codes,
        **context,
    )

    assert api_client.get_values.call_count == 3

    second_codes = {
        "EQ": {"E001", "E002", "E003"},
        "MO": {"P001", "P002"},
        "MA": {"M001", "M002"},
    }

    repository.load_cache(
        codes_by_group=second_codes,
        **context,
    )

    assert api_client.get_values.call_count == 6

    calls = api_client.get_values.call_args_list

    requested_codes = {
        frozenset(call.kwargs["generic_item_in"])
        for call in api_client.get_values.call_args_list
    }

    assert requested_codes == {
        frozenset({"E001", "E002"}),
        frozenset({"P001"}),
        frozenset({"M001"}),
        frozenset({"E003"}),
        frozenset({"P002"}),
        frozenset({"M002"}),
    }


def test_load_cache_clears_cache_when_context_changes() -> None:
    """Verifica a invalidação do cache quando o contexto muda."""
    api_client = Mock()

    def get_values(**kwargs):
        generic_item_in = kwargs["generic_item_in"]
        group = kwargs["group"]
        type_system = "NA" if group == "MA" else "ON"

        return [
            create_api_value(
                code=code,
                group=group,
                type_system=type_system,
            )
            for code in generic_item_in
        ]

    api_client.get_values.side_effect = get_values

    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    repository.load_cache(
        codes_by_group={
            "EQ": {"E001"},
            "MO": set(),
            "MA": set(),
        },
        type_system="ON",
        source_file_uf="DF",
        source_file_data_base=date(2021, 10, 1),
    )

    assert api_client.get_values.call_count == 1
    assert repository.cache_size == 1

    repository.load_cache(
        codes_by_group={
            "EQ": {"E001"},
            "MO": set(),
            "MA": set(),
        },
        type_system="ON",
        source_file_uf="GO",
        source_file_data_base=date(2021, 10, 1),
    )

    assert api_client.get_values.call_count == 2
    assert repository.cache_size == 1


def test_load_cache_batches_codes_by_group():
    api_client = Mock()
    api_client.get_values.return_value = []
    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    codes_by_group = {
        "EQ": {"E001", "E002", "E003"},
        "MO": {"M001", "M002"},
        "MA": {"A001", "A002", "A003", "A004"},
    }

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="GO",
        source_file_data_base=date(2026, 1, 1),
    )

    assert repository.api_client.get_values.call_count == 3

    calls = repository.api_client.get_values.call_args_list

    requested_codes = {
        frozenset(call.kwargs["generic_item_in"])
        for call in calls
    }

    assert requested_codes == {
        frozenset({"E001", "E002", "E003"}),
        frozenset({"M001", "M002"}),
        frozenset({"A001", "A002", "A003", "A004"}),
    }


def test_load_cache_splits_more_than_20_codes_into_batches():
    api_client = Mock()
    api_client.get_values.return_value = []
    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    equipment_codes = {
        f"E{index:03d}"
        for index in range(25)
    }

    codes_by_group = {
        "EQ": equipment_codes,
        "MO": set(),
        "MA": set(),
    }

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="GO",
        source_file_data_base=date(2026, 1, 1),
    )

    assert repository.api_client.get_values.call_count == 2

    calls = repository.api_client.get_values.call_args_list

    requested_codes = [
        call.kwargs["generic_item_in"]
        for call in calls
    ]

    assert len(requested_codes) == 2
    assert all(len(batch) <= 20 for batch in requested_codes)

    requested_codes_flat = set().union(*requested_codes)

    assert requested_codes_flat == equipment_codes


def test_load_cache_preserves_group_type_system():
    api_client = Mock()
    api_client.get_values.return_value = []
    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    codes_by_group = {
        "EQ": {"E001"},
        "MO": {"M001"},
        "MA": {"A001"},
    }

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="GO",
        source_file_data_base=date(2026, 1, 1),
    )

    calls = repository.api_client.get_values.call_args_list

    calls_by_group = {
        call.kwargs["group"]: call
        for call in calls
    }

    assert calls_by_group["EQ"].kwargs["type_system"] == "ON"
    assert calls_by_group["MO"].kwargs["type_system"] == "ON"
    assert calls_by_group["MA"].kwargs["type_system"] == "NA"

def test_load_cache_batches_only_missing_codes():
    api_client = Mock()

    def make_value_data(**kwargs):
        generic_item = kwargs["generic_item_in"]
        group = kwargs.get("group", "EQ")
        type_system = kwargs.get("type_system", "ON")
        source_file_uf = kwargs.get("source_file_uf")
        source_file_data_base = kwargs.get(
            "source_file_data_base"
        )

        source_file = None

        if (
            source_file_uf is not None
            or source_file_data_base is not None
        ):
            source_file = {
                "id": 1,
                "uf": source_file_uf,
                "data_base": (
                    source_file_data_base
                    if isinstance(
                        source_file_data_base,
                        str,
                    )
                    else (
                        source_file_data_base.isoformat()
                        if source_file_data_base is not None
                        else None
                    )
                ),
            }

        codes = generic_item

        return [
            {
                "id": code,
                "generic_item": code,
                "monetary_value": "100.00",
                "unit": "un",
                "classification": "PR",
                "group": group,
                "type_system": type_system,
                "source_file": source_file,
            }
            for code in codes
        ]

    api_client.get_values.side_effect = (
        make_value_data
    )

    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    codes_by_group = {
        "EQ": {"E001", "E002", "E003"},
    }

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="GO",
        source_file_data_base=date(2026, 1, 1),
    )

    first_call_count = (
        api_client.get_values.call_count
    )

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="GO",
        source_file_data_base=date(2026, 1, 1),
    )

    assert (
        api_client.get_values.call_count
        == first_call_count
    )