"""The `mckit_nuclides` package.

Provides information on chemical elements and nuclides as Polars tables.
"""

from __future__ import annotations

from importlib import metadata as _meta
from importlib.metadata import PackageNotFoundError, version

from .abundance import (
    MOLAR_MASS_TABLE,
    convert_to_atomic_fraction,
    expand_df_natural_presence,
    expand_natural_presence,
    normalize_column,
)
from .constants import (
    ATOMIC_MASS_CONSTANT,
    ATOMIC_MASS_CONSTANT_IN_MEV,
    AVOGADRO,
    NEUTRON_HALF_LIFE,
    NEUTRON_MASS,
    NEUTRON_MASS_IN_MEV,
)
from .elements import (
    ELEMENTS_PARQUET,
    ELEMENTS_TABLE_PL,
    SYMBOL_TO_Z,
    Z_TO_SYMBOL,
    atomic_mass,
    atomic_number,
    from_molecular_formula,
    symbol,
    z,
)
from .elements import get_property as get_element_property
from .nuclides import NUCLIDES_PARQUET, NUCLIDES_TABLE_PL, get_nuclide_mass
from .nuclides import get_property as get_nuclide_property

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

__distribution__ = _meta.distribution(__name__)
__meta_data__ = __distribution__.metadata
__author__ = __meta_data__["Author"]
__author_email__ = __meta_data__["Author-email"]
__license__ = __meta_data__["License"]
__summary__ = __meta_data__["Summary"]
__copyright__ = f"Copyright 2021 {__author__}"

__all__ = [
    "ATOMIC_MASS_CONSTANT",
    "ATOMIC_MASS_CONSTANT_IN_MEV",
    "AVOGADRO",
    "ELEMENTS_PARQUET",
    "ELEMENTS_TABLE_PL",
    "MOLAR_MASS_TABLE",
    "NEUTRON_HALF_LIFE",
    "NEUTRON_MASS",
    "NEUTRON_MASS_IN_MEV",
    "NUCLIDES_PARQUET",
    "NUCLIDES_TABLE_PL",
    "SYMBOL_TO_Z",
    "Z_TO_SYMBOL",
    "atomic_mass",
    "atomic_number",
    "convert_to_atomic_fraction",
    "expand_df_natural_presence",
    "expand_natural_presence",
    "from_molecular_formula",
    "get_element_property",
    "get_nuclide_mass",
    "get_nuclide_property",
    "normalize_column",
    "symbol",
    "z",
]
