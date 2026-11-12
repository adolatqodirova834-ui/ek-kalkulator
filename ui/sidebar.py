"""Shared process parameters (sidebar) -> Experiment factory."""

from __future__ import annotations

import streamlit as st

from ec_core import MATERIALS, Electrode, Experiment, Mode, Reactor

DEFAULTS = {
    "material": next(iter(MATERIALS)), "mode": Mode.BATCH.value,
    "I": 1.0, "U": 10.0, "t": 30.0, "Q": 2.0, "V": 1.0, "A": 100.0, "phi": 1.0,
    "price_e": 1000.0, "price_m": 35000.0, "C0": 1500.0, "C": 600.0, "target": 80.0,
}


def init_state() -> None:
    """Keep widget values alive across page switches."""
    for k, v in DEFAULTS.items():
        st.session_state[k] = st.session_state.get(k, v)


def render_sidebar() -> None:
    sb = st.sidebar
    sb.header("Jarayon parametrlari")
    sb.selectbox("Elektrod materiali", list(MATERIALS), key="material",
                 format_func=lambda s: f"{MATERIALS[s].name} ({s})")
    mat = MATERIALS[st.session_state["material"]]
    sb.caption(f"M = {mat.M} g/mol · z = {mat.z} · ρ = {mat.rho:.2f} g/cm³")
    sb.radio("Rejim", [Mode.BATCH.value, Mode.CONTINUOUS.value], key="mode", horizontal=True,
             format_func=lambda m: "Davriy" if m == Mode.BATCH.value else "Uzluksiz")
    sb.number_input("Tok kuchi, I (A)", min_value=0.0, step=0.1, format="%.3f", key="I")
    sb.number_input("Kuchlanish, U (V)", min_value=0.0, step=0.5, format="%.2f", key="U")
    if st.session_state["mode"] == Mode.BATCH.value:
        sb.number_input("Vaqt, t (min)", min_value=0.0, step=5.0, format="%.1f", key="t")
    else:
        sb.number_input("Oqim tezligi, Q (L/soat)", min_value=0.0, step=0.1, format="%.3f", key="Q",
                        help="Uzluksiz rejimda t o'rniga HRT = V/Q ishlatiladi.")
    sb.number_input("Suv hajmi, V (L)", min_value=0.0, step=0.1, format="%.3f", key="V")
    sb.number_input("Anodlarning umumiy faol yuzasi, A (cm²)", min_value=0.0, step=10.0, format="%.1f", key="A")
    sb.number_input("Tok samaradorligi, φ (o'lchamsiz)", min_value=0.0, step=0.05, format="%.2f", key="phi",
                    help="Nazariy qiymat: 1. Al uchun amalda ~1,1–1,5.")
    sb.subheader("Narxlar")
    sb.number_input("Elektr narxi (so'm/kWh)", min_value=0.0, step=50.0, format="%.0f", key="price_e",
                    help="Taxminiy namuna — amaldagi tarifni kiriting.")
    sb.number_input(f"{mat.name} narxi (so'm/kg)", min_value=0.0, step=1000.0, format="%.0f", key="price_m",
                    help="Taxminiy namuna — bozor narxini kiriting.")


def build_experiment() -> Experiment:
    s = st.session_state
    mode = Mode(s["mode"])
    return Experiment(
        electrode=Electrode.of(s["material"], s["A"], s["phi"]),
        reactor=Reactor(s["V"], mode, s["Q"] if mode is Mode.CONTINUOUS else None),
        current_A=s["I"], voltage_V=s["U"],
        time_min=s["t"] if mode is Mode.BATCH else None,
        c0_mg_L=s["C0"], c_mg_L=s["C"],
        price_electricity=s["price_e"], price_electrode=s["price_m"],
    )


def fmt(v: float | None, digits: int = 4) -> str:
    """Compact number formatting with a thin-space thousands separator."""
    if v is None:
        return "—"
    if v != 0 and abs(v) < 10 ** -(digits - 1):
        return f"{v:.{digits - 1}e}"
    s = f"{v:,.{digits}g}" if abs(v) < 10**digits else f"{v:,.0f}"
    return s.replace(",", " ")
