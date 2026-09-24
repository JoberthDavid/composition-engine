from datetime import date

from pydantic import BaseModel


class CompositionOperationContextRequest(BaseModel):
    """
    Contexto da operação de uma composição.

    Estes parâmetros definem o contexto em que a composição
    será resolvida e, quando aplicável, calculada.
    """

    source_file_uf: str
    type_system: str
    monetary_base_date: date
    reference_base_date: date