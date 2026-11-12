import io

import pandas as pd
import pytest

from ec_core import analyze
from ec_core.export import (inputs_table, kinetics_table, models_table, results_table, to_csv_bytes, to_xlsx_bytes)
from test_core import make
from test_kinetics import C, T


def test_results_table_has_all_11_quantities():
    exp = make()
    df = results_table(exp, exp.calculate())
    assert len(df) == 11
    assert df.loc[df["Belgi"] == "E", "Qiymat"].item() == pytest.approx(5.0)


def test_xlsx_roundtrip():
    exp = make()
    data = to_xlsx_bytes({"Natijalar": results_table(exp, exp.calculate()), "Kirish ma'lumotlari": inputs_table(exp)})
    back = pd.read_excel(io.BytesIO(data), sheet_name=None)
    assert list(back) == ["Natijalar", "Kirish ma'lumotlari"]
    assert back["Natijalar"]["Qiymat"][0] == pytest.approx(0.16778, abs=1e-5)


def test_kinetics_csv_roundtrip():
    res, _ = analyze(T, C, make())
    df = kinetics_table(res)
    back = pd.read_csv(io.BytesIO(to_csv_bytes(df)), encoding="utf-8-sig")
    assert list(back.columns) == list(df.columns) and len(back) == 7
    assert "Al dozasi, mg/L" in back.columns
    assert models_table(res)["Eng mos"].tolist() == ["Ha", ""]


def test_kinetics_table_without_experiment_drops_process_columns():
    res, _ = analyze(T, C)
    assert "Energiya, kWh/m³" not in kinetics_table(res).columns
