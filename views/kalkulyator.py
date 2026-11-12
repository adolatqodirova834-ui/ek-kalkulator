"""Main calculator page."""

import streamlit as st

from ec_core import Mode
from ec_core.export import inputs_table, results_table, to_csv_bytes, to_xlsx_bytes
from ui.sidebar import build_experiment, fmt

st.session_state["_last_page"] = "calc"
st.title("Elektrokoagulyatsiya kalkulyatori")
st.caption("Jarayon parametrlari chap paneldan kiritiladi. Barcha hisoblar Faradey qonuniga asoslangan (F = 96 485 C/mol).")

c1, c2 = st.columns(2)
c1.number_input("Boshlang'ich KXT, C₀ (mg/L)", min_value=0.0, step=50.0, format="%.1f", key="C0")
c2.number_input("Oxirgi KXT, C (mg/L)", min_value=0.0, step=50.0, format="%.1f", key="C")

exp = build_experiment()
errors, warnings = exp.validate()
for e in errors:
    st.error(e, icon="⛔")
if errors:
    st.info("Natijalarni ko'rish uchun yuqoridagi xatolarni tuzating.")
    st.stop()
for w in warnings:
    st.warning(w, icon="⚠️")

r = exp.calculate()
sym = exp.electrode.material.symbol
per_h = "/soat" if r.per_hour else ""

if exp.reactor.mode is Mode.CONTINUOUS:
    st.info(f"Uzluksiz rejim: HRT = V/Q = **{fmt(r.time_min)} min**. Doza, zaryad va energiya HRT bo'yicha, "
            "H₂ hajmi va anod yemirilishi 1 soatlik ish uchun hisoblangan.")

st.subheader("Natijalar")
cards = [
    (f"Erigan {sym} massasi, m", r.mass_g, "g"),
    ("Koagulyant dozasi", r.dose_mg_L, "mg/L"),
    ("Tok zichligi, j", r.current_density_mA_cm2, "mA/cm²"),
    ("Zaryad yuklamasi", r.charge_C_L, "C/L"),
    ("Energiya sarfi, E", r.energy_kWh_m3, "kWh/m³"),
    ("Elektrod sarfi, ELC", r.electrode_kg_m3, "kg/m³"),
    ("Tozalash samaradorligi, R", r.removal_pct, "%"),
    ("Solishtirma energiya", r.specific_energy_kWh_kg, "kWh/kg"),
    ("Xarajat", r.cost_sum_m3, "so'm/m³"),
    ("Anod yemirilishi", r.thickness_loss_mm, "mm" + per_h),
    ("H₂ hajmi, n.sh.", r.h2_mL, "mL" + per_h),
]
for i in range(0, len(cards), 4):
    cols = st.columns(4)
    for col, (label, value, unit) in zip(cols, cards[i:i + 4]):
        col.metric(f"{label} ({unit})", fmt(value), border=True)

st.subheader("Jadval va eksport")
res_df, in_df = results_table(exp, r), inputs_table(exp)
st.dataframe(res_df, hide_index=True, width="stretch",
             column_config={"Qiymat": st.column_config.NumberColumn(format="%.6g")})

d1, d2, _ = st.columns([1, 1, 2])
d1.download_button("⬇️ Excel (.xlsx)", to_xlsx_bytes({"Natijalar": res_df, "Kirish ma'lumotlari": in_df}),
                   "EK_natijalar.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
d2.download_button("⬇️ CSV", to_csv_bytes(res_df), "EK_natijalar.csv", "text/csv", width="stretch")

with st.expander("Formulalar"):
    st.markdown(r"""
| № | Kattalik | Formula |
|---|---|---|
| 1 | Erigan metall massasi, g | $m = \dfrac{I \cdot t \cdot M}{z \cdot F} \cdot \varphi$ |
| 2 | Koagulyant dozasi, mg/L | $D = m \cdot 1000 / V$ |
| 3 | Tok zichligi, mA/cm² | $j = I \cdot 1000 / A$ |
| 4 | Zaryad yuklamasi, C/L | $q = I \cdot t / V$ |
| 5 | Energiya sarfi, kWh/m³ | $E = U \cdot I \cdot t_{soat} / V$ |
| 6 | Elektrod sarfi, kg/m³ | $ELC = m / V$ |
| 7 | Tozalash samaradorligi, % | $R = (C_0 - C)/C_0 \cdot 100$ |
| 8 | Solishtirma energiya, kWh/kg KXT | $E / ((C_0 - C)/1000)$ |
| 9 | Ekspluatatsiya xarajati, so'm/m³ | $a \cdot E + b \cdot ELC$ |
| 10 | Anod qalinligining kamayishi, mm | $m / (\rho \cdot A) \cdot 10$ |
| 11 | H₂ hajmi, mL (n.sh.) | $I \cdot t / (2F) \cdot 22414$ |
""")
