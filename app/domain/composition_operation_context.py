from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CompositionOperationContext:
    source_file_uf: str
    type_system: str
    methodology: str
    monetary_base_date: date
    reference_base_date: date