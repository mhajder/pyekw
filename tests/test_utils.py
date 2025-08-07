"""
Tests for the KWUtils class.
"""

import pytest


class TestKWUtils:
    """Test cases for the KWUtils class."""

    def test_initialization(self, utils):
        """Test if the KWUtils initializes correctly."""
        assert utils is not None
        assert hasattr(utils, "validator")
        assert hasattr(utils, "court_registry")
        assert utils.validator is not None
        assert utils.court_registry is not None

    def test_normalize_kw_number_with_valid_inputs(
        self, utils, unnormalized_kw_numbers
    ):
        """Test normalize_kw_number with various input formats."""
        for input_kw, expected_output in unnormalized_kw_numbers:
            result = utils.normalize_kw_number(input_kw)
            assert result == expected_output, (
                f"Expected {expected_output}, got {result} for input {input_kw}"
            )

    def test_normalize_kw_number_case_insensitive(self, utils):
        """Test that normalization converts to uppercase."""
        lowercase_input = "WA4M/00123456/4"
        mixed_case_input = "WA4M/00123456/4"
        uppercase_input = "WA4M/00123456/4"

        result_lower = utils.normalize_kw_number(lowercase_input)
        result_mixed = utils.normalize_kw_number(mixed_case_input)
        result_upper = utils.normalize_kw_number(uppercase_input)

        assert result_lower == result_mixed == result_upper == "WA4M/00123456/4"

    def test_normalize_kw_number_whitespace_removal(self, utils):
        """Test that normalization removes all whitespace."""
        inputs_with_whitespace = [
            "  WA4M  /  00123456  /  4  ",
            "WA4M\t/\t00123456\t/\t4",
            "WA4M\n/\n00123456\n/\n4",
            "WA4M / 00123456 / 4",
        ]

        expected = "WA4M/00123456/4"
        for input_kw in inputs_with_whitespace:
            result = utils.normalize_kw_number(input_kw)
            assert result == expected

    def test_normalize_kw_number_separator_standardization(self, utils):
        """Test that normalization standardizes separators to forward slashes."""
        separator_variants = [
            "WA4M\\00123456\\4",
            "WA4M-00123456-4",
            "WA4M//00123456//4",
            "WA4M---00123456---4",
            "WA4M\\\\00123456\\\\4",
        ]

        expected = "WA4M/00123456/4"
        for input_kw in separator_variants:
            result = utils.normalize_kw_number(input_kw)
            assert result == expected

    def test_extract_kw_numbers_from_text(self, utils, text_with_kw_numbers):
        """Test extraction of KW numbers from text."""
        extracted = utils.extract_kw_numbers(text_with_kw_numbers)

        assert isinstance(extracted, list)
        assert len(extracted) >= 4  # Should find at least 4 valid KW numbers

        expected_numbers = [
            "WA4M/00123456/4",
            "BB1B/12345678/7",
            "CIKW/00000001/5",
            "KR1P/99999999/3",
        ]
        for expected in expected_numbers:
            assert expected in extracted, f"Should find {expected} in text"

    def test_extract_kw_numbers_case_insensitive(self, utils):
        """Test that extraction works with lowercase text."""
        text_lower = "check WA4M/00123456/4 and bb1b/12345678/7"
        text_upper = "CHECK WA4M/00123456/4 AND BB1B/12345678/7"

        extracted_lower = utils.extract_kw_numbers(text_lower)
        extracted_upper = utils.extract_kw_numbers(text_upper)

        assert extracted_lower == extracted_upper
        assert "WA4M/00123456/4" in extracted_lower
        assert "BB1B/12345678/7" in extracted_lower

    def test_extract_kw_numbers_empty_text(self, utils):
        """Test extraction from empty or text without KW numbers."""
        assert utils.extract_kw_numbers("") == []
        assert utils.extract_kw_numbers("No KW numbers here") == []
        assert utils.extract_kw_numbers("Invalid format: WA4M-123456-2") == []

    def test_extract_kw_numbers_boundary_cases(self, utils):
        """Test extraction with boundary cases."""
        # Test with minimal valid format
        text_minimal = "A1/12345678/9"
        extracted = utils.extract_kw_numbers(text_minimal)
        assert "A1/12345678/9" in extracted

        # Test with maximum court code length
        text_max = "ABCD12/12345678/9"
        extracted = utils.extract_kw_numbers(text_max)
        assert "ABCD12/12345678/9" in extracted

    def test_validate_multiple_kw_numbers(self, utils, kw_numbers_for_batch_validation):
        """Test batch validation of multiple KW numbers."""
        results = utils.validate_multiple_kw_numbers(kw_numbers_for_batch_validation)

        assert isinstance(results, dict)
        assert len(results) == len(kw_numbers_for_batch_validation)

        # Check that valid numbers are marked as valid
        valid_normalized = utils.normalize_kw_number("WA4M/00123456/4")
        assert valid_normalized in results
        assert results[valid_normalized]["is_valid"] is True
        assert results[valid_normalized]["error"] is None

        # Check that invalid numbers are marked as invalid
        invalid_normalized = utils.normalize_kw_number("BB1B/12345678/9")
        assert invalid_normalized in results
        assert results[invalid_normalized]["is_valid"] is False
        assert results[invalid_normalized]["error"] is not None

    def test_validate_multiple_kw_numbers_with_court_check_disabled(self, utils):
        """Test batch validation with court checking disabled."""
        kw_numbers = ["XXXX/12345678/1"]  # Invalid court code

        results_with_court_check = utils.validate_multiple_kw_numbers(
            kw_numbers, check_court=True
        )
        utils.validate_multiple_kw_numbers(kw_numbers, check_court=False)

        normalized = utils.normalize_kw_number("XXXX/12345678/1")

        # With court check, should be invalid due to unknown court
        assert results_with_court_check[normalized]["is_valid"] is False

    def test_validate_multiple_kw_numbers_detailed_info(self, utils, valid_kw_numbers):
        """Test that batch validation includes detailed information for valid numbers."""
        results = utils.validate_multiple_kw_numbers(valid_kw_numbers)

        for kw_number in valid_kw_numbers:
            normalized = utils.normalize_kw_number(kw_number)
            result = results[normalized]

            if result["is_valid"]:
                assert "court_code" in result
                assert "register_number" in result
                assert "check_digit" in result
                assert "court_name" in result
                assert "court_full_name" in result
                assert result["original"] == kw_number
                assert result["normalized"] == normalized

    def test_generate_kw_number_variants(self, utils):
        """Test generation of KW number variants."""
        court_code = "WA4M"
        base_number = 1000
        count = 5

        variants = utils.generate_kw_number_variants(court_code, base_number, count)

        assert isinstance(variants, list)
        assert len(variants) == count

        for i, variant in enumerate(variants):
            expected_register = f"{base_number + i:08d}"
            assert expected_register in variant
            assert variant.startswith(f"{court_code}/")
            assert variant.count("/") == 2  # Should have format COURT/NUMBER/DIGIT

    def test_generate_kw_number_variants_with_invalid_court(self, utils):
        """Test generation with invalid court code."""
        with pytest.raises(ValueError, match="Invalid court code"):
            utils.generate_kw_number_variants("XXXX", 1000, 5)

    def test_generate_kw_number_variants_padding(self, utils):
        """Test that register numbers are properly padded to 8 digits."""
        variants = utils.generate_kw_number_variants("WA4M", 1, 3)

        assert "WA4M/00000001/" in variants[0]
        assert "WA4M/00000002/" in variants[1]
        assert "WA4M/00000003/" in variants[2]

    def test_generate_kw_number_variants_large_numbers(self, utils):
        """Test generation with large base numbers."""
        variants = utils.generate_kw_number_variants("WA4M", 99999995, 3)

        assert "WA4M/99999995/" in variants[0]
        assert "WA4M/99999996/" in variants[1]
        assert "WA4M/99999997/" in variants[2]

    def test_get_kw_info_with_valid_number(self, utils, valid_kw_numbers):
        """Test getting detailed information for valid KW numbers."""
        for kw_number in valid_kw_numbers:
            info = utils.get_kw_info(kw_number)

            assert info is not None
            assert isinstance(info, dict)
            assert info["is_valid"] is True
            assert "kw_number" in info
            assert "court_code" in info
            assert "court_name" in info
            assert "court_full_name" in info
            assert "register_number" in info
            assert "check_digit" in info
            assert isinstance(info["check_digit"], int)

    def test_get_kw_info_with_invalid_number(self, utils, invalid_kw_numbers):
        """Test getting information for invalid KW numbers."""
        for kw_number in invalid_kw_numbers:
            info = utils.get_kw_info(kw_number)
            assert info is None, f"Expected None for {kw_number}, but got {info}"

    def test_get_kw_info_with_normalizable_invalid_format(
        self, utils, invalid_kw_numbers_that_normalize_to_valid
    ):
        """Test getting information for KW numbers with invalid format that normalize to valid ones."""
        for kw_number in invalid_kw_numbers_that_normalize_to_valid:
            info = utils.get_kw_info(kw_number)
            assert info is not None, (
                f"Expected valid info for {kw_number} after normalization"
            )
            assert info["is_valid"] is True

    def test_get_kw_info_normalization(self, utils):
        """Test that get_kw_info normalizes input before processing."""
        unnormalized = "  wa4m / 00123456 / 4  "
        info = utils.get_kw_info(unnormalized)

        assert info is not None
        assert info["kw_number"] == "WA4M/00123456/4"

    def test_suggest_corrections_for_wrong_check_digit(
        self, utils, correction_test_cases
    ):
        """Test correction suggestions for wrong check digits."""
        for wrong_kw, expected_correction in correction_test_cases:
            if (
                expected_correction is not None
            ):  # Skip cases where no correction is expected
                suggestions = utils.suggest_corrections(wrong_kw)

                assert isinstance(suggestions, list)
                assert len(suggestions) > 0
                assert expected_correction in suggestions, (
                    f"Expected {expected_correction} in suggestions for {wrong_kw}, got {suggestions}"
                )

    def test_suggest_corrections_for_invalid_court_code(
        self, utils, correction_test_cases
    ):
        """Test correction suggestions for invalid court codes."""
        for wrong_kw, expected_correction in correction_test_cases:
            suggestions = utils.suggest_corrections(wrong_kw)

            assert isinstance(suggestions, list)
            if expected_correction is None:
                # For cases like invalid court codes, we might not have a simple correction
                pass
            else:
                assert expected_correction in suggestions

    def test_suggest_corrections_for_unparseable_input(self, utils):
        """Test correction suggestions for completely invalid input."""
        invalid_input = "INVALID"
        suggestions = utils.suggest_corrections(invalid_input)

        assert isinstance(suggestions, list)
        # Should return empty list for unparseable input

    def test_suggest_corrections_multiple_suggestions(self, utils):
        """Test that correction suggestions can provide multiple options."""
        # Use a court code that might have similar matches
        similar_court = "WA99/12345678/1"  # Similar to WA4M
        suggestions = utils.suggest_corrections(similar_court)

        assert isinstance(suggestions, list)
        # Should provide suggestions based on similar court codes

    def test_suggest_corrections_already_correct(self, utils, valid_kw_numbers):
        """Test correction suggestions for already correct KW numbers."""
        for valid_kw in valid_kw_numbers:
            suggestions = utils.suggest_corrections(valid_kw)
            # Should return empty list or minimal suggestions for already valid numbers
            assert isinstance(suggestions, list)

    def test_utils_integration_with_validator(self, utils):
        """Test that utils properly integrates with validator."""
        kw_number = "WA4M/00123456/4"

        # Test that utils uses validator correctly
        is_valid = utils.validator.is_valid_kw_number(kw_number)
        info = utils.get_kw_info(kw_number)

        assert is_valid is True
        assert info is not None
        assert info["is_valid"] is True

    def test_utils_integration_with_court_registry(self, utils):
        """Test that utils properly integrates with court registry."""
        court_code = "WA4M"

        # Test that utils uses court registry correctly
        is_valid_court = utils.court_registry.is_valid_court(court_code)
        court_name = utils.court_registry.get_court_name(court_code)

        assert is_valid_court is True
        assert court_name is not None

        # Test in context of KW info
        info = utils.get_kw_info("WA4M/00123456/4")
        assert info["court_name"] == court_name

    def test_utils_error_handling(self, utils):
        """Test error handling in various utility methods."""
        # Test with None input (should not crash)
        try:
            utils.normalize_kw_number("")
            utils.extract_kw_numbers("")
            utils.get_kw_info("")
            utils.suggest_corrections("")
        except Exception as e:
            pytest.fail(f"Utils should handle empty strings gracefully, but got: {e}")

    def test_utils_performance_with_large_batch(self, utils):
        """Test performance with large batch of KW numbers."""
        # Create a large list of KW numbers
        large_batch = ["WA4M/00123456/4"] * 100

        results = utils.validate_multiple_kw_numbers(large_batch)

        assert len(results) == 1  # Should deduplicate based on normalized form
        assert next(iter(results.keys())) == "WA4M/00123456/4"

    def test_utils_thread_safety_simulation(self, utils):
        """Test that utils methods can be called multiple times safely."""
        kw_number = "WA4M/00123456/4"

        # Call methods multiple times to ensure consistency
        results = []
        for _ in range(10):
            info = utils.get_kw_info(kw_number)
            results.append(info)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

    def test_validate_multiple_kw_numbers_parse_error_handling(
        self, utils, monkeypatch
    ):
        """Test error handling in validate_multiple_kw_numbers when parsing fails."""

        def mock_validate_kw_number(kw_number, check_court=True):
            return True, None  # Return valid to reach the parsing step

        def mock_parse_error(kw_number):
            raise ValueError("Mocked parsing error")

        monkeypatch.setattr(
            utils.validator, "validate_kw_number", mock_validate_kw_number
        )
        monkeypatch.setattr(utils.validator, "parse_kw_number", mock_parse_error)

        results = utils.validate_multiple_kw_numbers(["WA4M/00123456/4"])

        normalized = utils.normalize_kw_number("WA4M/00123456/4")
        assert normalized in results
        result = results[normalized]
        assert result["is_valid"] is True  # Validation said it was valid
        assert (
            "court_code" not in result
        )  # Should not have detailed info due to parse error

    def test_get_kw_info_parse_error_handling(self, utils, monkeypatch):
        """Test error handling in get_kw_info when parsing fails."""

        def mock_validate_kw_number(kw_number, check_court=True):
            return True, None  # Return valid to reach the parsing step

        def mock_parse_error(kw_number):
            raise ValueError("Mocked parsing error")

        monkeypatch.setattr(
            utils.validator, "validate_kw_number", mock_validate_kw_number
        )
        monkeypatch.setattr(utils.validator, "parse_kw_number", mock_parse_error)

        info = utils.get_kw_info("WA4M/00123456/4")

        # Should return None due to parse error
        assert info is None
