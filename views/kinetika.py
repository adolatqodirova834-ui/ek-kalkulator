"""Kinetics page: data entry, model fitting, target time, charts."""

import pandas as pd
import streamlit as st

from ec_core import Mode, ValidationError, analyze, time_for_removal, validate_inputs
from ec_core.export import kinetics_table, models_table, to_csv_bytes, to_xlsx_bytes
from ui import charts
from ui.sidebar import build_experiment, fmt

T_COL, C_COL = "t, min", "KXT, mg/L"
SAMPLE = pd.DataFrame({T_COL: [0.0, 10, 20, 30, 40, 50, 60], C_COL: [1500.0, 1120, 820, 600, 450, 340, 260]})


def read_csv(file) -> pd.DataFrame:
    """First two columns = time, COD. Accepts ',' or ';' separators and decimal commas."""
    raw = file.getvalue().decode("utf-8-sig", errors="replace")
    sep = ";" if raw.count(";") > raw.count(",") else ("\t" if raw.count("\t") > raw.count(",") else ",")
    df = pd.read_csv(pd.io.common.StringIO(raw), sep=sep, header=None, dtype=str)
    if df.shape[1] < 2:
        raise ValueError("CSV faylda kamida ikkita ustun bo'lishi kerak: vaqt va KXT.")
    df = df.iloc[:, :2].apply(lambda s: pd.to_numeric(s.str.strip().str.replace(",", "."), errors="coerce"))
    df = df.dropna(how="any")  # drops the header row and blank lines
    if df.empty:
        raise ValueError("CSV faylda sonli qiymatlar topilmadi.")
    df.columns = [T_COL, C_COL]
    return df.reset_index(drop=True)


# Table edits live in widget state, which Streamlit drops when the page is left.
# On return, restore the last edited table as the new base.
if st.session_state.get("_last_page") != "kin" and "kin_current" in st.session_state:
    st.session_state["kin_data"] = st.session_state["kin_current"]
    st.session_state["kin_ver"] = st.session_state.get("kin_ver", 0) + 1
st.session_state["_last_page"] = "kin"

st.title("Kinetika")
st.caption("Vaqt va KXT qiymatlarini kiriting yoki CSV yuklang. t = 0 dagi qiymat C₀ deb olinadi. "
           "I, U, V, A va φ chap paneldan olinadi.")

left, right = st.columns([1, 1])
with right:
    up = st.file_uploader("CSV yuklash (1-ustun: vaqt, min; 2-ustun: KXT, mg/L)", type=["csv", "txt"])
    st.download_button("CSV namunasi", to_csv_bytes(SAMPLE), "kinetika_namuna.csv", "text/csv")
    if up is not None and st.session_state.get("kin_file") != (up.name, up.size):
        try:
            st.session_state["kin_data"] = read_csv(up)
            st.session_state["kin_file"] = (up.name, up.size)
            st.session_state["kin_ver"] = st.session_state.get("kin_ver", 0) + 1
        except Exception as e:  # malformed file
            st.error(f"CSV o'qilmadi: {e}", icon="⛔")
    target = st.number_input("Maqsadli tozalash samaradorligi, R (%)", min_value=0.0, max_value=99.9,
                             step=5.0, format="%.1f", key="target",
                             help="0 kiritilsa, kerakli vaqt hisoblanmaydi.")
with left:
    base = st.session_state.setdefault("kin_data", SAMPLE.copy())
    edited = st.data_editor(
        base, num_rows="dynamic", hide_index=True, width="stretch",
        key=f"kin_editor_{st.session_state.get('kin_ver', 0)}",
        column_config={T_COL: st.column_config.NumberColumn(min_value=0.0, format="%.2f", required=True),
                       C_COL: st.column_config.NumberColumn(min_value=0.0, format="%.2f", required=True)},
    )
    st.session_state["kin_current"] = edited.reset_index(drop=True)

# Process parameters (dose / charge / energy per point). Kinetics still works without them.
exp = build_experiment()
s = st.session_state
param_errors, param_warnings = validate_inputs(
    current_A=s["I"], voltage_V=s["U"], time_min=1.0, volume_L=s["V"], area_cm2=s["A"], phi=s["phi"],
    c0_mg_L=1.0, c_mg_L=1.0, price_electricity=s["price_e"], price_electrode=s["price_m"])
param_warnings = [w for w in param_warnings if "C₀" not in w]
if param_errors:
    for e in param_errors:
        st.error(e, icon="⛔")
    st.info("Jarayon parametrlari noto'g'ri — doza, zaryad va energiya ustunlari hisoblanmaydi.")
for w in param_warnings:
    st.warning(w, icon="⚠️")
if exp.reactor.mode is Mode.CONTINUOUS:
    st.info("Kinetik qator davriy tajriba deb qaraladi: har bir nuqta uchun doza va energiya "
            "jadvaldagi t bo'yicha hisoblanadi (Q ishlatilmaydi).")

