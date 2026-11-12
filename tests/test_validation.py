import pytest

from ec_core import ValidationError, validate_inputs
from test_core import make
from ec_core import Mode

OK = dict(current_A=1.0, voltage_V=10.0, time_min=30.0, volume_L=1.0, area_cm2=100.0,
          phi=1.0, c0_mg_L=1500.0, c_mg_L=600.0)


def check(**kw):
    return validate_inputs(**{**OK, **kw})


def test_clean_input():
    assert check() == ([], [])


@pytest.mark.parametrize("field", list(OK))
@pytest.mark.parametrize("value", [0, -1, None, float("nan"), float("inf")])
def test_non_positive_rejected(field, value):
    errors, _ = check(**{field: value})
    assert len(errors) == 1


def test_negative_price_rejected_zero_allowed():
    assert check(price_electricity=-1)[0]
    assert check(price_electricity=0, price_electrode=0) == ([], [])


def test_continuous_requires_flow_not_time():
    assert check(continuous=True, flow_L_h=None)[0]
    assert check(continuous=True, flow_L_h=0)[0]
    assert check(continuous=True, flow_L_h=2.0, time_min=None) == ([], [])


@pytest.mark.parametrize("kw,n", [
    (dict(current_A=10.0), 0), (dict(current_A=10.01, area_cm2=1000), 1),
    (dict(voltage_V=30.0), 0), (dict(voltage_V=30.1), 1),
    (dict(area_cm2=1000.0), 0), (dict(area_cm2=1001.0), 1),  # j = 1 / <1 mA/cm2
    (dict(area_cm2=10.0), 0), (dict(area_cm2=9.9), 1),  # j = 100 / >100
    (dict(phi=0.8), 0), (dict(phi=0.79), 1), (dict(phi=2.0), 0), (dict(phi=2.01), 1),
    (dict(c_mg_L=1600.0), 1), (dict(c_mg_L=1500.0), 1),
])
def test_warning_thresholds(kw, n):
    errors, warnings = check(**kw)
    assert errors == [] and len(warnings) == n


def test_calculate_raises_instead_of_dividing_by_zero():
    for kw in (dict(V=0), dict(A=0), dict(C0=0), dict(t=0), dict(I=-1)):
        with pytest.raises(ValidationError):
            make(**kw).calculate()
    with pytest.raises(ValidationError):
        make(mode=Mode.CONTINUOUS, Q=None).calculate()


def test_c_not_below_c0_gives_no_specific_energy():
    r = make(C=1500).calculate()
    assert r.removal_pct == 0 and r.specific_energy_kWh_kg is None
    r = make(C=1800).calculate()
    assert r.removal_pct == pytest.approx(-20.0) and r.specific_energy_kWh_kg is None
