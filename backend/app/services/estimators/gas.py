from datetime import date

from .schemas import GasEstimateInput, EstimateResult, SlabLine, SlabWarning

GST_GAS = 0.05
SNGPL_METER_RENT = 50.0
SSGC_METER_RENT = 50.0

SNGPL_SLABS = [
    {"min": 0,   "max": 0.5,  "rate": 850},
    {"min": 0.5, "max": 1.0,  "rate": 1050},
    {"min": 1.0, "max": 2.0,  "rate": 1250},
    {"min": 2.0, "max": 3.0,  "rate": 1600},
    {"min": 3.0, "max": None, "rate": 2000},
]

SSGC_SLABS = [
    {"min": 0,   "max": 0.5,  "rate": 850},
    {"min": 0.5, "max": 1.0,  "rate": 1050},
    {"min": 1.0, "max": 2.0,  "rate": 1250},
    {"min": 2.0, "max": 3.0,  "rate": 1600},
    {"min": 3.0, "max": None, "rate": 2000},
]

SLABS_BY_PROVIDER = {
    "sngpl": SNGPL_SLABS,
    "ssgc": SSGC_SLABS,
}

METER_RENT_BY_PROVIDER = {
    "sngpl": SNGPL_METER_RENT,
    "ssgc": SSGC_METER_RENT,
}


def estimate_gas(inp: GasEstimateInput) -> EstimateResult:
    slabs = SLABS_BY_PROVIDER[inp.provider_code]
    meter_rent = METER_RENT_BY_PROVIDER[inp.provider_code]

    units_remaining = inp.consumption_mmbtu
    energy_total = 0.0
    breakdown_lines = []
    current_slab_label = None

    for slab in slabs:
        if units_remaining <= 0:
            break
        slab_min = slab["min"]
        slab_max = slab["max"] if slab["max"] is not None else float("inf")
        slab_units = min(units_remaining, slab_max - slab_min)
        line_amount = round(slab_units * slab["rate"], 2)
        energy_total += line_amount
        label = f"{slab_min}-{slab['max']}" if slab["max"] else f"{slab_min}+"
        breakdown_lines.append(SlabLine(label=label, units=round(slab_units, 4), rate=slab["rate"], amount=line_amount))
        current_slab_label = label
        units_remaining -= slab_units

    gst = round(energy_total * GST_GAS, 2) if inp.include_taxes else 0.0
    total = round(energy_total + gst + meter_rent, 2)

    slab_warning = None
    for slab in slabs:
        if slab["max"] is not None and inp.consumption_mmbtu >= slab["min"] and inp.consumption_mmbtu < slab["max"]:
            next_idx = slabs.index(slab) + 1
            if next_idx < len(slabs) and slabs[next_idx]:
                next_s = slabs[next_idx]
                units_to_next = round(next_s["min"] - inp.consumption_mmbtu, 4)
                if units_to_next > 0:
                    extra = round(next_s["rate"] - slab["rate"], 2)
                    slab_warning = SlabWarning(
                        current_slab=current_slab_label or f"{slab['min']}-{slab['max']}",
                        next_slab_threshold=int(next_s["min"]) if next_s["min"] == int(next_s["min"]) else next_s["min"],
                        units_to_next_slab=units_to_next,
                        estimated_extra_cost_if_crossed=extra,
                    )
            break
        if slab["max"] is None and inp.consumption_mmbtu >= slab["min"]:
            break

    today = date.today()
    tariff_version = f"{today.year}-Q{(today.month - 1) // 3 + 1}"

    return EstimateResult(
        provider_code=inp.provider_code,
        utility_type="gas",
        units=inp.consumption_mmbtu,
        estimated_total=total,
        tariff_version=tariff_version,
        breakdown=breakdown_lines,
        taxes=round(gst, 2),
        slab_warning=slab_warning,
    )
