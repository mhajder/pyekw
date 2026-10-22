"""
PyeKW - Python library for Polish eKW (Elektroniczne Księgi Wieczyste).

This library provides utilities for working with Polish Land Registry (eKW) numbers,
including validation, check digit generation, and court code verification.
"""

from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _version

from .courts import CourtRegistry
from .generator import CheckDigitGenerator
from .models import KWInfo
from .models import KWValidationResult
from .utils import KWUtils
from .validator import KWValidator

try:
    __version__ = _version("pyekw")
except _PackageNotFoundError:  # running from a source tree without installing
    __version__ = "0.0.0"

__all__ = [
    "CheckDigitGenerator",
    "CourtRegistry",
    "KWInfo",
    "KWUtils",
    "KWValidationResult",
    "KWValidator",
    "__version__",
]
