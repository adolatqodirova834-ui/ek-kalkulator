"""Reference case: I = 1 A, U = 10 V, t = 30 min, V = 1 L, phi = 1."""

import pytest

from ec_core import Electrode, Experiment, Mode, Reactor, MATERIALS


def make(**kw):
    d = dict(I=1.0, U=10.0, t=30.0, V=1.0, A=100.0, phi=1.0, C0=1500.0, C=600.0,
             pe=900.0, pal=35000.0, mode=Mode.BATCH, Q=None)
    d.update(kw)
    return Experiment(
        electrode=Electrode.of("Al", d["A"], d["phi"]),
        reactor=Reactor(d["V"], d["mode"], d["Q"]),
        current_A=d["I"], voltage_V=d["U"], time_min=d["t"],
        c0_mg_L=d["C0"], c_mg_L=d["C"],
        price_electricity=d["pe"], price_electrode=d["pal"],
    )


@pytest.fixture
def r():
    return make().calculate()


def test_material_al():
    al = MATERIALS["Al"]
    assert (al.M, al.z, al.rho) == (26.98, 3, 2.70)


def test_reference_values(r):
    assert r.mass_g == pytest.approx(0.1678, abs=5e-5)
    assert r.dose_mg_L == pytest.approx(167.8, abs=0.05)
    assert r.energy_kWh_m3 == pytest.approx(5.00, abs=1e-12)
    assert r.h2_mL == pytest.approx(209.1, abs=0.05)


def test_exact_formulas(r):
    m = 1 * 1800 * 26.98 / (3 * 96485)
    assert r.mass_g == pytest.approx(m, rel=1e-12)  # 1
    assert r.dose_mg_L == pytest.approx(m * 1000, rel=1e-12)  # 2
    assert r.current_density_mA_cm2 == pytest.approx(10.0)  # 3
    assert r.charge_C_L == pytest.approx(1800.0)  # 4
    assert r.electrode_kg_m3 == pytest.approx(m, rel=1e-12)  # 6
    assert r.removal_pct == pytest.approx(60.0)  # 7
    assert r.specific_energy_kWh_kg == pytest.approx(5.0 / 0.9)  # 8
    assert r.cost_sum_m3 == pytest.approx(900 * 5.0 + 35000 * m)  # 9
    assert r.thickness_loss_mm == pytest.approx(m / (2.70 * 100) * 10)  # 10
    assert r.h2_mL == pytest.approx(1800 / (2 * 96485) * 22414)  # 11
    assert r.per_hour is False


def test_phi_scales_mass_only():
    a, b = make().calculate(), make(phi=1.5).calculate()
    assert b.mass_g == pytest.approx(1.5 * a.mass_g)
    assert b.dose_mg_L == pytest.approx(1.5 * a.dose_mg_L)
    assert b.energy_kWh_m3 == a.energy_kWh_m3
    assert b.h2_mL == a.h2_mL


def test_volume_scaling():
    r = make(V=2.5).calculate()
    assert r.energy_kWh_m3 == pytest.approx(2.0)
    assert r.charge_C_L == pytest.approx(720.0)
    assert r.dose_mg_L == pytest.approx(r.mass_g * 1000 / 2.5)


def test_continuous_uses_hrt():
    # V = 1 L, Q = 2 L/h -> HRT = 30 min: same per-volume numbers as the batch case
    c = make(mode=Mode.CONTINUOUS, Q=2.0, t=None).calculate()
    b = make().calculate()
    assert c.time_min == pytest.approx(30.0)
    for f in ("mass_g", "dose_mg_L", "charge_C_L", "energy_kWh_m3", "electrode_kg_m3", "cost_sum_m3"):
        assert getattr(c, f) == pytest.approx(getattr(b, f))
    # H2 and anode wear are reported per hour of operation
    assert c.per_hour is True
    assert c.h2_mL == pytest.approx(2 * b.h2_mL)
    assert c.thickness_loss_mm == pytest.approx(2 * b.thickness_loss_mm)


def test_continuous_ignores_batch_time():
    assert make(mode=Mode.CONTINUOUS, Q=2.0, t=999.0).calculate().time_min == pytest.approx(30.0)


def test_at_time_matches_calculate(r):
    p = make().at_time(30.0)
    assert (p.dose_mg_L, p.charge_C_L, p.energy_kWh_m3) == (r.dose_mg_L, r.charge_C_L, r.energy_kWh_m3)
    assert make().at_time(0.0).dose_mg_L == 0.0