try:
    res, skipped = analyze(edited[T_COL].tolist(), edited[C_COL].tolist(), None if param_errors else exp)
except ValidationError as err:
    for e in err.errors:
        st.error(e, icon="⛔")
    st.stop()
for m in skipped:
    st.warning(m, icon="⚠️")
above = [f"{p.time_min:g}" for p in res.points if p.c_mg_L > res.c0_mg_L]
if above:
    st.warning(f"t = {', '.join(above)} min da C > C₀: bu nuqtalarda samaradorlik manfiy.", icon="⚠️")

sym = exp.electrode.material.symbol
table = kinetics_table(res, sym)
st.subheader("Hisoblangan nuqtalar")
st.dataframe(table, hide_index=True, width="stretch", column_config={
    c: st.column_config.NumberColumn(format="%.3e" if c.startswith("1/C") else "%.4g") for c in table.columns})

st.subheader("Kinetik modellar")
best_name = "psevdo-birinchi tartib" if res.best == "first" else "psevdo-ikkinchi tartib"
st.success(f"Eng mos model: **{best_name}** (R² = {max(res.first.r2, res.second.r2):.4f})", icon="✅")
m1, m2 = st.columns(2)
with m1:
    st.markdown("**Psevdo-birinchi tartib:** ln(C₀/C) = k₁·t" + (" ✅" if res.best == "first" else ""))
    a, b, c = st.columns(3)
    a.metric("k₁ (1/min)", f"{res.k1:.5f}", border=True)
    b.metric("R²", f"{res.first.r2:.4f}", border=True)
    c.metric("t½ = ln2/k₁ (min)", fmt(res.half_life_min), border=True)
with m2:
    st.markdown("**Psevdo-ikkinchi tartib:** 1/C − 1/C₀ = k₂·t" + (" ✅" if res.best == "second" else ""))
    a, b = st.columns(2)
    a.metric("k₂ (L/(mg·min))", f"{res.k2:.3e}", border=True)
    b.metric("R²", f"{res.second.r2:.4f}", border=True)
st.caption("Qiyalik va R² erkin hadli chiziqli regressiya bilan hisoblanadi (Excel'dagi SLOPE va RSQ bilan bir xil).")

target_row = None
if target > 0:
    st.subheader(f"Maqsadli samaradorlik: R = {target:g} %")
    try:
        t_req = time_for_removal(target, res.k1)
        cols = st.columns(3)
        cols[0].metric("Kerakli vaqt (min)", f"{t_req:.1f}", border=True)
        target_row = {"Maqsadli R, %": target, "Kerakli vaqt, min": t_req}
        if not param_errors:
            p = exp.at_time(t_req)
            cols[1].metric("Energiya sarfi (kWh/m³)", fmt(p.energy_kWh_m3), border=True)
            cols[2].metric(f"{sym} dozasi (mg/L)", fmt(p.dose_mg_L), border=True)
            target_row |= {"Energiya sarfi, kWh/m³": p.energy_kWh_m3, f"{sym} dozasi, mg/L": p.dose_mg_L}
        st.caption("Birinchi tartib modeli bo'yicha: t = −ln(1 − R/100)/k₁.")
        if t_req > max(p.time_min for p in res.points):
            st.warning("Kerakli vaqt tajriba oralig'idan tashqarida — bu ekstrapolyatsiya.", icon="⚠️")
    except ValidationError as err:
        st.error(err.errors[0], icon="⛔")

st.subheader("Grafiklar")
figs = {
    "KXT – t": (charts.cod_vs_time(res), "KXT_vaqt.png"),
    "ln(C₀/C) – t": (charts.linearized(res, "first"), "birinchi_tartib.png"),
    "1/C − 1/C₀ – t": (charts.linearized(res, "second"), "ikkinchi_tartib.png"),
}
for tab, (name, (fig, fname)) in zip(st.tabs(list(figs)), figs.items()):
    with tab:
        st.plotly_chart(fig, config=charts.PLOT_CONFIG, theme=None, key=f"fig_{fname}")
        if st.toggle("PNG tayyorlash (3600×2240 px)", key=f"png_{fname}"):
            png = charts.to_png(fig)
            if png:
                st.download_button(f"⬇️ {fname}", png, fname, "image/png", key=f"dl_{fname}")
            else:
                st.info("PNG yaratib bo'lmadi (kaleido yoki Chrome o'rnatilmagan). "
                        "Grafikning o'ng yuqori burchagidagi 📷 tugmasi orqali ham yuqori sifatli PNG saqlash mumkin.")

st.subheader("Eksport")
sheets = {"Kinetika": table, "Modellar": models_table(res)}
if target_row:
    sheets["Maqsadli R"] = pd.DataFrame([target_row])
d1, d2, _ = st.columns([1, 1, 2])
d1.download_button("⬇️ Excel (.xlsx)", to_xlsx_bytes(sheets), "EK_kinetika.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
d2.download_button("⬇️ CSV", to_csv_bytes(table), "EK_kinetika.csv", "text/csv", width="stretch")
