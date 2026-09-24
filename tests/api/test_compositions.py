from decimal import Decimal
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api.dependencies import get_composition_explosion
from app.domain.aggregated_composition import AggregatedComposition
from app.domain.aggregated_input import AggregatedInput
from app.domain.composition import Composition
from app.domain.composition_node import CompositionNode
from app.domain.composition_explosion_result import (
    CompositionExplosionResult,
)
from app.main import app


client = TestClient(app)


def create_explosion_result() -> CompositionExplosionResult:
    composition = Composition(
        id=1,
        composition_group="C",
        generic_item="4011209",
        generic_description="Composição de teste",
        unit="m3",
        fic=Decimal("0"),
        production=Decimal("1"),
        equipments=[],
        workmen=[],
        materials=[],
        activities=[],
        transports=[],
    )

    root_node = CompositionNode(
        composition=composition,
    )

    aggregated_composition = AggregatedComposition(
        identifier=1,
        group="C",
        code="4011209",
        description="Composição de teste",
        unit="m3",
        quantity=Decimal("1.500"),
    )

    aggregated_input = AggregatedInput(
        identifier=10,
        group="EQ",
        code="E0001",
        description="Equipamento de teste",
        unit="h",
        quantity=Decimal("0"),
        productive_quantity=Decimal("1.250"),
        unproductive_quantity=Decimal("0.350"),
        proprietary_item=None,
    )

    return CompositionExplosionResult(
        root_node=root_node,
        compositions=[aggregated_composition],
        inputs=[aggregated_input],
    )


def test_explode_composition():
    explosion = Mock()
    explosion.explode.return_value = create_explosion_result()

    app.dependency_overrides[
        get_composition_explosion
    ] = lambda: explosion

    try:
        response = client.get(
            "/compositions/4011209/explosion",
            headers={
                "X-API-Key": "test-api-key",
            },
        )
        assert response.status_code == 200

        assert response.json() == {
            "composition": {
                "code": "4011209",
                "nodes": 1,
            },
            "compositions": [
                {
                    "identifier": 1,
                    "group": "C",
                    "code": "4011209",
                    "description": "Composição de teste",
                    "unit": "m3",
                    "quantity": "1.500",
                }
            ],
            "inputs": [
                {
                    "identifier": 10,
                    "group": "EQ",
                    "code": "E0001",
                    "description": "Equipamento de teste",
                    "unit": "h",
                    "quantity": "0",
                    "productive_quantity": "1.250",
                    "unproductive_quantity": "0.350",
                    "proprietary_item": None,
                }
            ],
        }

        explosion.explode.assert_called_once_with(
            "4011209"
        )

    finally:
        app.dependency_overrides.clear()

def test_explode_composition_returns_404_when_composition_is_not_found():
    explosion = Mock()
    explosion.explode.side_effect = ValueError(
        "Composition not found: 9999999"
    )

    app.dependency_overrides[
        get_composition_explosion
    ] = lambda: explosion

    try:
        response = client.get(
            "/compositions/9999999/explosion",
            headers={
                "X-API-Key": "test-api-key",
            },
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Composition not found: 9999999"
        }

        explosion.explode.assert_called_once_with(
            "9999999"
        )

    finally:
        app.dependency_overrides.pop(
            get_composition_explosion,
            None,
        )

def test_explode_composition_propagates_unexpected_error():
    explosion = Mock()
    explosion.explode.side_effect = RuntimeError(
        "Erro interno inesperado"
    )

    app.dependency_overrides[
        get_composition_explosion
    ] = lambda: explosion

    try:
        try:
            client.get(
                "/compositions/4011209/explosion",
            headers={
                "X-API-Key": "test-api-key",
            },
            )
            assert False, "Era esperado RuntimeError"
        except RuntimeError as exc:
            assert str(exc) == "Erro interno inesperado"

        explosion.explode.assert_called_once_with(
            "4011209"
        )

    finally:
        app.dependency_overrides.pop(
            get_composition_explosion,
            None,
        )