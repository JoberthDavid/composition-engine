from app.composition_root import CompositionRoot
from app.services.composition_explosion import CompositionExplosion


def get_composition_explosion() -> CompositionExplosion:
    """
    Fornece uma instância de CompositionExplosion
    configurada pelo CompositionRoot.

    A API não conhece as implementações concretas
    das dependências de infraestrutura.
    """

    root = CompositionRoot()

    return root.create_composition_explosion()