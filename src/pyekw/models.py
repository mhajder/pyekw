"""
Typed result structures returned by pyekw.
"""

from typing import TypedDict


class KWInfo(TypedDict):
    """Detailed information about a valid KW number, returned by KWUtils.get_kw_info()."""

    kw_number: str
    court_code: str
    court_name: str | None
    court_full_name: str | None
    register_number: str
    check_digit: int
    is_valid: bool


class _KWValidationResultBase(TypedDict):
    original: str
    normalized: str
    is_valid: bool
    error: str | None


class KWValidationResult(_KWValidationResultBase, total=False):
    """
    Validation result for one KW number, returned by KWUtils.validate_multiple_kw_numbers().

    The court and register fields are only present when the KW number is valid.
    """

    court_code: str
    register_number: str
    check_digit: str
    court_name: str | None
    court_full_name: str | None
