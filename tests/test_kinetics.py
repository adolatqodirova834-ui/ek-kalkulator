import math

import pytest

from ec_core import Electrode, Experiment, Reactor, ValidationError, analyze, linear_fit, time_for_removal

T = [0, 10, 20, 30, 40, 50, 60]
C = [1500, 1120, 820, 600, 450, 340, 260]


@pytest.fixture
def res():
    return analyze(T, C)[0]


def test_reference_first_order(res):
    assert res.k1 == pytest.approx(0.02944, abs=5e-6)
    assert res.first.r2 == pytest.approx(0.9993, abs=5e-5)
    assert time_for_removal(80, res.k1) == pytest.approx(54.7, abs=0.05)
    assert res.half_life_min == pytest.approx(math.log(2) / res.k1)
    assert res.half_life_min == pytest.approx(23.55, abs=0.01)


def test_best_model_is_higher_r2(res):
    assert res.first.r2 > res.second.r2
    assert res.best == "first"


def test_second_order_data_selects_second():
    c0, k2 = 1000.0, 2e-5
    cs = [1 / (1 / c0 + k2 * t) for t in T]
    r, _ = analyze(T, cs)
    assert r.best == "second"
    assert r.k2 == pytest.approx(k2, rel=1e-9)
    assert r.second.r2 == pytest.approx(1.0)


def test_point_table(res):
    p = res.points[3]  # t = 30, C = 600
    assert res.c0_mg_L == 1500
    assert p.c_ratio == pytest.approx(0.4)
    assert p.removal_pct == pytest.approx(60.0)
    assert p.ln_c0_c == pytest.approx(math.log(2.5))
    assert p.inv_diff == pytest.approx(1 / 600 - 1 / 1500)
    assert res.points[0].ln_c0_c == 0 and res.points[0].inv_diff == 0
    assert p.dose_mg_L is None


def test_point_table_with_experiment():
    exp = Experiment(Electrode.of("Al", 100), Reactor(1.0), 1.0, 10.0, 30.0, 1500, 600)
    r, _ = analyze(T, C, exp)
    p = r.points[3]
    assert p.dose_mg_L == pytest.approx(167.8, abs=0.05)
    assert p.charge_C_L == pytest.approx(1800)
    assert p.energy_kWh_m3 == pytest.approx(5.0)


def test_linear_fit_matches_numpy_style_ols():
    # y = 2x + 1 exactly
    f = linear_fit([0, 1, 2, 3], [1, 3, 5, 7])
    assert (f.slope, f.intercept, f.r2) == pytest.approx((2.0, 1.0, 1.0))
    # hand-checked noisy case: Excel SLOPE = 0.6, INTERCEPT = 2.2, RSQ = 0.6
    f = linear_fit([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])
    assert (f.slope, f.intercept, f.r2) == pytest.approx((0.6, 2.2, 0.6))


def test_unsorted_input_is_sorted():
    r, _ = analyze(T[::-1], C[::-1])
    assert r.k1 == pytest.approx(0.02944, abs=5e-6)


def test_bad_rows_skipped():
    r, skipped = analyze(T + [70, 80, None], C + [0, -5, 100])
    assert len(r.points) == 7 and len(skipped) == 3


@pytest.mark.parametrize("t,c", [
    ([10, 20, 30], [900, 800, 700]),  # no t = 0
    ([0, 10], [1000, 800]),  # too few points
    ([0, 10, 10], [1000, 800, 700]),  # duplicate time
    ([0, 10, 20], [0, 800, 700]),  # C0 invalid
])
def test_invalid_series(t, c):
    with pytest.raises(ValidationError):
        analyze(t, c)


@pytest.mark.parametrize("target", [0, 100, -5, 120])
def test_target_out_of_range(target):
    with pytest.raises(ValidationError):
        time_for_removal(target, 0.03)


def test_target_needs_positive_k1():
    with pytest.raises(ValidationError):
        time_for_removal(80, 0.0)
