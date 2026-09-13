from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.domain.calculation_context import (
CalculationContext,
)
from app.domain.composition_input import (
CompositionInput,
)
from app.domain.monetary_value import (
MonetaryValue,
)
from app.services.monetary_value_resolver import (
MonetaryValueResolver,
)

# ====================================================================

# CONFIGURAÇÕES

# ====================================================================

MATERIAL_CODE = "1416201"

MATERIAL_QUANTITY = Decimal(
"10.0000"
)

CONTEXT = CalculationContext(

source_file_uf="DF",

source_file_data_base=date(
    2021,
    10,
    1,
),

type_system="ON",

)

# ====================================================================

# ARREDONDAMENTOS

# ====================================================================

def round_2(
    value: Decimal,
    ) -> Decimal:
    """
    Arredonda um valor para 2 casas decimais.
    """


    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def round_4(
    value: Decimal,
    ) -> Decimal:
    """
    Arredonda um valor para 4 casas decimais.
    """


    return value.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


# ====================================================================

# FORMATAÇÃO

# ====================================================================

def format_decimal(
    value: Decimal | None,
    places: int = 4,
    ) -> str:
    """
    Formata Decimal mantendo quantidade fixa
    de casas decimais.
    """

    if value is None:

        return "None"

    format_string = (
        f".{places}f"
    )

    return format(
        value,
        format_string,
    )


# ====================================================================

# TESTE

# ====================================================================

def main() -> None:

    print()

    print(
        "=" * 100
    )

    print(
        "TESTE DE CÁLCULO REAL DE MATERIAL"
    )

    print(
        "=" * 100
    )

    print()

# ================================================================
# MATERIAL
# ================================================================

material = CompositionInput(

    id=1,

    input_group="MA",

    generic_item=MATERIAL_CODE,

    generic_description=(
        "Material de teste"
    ),

    unit="cm²",

    input_quantity=MATERIAL_QUANTITY,

)

print(
    "MATERIAL"
)

print(
    "-" * 100
)

print()

print(
    "Código:"
)

print()

print(
    material.generic_item
)

print()

print(
    "Quantidade:"
)

print()

print(
    format_decimal(
        material.input_quantity,
        places=4,
    )
)

print()

# ================================================================
# RESOLUÇÃO DO VALOR MONETÁRIO
# ================================================================

print(
    "-" * 100
)

print(
    "RESOLUÇÃO DO VALOR MONETÁRIO"
)

print(
    "-" * 100
)

print()

resolver = MonetaryValueResolver()

monetary_value: MonetaryValue = (
    resolver.resolve(

        code=material.generic_item,

        context=CONTEXT,

    )
)

print(
    "Valor unitário encontrado:"
)

print()

print(
    format_decimal(
        monetary_value.monetary_value,
        places=4,
    )
)

print()

print(
    "UF:"
)

print()

print(
    monetary_value.source_file_uf
)

print()

print(
    "Data-base:"
)

print()

print(
    monetary_value.source_file_data_base
)

print()

print(
    "Sistema:"
)

print()

print(
    monetary_value.type_system
)

print()

# ================================================================
# CÁLCULO
# ================================================================

print(
    "-" * 100
)

print(
    "CÁLCULO"
)

print(
    "-" * 100
)

print()

result_raw = (

    material.input_quantity

    *

    monetary_value.monetary_value

)

print(
    "Quantidade:"
)

print()

print(
    format_decimal(
        material.input_quantity,
        places=4,
    )
)

print()

print(
    "×"
)

print()

print(
    "Valor monetário:"
)

print()

print(
    format_decimal(
        monetary_value.monetary_value,
        places=4,
    )
)

print()

print(
    "="
)

print()

print(
    "Resultado bruto:"
)

print()

print(
    format_decimal(
        result_raw,
        places=4,
    )
)

print()

# ================================================================
# ARREDONDAMENTO
# ================================================================

print(
    "-" * 100
)

print(
    "ARREDONDAMENTO"
)

print(
    "-" * 100
)

print()

result_rounded = round_4(
    result_raw
)

print(
    "round_4:"
)

print()

print(
    format_decimal(
        result_rounded,
        places=4,
    )
)

print()

print(
    "=" * 100
)

print(
    "TESTE CONCLUÍDO"
)

print(
    "=" * 100
)

print()

# ====================================================================

# EXECUÇÃO

# ====================================================================

if __name__ == "__main__":
    main()