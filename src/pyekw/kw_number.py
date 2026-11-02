"""
First-class KWNumber value object for Polish eKW numbers.
"""

import functools
import json
import re
from dataclasses import dataclass
from typing import Any

from .constants import COURT_CODE_LENGTH
from .constants import REGISTER_NUMBER_LENGTH
from .courts import CourtRegistry
from .generator import CheckDigitGenerator
from .generator import is_ascii_digits
from .models import KWInfo
from .utils import KWUtils


@functools.cache
def _utils() -> KWUtils:
    """Shared KWUtils instance, so properties do not rebuild the court registry."""
    return KWUtils()


def _registry() -> CourtRegistry:
    return _utils().court_registry


@dataclass(frozen=True, slots=True, order=True)
class KWNumber:
    """
    Immutable value object representing a validated Polish land registry (eKW) number.

    Instances compare equal only to other KWNumber instances, never to strings
    (str(kw) == ... or KWNumber.from_string(...) can be used for that), so
    equality stays consistent with hashing.

    Attributes:
        court_code: 4-character court department code (e.g. 'WA4M')
        register_number: 8-digit land register number (e.g. '00123456')
        check_digit: 1-digit check digit (e.g. 4)
    """

    court_code: str
    register_number: str
    check_digit: int

    def __post_init__(self) -> None:
        if not isinstance(self.court_code, str):
            raise ValueError(f"Court code must be a string, got {self.court_code!r}")
        court = self.court_code.upper().strip()
        reg = str(self.register_number).strip()
        chk: object = self.check_digit
        if isinstance(chk, str) and is_ascii_digits(chk.strip()):
            chk = int(chk.strip())
        # bool is a subclass of int, but True/False are not check digits
        if isinstance(chk, bool) or not isinstance(chk, int):
            raise ValueError(
                f"Check digit must be an integer, got {self.check_digit!r}"
            )

        if len(court) != COURT_CODE_LENGTH or not re.fullmatch(r"[A-Z0-9]+", court):
            raise ValueError(
                f"Court code must be exactly {COURT_CODE_LENGTH} letters or digits,"
                f" got {self.court_code!r}"
            )
        if len(reg) != REGISTER_NUMBER_LENGTH or not is_ascii_digits(reg):
            raise ValueError(
                f"Register number must be exactly {REGISTER_NUMBER_LENGTH} digits,"
                f" got {self.register_number!r}"
            )
        if not (0 <= chk <= 9):
            raise ValueError(
                f"Check digit must be between 0 and 9, got {self.check_digit!r}"
            )

        expected_check = CheckDigitGenerator.calculate_check_digit(court, reg)
        if chk != expected_check:
            raise ValueError(
                f"Invalid check digit for {court}/{reg}: expected {expected_check}, got {chk}"
            )

        object.__setattr__(self, "court_code", court)
        object.__setattr__(self, "register_number", reg)
        object.__setattr__(self, "check_digit", chk)

    @classmethod
    def from_string(
        cls, kw_str: str, auto_pad: bool = False, check_court: bool = True
    ) -> "KWNumber":
        """
        Parse and validate a KW number from string.

        Args:
            kw_str: KW number string (standard 'WA4M/00123456/4' or compact 'WA4M001234564')
            auto_pad: Whether to pad register numbers shorter than 8 digits with leading zeros
            check_court: Whether to verify that the court code exists in the official registry

        Returns:
            Validated KWNumber instance

        Raises:
            ValueError: If the KW number is malformed or invalid
        """
        utils = _utils()
        normalized = utils.normalize_kw_number(kw_str, auto_pad=auto_pad)
        is_valid, error = utils.validator.validate_kw_number(
            normalized, check_court=check_court, allow_compact=True
        )
        if not is_valid:
            raise ValueError(f"Invalid KW number {kw_str!r}: {error}")

        court_code, register_number, check_digit = utils.validator.parse_kw_number(
            normalized, allow_compact=True
        )
        return cls(court_code, register_number, int(check_digit))

    @classmethod
    def from_parts(
        cls,
        court_code: str,
        register_number: str | int,
        auto_pad: bool = True,
        check_court: bool = True,
    ) -> "KWNumber":
        """
        Create a KWNumber from court code and register number, calculating the check digit.

        Args:
            court_code: 4-character court code
            register_number: 8-digit register number or integer (padded if auto_pad=True)
            auto_pad: Whether to pad register numbers shorter than 8 digits with zeros
            check_court: Whether to verify that the court code exists in the official registry

        Returns:
            KWNumber instance with calculated check digit

        Raises:
            ValueError: If court code or register number is invalid
        """
        court_clean = court_code.strip().upper()
        if check_court and not _registry().is_valid_court(court_clean):
            raise ValueError(f"Unknown court code: {court_code}")

        reg_str = str(register_number).strip()
        if (
            auto_pad
            and len(reg_str) <= REGISTER_NUMBER_LENGTH
            and is_ascii_digits(reg_str)
        ):
            reg_str = reg_str.zfill(REGISTER_NUMBER_LENGTH)

        check_digit = CheckDigitGenerator.calculate_check_digit(court_clean, reg_str)
        return cls(court_clean, reg_str, check_digit)

    @classmethod
    def from_legacy(
        cls,
        court_code: str,
        legacy_number: str | int,
        check_court: bool = True,
    ) -> "KWNumber":
        """
        Create a modern KWNumber from a legacy land registry number.

        Args:
            court_code: 4-character court code
            legacy_number: Old book number (e.g. 12345, 'KW 12345', 'Dz.Kw. 987')
            check_court: Whether to verify that the court code exists in the official registry

        Returns:
            Modern KWNumber instance
        """
        full_str = _utils().from_legacy(
            court_code, legacy_number, check_court=check_court
        )
        return cls.from_string(full_str, check_court=check_court)

    @property
    def formatted(self) -> str:
        """Standard formatted string representation: 'COURT/REGISTER/CHECK'."""
        return f"{self.court_code}/{self.register_number}/{self.check_digit}"

    @property
    def compact(self) -> str:
        """Compact 13-character string without separators: 'COURTREGISTERCHECK'."""
        return f"{self.court_code}{self.register_number}{self.check_digit}"

    @property
    def spaced(self) -> str:
        """Human-readable spaced format: 'COURT / REGISTER / CHECK'."""
        return f"{self.court_code} / {self.register_number} / {self.check_digit}"

    @property
    def court_name(self) -> str | None:
        """Short name of the court handling this book."""
        return _registry().get_court_name(self.court_code)

    @property
    def court_full_name(self) -> str | None:
        """Full territorial jurisdiction name of the court."""
        return _registry().get_court_full_name(self.court_code)

    @property
    def circuit(self) -> str | None:
        """Regional court circuit (Sąd Okręgowy) for this court."""
        return _registry().get_court_circuit(self.court_code)

    @property
    def voivodeship(self) -> str | None:
        """Voivodeship (województwo) where this court is located."""
        return _registry().get_court_voivodeship(self.court_code)

    @property
    def portal_url(self) -> str:
        """URL to the official Ministry of Justice eKW search portal."""
        return CourtRegistry.get_official_url()

    @property
    def portal_params(self) -> dict[str, str]:
        """Form parameters for the official Ministry of Justice eKW search portal."""
        return CourtRegistry.get_official_search_params(
            self.court_code, self.register_number, self.check_digit
        )

    @property
    def is_valid(self) -> bool:
        """Always True for constructed KWNumber instances."""
        return True

    def to_dict(self) -> KWInfo:
        """Export as a KWInfo dictionary."""
        return {
            "kw_number": self.formatted,
            "court_code": self.court_code,
            "court_name": self.court_name,
            "court_full_name": self.court_full_name,
            "circuit": self.circuit,
            "voivodeship": self.voivodeship,
            "register_number": self.register_number,
            "check_digit": self.check_digit,
            "compact": self.compact,
            "is_valid": True,
            "url": self.portal_url,
        }

    def to_json(self) -> str:
        """Export as a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def __str__(self) -> str:
        return self.formatted

    def __repr__(self) -> str:
        return f"KWNumber('{self.formatted}')"

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        """Pydantic V2 core schema hook for seamless validation in Pydantic models."""
        try:
            import importlib

            pydantic_core = importlib.import_module("pydantic_core")
            core_schema = pydantic_core.core_schema

            def validate(value: Any) -> "KWNumber":
                # Existing instances are accepted as-is (e.g. model_validate() on a
                # model's own field values), so only strings need parsing
                if isinstance(value, cls):
                    return value
                if isinstance(value, str):
                    return cls.from_string(value)
                raise ValueError("Expected a KW number string or KWNumber instance")

            return core_schema.json_or_python_schema(
                json_schema=core_schema.no_info_after_validator_function(
                    cls.from_string, core_schema.str_schema()
                ),
                python_schema=core_schema.no_info_plain_validator_function(validate),
                serialization=core_schema.to_string_ser_schema(),
            )
        except ImportError:  # pragma: no cover
            return handler(source_type)
