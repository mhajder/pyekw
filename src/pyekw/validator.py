"""
Validator for Polish eKW numbers.
"""

import re

from .constants import CHECK_DIGIT_LENGTH
from .constants import COURT_CODE_LENGTH
from .constants import KW_COMPACT_LENGTH
from .constants import KW_PARTS_COUNT
from .constants import REGISTER_NUMBER_LENGTH
from .courts import CourtRegistry
from .generator import CheckDigitGenerator
from .generator import is_ascii_digits


class KWValidator:
    """Validator for eKW (Land Registry) numbers."""

    def __init__(self):
        """Initialize the validator with court registry."""
        self.court_registry = CourtRegistry()

    def parse_kw_number(
        self,
        kw_number: str,
        auto_pad: bool = False,
        allow_compact: bool = False,
    ) -> tuple[str, str, str]:
        """
        Parse a KW number into its components.

        Args:
            kw_number: The KW number to parse (e.g., 'WA4M/00123456/4')
            auto_pad: Whether to pad register numbers shorter than 8 digits with leading zeros
            allow_compact: Whether to accept unseparated 13-character compact format

        Returns:
            Tuple of (court_code, register_number, check_digit)

        Raises:
            ValueError: If the KW number format is invalid
        """
        # Remove whitespace and convert to uppercase
        clean = kw_number.strip().upper()

        if allow_compact and "/" not in clean and len(clean) == KW_COMPACT_LENGTH:
            parts = [
                clean[:COURT_CODE_LENGTH],
                clean[COURT_CODE_LENGTH:-CHECK_DIGIT_LENGTH],
                clean[-CHECK_DIGIT_LENGTH:],
            ]
        else:
            parts = clean.split("/")

        if len(parts) != KW_PARTS_COUNT:
            raise ValueError(
                f"KW number must have exactly {KW_PARTS_COUNT} parts separated by '/', got {len(parts)}"
            )

        court_code, register_number, check_digit = parts

        if (
            auto_pad
            and (1 <= len(register_number) <= REGISTER_NUMBER_LENGTH)
            and is_ascii_digits(register_number)
        ):
            register_number = register_number.zfill(REGISTER_NUMBER_LENGTH)

        # Validate register number
        if len(register_number) != REGISTER_NUMBER_LENGTH:
            raise ValueError(
                f"Register number must be exactly {REGISTER_NUMBER_LENGTH} digits, got {len(register_number)}"
            )

        if not is_ascii_digits(register_number):
            raise ValueError("Register number must contain only digits")

        # Validate check digit
        if len(check_digit) != CHECK_DIGIT_LENGTH:
            raise ValueError(
                f"Check digit must be exactly {CHECK_DIGIT_LENGTH} digit, got {len(check_digit)}"
            )

        if not is_ascii_digits(check_digit):
            raise ValueError("Check digit must be a single digit")

        # Validate court code format (letters and digits only)
        if len(court_code) != COURT_CODE_LENGTH:
            raise ValueError(
                f"Court code must be exactly {COURT_CODE_LENGTH} characters, got {len(court_code)}"
            )

        if not re.fullmatch(r"[A-Z0-9]+", court_code):
            raise ValueError("Court code must contain only letters and digits")

        return court_code, register_number, check_digit

    def validate_court_code(self, court_code: str) -> bool:
        """
        Validate if a court code exists in the registry.

        Args:
            court_code: The court code to validate

        Returns:
            True if the court code is valid, False otherwise
        """
        return self.court_registry.is_valid_court(court_code)

    def validate_check_digit(
        self, court_code: str, register_number: str, check_digit: str
    ) -> bool:
        """
        Validate if the check digit is correct for given court code and register number.

        Args:
            court_code: The court code
            register_number: The 8-digit register number
            check_digit: The check digit to validate

        Returns:
            True if the check digit is correct, False otherwise
        """
        try:
            expected_check_digit = CheckDigitGenerator.calculate_check_digit(
                court_code, register_number
            )
            return str(expected_check_digit) == check_digit
        except ValueError:
            return False

    def validate_kw_number(
        self,
        kw_number: str,
        check_court: bool = True,
        auto_pad: bool = False,
        allow_compact: bool = False,
    ) -> tuple[bool, str | None]:
        """
        Validate a complete KW number.

        Args:
            kw_number: The KW number to validate
            check_court: Whether to validate the court code against the registry
            auto_pad: Whether to pad register numbers shorter than 8 digits with leading zeros
            allow_compact: Whether to accept unseparated 13-character compact format

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is None
        """
        try:
            # Parse the KW number
            court_code, register_number, check_digit = self.parse_kw_number(
                kw_number, auto_pad=auto_pad, allow_compact=allow_compact
            )

            # Validate court code if requested
            if check_court and not self.validate_court_code(court_code):
                return False, f"Unknown court code: {court_code}"

            # Validate check digit
            if not self.validate_check_digit(court_code, register_number, check_digit):
                expected = CheckDigitGenerator.calculate_check_digit(
                    court_code, register_number
                )
                return (
                    False,
                    f"Invalid check digit: expected {expected}, got {check_digit}",
                )

            return True, None

        except ValueError as e:
            return False, str(e)

    def is_valid_kw_number(
        self,
        kw_number: str,
        check_court: bool = True,
        auto_pad: bool = False,
        allow_compact: bool = False,
    ) -> bool:
        """
        Check if a KW number is valid.

        Args:
            kw_number: The KW number to validate
            check_court: Whether to validate the court code against the registry
            auto_pad: Whether to pad register numbers shorter than 8 digits with leading zeros
            allow_compact: Whether to accept unseparated 13-character compact format

        Returns:
            True if the KW number is valid, False otherwise
        """
        is_valid, _ = self.validate_kw_number(
            kw_number,
            check_court=check_court,
            auto_pad=auto_pad,
            allow_compact=allow_compact,
        )
        return is_valid
