"""
Tests for the integrity of the court data.
"""

import re

import pytest

from pyekw.constants import CHARACTER_VALUES
from pyekw.courts_data import COURTS
from pyekw.generator import CheckDigitGenerator
from pyekw.validator import KWValidator

# Codes that do not follow the regular "2 letters + digit + letter" pattern
SPECIAL_COURT_CODES = {"CIKW", "DIRS"}


@pytest.mark.parametrize("court_code", sorted(COURTS))
def test_court_code_format(court_code):
    """Every court code is 2 letters + digit + letter (e.g. WA4M), or a known special code."""
    assert (
        re.fullmatch(r"[A-Z]{2}[0-9][A-Z]", court_code)
        or court_code in SPECIAL_COURT_CODES
    )
    assert all(char in CHARACTER_VALUES for char in court_code)


@pytest.mark.parametrize("court_code", sorted(COURTS))
def test_court_data_fields(court_code):
    court = COURTS[court_code]

    assert set(court) == {"name", "full_name"}
    assert court["name"].strip() == court["name"] != ""
    assert court["full_name"].strip() == court["full_name"] != ""


def test_special_court_codes_exist():
    assert COURTS.keys() >= SPECIAL_COURT_CODES


def test_every_court_generates_valid_kw_numbers():
    validator = KWValidator()

    for court_code in COURTS:
        kw_number = CheckDigitGenerator.generate_full_kw_number(court_code, "00123456")
        assert validator.validate_kw_number(kw_number) == (True, None)
