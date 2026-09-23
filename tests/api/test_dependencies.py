from app.api.dependencies import get_composition_explosion
from app.services.composition_explosion import CompositionExplosion


def test_get_composition_explosion():
    explosion = get_composition_explosion()

    assert isinstance(explosion, CompositionExplosion)