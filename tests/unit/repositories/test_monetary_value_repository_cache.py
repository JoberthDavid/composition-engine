from datetime import date
from unittest.mock import Mock

from app.domain.monetary_value import MonetaryValue
from app.repositories.monetary_value_repository import (
    MonetaryValueRepository,
)


def make_value_data(
    code: str,
    group: str,
    type_system: str,
    value: str,
    value_id: int = 1,
) -> dict:
    """Cria um registro mínimo compatível com a API."""
    return {
        "id": value_id,
        "generic_item": code,
        "monetary_value": value,
        "unit": "un",
        "classification": "CT",
        "group": group,
        "type_system": type_system,
        "source_file": {
            "id": 1,
            "uf": "DF",
            "data_base": "2021-10-01",
        },
    }

def test_repository_cache_contract():
    api_client = Mock()

    api_client.get_values_by_code.side_effect = [
        [
            make_value_data(
                "EQ001",
                "EQ",
                "ON",
                "100.00",
            )
        ],
        [
            make_value_data(
                "MO001",
                "MO",
                "ON",
                "50.00",
            )
        ],
    ]

    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    # ------------------------------------------------------------
    # 1. get_by_code deve consultar a API na primeira chamada.
    # ------------------------------------------------------------

    first_result = repository.get_by_code("EQ001")

    assert len(first_result) == 1
    assert isinstance(first_result[0], MonetaryValue)
    assert first_result[0].generic_item == "EQ001"

    assert api_client.get_values_by_code.call_count == 1

    # ------------------------------------------------------------
    # 2. A segunda chamada deve utilizar o cache.
    # ------------------------------------------------------------

    second_result = repository.get_by_code("EQ001")

    assert second_result is first_result

    assert api_client.get_values_by_code.call_count == 1

    assert repository.cache_size == 1

    # ------------------------------------------------------------
    # 3. clear_cache deve remover o conteúdo e o contexto.
    # ------------------------------------------------------------

    repository.clear_cache()

    assert repository.cache_size == 0
    assert repository.is_cache_loaded is False

    assert repository.cache_context == {
        "source_file_uf": None,
        "source_file_data_base": None,
        "type_system": None,
    }


def test_load_cache_preserves_context_and_reuses_cached_codes():
    api_client = Mock()

    api_client.get_values.side_effect = [
        # Primeiro contexto: DF.
        [
            make_value_data(
                "EQ001",
                "EQ",
                "ON",
                "100.00",
            )
        ],
        [
            make_value_data(
                "MO001",
                "MO",
                "ON",
                "50.00",
            )
        ],
        [
            make_value_data(
                "MA001",
                "MA",
                "NA",
                "25.00",
            )
        ],

        # Segundo contexto: GO.
        [
            make_value_data(
                "EQ001",
                "EQ",
                "ON",
                "100.00",
            )
        ],
        [
            make_value_data(
                "MO001",
                "MO",
                "ON",
                "50.00",
            )
        ],
        [
            make_value_data(
                "MA001",
                "MA",
                "NA",
                "25.00",
            )
        ],
    ]

    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    context_date = date(2021, 10, 1)

    codes_by_group = {
        "EQ": {"EQ001"},
        "MO": {"MO001"},
        "MA": {"MA001"},
    }

    # ------------------------------------------------------------
    # Primeiro carregamento.
    # ------------------------------------------------------------

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="DF",
        source_file_data_base=context_date,
    )

    assert repository.cache_size == 3

    assert repository.cache_context == {
        "source_file_uf": "DF",
        "source_file_data_base": context_date,
        "type_system": "ON",
    }

    assert api_client.get_values.call_count == 3

    # ------------------------------------------------------------
    # Segundo carregamento com o mesmo contexto.
    #
    # Nenhum código deve ser consultado novamente.
    # ------------------------------------------------------------

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="DF",
        source_file_data_base=context_date,
    )

    assert repository.cache_size == 3
    assert api_client.get_values.call_count == 3

    # ------------------------------------------------------------
    # Novo contexto.
    #
    # O cache anterior deve ser invalidado.
    # ------------------------------------------------------------

    repository.load_cache(
        codes_by_group=codes_by_group,
        type_system="ON",
        source_file_uf="GO",
        source_file_data_base=context_date,
    )

    assert repository.cache_context == {
        "source_file_uf": "GO",
        "source_file_data_base": context_date,
        "type_system": "ON",
    }

    assert api_client.get_values.call_count == 6


def test_get_by_codes_uses_cache_and_queries_only_missing_codes():
    api_client = Mock()

    api_client.get_values.return_value = [
        make_value_data(
            "MA001",
            "MA",
            "NA",
            "25.00",
        ),
        make_value_data(
            "MA002",
            "MA",
            "NA",
            "30.00",
        ),
    ]

    repository = MonetaryValueRepository(
        api_client=api_client,
    )

    # Pré-carrega um código diretamente no cache.
    repository._cache["MA001"] = [
        MonetaryValue.from_api_data(
            make_value_data(
                "MA001",
                "MA",
                "NA",
                "25.00",
            )
        )
    ]

    result = repository.get_by_codes(
        ["MA001", "MA002"]
    )

    assert len(result) == 2

    assert {
        str(value.generic_item)
        for value in result
    } == {
        "MA001",
        "MA002",
    }

    api_client.get_values.assert_called_once_with(
        generic_item="MA002",
    )

    assert repository.cache_size == 2