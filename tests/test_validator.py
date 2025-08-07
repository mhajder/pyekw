"""
Tests for the KWValidator class.
"""

import pytest


class TestKWValidator:
    """Test cases for the KWValidator class."""

    def test_initialization(self, validator):
        """Test if the KWValidator initializes correctly."""
        assert validator is not None
        assert hasattr(validator, "court_registry")
        assert validator.court_registry is not None

    def test_parse_kw_number_with_valid_numbers(self, validator, valid_kw_numbers):
        """Test parsing valid KW numbers."""
        for kw_number in valid_kw_numbers:
            court_code, register_number, check_digit = validator.parse_kw_number(
                kw_number
            )

            assert isinstance(court_code, str)
            assert isinstance(register_number, str)
            assert isinstance(check_digit, str)
            assert len(register_number) == 8
            assert len(check_digit) == 1
            assert register_number.isdigit()
            assert check_digit.isdigit()

    def test_parse_kw_number_case_insensitive(self, validator):
        """Test that parsing handles case insensitive input."""
        lowercase_kw = "wa4m/00123456/4"
        uppercase_kw = "WA4M/00123456/4"
        mixed_case_kw = "Wa4M/00123456/4"

        result_lower = validator.parse_kw_number(lowercase_kw)
        result_upper = validator.parse_kw_number(uppercase_kw)
        result_mixed = validator.parse_kw_number(mixed_case_kw)

        assert result_lower == result_upper == result_mixed
        assert result_lower[0] == "WA4M"  # Court code should be uppercase

    def test_parse_kw_number_whitespace_handling(self, validator):
        """Test that parsing handles whitespace correctly."""
        kw_with_spaces = "  WA4M/00123456/4  "
        kw_without_spaces = "WA4M/00123456/4"

        result_with_spaces = validator.parse_kw_number(kw_with_spaces)
        result_without_spaces = validator.parse_kw_number(kw_without_spaces)

        assert result_with_spaces == result_without_spaces

    def test_parse_kw_number_with_malformed_numbers(
        self, validator, malformed_kw_numbers
    ):
        """Test parsing malformed KW numbers."""
        for malformed_kw in malformed_kw_numbers:
            with pytest.raises(ValueError):
                validator.parse_kw_number(malformed_kw)

    def test_parse_kw_number_with_invalid_register_numbers(
        self, validator, invalid_register_numbers_for_parsing
    ):
        """Test parsing KW numbers with invalid register numbers."""
        for invalid_kw in invalid_register_numbers_for_parsing:
            with pytest.raises(ValueError, match="Register number"):
                validator.parse_kw_number(invalid_kw)

    def test_parse_kw_number_with_invalid_check_digits(
        self, validator, invalid_check_digits_for_parsing
    ):
        """Test parsing KW numbers with invalid check digits."""
        for invalid_kw in invalid_check_digits_for_parsing:
            with pytest.raises(ValueError, match="Check digit"):
                validator.parse_kw_number(invalid_kw)

    def test_parse_kw_number_with_invalid_court_codes(
        self, validator, invalid_court_codes_for_parsing
    ):
        """Test parsing KW numbers with invalid court codes."""
        for invalid_kw in invalid_court_codes_for_parsing:
            if invalid_kw == "wa4m/12345678/2":
                # Lowercase should be handled by normalization, not cause parsing error
                result = validator.parse_kw_number(invalid_kw)
                assert result[0] == "WA4M"
            else:
                # All other cases should raise ValueError due to invalid characters
                with pytest.raises(ValueError, match="Court code"):
                    validator.parse_kw_number(invalid_kw)

    def test_parse_kw_number_parts_count_validation(self, validator):
        """Test that parsing validates the correct number of parts."""
        # Too few parts
        with pytest.raises(ValueError, match="must have exactly 3 parts"):
            validator.parse_kw_number("WA4M/00123456")

        # Too many parts
        with pytest.raises(ValueError, match="must have exactly 3 parts"):
            validator.parse_kw_number("WA4M/00123456/4/extra")

    def test_parse_kw_number_register_number_length_validation(self, validator):
        """Test register number length validation."""
        # Too short
        with pytest.raises(
            ValueError, match="Register number must be exactly 8 digits, got 7"
        ):
            validator.parse_kw_number("WA4M/1234567/4")

        # Too long
        with pytest.raises(
            ValueError, match="Register number must be exactly 8 digits, got 9"
        ):
            validator.parse_kw_number("WA4M/123456789/4")

    def test_parse_kw_number_check_digit_length_validation(self, validator):
        """Test check digit length validation."""
        # Empty check digit
        with pytest.raises(
            ValueError, match="Check digit must be exactly 1 digit, got 0"
        ):
            validator.parse_kw_number("WA4M/12345678/")

        # Too long check digit
        with pytest.raises(
            ValueError, match="Check digit must be exactly 1 digit, got 2"
        ):
            validator.parse_kw_number("WA4M/12345678/12")

    def test_validate_court_code_with_valid_codes(self, validator, valid_courts):
        """Test court code validation with valid codes."""
        for court_code in valid_courts:
            assert validator.validate_court_code(court_code) is True

    def test_validate_court_code_with_invalid_codes(self, validator, invalid_courts):
        """Test court code validation with invalid codes."""
        for court_code in invalid_courts:
            assert validator.validate_court_code(court_code) is False

    def test_validate_court_code_case_insensitive(self, validator):
        """Test that court code validation is case insensitive."""
        assert validator.validate_court_code("wa4m") is True
        assert validator.validate_court_code("WA4M") is True
        assert validator.validate_court_code("Wa4M") is True

    def test_validate_check_digit_with_known_cases(
        self, validator, check_digit_validation_cases
    ):
        """Test check digit validation with known correct/incorrect cases."""
        for (
            court_code,
            register_number,
            check_digit,
            expected_result,
        ) in check_digit_validation_cases:
            result = validator.validate_check_digit(
                court_code, register_number, check_digit
            )
            assert result == expected_result, (
                f"Expected {expected_result} for {court_code}/{register_number}/{check_digit}"
            )

    def test_validate_check_digit_with_invalid_input(self, validator):
        """Test check digit validation with invalid input that causes calculation errors."""
        # This should return False when CheckDigitGenerator raises ValueError
        result = validator.validate_check_digit("INVALID", "12345678", "1")
        assert result is False

    def test_validate_kw_number_with_valid_numbers(self, validator, valid_kw_numbers):
        """Test complete KW number validation with valid numbers."""
        for kw_number in valid_kw_numbers:
            is_valid, error = validator.validate_kw_number(kw_number)
            assert is_valid is True
            assert error is None

    def test_validate_kw_number_with_invalid_numbers(
        self, validator, invalid_kw_numbers
    ):
        """Test complete KW number validation with invalid numbers."""
        for kw_number in invalid_kw_numbers:
            is_valid, error = validator.validate_kw_number(kw_number)
            assert is_valid is False
            assert error is not None
            assert isinstance(error, str)
            assert len(error) > 0

    def test_validate_kw_number_with_court_check_disabled(self, validator):
        """Test KW number validation with court checking disabled."""
        # Use an invalid court code but valid format
        invalid_court_kw = "XXXX/12345678/1"

        # With court check enabled (default)
        is_valid_with_check, error_with_check = validator.validate_kw_number(
            invalid_court_kw, check_court=True
        )
        assert is_valid_with_check is False
        assert "Unknown court code" in error_with_check

        # With court check disabled
        is_valid_without_check, error_without_check = validator.validate_kw_number(
            invalid_court_kw, check_court=False
        )
        # Should still be invalid due to wrong check digit, but not due to court code
        assert is_valid_without_check is False
        assert "Invalid check digit" in error_without_check

    def test_validate_kw_number_wrong_check_digit_error_message(self, validator):
        """Test that wrong check digit provides correct error message."""
        wrong_check_digit_kw = "WA4M/00123456/9"  # Correct should be 4
        is_valid, error = validator.validate_kw_number(wrong_check_digit_kw)

        assert is_valid is False
        assert "Invalid check digit: expected 4, got 9" in error

    def test_validate_kw_number_unknown_court_error_message(self, validator):
        """Test that unknown court code provides correct error message."""
        unknown_court_kw = "XXXX/12345678/1"
        is_valid, error = validator.validate_kw_number(unknown_court_kw)

        assert is_valid is False
        assert "Unknown court code: XXXX" in error

    def test_validate_kw_number_parsing_error_handling(
        self, validator, malformed_kw_numbers
    ):
        """Test that parsing errors are properly handled in validation."""
        for malformed_kw in malformed_kw_numbers:
            is_valid, error = validator.validate_kw_number(malformed_kw)
            assert is_valid is False
            assert error is not None
            assert isinstance(error, str)

    def test_is_valid_kw_number_with_valid_numbers(self, validator, valid_kw_numbers):
        """Test is_valid_kw_number convenience method with valid numbers."""
        for kw_number in valid_kw_numbers:
            assert validator.is_valid_kw_number(kw_number) is True

    def test_is_valid_kw_number_with_invalid_numbers(
        self, validator, invalid_kw_numbers
    ):
        """Test is_valid_kw_number convenience method with invalid numbers."""
        for kw_number in invalid_kw_numbers:
            assert validator.is_valid_kw_number(kw_number) is False

    def test_is_valid_kw_number_with_court_check_parameter(self, validator):
        """Test is_valid_kw_number with court check parameter."""
        invalid_court_kw = "XXXX/12345678/1"

        # With court check (default)
        assert validator.is_valid_kw_number(invalid_court_kw) is False
        assert validator.is_valid_kw_number(invalid_court_kw, check_court=True) is False

        # Without court check
        assert (
            validator.is_valid_kw_number(invalid_court_kw, check_court=False) is False
        )

    def test_validator_integration_with_court_registry(self, validator):
        """Test that validator properly integrates with court registry."""
        # Test that validator uses the same court registry as expected
        assert validator.validate_court_code("WA4M") is True
        assert validator.validate_court_code("XXXX") is False

        # Test that court registry methods work as expected
        assert validator.court_registry.is_valid_court("WA4M") is True
        assert validator.court_registry.is_valid_court("XXXX") is False

    def test_validator_integration_with_check_digit_generator(self, validator):
        """Test that validator properly integrates with check digit generator."""
        # Test that validator correctly uses CheckDigitGenerator
        assert validator.validate_check_digit("WA4M", "00123456", "4") is True
        assert validator.validate_check_digit("WA4M", "00123456", "9") is False

    def test_validator_consistency_across_methods(self, validator, valid_kw_numbers):
        """Test consistency between different validation methods."""
        for kw_number in valid_kw_numbers:
            # Parse the number
            court_code, register_number, check_digit = validator.parse_kw_number(
                kw_number
            )

            # Validate components individually
            court_valid = validator.validate_court_code(court_code)
            check_digit_valid = validator.validate_check_digit(
                court_code, register_number, check_digit
            )

            # Validate complete number
            is_valid_complete = validator.is_valid_kw_number(kw_number)
            is_valid_detailed, _ = validator.validate_kw_number(kw_number)

            # All should be consistent
            assert court_valid is True
            assert check_digit_valid is True
            assert is_valid_complete is True
            assert is_valid_detailed is True

    def test_validator_error_handling_edge_cases(self, validator):
        """Test validator error handling with edge cases."""
        edge_cases = [
            None,  # This would cause AttributeError, but we'll handle it
            123,  # Non-string input
            [],  # List input
            {},  # Dict input
        ]

        for edge_case in edge_cases:
            # These should either work or raise appropriate errors
            if edge_case is None:
                with pytest.raises(AttributeError):
                    validator.parse_kw_number(edge_case)
            else:
                # Non-string inputs should be handled gracefully or raise TypeError
                with pytest.raises((TypeError, AttributeError)):
                    validator.parse_kw_number(edge_case)

    def test_validator_performance_with_repeated_calls(self, validator):
        """Test validator performance and consistency with repeated calls."""
        kw_number = "WA4M/00123456/4"

        # Call validation methods multiple times
        results = []
        for _ in range(10):
            result = validator.is_valid_kw_number(kw_number)
            results.append(result)

        # All results should be identical and True
        assert all(results)
        assert len(set(results)) == 1  # All results are the same

    def test_validator_thread_safety_simulation(self, validator, valid_kw_numbers):
        """Test validator thread safety by calling methods with different inputs."""
        # Simulate concurrent calls with different inputs
        results = {}
        for kw_number in valid_kw_numbers:
            results[kw_number] = validator.is_valid_kw_number(kw_number)

        # All valid numbers should return True
        assert all(results.values())

        # Test with invalid numbers
        invalid_results = {}
        for kw_number in ["XXXX/12345678/1", "WA4M/12345678/9"]:
            invalid_results[kw_number] = validator.is_valid_kw_number(kw_number)

        # All invalid numbers should return False
        assert not any(invalid_results.values())

    def test_validator_with_unnormalized_input(self, validator):
        """Test validator behavior with unnormalized input."""
        # The validator only handles basic leading/trailing whitespace and case conversion
        # It doesn't handle separator normalization or internal spaces like the utils class

        # Test cases that should work (only leading/trailing whitespace and case)
        working_cases = [
            ("  WA4M/00123456/4  ", "WA4M/00123456/4"),
            ("wa4m/00123456/4", "WA4M/00123456/4"),
            ("  wa4m/00123456/4  ", "WA4M/00123456/4"),
        ]

        for unnormalized, normalized in working_cases:
            result_unnormalized = validator.is_valid_kw_number(unnormalized)
            result_normalized = validator.is_valid_kw_number(normalized)
            assert result_unnormalized == result_normalized is True

        # Test cases that should fail (internal spaces, wrong separators)
        failing_cases = [
            "WA4M / 00123456 / 4",  # Internal spaces
            "wa4m\\00123456\\4",  # Backslash separators
            "WA4M-00123456-4",  # Dash separators
            "wa4m//00123456//4",  # Double slashes
        ]

        for failing_case in failing_cases:
            result = validator.is_valid_kw_number(failing_case)
            assert result is False
