"""Unit tests for Bill Estimator — P08.

Run: python -m pytest backend/tests/test_estimators.py -v
"""
import sys
sys.path.insert(0, "backend")

from app.services.estimators.schemas import (
    ElectricityEstimateInput,
    GasEstimateInput,
    WaterEstimateInput,
    EstimateResult,
    SlabLine,
    SlabWarning,
)


def test_electricity_estimate_schema_lesco():
    inp = ElectricityEstimateInput(
        provider_code="lesco",
        units=312,
        phase_type="single_phase",
        connection_type="residential",
        protected_customer=False,
        include_taxes=True,
        arrears=0,
    )
    assert inp.provider_code == "lesco"
    assert inp.units == 312
    assert inp.phase_type == "single_phase"
    assert inp.include_taxes is True


def test_electricity_estimate_schema_ke():
    inp = ElectricityEstimateInput(
        provider_code="kelectric",
        units=150,
        phase_type="three_phase",
    )
    assert inp.provider_code == "kelectric"
    assert inp.protected_customer is False
    assert inp.arrears == 0.0


def test_electricity_estimate_schema_validation():
    import pydantic
    try:
        ElectricityEstimateInput(
            provider_code="lesco",
            units=-1,
            phase_type="single_phase",
        )
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass

    try:
        ElectricityEstimateInput(
            provider_code="lesco",
            units=5001,
            phase_type="single_phase",
        )
        assert False, "Should have raised ValidationError for >5000"
    except pydantic.ValidationError:
        pass


def test_gas_estimate_schema():
    inp = GasEstimateInput(
        provider_code="sngpl",
        consumption_mmbtu=2.5,
        include_taxes=True,
    )
    assert inp.provider_code == "sngpl"
    assert inp.consumption_mmbtu == 2.5

    inp2 = GasEstimateInput(provider_code="ssgc", consumption_mmbtu=0.5)
    assert inp2.provider_code == "ssgc"


def test_water_estimate_schema():
    inp = WaterEstimateInput(
        provider_code="wasa_lhr",
        property_type="residential",
        property_size_marla=5,
    )
    assert inp.provider_code == "wasa_lhr"

    inp2 = WaterEstimateInput(
        provider_code="kwsb",
        property_type="commercial",
    )
    assert inp2.property_size_marla is None


def test_estimate_result_contract():
    result = EstimateResult(
        provider_code="lesco",
        utility_type="electricity",
        units=312,
        estimated_total=4280.0,
        tariff_version="2025-Q2",
        breakdown=[
            SlabLine(label="0-100", units=100, rate=7.74, amount=774),
            SlabLine(label="101-200", units=100, rate=10.06, amount=1006),
            SlabLine(label="201-300", units=100, rate=16.80, amount=1680),
            SlabLine(label="301-400", units=12, rate=20.15, amount=242),
        ],
        taxes=578.0,
        slab_warning=SlabWarning(
            current_slab="301-400",
            next_slab_threshold=401,
            units_to_next_slab=89,
            estimated_extra_cost_if_crossed=0,
        ),
    )
    assert result.currency == "PKR"
    assert len(result.breakdown) == 4
    assert result.slab_warning is not None
    assert result.slab_warning.units_to_next_slab == 89
    assert result.estimated_total == 4280.0


def test_estimate_result_no_warning():
    result = EstimateResult(
        provider_code="sngpl",
        utility_type="gas",
        units=2.5,
        estimated_total=3200.0,
        tariff_version="2025-Q2",
        breakdown=[SlabLine(label="1.0-2.0", units=1.0, rate=1250, amount=1250)],
        taxes=160.0,
        slab_warning=None,
    )
    assert result.slab_warning is None
    assert result.utility_type == "gas"


def test_electricity_estimate_zero_units():
    inp = ElectricityEstimateInput(
        provider_code="lesco",
        units=0,
        phase_type="single_phase",
    )
    assert inp.units == 0


def test_lifeline_customer():
    inp = ElectricityEstimateInput(
        provider_code="lesco",
        units=50,
        phase_type="single_phase",
        lifeline_customer=True,
    )
    assert inp.lifeline_customer is True
    assert inp.protected_customer is False


def test_arrears_included():
    inp = ElectricityEstimateInput(
        provider_code="lesco",
        units=200,
        phase_type="single_phase",
        arrears=1500.0,
    )
    assert inp.arrears == 1500.0


def test_water_default_marla():
    inp = WaterEstimateInput(
        provider_code="wasa_lhr",
        property_type="residential",
    )
    marla = inp.property_size_marla or 5.0
    assert marla == 5.0


def test_gas_estimate_without_taxes():
    inp = GasEstimateInput(
        provider_code="sngpl",
        consumption_mmbtu=1.0,
        include_taxes=False,
    )
    assert inp.include_taxes is False
