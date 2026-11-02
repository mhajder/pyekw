"""
Utility functions for working with eKW numbers.
"""

import re

from .constants import CHARACTER_VALUES
from .constants import CHECK_DIGIT_LENGTH
from .constants import COURT_CODE_LENGTH
from .constants import KW_COMPACT_LENGTH
from .constants import REGISTER_NUMBER_LENGTH
from .generator import CheckDigitGenerator
from .generator import is_ascii_digits
from .models import KWInfo
from .models import KWValidationResult
from .validator import KWValidator

# Standard KW number with separators (slash, backslash or hyphen) and optional spaces
_SEPARATED_PATTERN = (
    r"\b([A-Z0-9]{4})[^\S\r\n]*[/\\-][^\S\r\n]*([0-9]{8})"
    r"[^\S\r\n]*[/\\-][^\S\r\n]*([0-9])\b"
)
# Compact 13-character KW number. The court code must start with two letters,
# so all-digit tokens such as ISBN-13 numbers or order IDs are not matched.
_COMPACT_PATTERN = r"\b([A-Z]{2}[A-Z0-9]{2})([0-9]{8})([0-9])\b"
_SEPARATED_RE = re.compile(_SEPARATED_PATTERN)
_SEPARATED_OR_COMPACT_RE = re.compile(f"{_SEPARATED_PATTERN}|{_COMPACT_PATTERN}")


