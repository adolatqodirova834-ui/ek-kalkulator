"""Electrode materials. To add a new one (e.g. Fe), add one entry to MATERIALS."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    symbol: str
    name: str  # display name (Uzbek)
    M: float  # molar mass, g/mol
    z: int  # electrons transferred per dissolved atom
    rho: float  # density, g/cm3


MATERIALS: dict[str, Material] = {
    "Al": Material(symbol="Al", name="Alyuminiy", M=26.98, z=3, rho=2.70),
    # "Fe": Material(symbol="Fe", name="Temir", M=55.845, z=2, rho=7.87),
}


def get_material(symbol: str) -> Material:
    try:
        return MATERIALS[symbol]
    except KeyError:
        raise ValueError(f"Noma'lum elektrod materiali: {symbol!r}") from None
