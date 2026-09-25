from datetime import date

from app.api.dependencies import (
    create_composition_calculation_service,
)
from app.schemas.composition_calculation import (
    CompositionCalculationRequest,
)
from app.services.composition_calculation_service import (
    CompositionCalculationService,
)


def _build_request() -> CompositionCalculationRequest:
    return CompositionCalculationRequest(
        composition_id="0919013",
        source_file_uf="DF",
        type_system="ON",
        methodology="SC",
        monetary_base_date=date(2021, 10, 1),
        reference_base_date=date(2021, 10, 1),
    )

def test_factory_passes_source_file_uf_to_calculation_context(
    monkeypatch,
) -> None:
    captured = {}

    class FakeService:
        pass

    class FakeRoot:
        def __init__(
            self,
            composition_data_base,
        ) -> None:
            captured["composition_data_base"] = (
                composition_data_base
            )

        def create_composition_calculation(
            self,
            calculation_context,
        ):
            captured["context"] = calculation_context
            return FakeService()


    monkeypatch.setattr(
        "app.api.dependencies.CompositionRoot",
        FakeRoot,
    )

    request = _build_request()

    create_composition_calculation_service(
        request
    )

    context = captured["context"]

    assert captured["context"].source_file_uf == "DF"


def test_factory_passes_monetary_base_date_to_calculation_context(
    monkeypatch,
) -> None:
    captured = {}

    class FakeService:
        pass

    class FakeRoot:
        def __init__(
            self,
            composition_data_base,
        ) -> None:
            pass

        def create_composition_calculation(
            self,
            calculation_context,
        ):
            captured["context"] = calculation_context
            return FakeService()

    monkeypatch.setattr(
        "app.api.dependencies.CompositionRoot",
        FakeRoot,
    )

    request = _build_request()

    create_composition_calculation_service(
        request
    )

    context = captured["context"]

    assert (
        context.source_file_data_base
        == date(2021, 10, 1)
    )


def test_factory_passes_reference_base_date_to_composition_root(
    monkeypatch,
) -> None:
    captured = {}

    class FakeService:
        pass

    class FakeRoot:
        def __init__(
            self,
            composition_data_base,
        ) -> None:
            captured["composition_data_base"] = (
                composition_data_base
            )

        def create_composition_calculation(
            self,
            calculation_context,
        ):
            captured["context"] = calculation_context
            return FakeService()

    monkeypatch.setattr(
        "app.api.dependencies.CompositionRoot",
        FakeRoot,
    )

    request = _build_request()

    create_composition_calculation_service(
        request
    )

    assert (
        captured["composition_data_base"]
        == "2021-10-01"
    )

def test_factory_returns_composition_calculation_service(
    monkeypatch,
) -> None:
    captured = {}

    class FakeRoot:
        def __init__(
            self,
            composition_data_base,
        ) -> None:
            pass

        def create_composition_calculation(
            self,
            calculation_context,
        ):
            captured["context"] = calculation_context

            return CompositionCalculationService(
                resolver=None,
                monetary_value_repository=None,
                composition_calculator=None,
                calculation_context=calculation_context,
            )

    monkeypatch.setattr(
        "app.api.dependencies.CompositionRoot",
        FakeRoot,
    )

    request = _build_request()

    service = create_composition_calculation_service(
        request
    )

    assert isinstance(
        service,
        CompositionCalculationService,
    )


def test_factory_passes_methodology_to_calculation_context(
    monkeypatch,
) -> None:
    captured = {}

    class FakeService:
        pass

    class FakeRoot:
        def __init__(
            self,
            composition_data_base,
        ) -> None:
            pass

        def create_composition_calculation(
            self,
            calculation_context,
        ):
            captured["context"] = calculation_context
            return FakeService()

    monkeypatch.setattr(
        "app.api.dependencies.CompositionRoot",
        FakeRoot,
    )

    request = _build_request()

    create_composition_calculation_service(
        request
    )

    assert (
        captured["context"].methodology
        == "SC"
    )