class KWUtils:
    """Utility class for eKW number operations."""

    def __init__(self):
        """Initialize utilities with validator and court registry."""
        self.validator = KWValidator()
        self.court_registry = self.validator.court_registry

    def normalize_kw_number(
        self, kw_number: str, auto_pad: bool = False, compact: bool = False
    ) -> str:
        """
        Normalize a KW number to standard or compact format.

        Args:
            kw_number: The KW number to normalize (standard, compact, or with arbitrary separators)
            auto_pad: Whether to pad register numbers shorter than 8 digits with leading zeros
            compact: If True, return unseparated 13-character format (COURT12345678D);
                otherwise standard format (COURT/12345678/D)

        Returns:
            Normalized KW number
        """
        # Remove all whitespace, convert to uppercase and standardize separators to '/'
        clean = re.sub(r"[/\\-]+", "/", re.sub(r"\s+", "", kw_number.upper()))

        # Split an unseparated compact string. Only the exact 13-character form is
        # split: a shorter string is ambiguous (a missing check digit would silently
        # turn the last register digit into the check digit).
        if (
            "/" not in clean
            and len(clean) == KW_COMPACT_LENGTH
            and is_ascii_digits(clean[COURT_CODE_LENGTH:])
        ):
            c = clean[:COURT_CODE_LENGTH]
            r = clean[COURT_CODE_LENGTH:-CHECK_DIGIT_LENGTH]
            d = clean[-CHECK_DIGIT_LENGTH:]
            clean = f"{c}/{r}/{d}"

        # If auto_pad and has 3 parts, pad register number
        parts = clean.split("/")
        if auto_pad and len(parts) == 3:
            court, reg, check = parts
            if 1 <= len(reg) <= REGISTER_NUMBER_LENGTH and is_ascii_digits(reg):
                clean = f"{court}/{reg.zfill(REGISTER_NUMBER_LENGTH)}/{check}"

        if compact:
            parts = clean.split("/")
            if len(parts) == 3:
                return "".join(parts)

        return clean

    def extract_kw_numbers(self, text: str, include_compact: bool = False) -> list[str]:
        """
        Extract potential KW numbers from text.

        Args:
            text: Text to search for KW numbers
            include_compact: Whether to also extract 13-character compact KW numbers without slashes

        Returns:
            Potential KW numbers in the order they appear in the text (duplicates
            included), normalized to COURT/REGISTER/CHECK
        """
        pattern = _SEPARATED_OR_COMPACT_RE if include_compact else _SEPARATED_RE
        # Each match fills either the separated groups (1-3) or the compact ones (4-6)
        return [
            "/".join(group for group in match.groups() if group is not None)
            for match in pattern.finditer(text.upper())
        ]

    def validate_multiple_kw_numbers(
        self,
        kw_numbers: list[str],
        check_court: bool = True,
        auto_pad: bool = False,
    ) -> dict[str, KWValidationResult]:
        """
        Validate multiple KW numbers at once.

        Args:
            kw_numbers: List of KW numbers to validate
            check_court: Whether to validate court codes
            auto_pad: Whether to pad register numbers shorter than 8 digits

        Returns:
            Dictionary with validation results for each KW number
        """
        results: dict[str, KWValidationResult] = {}

        for kw_number in kw_numbers:
            normalized = self.normalize_kw_number(kw_number, auto_pad=auto_pad)
            is_valid, error = self.validator.validate_kw_number(
                normalized, check_court=check_court, auto_pad=auto_pad
            )

            result: KWValidationResult = {
                "original": kw_number,
                "normalized": normalized,
                "is_valid": is_valid,
                "error": error,
            }

            if is_valid:
                try:
                    court_code, register_number, check_digit = (
                        self.validator.parse_kw_number(normalized, auto_pad=auto_pad)
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
                            "circuit": self.court_registry.get_court_circuit(
                                court_code
                            ),
                            "voivodeship": self.court_registry.get_court_voivodeship(
                                court_code
                            ),
                            "compact": f"{court_code}{register_number}{check_digit}",
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

    def from_legacy(
        self, court_code: str, legacy_number: str | int, check_court: bool = True
    ) -> str:
        """
        Convert a legacy land registry number to a modern eKW number.

        Args:
            court_code: The 4-character court code (e.g. 'WA4M')
            legacy_number: Old book number (e.g. 12345, '12345', 'KW 12345', 'Dz.Kw. 987')
            check_court: Whether to verify that the court code exists in the registry

        Returns:
            Complete valid modern eKW number (e.g. 'WA4M/00012345/9')

        Raises:
            ValueError: If court_code is unknown (with check_court) or has invalid
                characters, or legacy_number contains no digits, several
                separate groups of digits or more than 8 digits.
        """
        court_clean = court_code.strip().upper()
        if check_court and not self.court_registry.is_valid_court(court_clean):
            raise ValueError(f"Invalid court code: {court_code}")

        # Extract the digits of the legacy book number. Several separate digit groups
        # (e.g. 'KW 123/45' or 'KW 12345 z 1990') are ambiguous, and joining them
        # would silently produce a different register number.
        digit_groups = re.findall(r"[0-9]+", str(legacy_number))
        if not digit_groups:
            raise ValueError(
                f"Legacy number must contain at least one digit: {legacy_number!r}"
            )
        if len(digit_groups) > 1:
            raise ValueError(
                f"Legacy number must contain a single group of digits: {legacy_number!r}"
            )
        digits = digit_groups[0]
        if len(digits) > REGISTER_NUMBER_LENGTH:
            raise ValueError(
                f"Legacy register number cannot exceed {REGISTER_NUMBER_LENGTH} digits, got {len(digits)}"
            )

        register_number = digits.zfill(REGISTER_NUMBER_LENGTH)
        return CheckDigitGenerator.generate_full_kw_number(court_clean, register_number)

    def get_kw_info(self, kw_number: str, auto_pad: bool = False) -> KWInfo | None:
        """
        Get detailed information about a KW number.

        Args:
            kw_number: The KW number to analyze
            auto_pad: Whether to pad register numbers shorter than 8 digits

        Returns:
            Dictionary with KW number information or None if invalid
        """
        normalized = self.normalize_kw_number(kw_number, auto_pad=auto_pad)
        is_valid, _error = self.validator.validate_kw_number(
            normalized, auto_pad=auto_pad
        )

        if not is_valid:
            return None

        try:
            court_code, register_number, check_digit = self.validator.parse_kw_number(
                normalized, auto_pad=auto_pad
            )

            return {
                "kw_number": normalized,
                "court_code": court_code,
                "court_name": self.court_registry.get_court_name(court_code),
                "court_full_name": self.court_registry.get_court_full_name(court_code),
                "circuit": self.court_registry.get_court_circuit(court_code),
                "voivodeship": self.court_registry.get_court_voivodeship(court_code),
                "register_number": register_number,
                "check_digit": int(check_digit),
                "compact": f"{court_code}{register_number}{check_digit}",
                "is_valid": True,
                "url": self.court_registry.get_official_url(),
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
