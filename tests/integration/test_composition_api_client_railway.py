from time import perf_counter

from app.infrastructure.composition_api_client import CompositionApiClient


COMPOSITION_CODES = [
    "0919013",
    "3807864",
    "1107892",
    "1106057",
    "1619004",
    "1619003",
    "0919079",
    "0407819",
    "2009619",
    "1109697",
    "1109669",
    "1109675",
    "1109622",
    "5914655",
    "5914647",
    "5914675",
    "1416201",
    "0903860",
    "0903818",
    "0903788",
    "0903789",
    "0903848",
    "0909617",
    "0909620",
    "4805754",
    "3107997",
    "4815671",
]

DATA_BASE = "2021-10-01"


def test_get_composition_activities_from_railway():
    """
    Valida a consulta real das atividades auxiliares no Railway.
    """

    client = CompositionApiClient()

    start_time = perf_counter()

    activities = client.get_composition_activities_by_codes(
        COMPOSITION_CODES,
        data_base=DATA_BASE,
    )

    duration = perf_counter() - start_time

    assert activities

    composition_codes = {
        activity["composition_code"]
        for activity in activities
    }

    activity_codes = {
        activity["generic_item"]
        for activity in activities
    }

    print()
    print("=== Railway - Composition Activities ===")
    print(f"Tempo da requisição: {duration:.3f} s")
    print(f"Registros retornados: {len(activities)}")
    print(f"Composições distintas: {len(composition_codes)}")
    print(f"Atividades distintas: {len(activity_codes)}")
    print(f"Composições encontradas: {sorted(composition_codes)}")
    print(f"Atividades encontradas: {sorted(activity_codes)}")

    assert composition_codes
    assert activity_codes


def test_get_composition_activities_from_railway_returns_expected_structure():
    """
    Valida a estrutura mínima dos registros retornados pelo Railway.
    """

    client = CompositionApiClient()

    activities = client.get_composition_activities_by_codes(
        COMPOSITION_CODES,
        data_base=DATA_BASE,
    )

    assert activities

    for activity in activities:
        assert "composition_code" in activity
        assert "generic_item" in activity
        assert "input_quantity" in activity

        assert activity["composition_code"]
        assert activity["generic_item"]
        assert activity["input_quantity"] is not None


def test_get_composition_activities_from_railway_contains_expected_composition():
    """
    Confirma que a composição raiz 0919013 possui atividades no retorno.
    """

    client = CompositionApiClient()

    activities = client.get_composition_activities_by_codes(
        COMPOSITION_CODES,
        data_base=DATA_BASE,
    )

    root_activities = [
        activity
        for activity in activities
        if activity["composition_code"] == "0919013"
    ]

    assert root_activities

    assert len(root_activities) == 12


def test_get_composition_activities_from_railway_contains_expected_activity_codes():
    """
    Confirma algumas relações de atividades conhecidas da composição 0919013.
    """

    client = CompositionApiClient()

    activities = client.get_composition_activities_by_codes(
        COMPOSITION_CODES,
        data_base=DATA_BASE,
    )

    root_activity_codes = {
        activity["generic_item"]
        for activity in activities
        if activity["composition_code"] == "0919013"
    }

    expected_activity_codes = {
        "0407819",
        "3807864",
        "1107892",
        "1106057",
        "1619004",
        "1619003",
        "0919079",
        "4805751",
        "3107997",
        "0903848",
        "0909617",
        "4815671",
    }

    assert root_activity_codes == expected_activity_codes


def test_get_composition_activities_from_railway_does_not_discover_unrequested_compositions():
    """
    Confirma que todas as composições retornadas pertencem ao conjunto solicitado.
    """

    client = CompositionApiClient()

    activities = client.get_composition_activities_by_codes(
        COMPOSITION_CODES,
        data_base=DATA_BASE,
    )

    requested_codes = set(COMPOSITION_CODES)

    returned_composition_codes = {
        activity["composition_code"]
        for activity in activities
    }

    unexpected_codes = returned_composition_codes - requested_codes

    assert not unexpected_codes