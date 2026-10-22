"""
Utility functions for working with eKW numbers.
"""

import re

from .constants import CHARACTER_VALUES
from .courts import CourtRegistry
from .generator import CheckDigitGenerator
from .models import KWInfo
from .models import KWValidationResult
from .validator import KWValidator


class KWUtils:
    """Utility class for eKW number operations."""

    def __init__(self):
        """Initialize utilities with validator and court registry."""
        self.validator = KWValidator()
        self.court_registry = CourtRegistry()

    def normalize_kw_number(self, kw_number: str) -> str:
        """
        Normalize a KW number to standard format.

        Args:
            kw_number: The KW number to normalize

        Returns:
            Normalized KW number in format: COURT/12345678/D
        """
        # Remove all whitespace and convert to uppercase
        normalized = re.sub(r"\s+", "", kw_number.upper())

        # Ensure proper separator format
        normalized = re.sub(r"[/\\-]+", "/", normalized)

        return normalized

    def extract_kw_numbers(self, text: str) -> list[str]:
        """
        Extract potential KW numbers from text.

        Args:
            text: Text to search for KW numbers

        Returns:
            List of potential KW numbers found in the text
        """
        # Pattern for KW numbers: 4 letters/digits + / + 8 digits + / + 1 digit,
        # allowing horizontal whitespace (e.g. spaces, tabs, non-breaking spaces)
        # around the separators
        pattern = r"\b([A-Z0-9]{4})[^\S\r\n]*/[^\S\r\n]*([0-9]{8})[^\S\r\n]*/[^\S\r\n]*([0-9])\b"
        matches = re.findall(pattern, text.upper())
        return ["/".join(parts) for parts in matches]

    def validate_multiple_kw_numbers(
        self, kw_numbers: list[str], check_court: bool = True
    ) -> dict[str, KWValidationResult]:
        """
        Validate multiple KW numbers at once.

        Args:
            kw_numbers: List of KW numbers to validate
            check_court: Whether to validate court codes

        Returns:
            Dictionary with validation results for each KW number
        """
        results: dict[str, KWValidationResult] = {}

        for kw_number in kw_numbers:
            normalized = self.normalize_kw_number(kw_number)
            is_valid, error = self.validator.validate_kw_number(normalized, check_court)

            result: KWValidationResult = {
                "original": kw_number,
                "normalized": normalized,
                "is_valid": is_valid,
                "error": error,
            }

            if is_valid:
                try:
                    court_code, register_number, check_digit = (
                        self.validator.parse_kw_number(normalized)
                    )
                    result.update(
                        {
                            "court_code": court_code,
                            "register_number": register_number,
                            "check_digit": check_digit,
                            "court_name": self.court_registry.get_court_name(
                                court_code
                            ),
                            "court_full_name": self.court_registry.get_court_full_name(
                                court_code
                            ),
                        }
                    )
                except ValueError:
                    pass

            results[normalized] = result

        return results

    def generate_kw_number_variants(
        self, court_code: str, base_number: int, count: int = 10
    ) -> list[str]:
        """
        Generate a series of KW numbers starting from a base number.

        Args:
            court_code: The court code to use
            base_number: Starting register number (will be padded to 8 digits)
            count: Number of KW numbers to generate

        Returns:
            List of generated KW numbers
        """
        if not self.court_registry.is_valid_court(court_code):
            raise ValueError(f"Invalid court code: {court_code}")

        variants = []
        for i in range(count):
            register_number = f"{base_number + i:08d}"
            kw_number = CheckDigitGenerator.generate_full_kw_number(
                court_code, register_number
            )
            variants.append(kw_number)

        return variants

    def get_kw_info(self, kw_number: str) -> KWInfo | None:
        """
        Get detailed information about a KW number.

        Args:
            kw_number: The KW number to analyze

        Returns:
            Dictionary with KW number information or None if invalid
        """
        normalized = self.normalize_kw_number(kw_number)
        is_valid, _error = self.validator.validate_kw_number(normalized)

        if not is_valid:
            return None

        try:
            court_code, register_number, check_digit = self.validator.parse_kw_number(
                normalized
            )

            return {
                "kw_number": normalized,
                "court_code": court_code,
                "court_name": self.court_registry.get_court_name(court_code),
                "court_full_name": self.court_registry.get_court_full_name(court_code),
                "register_number": register_number,
                "check_digit": int(check_digit),
                "is_valid": True,
            }
        except ValueError:
            return None

    def suggest_corrections(
        self, kw_number: str, check_court: bool = True
    ) -> list[str]:
        """
        Suggest possible corrections for an invalid KW number.

        Args:
            kw_number: The potentially invalid KW number
            check_court: Whether the court code must exist in the registry. If False,
                any court code is accepted and only the check digit is corrected.

        Returns:
            List of suggested corrections
        """
        suggestions = []
        normalized = self.normalize_kw_number(kw_number)

        try:
            court_code, register_number, provided_check_digit = (
                self.validator.parse_kw_number(normalized)
            )
        except ValueError:
            # If parsing fails completely, can't suggest much
            return suggestions

        court_code_is_accepted = self.court_registry.is_valid_court(court_code) or (
            not check_court and all(char in CHARACTER_VALUES for char in court_code)
        )
        if court_code_is_accepted:
            # Known (or accepted) court: only the check digit can be wrong
            correct_check_digit = CheckDigitGenerator.calculate_check_digit(
                court_code, register_number
            )
            if str(correct_check_digit) != provided_check_digit:
                suggestions.append(
                    f"{court_code}/{register_number}/{correct_check_digit}"
                )
        else:
            # Unknown court code: suggest similar known ones
            for similar_code in self._similar_court_codes(court_code):
                corrected_check_digit = CheckDigitGenerator.calculate_check_digit(
                    similar_code, register_number
                )
                suggestions.append(
                    f"{similar_code}/{register_number}/{corrected_check_digit}"
                )

        return suggestions

    def _similar_court_codes(
        self, court_code: str, max_distance: int = 2, limit: int = 3
    ) -> list[str]:
        """Find known court codes that differ from court_code in at most max_distance positions."""
        distances = [
            (sum(a != b for a, b in zip(code, court_code, strict=True)), code)
            for code in self.court_registry.get_all_courts()
            if len(code) == len(court_code)
        ]
        return [
            code for distance, code in sorted(distances) if distance <= max_distance
        ][:limit]
