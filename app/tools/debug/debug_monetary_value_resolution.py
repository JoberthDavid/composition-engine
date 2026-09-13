from datetime import date

from app.domain.calculation_context import (
CalculationContext,
)
from app.repositories.monetary_value_repository import (
MonetaryValueRepository,
)
from app.services.monetary_value_resolver import (
MonetaryValueResolver,
)

# ============================================================

# CONFIGURAÇÃO DO TESTE

# ============================================================

INPUT_CODE = "1416201"

# CONTEXT = CalculationContext(
#     source_file_uf="GO",
#     source_file_data_base=date(
#     2025,
#     7,
#     1,
#     ),
#     classification=None,
#     group=None,
#     type_system=None,
#     )

CONTEXT = CalculationContext(
    source_file_uf="DF",
    source_file_data_base=date(
        2021,
        10,
        1,
    ),
    type_system="ON",
)

# ============================================================

# FORMATAÇÃO

# ============================================================

SEPARATOR = "=" * 100
SUB_SEPARATOR = "-" * 100

def print_header(
    title: str,
    ) -> None:


    print()
    print(SEPARATOR)
    print(title)
    print(SEPARATOR)


def print_value(
    value,
    ) -> None:


    print(
        f"ID:                 {value.id}"
    )

    print(
        f"Código:             "
        f"{value.generic_item}"
    )

    print(
        f"Valor monetário:    "
        f"{value.monetary_value}"
    )

    print(
        f"Unidade:            "
        f"{value.unit}"
    )

    print(
        f"Classificação:      "
        f"{value.classification}"
    )

    print(
        f"Grupo:              "
        f"{value.group}"
    )

    print(
        f"Sistema:            "
        f"{value.type_system}"
    )

    print(
        f"UF:                 "
        f"{value.source_file_uf}"
    )

    print(
        f"Data-base:          "
        f"{value.source_file_data_base}"
    )


# ============================================================

# INÍCIO DO TESTE

# ============================================================

print_header(
    "TESTE DE RESOLUÇÃO DE VALOR MONETÁRIO"
    )

print()

print(
    "Código do insumo:"
    )

print(
    INPUT_CODE
    )

# ============================================================

# CONTEXTO

# ============================================================

print()
print(SUB_SEPARATOR)

print(
    "CALCULATION CONTEXT"
    )

print(SUB_SEPARATOR)

print()

print(
    f"UF: "
    f"{CONTEXT.source_file_uf}"
    )

print(
    f"Data-base: "
    f"{CONTEXT.source_file_data_base}"
    )

print(
    f"Classificação: "
    f"{CONTEXT.classification}"
    )

print(
f"Grupo: "
f"{CONTEXT.group}"
)

print(
    f"Sistema: "
    f"{CONTEXT.type_system}"
    )

# ============================================================

# REPOSITÓRIO

# ============================================================

repository = MonetaryValueRepository()

print()
print(SUB_SEPARATOR)

print(
    "CONSULTANDO VALORES MONETÁRIOS"
    )

print(SUB_SEPARATOR)

print()

monetary_values = (
    repository.get_by_code(
    INPUT_CODE
    )
    )

print(
    f"Quantidade de valores encontrados: "
    f"{len(monetary_values)}"
    )

# ============================================================

# VALORES DISPONÍVEIS

# ============================================================

print()
print(SUB_SEPARATOR)

print(
    "VALORES DISPONÍVEIS"
    )

print(SUB_SEPARATOR)

if not monetary_values:


    print()

    print(
        "Nenhum valor monetário encontrado."
    )


else:


    for index, value in enumerate(
        monetary_values,
        start=1,
    ):

        print()

        print(
            f"VALOR #{index}"
        )

        print_value(
            value
        )


# ============================================================

# RESOLVER

# ============================================================

resolver = MonetaryValueResolver(
    repository=repository
    )

print()
print(SEPARATOR)

print(
    "TENTANDO RESOLVER O VALOR MONETÁRIO"
    )

print(SEPARATOR)

try:


    resolved_value = (
        resolver.resolve(
            code=INPUT_CODE,
            context=CONTEXT,
        )
    )


    print()

    print(
        "VALOR SELECIONADO"
    )

    print()

    print_value(
        resolved_value
    )


except ValueError as error:


    print()

    print(
        "ERRO DURANTE A RESOLUÇÃO"
    )

    print()

    print(
        str(error)
    )


# ============================================================

# FINAL

# ============================================================

print()
print(SEPARATOR)

print(
"FIM DO TESTE"
)

print(SEPARATOR)
