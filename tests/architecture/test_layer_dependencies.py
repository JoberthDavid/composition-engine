import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "app"

DOMAIN_DIR = APP_ROOT / "domain"
SERVICES_DIR = APP_ROOT / "services"
REPOSITORIES_DIR = APP_ROOT / "repositories"
INFRASTRUCTURE_DIR = APP_ROOT / "infrastructure"


def _python_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.py"))


def _imports_from_directory(directory: Path) -> set[str]:
    """
    Retorna os módulos de app importados pelos arquivos
    Python do diretório informado.
    """

    imports: set[str] = set()

    for path in _python_files(directory):
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:

                    if alias.name.startswith("app."):
                        imports.add(alias.name)

            elif isinstance(node, ast.ImportFrom):

                if node.module is None:
                    continue

                if node.module.startswith("app."):
                    imports.add(node.module)

    return imports


def _imports_for_file(path: Path) -> set[str]:
    """
    Retorna os módulos de app importados por um único arquivo.
    """

    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    imports: set[str] = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:

                if alias.name.startswith("app."):
                    imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module is None:
                continue

            if node.module.startswith("app."):
                imports.add(node.module)

    return imports


# ============================================================
# DOMAIN
# ============================================================


def test_domain_does_not_depend_on_infrastructure():
    imports = _imports_from_directory(
        DOMAIN_DIR,
    )

    infrastructure_imports = {
        module
        for module in imports
        if module.startswith("app.infrastructure")
    }

    assert infrastructure_imports == set(), (
        "O domínio não deve depender diretamente da infraestrutura. "
        f"Dependências encontradas: {sorted(infrastructure_imports)}"
    )


def test_domain_does_not_depend_on_repositories():
    imports = _imports_from_directory(
        DOMAIN_DIR,
    )

    repository_imports = {
        module
        for module in imports
        if module.startswith("app.repositories")
    }

    assert repository_imports == set(), (
        "O domínio não deve depender de repositories. "
        f"Dependências encontradas: {sorted(repository_imports)}"
    )


def test_domain_does_not_depend_on_services():
    imports = _imports_from_directory(
        DOMAIN_DIR,
    )

    service_imports = {
        module
        for module in imports
        if module.startswith("app.services")
    }

    assert service_imports == set(), (
        "O domínio não deve depender de services. "
        f"Dependências encontradas: {sorted(service_imports)}"
    )


def test_domain_does_not_depend_on_http_library():
    """
    O domínio não deve conhecer detalhes do protocolo HTTP.
    """

    forbidden_modules = {
        "requests",
        "httpx",
        "aiohttp",
    }

    violations: list[str] = []

    for path in _python_files(DOMAIN_DIR):

        imports = _imports_for_file(path)

        for module in imports:
            if module in forbidden_modules:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} -> {module}"
                )

    assert violations == [], (
        "O domínio não deve depender diretamente de bibliotecas HTTP. "
        f"Violações: {violations}"
    )


# ============================================================
# SERVICES
# ============================================================


def test_services_do_not_depend_on_infrastructure():
    imports = _imports_from_directory(
        SERVICES_DIR,
    )

    infrastructure_imports = {
        module
        for module in imports
        if module.startswith("app.infrastructure")
    }

    assert infrastructure_imports == set(), (
        "Services não devem depender diretamente da infraestrutura. "
        f"Dependências encontradas: {sorted(infrastructure_imports)}"
    )


# ============================================================
# REPOSITORIES
# ============================================================


def test_repositories_do_not_depend_on_routes():
    imports = _imports_from_directory(
        REPOSITORIES_DIR,
    )

    route_imports = {
        module
        for module in imports
        if module.startswith("app.routes")
    }

    assert route_imports == set(), (
        "Repositories não devem depender da camada de rotas. "
        f"Dependências encontradas: {sorted(route_imports)}"
    )


# ============================================================
# RESOLVER
# ============================================================


def test_monetary_value_resolver_does_not_depend_on_infrastructure():
    path = (
        SERVICES_DIR
        / "monetary_value_resolver.py"
    )

    imports = _imports_for_file(path)

    infrastructure_imports = {
        module
        for module in imports
        if module.startswith("app.infrastructure")
    }

    assert infrastructure_imports == set(), (
        "MonetaryValueResolver não deve conhecer infraestrutura. "
        f"Dependências encontradas: {sorted(infrastructure_imports)}"
    )


# ============================================================
# COMPOSITION EXPLOSION
# ============================================================


def test_composition_explosion_does_not_depend_on_infrastructure():
    """
    CompositionExplosion é serviço de aplicação.

    "CompositionExplosion não deve depender diretamente
    de clients de infraestrutura."
    """

    path = (
        SERVICES_DIR
        / "composition_explosion.py"
    )

    imports = _imports_for_file(path)

    infrastructure_imports = {
        module
        for module in imports
        if module.startswith("app.infrastructure")
    }

    assert infrastructure_imports == set(), (
        "CompositionExplosion não deve depender diretamente "
        "de clients de infraestrutura. "
        f"Dependências encontradas: {sorted(infrastructure_imports)}"
    )