"""Parity with the Excel prototype EK_kalkulyator_Al.xlsx.

1. Cached values: every result cell Excel itself computed must equal ec_core.
2. Formula level: the workbook's formulas are evaluated by a small interpreter
   (independent of ec_core) for other input sets and compared again, so the
   match is not limited to the single saved example.
"""

import math
import re
import statistics
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from ec_core import Electrode, Experiment, Reactor, analyze, time_for_removal, validate_inputs
from ec_core.constants import FARADAY
from ec_core.materials import MATERIALS

XLSX = Path(__file__).resolve().parents[1] / "EK_kalkulyator_Al.xlsx"
pytestmark = pytest.mark.skipif(not XLSX.exists(), reason="Excel prototipi topilmadi")

S1, S2 = "EK kalkulyatori (Al)", "Kinetika"
REL = 1e-12

# Excel cell -> Results attribute
RESULT_CELLS = {
    "B19": "mass_g", "B20": "dose_mg_L", "B21": "current_density_mA_cm2", "B22": "charge_C_L",
    "B23": "energy_kWh_m3", "B24": "electrode_kg_m3", "B25": "removal_pct", "B26": "specific_energy_kWh_kg",
    "B27": "cost_sum_m3", "B28": "thickness_loss_mm", "B29": "h2_mL",
}
POINT_COLS = {"C": "c_ratio", "D": "removal_pct", "E": "ln_c0_c", "F": "inv_diff",
              "G": "dose_mg_L", "H": "charge_C_L", "I": "energy_kWh_m3"}
KIN_ROWS = range(4, 11)


class Workbook:
    """Minimal evaluator for the arithmetic / IF / IFERROR / LN / SLOPE / RSQ formulas in the prototype."""

    def __init__(self, overrides=None):
        wb = openpyxl.load_workbook(XLSX)
        self.cells = {(ws.title, c.coordinate): c.value for ws in wb for row in ws.iter_rows() for c in row}
        self.cells.update(overrides or {})
        self.memo = {}

    def value(self, sheet, ref):
        key = (sheet, ref)
        if key not in self.memo:
            raw = self.cells.get(key)
            self.memo[key] = self._eval(sheet, raw[1:]) if isinstance(raw, str) and raw.startswith("=") else raw
        v = self.memo[key]
        return "" if v is None else v

    def _eval(self, sheet, f):
        f = f.replace("$", "")
        f = re.sub(r"(?<![<>=])=(?!=)", "==", f).replace("<>", "!=")
        f = re.sub(r"\b([A-Z]+)(\d+):([A-Z]+)(\d+)\b", lambda m: f'RNG("{sheet}","{m[1]}",{m[2]},{m[4]})', f)
        f = re.sub(r"(?:'([^']+)'!)?\b([A-Z]{1,2}\d+)\b(?!\")",
                   lambda m: f'V("{m[1] or sheet}","{m[2]}")', f)
        env = {
            "V": self.value,
            "RNG": lambda s, col, a, b: [self.value(s, f"{col}{i}") for i in range(a, b + 1)],
            "IF": lambda c, a, b: a if c else b,
            "IFERROR": lambda a, b: a,
            "LN": math.log,
            "SLOPE": lambda y, x: statistics.linear_regression(x, y).slope,
            "RSQ": lambda y, x: statistics.correlation(x, y) ** 2,
        }
        return eval(f, {"__builtins__": {}}, env)  # formulas come from our own workbook


def experiment_from(wb: Workbook) -> Experiment:
    v = lambda ref: wb.value(S1, ref)
    return Experiment(
        electrode=Electrode.of("Al", v("B11"), v("B12")), reactor=Reactor(v("B10")),
        current_A=v("B7"), voltage_V=v("B8"), time_min=v("B9"), c0_mg_L=v("B13"), c_mg_L=v("B14"),
        price_electricity=v("B15"), price_electrode=v("B16"),
    )


