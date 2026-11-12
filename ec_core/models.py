"""Domain classes: Electrode, Reactor, Experiment and the Results container."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum

from .constants import FARADAY, H2_ELECTRONS, MOLAR_VOLUME_ML
from .materials import Material, get_material
from .validation import ValidationError, validate_inputs


class Mode(str, Enum):
    BATCH = "batch"  # davriy
    CONTINUOUS = "continuous"  # uzluksiz


@dataclass(frozen=True)
class Electrode:
    material: Material
    area_cm2: float  # total active anode area
    phi: float = 1.0  # current (faradaic) efficiency

    @classmethod
    def of(cls, symbol: str, area_cm2: float, phi: float = 1.0) -> "Electrode":
        return cls(get_material(symbol), area_cm2, phi)

    def dissolved_mass_g(self, current_A: float, time_s: float) -> float:
        """Formula 1 (Faraday's law): m = I*t*M / (z*F) * phi."""
        mat = self.material
        return current_A * time_s * mat.M / (mat.z * FARADAY) * self.phi

    def current_density_mA_cm2(self, current_A: float) -> float:
        """Formula 3: j = I*1000 / A."""
        return current_A * 1000.0 / self.area_cm2

    def thickness_loss_mm(self, mass_g: float) -> float:
        """Formula 10: m / (rho*A) * 10  (cm -> mm)."""
        return mass_g / (self.material.rho * self.area_cm2) * 10.0


@dataclass(frozen=True)
class Reactor:
    volume_L: float
    mode: Mode = Mode.BATCH
    flow_L_h: float | None = None  # continuous mode only

    @property
    def hrt_min(self) -> float | None:
        """Hydraulic retention time V/Q in minutes (continuous mode)."""
        if self.mode is Mode.CONTINUOUS and self.flow_L_h:
            return self.volume_L / self.flow_L_h * 60.0
        return None

    def treatment_time_min(self, batch_time_min: float | None) -> float:
        """Batch: electrolysis time t. Continuous: HRT = V/Q."""
        if self.mode is Mode.CONTINUOUS:
            hrt = self.hrt_min
            if hrt is None:
                raise ValidationError(["Uzluksiz rejim uchun oqim tezligi Q (L/soat) kiritilishi shart."])
            return hrt
        if batch_time_min is None:
            raise ValidationError(["Davriy rejim uchun vaqt t (min) kiritilishi shart."])
        return batch_time_min


@dataclass(frozen=True)
class PointMetrics:
    """Time-dependent quantities at an arbitrary treatment time."""

    time_min: float
    mass_g: float
    dose_mg_L: float
    charge_C_L: float
    energy_kWh_m3: float
    electrode_kg_m3: float


@dataclass(frozen=True)
class Results:
    mode: str
    time_min: float  # treatment time used (t or HRT)
    mass_g: float  # 1
    dose_mg_L: float  # 2
    current_density_mA_cm2: float  # 3
    charge_C_L: float  # 4
    energy_kWh_m3: float  # 5
    electrode_kg_m3: float  # 6
    removal_pct: float  # 7
    specific_energy_kWh_kg: float | None  # 8 (None if C >= C0)
    cost_sum_m3: float  # 9
    # 10 and 11 depend on operating time. Batch: totals over t.
    # Continuous: per hour of operation (see `per_hour`).
    thickness_loss_mm: float  # 10
    h2_mL: float  # 11
    per_hour: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Experiment:
    electrode: Electrode
    reactor: Reactor
    current_A: float
    voltage_V: float
    time_min: float | None  # batch electrolysis time; ignored in continuous mode
    c0_mg_L: float
    c_mg_L: float
    price_electricity: float = 0.0  # so'm/kWh
    price_electrode: float = 0.0  # so'm/kg

    # ---- validation -------------------------------------------------
    def validate(self) -> tuple[list[str], list[str]]:
        """Return (errors, warnings) as Uzbek messages."""
        return validate_inputs(
            current_A=self.current_A,
            voltage_V=self.voltage_V,
            time_min=self.time_min,
            volume_L=self.reactor.volume_L,
            area_cm2=self.electrode.area_cm2,
            phi=self.electrode.phi,
            c0_mg_L=self.c0_mg_L,
            c_mg_L=self.c_mg_L,
            price_electricity=self.price_electricity,
            price_electrode=self.price_electrode,
            continuous=self.reactor.mode is Mode.CONTINUOUS,
            flow_L_h=self.reactor.flow_L_h,
        )

    # ---- time-dependent part (reused by the kinetics module) --------
    def at_time(self, time_min: float) -> PointMetrics:
        t_s = time_min * 60.0
        t_h = time_min / 60.0
        v = self.reactor.volume_L
        m = self.electrode.dissolved_mass_g(self.current_A, t_s)
        return PointMetrics(
            time_min=time_min,
            mass_g=m,
            dose_mg_L=m * 1000.0 / v,  # 2
            charge_C_L=self.current_A * t_s / v,  # 4
            energy_kWh_m3=self.voltage_V * self.current_A * t_h / v,  # 5 (Wh/L == kWh/m3)
            electrode_kg_m3=m / v,  # 6 (g/L == kg/m3)
        )

    def h2_volume_mL(self, time_min: float) -> float:
        """Formula 11: I*t / (2F) * 22414."""
        return self.current_A * time_min * 60.0 / (H2_ELECTRONS * FARADAY) * MOLAR_VOLUME_ML

    # ---- full calculation -------------------------------------------
    def calculate(self) -> Results:
        errors, _ = self.validate()
        if errors:
            raise ValidationError(errors)

        t = self.reactor.treatment_time_min(self.time_min)
        p = self.at_time(t)

        removed = self.c0_mg_L - self.c_mg_L
        removal_pct = removed / self.c0_mg_L * 100.0  # 7
        specific = p.energy_kWh_m3 / (removed / 1000.0) if removed > 0 else None  # 8
        cost = self.price_electricity * p.energy_kWh_m3 + self.price_electrode * p.electrode_kg_m3  # 9

        continuous = self.reactor.mode is Mode.CONTINUOUS
        t_op = 60.0 if continuous else t  # operating-time basis for 10 and 11
        m_op = self.electrode.dissolved_mass_g(self.current_A, t_op * 60.0)

        return Results(
            mode=self.reactor.mode.value,
            time_min=t,
            mass_g=p.mass_g,
            dose_mg_L=p.dose_mg_L,
            current_density_mA_cm2=self.electrode.current_density_mA_cm2(self.current_A),
            charge_C_L=p.charge_C_L,
            energy_kWh_m3=p.energy_kWh_m3,
            electrode_kg_m3=p.electrode_kg_m3,
            removal_pct=removal_pct,
            specific_energy_kWh_kg=specific,
            cost_sum_m3=cost,
            thickness_loss_mm=self.electrode.thickness_loss_mm(m_op),
            h2_mL=self.h2_volume_mL(t_op),
            per_hour=continuous,
        )
