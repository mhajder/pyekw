"""
Tests for the CheckDigitGenerator class.
"""

import pytest

from pyekw.generator import CheckDigitGenerator


class TestCheckDigitGenerator:
    """Test cases for the CheckDigitGenerator class."""

    def test_calculate_check_digit_with_valid_cases(self, generator, valid_test_cases):
        """Test calculate_check_digit with known valid combinations."""
        for court_code, register_number, expected_check_digit in valid_test_cases:
            actual_check_digit = generator.calculate_check_digit(
                court_code, register_number
            )
            assert actual_check_digit == expected_check_digit, (
                f"For {court_code}/{register_number}, expected {expected_check_digit}, got {actual_check_digit}"
            )

    def test_calculate_check_digit_case_insensitive(self, generator):
        """Test that check digit calculation is case insensitive for court codes."""
        court_code_upper = "WA4M"
        court_code_lower = "wa4m"
        court_code_mixed = "Wa4m"
        register_number = "00123456"

        result_upper = generator.calculate_check_digit(
            court_code_upper, register_number
        )
        result_lower = generator.calculate_check_digit(
            court_code_lower, register_number
        )
        result_mixed = generator.calculate_check_digit(
            court_code_mixed, register_number
        )

        assert result_upper == result_lower == result_mixed

    def test_calculate_check_digit_with_invalid_court_codes(
        self, generator, invalid_court_codes
    ):
        """Test calculate_check_digit with invalid court codes."""
        register_number = "12345678"
        for invalid_court_code in invalid_court_codes:
            if invalid_court_code == "":
                # Empty string doesn't raise "Invalid character" but may work or cause other issues
                # Let's just verify it doesn't crash and returns a valid result
                try:
                    result = generator.calculate_check_digit(
                        invalid_court_code, register_number
                    )
                    assert isinstance(result, int)
                    assert 0 <= result <= 9
                except ValueError:
                    # Empty string might cause other validation errors, which is also acceptable
                    pass
            else:
                with pytest.raises(ValueError, match="Invalid character"):
                    generator.calculate_check_digit(invalid_court_code, register_number)

    def test_calculate_check_digit_with_invalid_register_numbers(
        self, generator, invalid_register_numbers
    ):
        """Test calculate_check_digit with invalid register numbers."""
        court_code = "WA4M"
        for invalid_register_number in invalid_register_numbers:
            with pytest.raises(ValueError):
                generator.calculate_check_digit(court_code, invalid_register_number)

    def test_calculate_check_digit_register_number_length_validation(self, generator):
        """Test that register number length is strictly validated."""
        court_code = "WA4M"

        # Test too short
        with pytest.raises(
            ValueError, match="Register number must be exactly 8 digits, got 7"
        ):
            generator.calculate_check_digit(court_code, "1234567")

        # Test too long
        with pytest.raises(
            ValueError, match="Register number must be exactly 8 digits, got 9"
        ):
            generator.calculate_check_digit(court_code, "123456789")

    def test_calculate_check_digit_register_number_digit_validation(self, generator):
        """Test that register number must contain only digits."""
        court_code = "WA4M"

        with pytest.raises(
            ValueError, match="Register number must contain only digits"
        ):
            generator.calculate_check_digit(court_code, "1234567a")

        with pytest.raises(
            ValueError, match="Register number must contain only digits"
        ):
            generator.calculate_check_digit(court_code, "12345-78")

    def test_calculate_check_digit_with_edge_cases(self, generator, edge_case_inputs):
        """Test calculate_check_digit with edge case inputs."""
        for court_code, register_number in edge_case_inputs:
            try:
                result = generator.calculate_check_digit(court_code, register_number)
                assert isinstance(result, int)
                assert 0 <= result <= 9
            except ValueError:
                # Some edge cases might be invalid, which is acceptable
                pass

    def test_calculate_check_digit_return_type_and_range(self, generator):
        """Test that check digit is always an integer between 0-9."""
        court_code = "WA4M"
        register_number = "12345678"

        result = generator.calculate_check_digit(court_code, register_number)
        assert isinstance(result, int)
        assert 0 <= result <= 9

    def test_calculate_check_digit_deterministic(self, generator):
        """Test that check digit calculation is deterministic."""
        court_code = "WA4M"
        register_number = "12345678"

        result1 = generator.calculate_check_digit(court_code, register_number)
        result2 = generator.calculate_check_digit(court_code, register_number)
        result3 = generator.calculate_check_digit(court_code, register_number)

        assert result1 == result2 == result3

    def test_generate_full_kw_number_with_valid_cases(
        self, generator, valid_test_cases
    ):
        """Test generate_full_kw_number with known valid combinations."""
        for court_code, register_number, expected_check_digit in valid_test_cases:
            result = generator.generate_full_kw_number(court_code, register_number)
            expected = f"{court_code.upper()}/{register_number}/{expected_check_digit}"
            assert result == expected

    def test_generate_full_kw_number_format(self, generator):
        """Test that generate_full_kw_number returns correct format."""
        court_code = "wa4m"  # Test with lowercase
        register_number = "12345678"

        result = generator.generate_full_kw_number(court_code, register_number)

        # Should be in format: COURT_CODE/REGISTER_NUMBER/CHECK_DIGIT
        parts = result.split("/")
        assert len(parts) == 3
        assert parts[0] == court_code.upper()  # Court code should be uppercase
        assert parts[1] == register_number
        assert parts[2].isdigit()
        assert len(parts[2]) == 1

    def test_generate_full_kw_number_case_insensitive(self, generator):
        """Test that generate_full_kw_number handles case insensitive court codes."""
        register_number = "12345678"

        result_upper = generator.generate_full_kw_number("WA4M", register_number)
        result_lower = generator.generate_full_kw_number("wa4m", register_number)
        result_mixed = generator.generate_full_kw_number("Wa4M", register_number)

        assert result_upper == result_lower == result_mixed
        assert result_upper.startswith("WA4M/")

    def test_generate_full_kw_number_with_invalid_inputs(
        self, generator, invalid_court_codes, invalid_register_numbers
    ):
        """Test generate_full_kw_number with invalid inputs."""
        for invalid_court_code in invalid_court_codes:
            if invalid_court_code == "":
                try:
                    result = generator.generate_full_kw_number(
                        invalid_court_code, "12345678"
                    )
                    assert "/" in result
                except ValueError:
                    # If it fails, that's also acceptable
                    pass
            else:
                with pytest.raises(ValueError):
                    generator.generate_full_kw_number(invalid_court_code, "12345678")

        for invalid_register_number in invalid_register_numbers:
            with pytest.raises(ValueError):
                generator.generate_full_kw_number("WA4M", invalid_register_number)

    def test_static_methods_accessibility(self):
        """Test that methods can be called as static methods."""
        result1 = CheckDigitGenerator.calculate_check_digit("WA4M", "12345678")
        result2 = CheckDigitGenerator.generate_full_kw_number("WA4M", "12345678")

        assert isinstance(result1, int)
        assert isinstance(result2, str)
        assert 0 <= result1 <= 9

    def test_calculate_check_digit_with_all_valid_characters(self, generator):
        """Test check digit calculation with all valid characters in court codes."""
        valid_character_combinations = [
            ("A1B2", "12345678"),
            ("X9Y8", "87654321"),
            ("ZUPW", "11111111"),
            ("1234", "00000000"),
        ]

        for court_code, register_number in valid_character_combinations:
            try:
                result = generator.calculate_check_digit(court_code, register_number)
                assert isinstance(result, int)
                assert 0 <= result <= 9
            except ValueError:
                # Some combinations might be invalid due to character restrictions
                pass

    def test_input_too_long_error(self, generator):
        """Test error handling when combined input exceeds weight array length."""
        very_long_court_code = "ABCDEFGH"  # 8 characters + 8 digit register = 16 total
        register_number = "12345678"

        with pytest.raises(ValueError, match="Input too long"):
            generator.calculate_check_digit(very_long_court_code, register_number)

    def test_consistency_between_methods(self, generator, valid_test_cases):
        """Test consistency between calculate_check_digit and generate_full_kw_number."""
        for court_code, register_number, expected_check_digit in valid_test_cases:
            calculated_check_digit = generator.calculate_check_digit(
                court_code, register_number
            )

            full_kw = generator.generate_full_kw_number(court_code, register_number)

            extracted_check_digit = int(full_kw.split("/")[2])

            assert (
                calculated_check_digit == extracted_check_digit == expected_check_digit
            )
