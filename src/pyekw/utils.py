"""
Utility functions for working with eKW numbers.
"""

import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .courts import CourtRegistry
from .generator import CheckDigitGenerator
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

    def extract_kw_numbers(self, text: str) -> List[str]:
        """
        Extract potential KW numbers from text.

        Args:
            text: Text to search for KW numbers

        Returns:
            List of potential KW numbers found in the text
        """
        # Pattern for KW numbers: letters/digits + / + 8 digits + / + 1 digit
        pattern = r"\b[A-Z0-9]{2,6}/\d{8}/\d\b"
        matches = re.findall(pattern, text.upper())
        return matches

    def validate_multiple_kw_numbers(
        self, kw_numbers: List[str], check_court: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate multiple KW numbers at once.

        Args:
            kw_numbers: List of KW numbers to validate
            check_court: Whether to validate court codes

        Returns:
            Dictionary with validation results for each KW number
        """
        results = {}

        for kw_number in kw_numbers:
            normalized = self.normalize_kw_number(kw_number)
            is_valid, error = self.validator.validate_kw_number(normalized, check_court)

            result = {
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
    ) -> List[str]:
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

    def get_kw_info(self, kw_number: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a KW number.

        Args:
            kw_number: The KW number to analyze

        Returns:
            Dictionary with KW number information or None if invalid
        """
        normalized = self.normalize_kw_number(kw_number)
        is_valid, error = self.validator.validate_kw_number(normalized)

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

    def suggest_corrections(self, kw_number: str) -> List[str]:
        """
        Suggest possible corrections for an invalid KW number.

        Args:
            kw_number: The potentially invalid KW number

        Returns:
            List of suggested corrections
        """
        suggestions = []
        normalized = self.normalize_kw_number(kw_number)

        try:
            court_code, register_number, provided_check_digit = (
                self.validator.parse_kw_number(normalized)
            )

            # Suggest correct check digit
            correct_check_digit = CheckDigitGenerator.calculate_check_digit(
                court_code, register_number
            )
            if str(correct_check_digit) != provided_check_digit:
                corrected = f"{court_code}/{register_number}/{correct_check_digit}"
                suggestions.append(corrected)

            # If court code is invalid, suggest similar ones
            if not self.court_registry.is_valid_court(court_code):
                similar_courts = self.court_registry.search_courts(court_code[:2])
                for similar_code, _ in similar_courts[:3]:  # Top 3 suggestions
                    corrected_check_digit = CheckDigitGenerator.calculate_check_digit(
                        similar_code, register_number
                    )
                    corrected = (
                        f"{similar_code}/{register_number}/{corrected_check_digit}"
                    )
                    suggestions.append(corrected)

        except ValueError:
            # If parsing fails completely, can't suggest much
            pass

        return suggestions
