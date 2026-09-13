from collections import defaultdict

from app.services.composition_explosion import CompositionExplosion


def main() -> None:
    """Identifica os fatores de utilização encontrados para cada equipamento."""
    composition_code = "0919013"

    explosion = CompositionExplosion()
    result = explosion.explode(composition_code)

    uses_by_code: dict[str, set] = defaultdict(set)

    for node in result.root_node.walk():
        for composition_input in node.composition.equipments:
            uses_by_code[composition_input.code].add(
                composition_input.use
            )

    print()
    print("Fatores de utilização dos equipamentos")
    print("=" * 80)

    for code, uses in sorted(uses_by_code.items()):
        print(
            f"{code} | "
            f"use encontrados: "
            f"{', '.join(str(use) for use in sorted(uses, key=str))}"
        )


if __name__ == "__main__":
    main()