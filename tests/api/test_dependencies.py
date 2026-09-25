from datetime import date

from app.api.dependencies import get_composition_explosion
from app.schemas.composition_operation import (
    CompositionOperationContextRequest,
)
from app.services.composition_explosion import CompositionExplosion


def test_get_composition_explosion():
    context = CompositionOperationContextRequest(
        source_file_uf="DF",
        type_system="ON",
        methodology="SC",
        monetary_base_date=date(2021, 10, 1),
        reference_base_date=date(2021, 10, 1),
    )

    explosion = get_composition_explosion(
        context,
    )

    assert isinstance(explosion, CompositionExplosion)

def test_get_composition_explosion_passes_reference_base_date_to_root(
    monkeypatch,
) -> None:
    captured = {}

    class FakeRoot:
        def __init__(
            self,
            composition_data_base,
        ) -> None:
            captured["composition_data_base"] = (
                composition_data_base
            )

        def create_composition_explosion(
            self,
            context,
        ):
            captured["context"] = context

            return CompositionExplosion(
                resolver=None,
                context=context,
            )

    monkeypatch.setattr(
        "app.api.dependencies.CompositionRoot",
        FakeRoot,
    )

    context = CompositionOperationContextRequest(
        source_file_uf="DF",
        type_system="ON",
        methodology="SC",
        monetary_base_date=date(2021, 10, 1),
        reference_base_date=date(2021, 10, 1),
    )

    explosion = get_composition_explosion(
        context,
    )

    assert isinstance(
        explosion,
        CompositionExplosion,
    )
    assert captured["context"] is context