"""Kinetics: per-point table, linear regression (Excel SLOPE/INTERCEPT/RSQ), model choice."""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from .models import Experiment
from .validation import ValidationError

MIN_POINTS = 3


@dataclass(frozen=True)
class KineticPoint:
    time_min: float
    c_mg_L: float
    c_ratio: float  # C/C0
    removal_pct: float
    ln_c0_c: float  # ln(C0/C)
    inv_diff: float  # 1/C - 1/C0, L/mg
    dose_mg_L: float | None = None
    charge_C_L: float | None = None
    energy_kWh_m3: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LinearFit:
    slope: float
    intercept: float
    r2: float
    n: int

    def predict(self, x: float) -> float:
        return self.slope * x + self.intercept


@dataclass(frozen=True)
class KineticsResult:
    c0_mg_L: float
    points: list[KineticPoint]
    first: LinearFit  # ln(C0/C) vs t  -> k1 = slope, 1/min
    second: LinearFit  # 1/C - 1/C0 vs t -> k2 = slope, L/(mg*min)
    best: str  # "first" | "second"

    @property
    def k1(self) -> float:
        return self.first.slope

    @property
    def k2(self) -> float:
        return self.second.slope

    @property
    def half_life_min(self) -> float | None:
        """t1/2 = ln2 / k1 (first-order)."""
        return math.log(2) / self.k1 if self.k1 > 0 else None


def linear_fit(x: list[float], y: list[float]) -> LinearFit:
    """Ordinary least squares with intercept — identical to Excel SLOPE, INTERCEPT, RSQ."""
    n = len(x)
    if n != len(y):
        raise ValueError("x va y uzunligi bir xil bo'lishi kerak.")
    if n < 2:
        raise ValidationError(["Regressiya uchun kamida 2 ta nuqta kerak."])
    mx, my = math.fsum(x) / n, math.fsum(y) / n
    sxx = math.fsum((a - mx) ** 2 for a in x)
    syy = math.fsum((b - my) ** 2 for b in y)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    if sxx == 0:
        raise ValidationError(["Regressiya uchun vaqt qiymatlari har xil bo'lishi kerak."])
    slope = sxy / sxx
    r2 = sxy**2 / (sxx * syy) if syy > 0 else 0.0
    return LinearFit(slope=slope, intercept=my - slope * mx, r2=r2, n=n)


def clean_points(times, concs) -> tuple[list[tuple[float, float]], list[str]]:
    """Drop unusable rows; return (sorted valid points, messages about skipped rows)."""
    valid: list[tuple[float, float]] = []
    skipped: list[str] = []
    for i, (t, c) in enumerate(zip(times, concs), start=1):
        try:
            t, c = float(t), float(c)
        except (TypeError, ValueError):
            skipped.append(f"{i}-qator: qiymat son emas yoki bo'sh — tashlab ketildi.")
            continue
        if not (math.isfinite(t) and math.isfinite(c)):
            skipped.append(f"{i}-qator: qiymat bo'sh — tashlab ketildi.")
        elif t < 0:
            skipped.append(f"{i}-qator: vaqt manfiy — tashlab ketildi.")
        elif c <= 0:
            skipped.append(f"{i}-qator: KXT noldan katta bo'lishi kerak — tashlab ketildi.")
        else:
            valid.append((t, c))
    valid.sort(key=lambda p: p[0])
    return valid, skipped


def analyze(times, concs, experiment: Experiment | None = None) -> tuple[KineticsResult, list[str]]:
    """Build the kinetic table and fit both models.

    The value at t = 0 is taken as C0. If `experiment` is given, Al dose, charge
    loading and energy are computed for every point from its I, U, V, phi.
    Returns (result, messages about skipped rows).
    """
    pts, skipped = clean_points(times, concs)
    errors = []
    if not pts or pts[0][0] != 0:
        errors.append("t = 0 dagi KXT qiymati (C₀) kiritilishi shart.")
    if len({t for t, _ in pts}) != len(pts):
        errors.append("Vaqt qiymatlari takrorlanmasligi kerak.")
    if len(pts) < MIN_POINTS:
        errors.append(f"Kinetik tahlil uchun kamida {MIN_POINTS} ta to'g'ri nuqta kerak.")
    if errors:
        raise ValidationError(errors + skipped)

    c0 = pts[0][1]
    rows = []
    for t, c in pts:
        m = experiment.at_time(t) if experiment is not None else None
        rows.append(
            KineticPoint(
                time_min=t,
                c_mg_L=c,
                c_ratio=c / c0,
                removal_pct=(c0 - c) / c0 * 100.0,
                ln_c0_c=math.log(c0 / c),
                inv_diff=1.0 / c - 1.0 / c0,
                dose_mg_L=m.dose_mg_L if m else None,
                charge_C_L=m.charge_C_L if m else None,
                energy_kWh_m3=m.energy_kWh_m3 if m else None,
            )
        )

    ts = [r.time_min for r in rows]
    first = linear_fit(ts, [r.ln_c0_c for r in rows])
    second = linear_fit(ts, [r.inv_diff for r in rows])
    best = "first" if first.r2 >= second.r2 else "second"
    return KineticsResult(c0_mg_L=c0, points=rows, first=first, second=second, best=best), skipped


def time_for_removal(target_pct: float, k1: float) -> float:
    """First-order time to reach a target removal: t = -ln(1 - R/100) / k1, min."""
    if not 0 < target_pct < 100:
        raise ValidationError(["Maqsadli samaradorlik 0 va 100 % orasida bo'lishi kerak."])
    if k1 <= 0:
        raise ValidationError(["k₁ musbat emas — KXT kamaymayapti, kerakli vaqtni hisoblab bo'lmaydi."])
    return -math.log(1.0 - target_pct / 100.0) / k1
