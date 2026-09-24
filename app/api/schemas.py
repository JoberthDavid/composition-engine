from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RootCompositionSummary(BaseModel):
    code: str
    nodes: int


class AggregatedCompositionResponse(BaseModel):
    identifier: int
    group: str
    code: str
    description: str
    unit: str
    quantity: Decimal


class AggregatedInputResponse(BaseModel):
    identifier: int
    group: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    productive_quantity: Decimal
    unproductive_quantity: Decimal
    proprietary_item: str | None


class CompositionExplosionResponse(BaseModel):
    composition: RootCompositionSummary
    compositions: list[AggregatedCompositionResponse]
    inputs: list[AggregatedInputResponse]


class CompositionItemInputSchema(BaseModel):
    composition_id: str
    reference_base_date: str
    factor: Decimal


class ServiceItemInputSchema(BaseModel):
    id: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    compositions: list[CompositionItemInputSchema]


class BudgetCalculationRequestSchema(BaseModel):
    project_id: str
    type_system: str
    monetary_base_date: str
    services: list[ServiceItemInputSchema]
    budget_id: str | None = None
    overrides: dict = Field(default_factory=dict)


class ValidationIssueResponse(BaseModel):
    code: str
    severity: str
    entity: str
    entity_id: str
    message: str


class CompositionResultResponse(BaseModel):
    composition_id: str
    reference_base_date: str
    factor: Decimal
    unit_cost: Decimal
    total_cost: Decimal


class ServiceItemResultResponse(BaseModel):
    id: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    compositions: list[CompositionResultResponse]


class CalculatedBudgetResponse(BaseModel):
    id: str
    project_id: str
    type_system: str
    monetary_base_date: str
    total_cost: Decimal
    services: list[ServiceItemResultResponse]


class BudgetCalculationResponse(BaseModel):
    calculation_id: str
    budget: CalculatedBudgetResponse | None
    issues: list[ValidationIssueResponse]