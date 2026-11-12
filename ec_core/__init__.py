"""Electrocoagulation calculation core (no UI dependencies)."""

from .constants import FARADAY, MOLAR_VOLUME_ML
from .materials import MATERIALS, Material, get_material
from .models import Electrode, Experiment, Mode, PointMetrics, Reactor, Results
from .validation import ValidationError, validate_inputs
from .kinetics import KineticPoint, KineticsResult, LinearFit, analyze, linear_fit, time_for_removal

__all__ = [
    "FARADAY", "MOLAR_VOLUME_ML", "MATERIALS", "Material", "get_material",
    "Electrode", "Experiment", "Mode", "PointMetrics", "Reactor", "Results",
    "ValidationError", "validate_inputs",
    "KineticPoint", "KineticsResult", "LinearFit", "analyze", "linear_fit", "time_for_removal",
]
