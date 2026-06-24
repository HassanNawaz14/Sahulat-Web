from datetime import date

from .schemas import WaterEstimateInput, EstimateResult, SlabLine, SlabWarning

WASA_LHR_RATES = {
    "residential": {"per_marla": 85, "minimum": 500},
    "commercial": {"per_marla": 220, "minimum": 1200},
}

KWSB_RATES = {
    "residential": {"per_marla": 95, "minimum": 600},
    "commercial": {"per_marla": 250, "minimum": 1500},
}

RATES_BY_PROVIDER = {
    "wasa_lhr": WASA_LHR_RATES,
    "kwsb": KWSB_RATES,
}

PROVIDER_LABELS = {
    "wasa_lhr": "WASA Lahore",
    "kwsb": "KW&SB",
}


def estimate_water(inp: WaterEstimateInput) -> EstimateResult:
    rates = RATES_BY_PROVIDER.get(inp.provider_code, WASA_LHR_RATES)
    type_rates = rates.get(inp.property_type, rates["residential"])

    marla = inp.property_size_marla or 5.0
    base_amount = max(type_rates["minimum"], marla * type_rates["per_marla"])

    breakdown = [
        SlabLine(
            label=f"Flat rate ({inp.property_type})",
            units=marla,
            rate=type_rates["per_marla"],
            amount=round(base_amount, 2),
        )
    ]

    taxes = round(base_amount * 0.05, 2)
    total = round(base_amount + taxes, 2)

    today = date.today()
    tariff_version = f"{today.year}-Q{(today.month - 1) // 3 + 1}"

    return EstimateResult(
        provider_code=inp.provider_code,
        utility_type="water",
        units=marla,
        estimated_total=total,
        tariff_version=tariff_version,
        breakdown=breakdown,
        taxes=taxes,
        slab_warning=None,
    )
