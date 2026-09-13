from app.infrastructure.composition_api_client import CompositionApiClient


client = CompositionApiClient()

codes = [
    "0919079",
    "0407819",
    "3807864",
]

for code in codes:
    result = client.get_compositions_by_codes([code])

    print()
    print(f"=== {code} ===")
    print(f"Quantidade: {len(result)}")

    for composition in result:
        print(composition["generic_item"])