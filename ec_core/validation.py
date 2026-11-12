"""Input validation. Errors block the calculation; warnings do not."""

from __future__ import annotations

import math

# Power supply: Wanptek DPS3010U
MAX_CURRENT_A = 10.0
MAX_VOLTAGE_V = 30.0
J_RANGE_MA_CM2 = (1.0, 100.0)
PHI_RANGE = (0.8, 2.0)


class ValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


def _bad(x) -> bool:
    return x is None or not isinstance(x, (int, float)) or not math.isfinite(x)


def validate_inputs(
    *,
    current_A,
    voltage_V,
    time_min,
    volume_L,
    area_cm2,
    phi,
    c0_mg_L,
    c_mg_L,
    price_electricity=0.0,
    price_electrode=0.0,
    continuous=False,
    flow_L_h=None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    positive = [
        ("Tok kuchi I (A)", current_A),
        ("Kuchlanish U (V)", voltage_V),
        ("Suv hajmi V (L)", volume_L),
        ("Anod yuzasi A (cm²)", area_cm2),
        ("Tok samaradorligi φ", phi),
        ("Boshlang'ich KXT C₀ (mg/L)", c0_mg_L),
        ("Oxirgi KXT C (mg/L)", c_mg_L),
    ]
    if continuous:
        positive.append(("Oqim tezligi Q (L/soat)", flow_L_h))
    else:
        positive.append(("Vaqt t (min)", time_min))

    for label, value in positive:
        if _bad(value):
            errors.append(f"{label}: qiymat kiritilmagan yoki noto'g'ri.")
        elif value <= 0:
            errors.append(f"{label}: qiymat noldan katta bo'lishi kerak.")

    for label, value in [("Elektr narxi (so'm/kWh)", price_electricity), ("Elektrod narxi (so'm/kg)", price_electrode)]:
        if _bad(value):
            errors.append(f"{label}: qiymat kiritilmagan yoki noto'g'ri.")
        elif value < 0:
            errors.append(f"{label}: qiymat manfiy bo'lishi mumkin emas.")

    if errors:
        return errors, warnings

    if current_A > MAX_CURRENT_A:
        warnings.append(f"Tok kuchi {current_A:g} A — manba chegarasidan ({MAX_CURRENT_A:g} A, Wanptek DPS3010U) yuqori.")
    if voltage_V > MAX_VOLTAGE_V:
        warnings.append(f"Kuchlanish {voltage_V:g} V — manba chegarasidan ({MAX_VOLTAGE_V:g} V, Wanptek DPS3010U) yuqori.")
    j = current_A * 1000.0 / area_cm2
    if not J_RANGE_MA_CM2[0] <= j <= J_RANGE_MA_CM2[1]:
        warnings.append(
            f"Tok zichligi {j:.2f} mA/cm² — odatiy oraliqdan ({J_RANGE_MA_CM2[0]:g}–{J_RANGE_MA_CM2[1]:g} mA/cm²) tashqarida."
        )
    if not PHI_RANGE[0] <= phi <= PHI_RANGE[1]:
        warnings.append(f"Tok samaradorligi φ = {phi:g} — odatiy oraliqdan ({PHI_RANGE[0]:g}–{PHI_RANGE[1]:g}) tashqarida.")
    if c_mg_L > c0_mg_L:
        warnings.append("Oxirgi KXT boshlang'ichdan katta (C > C₀): samaradorlik manfiy, solishtirma energiya hisoblanmaydi.")
    elif c_mg_L == c0_mg_L:
        warnings.append("C = C₀: tozalash samaradorligi 0 %, solishtirma energiya hisoblanmaydi.")

    return errors, warnings
