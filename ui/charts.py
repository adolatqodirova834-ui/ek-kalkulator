"""Plotly figures styled for publications, plus PNG export."""

from __future__ import annotations

import math

import plotly.graph_objects as go

from ec_core.kinetics import KineticsResult, LinearFit

DATA = "#2a78d6"  # measured points
FIT = "#52514e"  # model line
INK = "#0b0b0b"
GRID = "#e6e5e1"

# Mode-bar camera button: high-resolution PNG without any extra dependency
PLOT_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "width": 900, "height": 560, "scale": 4},
}


def _layout(fig: go.Figure, x_title: str, y_title: str) -> go.Figure:
    axis = dict(showline=True, linecolor=INK, linewidth=1, ticks="outside", tickcolor=INK,
                gridcolor=GRID, zeroline=False, title_font_size=16, tickfont_size=14, rangemode="tozero")
    fig.update_layout(
        template="none", paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial, Helvetica, sans-serif", color=INK, size=14),
        xaxis=dict(title=x_title, **axis), yaxis=dict(title=y_title, **axis),
        legend=dict(x=0.99, y=0.99, xanchor="right", yanchor="top", bgcolor="rgba(255,255,255,0.8)"),
        margin=dict(l=75, r=25, t=25, b=65), width=900, height=560, hovermode="x unified",
    )
    return fig


def _points(x, y, name, fmt) -> go.Scatter:
    return go.Scatter(x=x, y=y, mode="markers", name=name, cliponaxis=False,
                      marker=dict(size=10, color=DATA, line=dict(color="white", width=2)),
                      hovertemplate=fmt + "<extra>" + name + "</extra>")


def _fmt_num(v: float) -> str:
    return f"{v:.4g}" if 1e-3 <= abs(v) < 1e4 else f"{v:.3e}"


def equation(fit: LinearFit) -> str:
    sign = "+" if fit.intercept >= 0 else "−"
    return f"y = {_fmt_num(fit.slope)}·x {sign} {_fmt_num(abs(fit.intercept))}"


def cod_vs_time(res: KineticsResult) -> go.Figure:
    """KXT - t: measured points and the fitted first-order curve."""
    t = [p.time_min for p in res.points]
    fig = go.Figure()
    if res.k1 > 0:
        n = 100
        xs = [max(t) * i / n for i in range(n + 1)]
        ys = [res.c0_mg_L * math.exp(-res.first.predict(x)) for x in xs]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name="Psevdo-birinchi tartib modeli",
                                 line=dict(color=FIT, width=2, dash="dash"),
                                 hovertemplate="%{y:.0f} mg/L<extra>Model</extra>"))
    fig.add_trace(_points(t, [p.c_mg_L for p in res.points], "Tajriba", "%{y:.0f} mg/L"))
    return _layout(fig, "Vaqt, min", "KXT, mg/L")


def linearized(res: KineticsResult, order: str = "first") -> go.Figure:
    """ln(C0/C) - t (first) or 1/C - 1/C0 - t (second) with regression line, equation and R2."""
    fit = res.first if order == "first" else res.second
    t = [p.time_min for p in res.points]
    y = [p.ln_c0_c if order == "first" else p.inv_diff for p in res.points]
    y_title = "ln(C₀/C)" if order == "first" else "1/C − 1/C₀, L/mg"
    xs = [0.0, max(t)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[fit.predict(x) for x in xs], mode="lines", name="Chiziqli regressiya",
                             line=dict(color=FIT, width=2), hoverinfo="skip"))
    fig.add_trace(_points(t, y, "Tajriba", "%{y:.4g}"))
    fig.add_annotation(
        xref="paper", yref="paper", x=0.03, y=0.97, xanchor="left", yanchor="top", showarrow=False, align="left",
        text=f"{equation(fit)}<br>R² = {fit.r2:.4f}", font=dict(size=16, color=INK),
        bgcolor="rgba(255,255,255,0.85)", bordercolor=GRID, borderpad=6,
    )
    fig = _layout(fig, "Vaqt, min", y_title)
    fig.update_layout(legend=dict(x=0.99, y=0.03, xanchor="right", yanchor="bottom"))
    return fig


def to_png(fig: go.Figure, scale: int = 4) -> bytes | None:
    """Render a 3600x2240 px PNG (300 dpi at 12 inch width). None if kaleido/Chrome is unavailable."""
    try:
        return fig.to_image(format="png", scale=scale)
    except Exception:
        return None
