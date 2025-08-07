"""
Tests for the CourtRegistry class.
"""


class TestCourtRegistry:
    """Test cases for the CourtRegistry class."""

    def test_initialization(self, registry):
        """Test if the CourtRegistry initializes correctly."""
        assert registry is not None
        assert hasattr(registry, "_courts_data")
        assert registry._courts_data is not None
        assert len(registry._courts_data) > 0

    def test_is_valid_court_with_valid_codes(self, registry, valid_courts):
        """Test is_valid_court with known valid court codes."""
        for court_code in valid_courts:
            assert registry.is_valid_court(court_code), (
                f"Court {court_code} should be valid"
            )

    def test_is_valid_court_case_insensitive(self, registry):
        """Test that court validation is case insensitive."""
        assert registry.is_valid_court("wa4m")
        assert registry.is_valid_court("bb1b")
        assert registry.is_valid_court("Wa4M")
        assert registry.is_valid_court("bB1b")

    def test_is_valid_court_with_invalid_codes(self, registry, invalid_courts):
        """Test is_valid_court with invalid court codes."""
        for court_code in invalid_courts:
            assert not registry.is_valid_court(court_code), (
                f"Court {court_code} should be invalid"
            )

    def test_get_court_name_with_valid_codes(self, registry, known_courts):
        """Test get_court_name with valid court codes."""
        for court_code, expected_name in known_courts.items():
            actual_name = registry.get_court_name(court_code)
            assert actual_name == expected_name, (
                f"Expected {expected_name}, got {actual_name}"
            )

    def test_get_court_name_case_insensitive(self, registry):
        """Test that get_court_name is case insensitive."""
        assert registry.get_court_name("wa4m") == registry.get_court_name("WA4M")
        assert registry.get_court_name("bb1b") == registry.get_court_name("BB1B")

    def test_get_court_name_with_invalid_codes(self, registry, invalid_courts):
        """Test get_court_name with invalid court codes."""
        for court_code in invalid_courts:
            assert registry.get_court_name(court_code) is None

    def test_get_court_full_name_with_valid_codes(self, registry):
        """Test get_court_full_name with valid court codes."""
        court_code = "WA4M"
        short_name = registry.get_court_name(court_code)
        full_name = registry.get_court_full_name(court_code)
        assert full_name is not None
        assert len(full_name) > len(short_name)
        full_name_lower = full_name.lower()
        assert "warszaw" in full_name_lower or "mokotow" in full_name_lower

    def test_get_court_full_name_case_insensitive(self, registry):
        """Test that get_court_full_name is case insensitive."""
        assert registry.get_court_full_name("wa4m") == registry.get_court_full_name(
            "WA4M"
        )

    def test_get_court_full_name_with_invalid_codes(self, registry, invalid_courts):
        """Test get_court_full_name with invalid court codes."""
        for court_code in invalid_courts:
            assert registry.get_court_full_name(court_code) is None

    def test_get_all_courts(self, registry):
        """Test get_all_courts returns correct format."""
        all_courts = registry.get_all_courts()
        assert isinstance(all_courts, dict)
        assert len(all_courts) > 0
        for code, name in all_courts.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(code) > 0
            assert len(name) > 0
        assert "WA4M" in all_courts
        assert "BB1B" in all_courts

    def test_get_all_courts_detailed(self, registry):
        """Test get_all_courts_detailed returns correct format."""
        detailed_courts = registry.get_all_courts_detailed()
        assert isinstance(detailed_courts, dict)
        assert len(detailed_courts) > 0
        for code, data in detailed_courts.items():
            assert isinstance(code, str)
            assert isinstance(data, dict)
            assert "name" in data
            assert "full_name" in data
            assert isinstance(data["name"], str)
            assert isinstance(data["full_name"], str)
        assert "WA4M" in detailed_courts
        wa4m_data = detailed_courts["WA4M"]
        assert "name" in wa4m_data
        assert "full_name" in wa4m_data

    def test_search_courts_by_code(self, registry):
        """Test searching courts by court code."""
        results = registry.search_courts("WA")
        assert isinstance(results, list)
        assert len(results) > 0
        for code, name in results:
            assert isinstance(code, str)
            assert isinstance(name, str)
        wa_codes = [code for code, name in results if "WA" in code]
        assert len(wa_codes) > 0, "Should find at least one court code containing 'WA'"

    def test_search_courts_by_name(self, registry):
        """Test searching courts by court name."""
        results = registry.search_courts("WARSZAWA")
        assert isinstance(results, list)
        assert len(results) > 0
        found_wa4m = False
        found_cikw = False
        for code, _name in results:
            if code == "WA4M":
                found_wa4m = True
            elif code == "CIKW":
                found_cikw = True
        assert found_wa4m or found_cikw, "Should find at least one Warsaw court"

    def test_search_courts_by_full_name(self, registry):
        """Test searching courts by full name content."""
        results = registry.search_courts("Mokotowa")
        assert isinstance(results, list)

    def test_search_courts_case_insensitive(self, registry):
        """Test that court search is case insensitive."""
        results_upper = registry.search_courts("WARSZAWA")
        results_lower = registry.search_courts("warszawa")
        results_mixed = registry.search_courts("Warszawa")
        assert len(results_upper) == len(results_lower) == len(results_mixed)

    def test_search_courts_empty_query(self, registry):
        """Test searching with empty query."""
        results = registry.search_courts("")
        assert isinstance(results, list)
        assert len(results) == len(registry.get_all_courts())

    def test_search_courts_no_matches(self, registry):
        """Test searching with query that has no matches."""
        results = registry.search_courts("NONEXISTENT")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_data_consistency(self, registry):
        """Test that data is consistent across different methods."""
        all_courts = registry.get_all_courts()
        detailed_courts = registry.get_all_courts_detailed()
        assert len(all_courts) == len(detailed_courts)
        for code, name in all_courts.items():
            assert code in detailed_courts
            assert detailed_courts[code]["name"] == name

    def test_court_data_not_empty(self, registry):
        """Test that court data is not empty and has expected structure."""
        all_courts = registry.get_all_courts()
        assert len(all_courts) > 100, "Should have more than 100 courts"
        for code in all_courts.keys():
            assert len(code) >= 3, f"Court code {code} too short"
            assert len(code) <= 6, f"Court code {code} too long"
            assert code.isupper(), f"Court code {code} should be uppercase"

    def test_specific_known_courts(self, registry, known_courts):
        """Test specific courts that we know should exist."""
        for code, expected_name in known_courts.items():
            assert registry.is_valid_court(code), f"Court {code} should exist"
            actual_name = registry.get_court_name(code)
            assert actual_name == expected_name, (
                f"Expected {expected_name}, got {actual_name}"
            )
            full_name = registry.get_court_full_name(code)
            assert full_name is not None, f"Court {code} should have full name"
            assert len(full_name) > 0, f"Court {code} full name should not be empty"

    def test_registry_immutability(self, registry):
        """Test that registry data cannot be accidentally modified."""
        all_courts = registry.get_all_courts()
        detailed_courts = registry.get_all_courts_detailed()
        original_length = len(all_courts)
        all_courts["TEST"] = "TEST COURT"
        detailed_courts["TEST"] = {"name": "TEST", "full_name": "TEST COURT"}
        fresh_all_courts = registry.get_all_courts()
        fresh_detailed_courts = registry.get_all_courts_detailed()
        assert len(fresh_all_courts) == original_length
        assert "TEST" not in fresh_all_courts
        assert "TEST" not in fresh_detailed_courts
