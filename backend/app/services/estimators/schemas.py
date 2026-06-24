from pydantic import BaseModel, Field
from typing import Literal, Optional


class ElectricityEstimateInput(BaseModel):
    provider_code: str
    units: float = Field(..., ge=0, le=5000)
    phase_type: Literal["single_phase", "three_phase"]
    connection_type: Literal["residential"] = "residential"
    protected_customer: bool = False
    lifeline_customer: bool = False
    include_taxes: bool = True
    arrears: float = 0.0


class GasEstimateInput(BaseModel):
    provider_code: Literal["sngpl", "ssgc"]
    consumption_mmbtu: float = Field(..., ge=0, le=50)
    include_taxes: bool = True


class WaterEstimateInput(BaseModel):
    provider_code: str
    usage_units: Optional[float] = None
    property_type: Literal["residential", "commercial"]
    property_size_marla: Optional[float] = None


class SlabLine(BaseModel):
    label: str
    units: float
    rate: float
    amount: float


class SlabWarning(BaseModel):
    current_slab: str
    next_slab_threshold: Optional[int] = None
    units_to_next_slab: Optional[int] = None
    estimated_extra_cost_if_crossed: float


class EstimateResult(BaseModel):
    provider_code: str
    utility_type: str
    units: float
    estimated_total: float
    currency: str = "PKR"
    tariff_version: str
    breakdown: list[SlabLine]
    taxes: float
    slab_warning: Optional[SlabWarning] = None