def assert_parity(wb: Workbook):
    exp = experiment_from(wb)
    r = exp.calculate()
    for cell, attr in RESULT_CELLS.items():
        assert getattr(r, attr) == pytest.approx(wb.value(S1, cell), rel=REL), cell

    t = [wb.value(S2, f"A{i}") for i in KIN_ROWS]
    c = [wb.value(S2, f"B{i}") for i in KIN_ROWS]
    res, _ = analyze(t, c, exp)
    for i, p in zip(KIN_ROWS, res.points):
        for col, attr in POINT_COLS.items():
            assert getattr(p, attr) == pytest.approx(wb.value(S2, f"{col}{i}"), rel=REL, abs=1e-15), f"{col}{i}"
    k = lambda ref: wb.value(S2, ref)
    assert res.k1 == pytest.approx(k("D13"), rel=1e-10)
    assert res.first.r2 == pytest.approx(k("D14"), rel=1e-10)
    assert res.half_life_min == pytest.approx(k("D15"), rel=1e-10)
    assert res.k2 == pytest.approx(k("D16"), rel=1e-10)
    assert res.second.r2 == pytest.approx(k("D17"), rel=1e-10)
    assert {"first": "1-tartib", "second": "2-tartib"}[res.best] == k("D18")
    t_req = time_for_removal(k("D21"), res.k1)
    at = exp.at_time(t_req)
    assert t_req == pytest.approx(k("D22"), rel=1e-10)
    assert at.energy_kWh_m3 == pytest.approx(k("D23"), rel=1e-10)
    assert at.dose_mg_L == pytest.approx(k("D24"), rel=1e-10)


def test_constants_match_workbook():
    wb = Workbook()
    al = MATERIALS["Al"]
    assert (wb.value(S1, "B2"), wb.value(S1, "B3"), wb.value(S1, "B4"), wb.value(S1, "B5")) == (FARADAY, al.M, al.z, al.rho)


def test_cached_excel_values():
    """Compare against the numbers Excel itself stored in the file."""
    cached = openpyxl.load_workbook(XLSX, data_only=True)

    class Cached:
        def value(self, sheet, ref):
            return cached[sheet][ref].value

    assert Cached().value(S1, "B19") is not None, "Faylda hisoblangan qiymatlar saqlanmagan"
    assert_parity(Cached())


def test_evaluator_reproduces_cached_values():
    """The mini-interpreter must agree with Excel before it is trusted for other inputs."""
    cached = openpyxl.load_workbook(XLSX, data_only=True)
    wb = Workbook()
    for (sheet, ref), raw in wb.cells.items():
        if isinstance(raw, str) and raw.startswith("="):
            got, want = wb.value(sheet, ref), cached[sheet][ref].value
            if isinstance(want, str):
                assert got == want, (sheet, ref)
            else:
                assert got == pytest.approx(want, rel=1e-10, abs=1e-15), (sheet, ref)


@pytest.mark.parametrize("inputs,cod", [
    (dict(B7=2.5, B8=12.3, B9=45, B10=1.5, B11=180, B12=1.3, B13=2200, B14=410, B15=1200, B16=42000),
     [2200, 1500, 1010, 720, 540, 410, 330]),
    (dict(B7=0.35, B8=6.8, B9=17.5, B10=0.8, B11=56, B12=0.9, B13=980, B14=735, B15=850, B16=31000),
     [980, 610, 450, 350, 290, 245, 213]),  # second-order-like decay
    (dict(B7=9.8, B8=29.5, B9=120, B10=25, B11=1250, B12=1.95, B13=5400, B14=95, B15=1000, B16=35000),
     [5400, 3900, 2500, 1900, 1150, 800, 610]),
])
def test_formula_parity_for_other_inputs(inputs, cod):
    over = {(S1, k): v for k, v in inputs.items()}
    over |= {(S2, f"B{i}"): c for i, c in zip(KIN_ROWS, cod)}
    over[(S2, "D21")] = 92.5
    assert_parity(Workbook(over))


def test_second_order_case_is_selected_like_excel():
    over = {(S2, f"B{i}"): c for i, c in zip(KIN_ROWS, [980, 610, 450, 350, 290, 245, 213])}
    wb = Workbook(over)
    assert wb.value(S2, "D18") == "2-tartib"


@pytest.mark.parametrize("kw,red", [
    (dict(current_A=10.0), False), (dict(current_A=10.5, area_cm2=500), True),  # B7 > 10
    (dict(voltage_V=30.0), False), (dict(voltage_V=30.5), True),  # B8 > 30
    (dict(area_cm2=1000.0), False), (dict(area_cm2=1100.0), True), (dict(area_cm2=9.0), True),  # B21 <1 or >100
    (dict(phi=0.8), False), (dict(phi=2.0), False), (dict(phi=0.7), True), (dict(phi=2.1), True),  # B12
    (dict(c_mg_L=1501.0), True),  # B14 > B13
])
def test_warning_rules_match_conditional_formatting(kw, red):
    base = dict(current_A=1.0, voltage_V=10.0, time_min=30.0, volume_L=1.0, area_cm2=100.0, phi=1.0,
                c0_mg_L=1500.0, c_mg_L=600.0)
    errors, warnings = validate_inputs(**{**base, **kw})
    assert not errors and bool(warnings) is red
