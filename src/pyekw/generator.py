"""
Check digit generator for Polish eKW numbers.
"""

from .constants import CHARACTER_VALUES
from .constants import COURT_CODE_LENGTH
from .constants import REGISTER_NUMBER_LENGTH
from .constants import WEIGHTS


def is_ascii_digits(value: str) -> bool:
    """Check if a string contains only ASCII digits (str.isdigit() also accepts e.g. '²')."""
    return value.isascii() and value.isdigit()


class CheckDigitGenerator:
    """Generator for eKW check digits."""

    @staticmethod
    def calculate_check_digit(court_code: str, register_number: str) -> int:
        """
        Calculate the check digit for a given court code and register number.

        Args:
            court_code: The court code (e.g., 'WA4M')
            register_number: The 8-digit register number (e.g., '00123456')

        Returns:
            The calculated check digit (0-9)

        Raises:
            ValueError: If input contains invalid characters or wrong length
        """
        # Combine court code and register number
        full_number = court_code.upper() + register_number

        # Validate input
        if len(court_code) != COURT_CODE_LENGTH:
            raise ValueError(
                f"Court code must be exactly {COURT_CODE_LENGTH} characters, got {len(court_code)}"
            )

        if len(register_number) != REGISTER_NUMBER_LENGTH:
            raise ValueError(
                f"Register number must be exactly {REGISTER_NUMBER_LENGTH} digits, got {len(register_number)}"
            )

        if not is_ascii_digits(register_number):
            raise ValueError("Register number must contain only digits")

        # Validate court code characters
        for char in court_code.upper():
            if char not in CHARACTER_VALUES:
                raise ValueError(f"Invalid character '{char}' in court code")

        # Calculate weighted sum
        total = 0
        for char, weight in zip(full_number, WEIGHTS, strict=True):
            total += CHARACTER_VALUES[char] * weight

        return total % 10

    @staticmethod
    def generate_full_kw_number(court_code: str, register_number: str) -> str:
        """
        Generate a complete KW number with check digit.

        Args:
            court_code: The court code (e.g., 'WA4M')
            register_number: The 8-digit register number (e.g., '00123456')

        Returns:
            Complete KW number in format: court_code/register_number/check_digit
        """
        check_digit = CheckDigitGenerator.calculate_check_digit(
            court_code, register_number
        )
        return f"{court_code.upper()}/{register_number}/{check_digit}"
