from datetime import date

from app.services.tariff import (
    compute_electricity_bill,
    get_active_tariffs,
    get_current_slab,
    get_next_slab,
)
from .schemas import ElectricityEstimateInput, EstimateResult, SlabLine, SlabWarning


def estimate_electricity(inp: ElectricityEstimateInput) -> EstimateResult:
    category = "protected" if inp.protected_customer else "unprotected"
    raw = compute_electricity_bill(inp.units, inp.provider_code, category)

    breakdown = [
        SlabLine(label=s["slab"], units=s["units"], rate=s["rate"], amount=s["cost"])
        for s in raw["slabs"]
    ]

    taxes = raw["fc_surcharge"] + raw["gst"] if inp.include_taxes else 0.0
    total = raw["energy_charges"] + taxes + raw["meter_rent"] + inp.arrears
    if inp.arrears > 0:
        breakdown.append(SlabLine(label="Arrears", units=0, rate=0, amount=inp.arrears))

    slab_warning = None
    current = raw.get("current_slab")
    if current:
        slabs = get_active_tariffs(inp.provider_code, category)
        next_s = get_next_slab(current, slabs)
        units_to_next = int(current["max"] - inp.units) + 1 if current.get("max") is not None else None
        if next_s and units_to_next is not None:
            slab_warning = SlabWarning(
                current_slab=f"{int(current['min'])}-{int(current['max'])}",
                next_slab_threshold=int(current["max"]) + 1,
                units_to_next_slab=units_to_next,
                estimated_extra_cost_if_crossed=round(next_s["rate"] - current["rate"], 2),
            )

    today = date.today()
    tariff_version = f"{today.year}-Q{(today.month - 1) // 3 + 1}"

    return EstimateResult(
        provider_code=inp.provider_code,
        utility_type="electricity",
        units=inp.units,
        estimated_total=round(total, 2),
        tariff_version=tariff_version,
        breakdown=breakdown,
        taxes=round(taxes, 2),
        slab_warning=slab_warning,
    )
