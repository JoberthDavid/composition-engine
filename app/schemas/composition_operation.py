from datetime import date
from typing import Literal

from pydantic import BaseModel


class CompositionOperationContextRequest(BaseModel):
    """
    Contexto da operação de uma composição.

    Estes parâmetros definem o contexto em que a composição
    será resolvida e, quando aplicável, calculada.
    """

    source_file_uf: str
    type_system: Literal["ON", "DS", "NA"]
    methodology: Literal["SC", "SN"]
    monetary_base_date: date
    reference_base_date: date