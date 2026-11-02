"""
Tests for the KWNumber value object class.
"""

import json
from typing import Any
from typing import cast

import pytest

from pyekw.kw_number import KWNumber


class TestKWNumber:
    """Test suite for KWNumber value object."""

    def test_init_and_attributes(self):
        kw = KWNumber("wa4m", "00123456", 4)
        assert kw.court_code == "WA4M"
        assert kw.register_number == "00123456"
        assert kw.check_digit == 4
        assert kw.is_valid is True

    def test_init_validation(self):
        # Invalid court code length
        with pytest.raises(
            ValueError, match="Court code must be exactly 4 letters or digits"
        ):
            KWNumber("ABC", "00123456", 4)

        # Non-string court code
        with pytest.raises(ValueError, match="Court code must be a string"):
            KWNumber(cast(str, None), "00123456", 4)

        # Invalid court code characters
        with pytest.raises(
            ValueError, match="Court code must be exactly 4 letters or digits"
        ):
            KWNumber("WA-M", "00123456", 4)

        # Invalid register number length
        with pytest.raises(
            ValueError, match="Register number must be exactly 8 digits"
        ):
            KWNumber("WA4M", "123456", 4)

        # Invalid register number non-digits
        with pytest.raises(
            ValueError, match="Register number must be exactly 8 digits"
        ):
            KWNumber("WA4M", "0012345A", 4)

        # Non-integer check digit
        with pytest.raises(ValueError, match="Check digit must be an integer"):
            KWNumber("WA4M", "00123456", cast(int, "abc"))

        # Floats and bools are not silently truncated into check digits
        with pytest.raises(ValueError, match="Check digit must be an integer"):
            KWNumber("WA4M", "00123456", cast(int, 4.7))
        with pytest.raises(ValueError, match="Check digit must be an integer"):
            KWNumber("WA4M", "00123456", cast(int, True))

        # Check digit out of range 0..9
        with pytest.raises(ValueError, match="Check digit must be between 0 and 9"):
            KWNumber("WA4M", "00123456", 15)

        # Check digit mismatch
        with pytest.raises(ValueError, match="Invalid check digit for WA4M/00123456"):
            KWNumber("WA4M", "00123456", 9)

    def test_init_accepts_digit_string_check_digit(self):
        kw = KWNumber("WA4M", "00123456", cast(int, " 4 "))
        assert kw.check_digit == 4

    def test_from_string_wraps_parse_errors(self):
        with pytest.raises(ValueError, match="Invalid KW number 'WA4M/1/2': Register"):
            KWNumber.from_string("WA4M/1/2")

    def test_from_string_valid(self):
        kw = KWNumber.from_string("WA4M/00123456/4")
        assert kw.court_code == "WA4M"
        assert kw.register_number == "00123456"
        assert kw.check_digit == 4

    def test_from_string_spaced(self):
        kw = KWNumber.from_string("WA4M / 00123456 / 4")
        assert kw.court_code == "WA4M"
        assert kw.register_number == "00123456"
        assert kw.check_digit == 4

    def test_from_string_lowercase(self):
        kw = KWNumber.from_string("wa4m/00123456/4")
        assert kw.court_code == "WA4M"
        assert kw.register_number == "00123456"
        assert kw.check_digit == 4

    def test_from_string_compact(self):
        kw = KWNumber.from_string("WA4M001234564")
        assert kw.formatted == "WA4M/00123456/4"
        assert kw.compact == "WA4M001234564"

    def test_from_string_with_auto_pad(self):
        kw = KWNumber.from_string("WA4M/123456/4", auto_pad=True)
        assert kw.register_number == "00123456"
        assert kw.formatted == "WA4M/00123456/4"

    def test_from_string_invalid_check_digit(self):
        with pytest.raises(ValueError, match="Invalid check digit"):
            KWNumber.from_string("WA4M/00123456/5")

    def test_from_string_unknown_court(self):
        with pytest.raises(ValueError, match="Unknown court code"):
            KWNumber.from_string("ZZ9Z/00123456/4")

    def test_from_string_unknown_court_allowed(self):
        # ZZ9Z with 00123456 has calculated check digit 7
        kw = KWNumber.from_string("ZZ9Z/00123456/7", check_court=False)
        assert kw.court_code == "ZZ9Z"

    def test_from_parts(self):
        kw = KWNumber.from_parts("WA4M", "00123456")
        assert kw.formatted == "WA4M/00123456/4"

    def test_from_parts_with_int_and_auto_pad(self):
        kw = KWNumber.from_parts("WA4M", 123456, auto_pad=True)
        assert kw.register_number == "00123456"
        assert kw.check_digit == 4

    def test_from_parts_without_auto_pad(self):
        kw = KWNumber.from_parts("WA4M", "00123456", auto_pad=False)
        assert kw.register_number == "00123456"
        assert kw.check_digit == 4

    def test_from_parts_invalid_court(self):
        with pytest.raises(ValueError, match="Unknown court code"):
            KWNumber.from_parts("ZZ9Z", "00123456")

    def test_from_parts_allow_unknown_court(self):
        kw = KWNumber.from_parts("ZZ9Z", "00123456", check_court=False)
        assert kw.court_code == "ZZ9Z"
        assert kw.check_digit == 7

    def test_from_legacy(self):
        kw = KWNumber.from_legacy("WA4M", "KW 123456")
        assert kw.formatted == "WA4M/00123456/4"

    def test_from_legacy_unknown_court(self):
        with pytest.raises(ValueError, match="Invalid court code: ZZ9Z"):
            KWNumber.from_legacy("ZZ9Z", 5)

    def test_from_legacy_unknown_court_allowed(self):
        kw = KWNumber.from_legacy("ZZ9Z", 12345, check_court=False)
        assert kw.formatted == "ZZ9Z/00012345/5"

    def test_properties(self):
        kw = KWNumber.from_string("WA4M/00123456/4")
        assert kw.formatted == "WA4M/00123456/4"
        assert kw.compact == "WA4M001234564"
        assert kw.spaced == "WA4M / 00123456 / 4"
        assert kw.court_name == "WARSZAWA (X)"
        assert kw.court_full_name is not None
        assert "Warszawy-Mokotowa" in kw.court_full_name
        assert kw.circuit == "Sąd Okręgowy w Warszawie"
        assert kw.voivodeship == "mazowieckie"
        assert "przegladarka-ekw.ms.gov.pl" in kw.portal_url
        assert kw.portal_params == {
            "kodWydzialu": "WA4M",
            "numerKw": "00123456",
            "cyfraKontrolna": "4",
        }

    def test_to_dict_and_to_json(self):
        kw = KWNumber.from_string("WA4M/00123456/4")
        d = kw.to_dict()
        assert d["kw_number"] == "WA4M/00123456/4"
        assert d["court_code"] == "WA4M"
        assert d["court_name"] == "WARSZAWA (X)"
        assert d["court_full_name"] is not None
        assert "Warszawy-Mokotowa" in d["court_full_name"]
        assert d["circuit"] == "Sąd Okręgowy w Warszawie"
        assert d["voivodeship"] == "mazowieckie"
        assert d["register_number"] == "00123456"
        assert d["check_digit"] == 4
        assert d["compact"] == "WA4M001234564"
        assert d["is_valid"] is True
        assert "przegladarka-ekw.ms.gov.pl" in d["url"]

        json_str = kw.to_json()
        assert json.loads(json_str) == d

    def test_str_and_repr(self):
        kw = KWNumber.from_string("WA4M/00123456/4")
        assert str(kw) == "WA4M/00123456/4"
        assert repr(kw) == "KWNumber('WA4M/00123456/4')"

    def test_equality(self):
        kw1 = KWNumber.from_string("WA4M/00123456/4")
        kw2 = KWNumber.from_string("wa4m/00123456/4")
        kw3 = KWNumber.from_string("KR1P/00012345/2")

        assert kw1 == kw2
        assert kw1 != kw3
        # Never equal to strings, so equality stays consistent with hashing
        assert kw1 != "WA4M/00123456/4"
        assert kw1 != 12345
        assert str(kw1) == "WA4M/00123456/4"

    def test_ordering(self):
        kw1 = KWNumber.from_string("BB1B/12345678/7")
        kw2 = KWNumber.from_string("KR1P/00012345/2")
        kw3 = KWNumber.from_string("WA4M/00123456/4")

        assert sorted([kw3, kw1, kw2]) == [kw1, kw2, kw3]
        assert kw1 < kw2
        assert kw1 <= kw2
        assert kw2 > kw1
        assert kw2 >= kw1
        assert kw1 <= kw1
        assert kw1 >= kw1
        with pytest.raises(TypeError):
            _ = kw1 < cast(Any, "string")
        with pytest.raises(TypeError):
            _ = kw1 <= cast(Any, "string")

    def test_hash(self):
        kw1 = KWNumber.from_string("WA4M/00123456/4")
        kw2 = KWNumber.from_string("wa4m/00123456/4")
        kw_set = {kw1, kw2}
        assert len(kw_set) == 1
        assert "WA4M/00123456/4" not in kw_set

    def test_pydantic_core_schema_fallback_when_not_installed(self):
        fallback_res = KWNumber.__get_pydantic_core_schema__(
            KWNumber, lambda _: "fallback_schema"
        )
        assert fallback_res == "fallback_schema"

    def test_pydantic_core_schema_hook_with_mock_pydantic(self, monkeypatch):
        import sys
        from unittest.mock import MagicMock

        mock_core = MagicMock()
        mock_pydantic_core = MagicMock()
        mock_pydantic_core.core_schema = mock_core

        calls = {}

        def record(name):
            def schema_fn(*args, **kwargs):
                calls[name] = (args, kwargs)
                return {"type": name}

            return schema_fn

        for name in (
            "str_schema",
            "no_info_after_validator_function",
            "no_info_plain_validator_function",
            "json_or_python_schema",
            "to_string_ser_schema",
        ):
            setattr(mock_core, name, record(name))

        monkeypatch.setitem(sys.modules, "pydantic_core", mock_pydantic_core)
        monkeypatch.setitem(sys.modules, "pydantic_core.core_schema", mock_core)

        schema = KWNumber.__get_pydantic_core_schema__(KWNumber, lambda _: None)
        assert schema == {"type": "json_or_python_schema"}

        # JSON input is a string parsed with from_string()
        (json_fn, str_schema), _ = calls["no_info_after_validator_function"]
        assert json_fn == KWNumber.from_string
        assert str_schema == {"type": "str_schema"}
        _, json_or_python_kwargs = calls["json_or_python_schema"]
        assert json_or_python_kwargs["json_schema"] == {
            "type": "no_info_after_validator_function"
        }

        # Python input may also be an existing KWNumber instance
        ((validator_fn,), _) = calls["no_info_plain_validator_function"]
        kw = KWNumber.from_string("WA4M/00123456/4")
        assert validator_fn(kw) is kw
        assert validator_fn("wa4m001234564") == kw
        with pytest.raises(ValueError, match="Expected a KW number string or KWNumber"):
            validator_fn(12345)
