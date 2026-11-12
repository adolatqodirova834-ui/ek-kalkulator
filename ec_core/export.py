"""Report tables (Uzbek labels) and Excel/CSV serialisation."""

from __future__ import annotations

import io

import pandas as pd

from .kinetics import KineticsResult
from .models import Experiment, Mode, Results

COLS = ["Ko'rsatkich", "Belgi", "Qiymat", "Birlik"]


def inputs_table(exp: Experiment) -> pd.DataFrame:
    mat = exp.electrode.material
    continuous = exp.reactor.mode is Mode.CONTINUOUS
    rows = [
        ("Elektrod materiali", "", f"{mat.name} ({mat.symbol})", ""),
        ("Rejim", "", "Uzluksiz" if continuous else "Davriy", ""),
        ("Tok kuchi", "I", exp.current_A, "A"),
        ("Kuchlanish", "U", exp.voltage_V, "V"),
    ]
    if continuous:
        rows += [("Oqim tezligi", "Q", exp.reactor.flow_L_h, "L/soat"),
                 ("Gidravlik ushlanish vaqti", "HRT", exp.reactor.hrt_min, "min")]
    else:
        rows.append(("Vaqt", "t", exp.time_min, "min"))
    rows += [
        ("Suv hajmi", "V", exp.reactor.volume_L, "L"),
        ("Anodlarning faol yuzasi", "A", exp.electrode.area_cm2, "cm²"),
        ("Tok samaradorligi", "φ", exp.electrode.phi, "—"),
        ("Boshlang'ich KXT", "C₀", exp.c0_mg_L, "mg/L"),
        ("Oxirgi KXT", "C", exp.c_mg_L, "mg/L"),
        ("Elektr narxi", "", exp.price_electricity, "so'm/kWh"),
        (f"{mat.name} narxi", "", exp.price_electrode, "so'm/kg"),
    ]
    return pd.DataFrame(rows, columns=COLS)


def results_table(exp: Experiment, r: Results) -> pd.DataFrame:
    sym = exp.electrode.material.symbol
    per_h = "/soat" if r.per_hour else ""
    rows = [
        (f"Erigan {sym} massasi" + (" (HRT davomida)" if r.per_hour else ""), "m", r.mass_g, "g"),
        ("Koagulyant dozasi", "D", r.dose_mg_L, "mg/L"),
        ("Tok zichligi", "j", r.current_density_mA_cm2, "mA/cm²"),
        ("Zaryad yuklamasi", "q", r.charge_C_L, "C/L"),
        ("Energiya sarfi", "E", r.energy_kWh_m3, "kWh/m³"),
        ("Elektrod sarfi", "ELC", r.electrode_kg_m3, "kg/m³"),
        ("Tozalash samaradorligi", "R", r.removal_pct, "%"),
        ("Solishtirma energiya", "SEC", r.specific_energy_kWh_kg, "kWh/kg KXT"),
        ("Ekspluatatsiya xarajati", "OC", r.cost_sum_m3, "so'm/m³"),
        ("Anod qalinligining kamayishi", "Δd", r.thickness_loss_mm, "mm" + per_h),
        ("Ajralgan H₂ hajmi (n.sh.)", "V(H₂)", r.h2_mL, "mL" + per_h),
    ]
    return pd.DataFrame(rows, columns=COLS)


KINETIC_COLS = {
    "time_min": "t, min",
    "c_mg_L": "KXT, mg/L",
    "c_ratio": "C/C₀",
    "removal_pct": "R, %",
    "ln_c0_c": "ln(C₀/C)",
    "inv_diff": "1/C − 1/C₀, L/mg",
    "dose_mg_L": "Al dozasi, mg/L",
    "charge_C_L": "Zaryad yuklamasi, C/L",
    "energy_kWh_m3": "Energiya, kWh/m³",
}


def kinetics_table(res: KineticsResult, symbol: str = "Al") -> pd.DataFrame:
    df = pd.DataFrame([p.to_dict() for p in res.points]).rename(columns=KINETIC_COLS)
    return df.rename(columns={"Al dozasi, mg/L": f"{symbol} dozasi, mg/L"}).dropna(axis=1, how="all")


def models_table(res: KineticsResult) -> pd.DataFrame:
    rows = [
        ("Psevdo-birinchi tartib", "ln(C₀/C) = k₁·t", res.first.slope, "1/min", res.first.intercept, res.first.r2,
         res.half_life_min, "Ha" if res.best == "first" else ""),
        ("Psevdo-ikkinchi tartib", "1/C − 1/C₀ = k₂·t", res.second.slope, "L/(mg·min)", res.second.intercept,
         res.second.r2, None, "Ha" if res.best == "second" else ""),
    ]
    return pd.DataFrame(rows, columns=["Model", "Tenglama", "k (qiyalik)", "k birligi", "Erkin had", "R²",
                                       "t½, min", "Eng mos"])


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """UTF-8 with BOM so that Excel opens Uzbek text and symbols correctly."""
    return df.to_csv(index=False).encode("utf-8-sig")


def to_xlsx_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
            ws = writer.sheets[name[:31]]
            for i, col in enumerate(df.columns, start=1):
                width = max([len(str(col))] + [len(str(v)) for v in df[col]]) + 2
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(width, 45)
    return buf.getvalue()
