"""
Pytest configuration and fixtures.
"""

import pytest

from pyekw.courts import CourtRegistry
from pyekw.generator import CheckDigitGenerator
from pyekw.utils import KWUtils
from pyekw.validator import KWValidator


@pytest.fixture
def registry():
    return CourtRegistry()


@pytest.fixture
def valid_courts():
    return ["WA4M", "BB1B", "KR1P", "CIKW", "GD1G"]


@pytest.fixture
def invalid_courts():
    return ["XXXX", "INVALID", "1234", "", "ZZZZ"]


@pytest.fixture
def known_courts():
    return {
        "WA4M": "WARSZAWA (X)",
        "BB1B": "BIELSKO-BIAŁA",
        "CIKW": "WARSZAWA",
        "KR1P": "KRAKÓW",
    }


@pytest.fixture
def generator():
    return CheckDigitGenerator()


@pytest.fixture
def valid_test_cases():
    """Known valid court code and register number combinations with expected check digits."""
    return [
        ("WA4M", "00123456", 4),
        ("BB1B", "12345678", 7),
        ("CIKW", "00000001", 5),
        ("KR1P", "99999999", 3),
        ("GD1G", "11111111", 5),
    ]


@pytest.fixture
def invalid_court_codes():
    """Invalid court codes for testing error handling."""
    return [
        "INVALID",  # Contains invalid character 'V'
        "WA4Q",  # Contains invalid character 'Q'
        "WA4V",  # Contains invalid character 'V'
        "",  # Empty string
    ]


@pytest.fixture
def invalid_register_numbers():
    """Invalid register numbers for testing error handling."""
    return [
        "1234567",  # Too short (7 digits)
        "123456789",  # Too long (9 digits)
        "123abc45",  # Contains letters
        "1234567a",  # Contains letter at end
        "",  # Empty string
        "12345678 ",  # Contains space
        "12-345678",  # Contains hyphen
    ]


@pytest.fixture
def edge_case_inputs():
    """Edge case inputs for comprehensive testing."""
    return [
        ("A", "00000000"),  # Single character court code
        ("ABCD", "00000000"),  # Maximum length court code
        ("WA4M", "00000000"),  # All zeros register number
        ("WA4M", "99999999"),  # All nines register number
    ]


@pytest.fixture
def utils():
    return KWUtils()


@pytest.fixture
def valid_kw_numbers():
    """Valid KW numbers for testing."""
    return [
        "WA4M/00123456/4",
        "BB1B/12345678/7",
        "CIKW/00000001/5",
        "KR1P/99999999/3",
    ]


@pytest.fixture
def invalid_kw_numbers():
    """Invalid KW numbers for testing."""
    return [
        "WA4M/00123456/9",  # Wrong check digit
        "XXXX/12345678/1",  # Invalid court code
        "WA4M/1234567/2",  # Wrong register number length
        "WA4M/1234567a/2",  # Non-digit in register number
        "",  # Empty string
        "INVALID",  # Not a KW number format
        "WA4M/123456789/2",  # Register number too long
        "WA4M/00123456",  # Missing check digit
    ]


@pytest.fixture
def unnormalized_kw_numbers():
    """KW numbers that need normalization."""
    return [
        ("WA4M / 00123456 / 4", "WA4M/00123456/4"),
        ("wa4m\\00123456\\4", "WA4M/00123456/4"),
        ("WA4M-00123456-4", "WA4M/00123456/4"),
        ("  WA4M  /  00123456  /  4  ", "WA4M/00123456/4"),
        ("wa4m//00123456//4", "WA4M/00123456/4"),
    ]


@pytest.fixture
def invalid_kw_numbers_that_normalize_to_valid():
    """KW numbers that are invalid in format but normalize to valid ones."""
    return [
        "WA4M-00123456-4",  # Wrong separators but normalizes to valid
        "  wa4m / 00123456 / 4  ",  # Spacing and case issues but normalizes to valid
    ]


@pytest.fixture
def text_with_kw_numbers():
    """Text containing KW numbers for extraction testing."""
    return """
    Please check the following land registry numbers:
    WA4M/00123456/4 and BB1B/12345678/7.
    Also verify CIKW/00000001/5 in the documents.
    Invalid format: WA4M-123456-2 should not be matched.
    Another valid one: KR1P/99999999/3.
    """


@pytest.fixture
def kw_numbers_for_batch_validation():
    """Mixed valid and invalid KW numbers for batch testing."""
    return [
        "WA4M/00123456/4",  # Valid
        "BB1B/12345678/9",  # Invalid check digit
        "XXXX/12345678/1",  # Invalid court code
        "CIKW/00000001/5",  # Valid
        "WA4M/1234567/2",  # Invalid register number length
    ]


@pytest.fixture
def correction_test_cases():
    """KW numbers that need corrections."""
    return [
        ("WA4M/00123456/9", "WA4M/00123456/4"),  # Wrong check digit
        ("BB1B/12345678/1", "BB1B/12345678/7"),  # Wrong check digit
        ("XXXX/12345678/1", None),  # Invalid court code (no simple correction)
    ]


@pytest.fixture
def validator():
    return KWValidator()


@pytest.fixture
def malformed_kw_numbers():
    """KW numbers with various format issues for parsing tests."""
    return [
        "WA4M/00123456",  # Missing check digit
        "WA4M/00123456/4/extra",  # Too many parts
        "WA4M-00123456-4",  # Wrong separators
        "WA4M",  # Only court code
        "/00123456/4",  # Missing court code
        "WA4M//4",  # Missing register number
        "",  # Empty string
        "   ",  # Only whitespace
    ]


@pytest.fixture
def invalid_register_numbers_for_parsing():
    """Invalid register numbers for parsing validation."""
    return [
        "WA4M/1234567/4",  # Too short (7 digits)
        "WA4M/123456789/4",  # Too long (9 digits)
        "WA4M/1234567a/4",  # Contains letter
        "WA4M/12345-78/4",  # Contains hyphen
        "WA4M/ 2345678/4",  # Contains space
        "WA4M/12345678 /4",  # Trailing space
    ]


@pytest.fixture
def invalid_check_digits_for_parsing():
    """Invalid check digits for parsing validation."""
    return [
        "WA4M/12345678/",  # Empty check digit
        "WA4M/12345678/12",  # Too long (2 digits)
        "WA4M/12345678/a",  # Letter instead of digit
        "WA4M/12345678/-",  # Special character
        "WA4M/12345678/ ",  # Space
    ]


@pytest.fixture
def invalid_court_codes_for_parsing():
    """Invalid court codes for parsing validation."""
    return [
        "WA-4M/12345678/2",  # Contains hyphen
        "WA 4M/12345678/2",  # Contains space
        "WA4M!/12345678/2",  # Contains special character
        "wa4m/12345678/2",  # Lowercase (should be handled by normalization)
    ]


@pytest.fixture
def check_digit_validation_cases():
    """Test cases for check digit validation with known correct/incorrect pairs."""
    return [
        ("WA4M", "00123456", "4", True),  # Correct
        ("WA4M", "00123456", "9", False),  # Incorrect
        ("BB1B", "12345678", "7", True),  # Correct
        ("BB1B", "12345678", "1", False),  # Incorrect
        ("CIKW", "00000001", "5", True),  # Correct
        ("CIKW", "00000001", "0", False),  # Incorrect
    ]
