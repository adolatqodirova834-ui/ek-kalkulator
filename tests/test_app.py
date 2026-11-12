"""Smoke tests of the Streamlit UI (headless, via streamlit.testing)."""

from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
ROOT = Path(__file__).resolve().parents[1]


def run(page=None, **state):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if page:
        at.switch_page(page).run()
    assert not at.exception, at.exception
    return at


def metrics(at):
    return {m.label: m.value for m in at.metric}


def test_calculator_reference_case():
    m = metrics(run())
    assert m["Erigan Al massasi, m (g)"] == "0.1678"
    assert m["Koagulyant dozasi (mg/L)"] == "167.8"
    assert m["Energiya sarfi, E (kWh/m³)"] == "5"
    assert m["H₂ hajmi, n.sh. (mL)"] == "209.1"


def test_zero_input_shows_error_not_crash():
    at = run(V=0.0)
    assert len(at.error) == 1 and not at.metric


def test_warnings_shown():
    at = run(I=12.0, U=31.0, A=1000.0, phi=0.5, C=2000.0)
    assert len(at.warning) == 4  # I, U, phi, C > C0 (j = 12 mA/cm2 is in range)
    assert len(run(I=12.0).warning) == 2  # I and j = 120 mA/cm2


def test_continuous_mode():
    at = run(mode="continuous", Q=2.0)
    assert metrics(at)["Energiya sarfi, E (kWh/m³)"] == "5"
    assert "H₂ hajmi, n.sh. (mL/soat)" in metrics(at)


def test_kinetics_page_reference_case():
    at = run(page="views/kinetika.py")
    m = metrics(at)
    assert m["k₁ (1/min)"] == "0.02944"
    assert [x.value for x in at.metric if x.label == "R²"][0] == "0.9993"
    assert m["Kerakli vaqt (min)"] == "54.7"
