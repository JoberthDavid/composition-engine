import inspect

from app.repositories.composition_repository import (
    CompositionRepository,
)
from app.repositories.monetary_value_repository import (
    MonetaryValueRepository,
)
from app.repositories.optimized_composition_repository import (
    OptimizedCompositionRepository,
)
from app.services.composition_resolver import (
    CompositionResolver,
)
from app.services.monetary_value_resolver import (
    MonetaryValueResolver,
)


def test_composition_resolver_requires_repository() -> None:
    """
    O CompositionResolver não deve possuir um repositório implícito.

    A construção do CompositionRepository deve ocorrer no
    CompositionRoot.
    """

    signature = inspect.signature(
        CompositionResolver.__init__
    )

    repository_parameter = signature.parameters[
        "repository"
    ]

    assert (
        repository_parameter.default
        is inspect.Parameter.empty
    ), (
        "CompositionResolver deve exigir "
        "CompositionRepository explicitamente."
    )


def test_composition_resolver_does_not_construct_repository() -> None:
    """
    O CompositionResolver não deve instanciar
    CompositionRepository internamente.
    """

    source = inspect.getsource(
        CompositionResolver.__init__
    )

    assert "CompositionRepository()" not in source, (
        "CompositionResolver não deve construir "
        "CompositionRepository implicitamente."
    )


def test_monetary_value_resolver_requires_repository() -> None:
    """
    O MonetaryValueResolver não deve possuir um repositório implícito.

    A construção do MonetaryValueRepository deve ocorrer no
    CompositionRoot.
    """

    signature = inspect.signature(
        MonetaryValueResolver.__init__
    )

    repository_parameter = signature.parameters[
        "repository"
    ]

    assert (
        repository_parameter.default
        is inspect.Parameter.empty
    ), (
        "MonetaryValueResolver deve exigir "
        "MonetaryValueRepository explicitamente."
    )


def test_monetary_value_resolver_does_not_construct_repository() -> None:
    """
    O MonetaryValueResolver não deve instanciar
    MonetaryValueRepository internamente.
    """

    source = inspect.getsource(
        MonetaryValueResolver.__init__
    )

    assert "MonetaryValueRepository()" not in source, (
        "MonetaryValueResolver não deve construir "
        "MonetaryValueRepository implicitamente."
    )


def test_composition_repository_requires_api_client() -> None:
    """
    O CompositionRepository não deve construir
    CompositionApiClient internamente.
    """

    signature = inspect.signature(
        CompositionRepository.__init__
    )

    api_client_parameter = signature.parameters[
        "api_client"
    ]

    assert (
        api_client_parameter.default
        is inspect.Parameter.empty
    ), (
        "CompositionRepository deve exigir "
        "CompositionApiClient explicitamente."
    )


def test_optimized_composition_repository_requires_api_client() -> None:
    """
    O OptimizedCompositionRepository não deve construir
    CompositionApiClient internamente.
    """

    signature = inspect.signature(
        OptimizedCompositionRepository.__init__
    )

    api_client_parameter = signature.parameters[
        "api_client"
    ]

    assert (
        api_client_parameter.default
        is inspect.Parameter.empty
    ), (
        "OptimizedCompositionRepository deve exigir "
        "CompositionApiClient explicitamente."
    )


def test_monetary_value_repository_requires_api_client() -> None:
    """
    O MonetaryValueRepository não deve construir
    MonetaryValueApiClient internamente.
    """

    signature = inspect.signature(
        MonetaryValueRepository.__init__
    )

    api_client_parameter = signature.parameters[
        "api_client"
    ]

    assert (
        api_client_parameter.default
        is inspect.Parameter.empty
    ), (
        "MonetaryValueRepository deve exigir "
        "MonetaryValueApiClient explicitamente."
    )