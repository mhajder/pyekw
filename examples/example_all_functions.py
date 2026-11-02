"""
Example usage of all main pyekw library functions and classes.
"""

from pyekw import CheckDigitGenerator
from pyekw import CourtRegistry
from pyekw import KWNumber
from pyekw import KWUtils
from pyekw import KWValidator

# --- KWValidator ---
print("*" * 10, "KWValidator Example", "*" * 10)
validator = KWValidator()

# Validate a KW number
kw_number = "WA4M/00123456/4"
is_valid, error = validator.validate_kw_number(kw_number)
print(f"Valid: {is_valid}, Error: {error}")

# Parse KW number components
court_code, register_number, check_digit = validator.parse_kw_number(kw_number)
print(
    f"Parsed: court_code={court_code}, register_number={register_number}, check_digit={check_digit}"
)

# Validate individual components
print("Court code valid:", validator.validate_court_code(court_code))
print(
    "Check digit valid:",
    validator.validate_check_digit(court_code, register_number, check_digit),
)

# --- CheckDigitGenerator ---
print("*" * 10, "CheckDigitGenerator Example", "*" * 10)
generator = CheckDigitGenerator()

# Calculate check digit
calc_check_digit = generator.calculate_check_digit(court_code, register_number)
print(f"Calculated check digit: {calc_check_digit}")

# Generate complete KW number
full_kw = generator.generate_full_kw_number(court_code, register_number)
print(f"Full KW number: {full_kw}")

# --- CourtRegistry ---
print("*" * 10, "CourtRegistry Example", "*" * 10)
registry = CourtRegistry()

# Check if court exists
print("Court exists:", registry.is_valid_court(court_code))

# Get court name
print("Court name:", registry.get_court_name(court_code))

# Regional Court circuit and voivodeship
print("Circuit:", registry.get_court_circuit(court_code))
print("Voivodeship:", registry.get_court_voivodeship(court_code))

# Search courts
search_results = registry.search_courts("WARSZAWA")
print("Search results:", search_results)

# Get all courts
all_courts = registry.get_all_courts()
print(f"Total courts: {len(all_courts)}")

# --- KWUtils ---
print("*" * 10, "KWUtils Example", "*" * 10)
utils = KWUtils()

# Normalize KW number format (standard and compact)
normalized = utils.normalize_kw_number(" wa4m / 00123456 / 4 ")
print(f"Normalized: {normalized}")
compact_kw = utils.normalize_kw_number("WA4M/00123456/4", compact=True)
print(f"Compact format: {compact_kw}")

# Convert legacy book number to modern eKW
legacy_converted = utils.from_legacy("WA4M", "KW 12345")
print(f"Legacy converted: {legacy_converted}")

# Extract KW numbers from text
text = "Properties: WA4M/00123456/4 and BB1B/12345678/9"
extracted = utils.extract_kw_numbers(text)
print(f"Extracted KW numbers: {extracted}")

# Get detailed KW information
info = utils.get_kw_info(kw_number)
print(f"KW info: {info}")

# Generate series of KW numbers
series = utils.generate_kw_number_variants(court_code, 123456, 3)
print(f"KW number series: {series}")

# Validate multiple KW numbers
multi_results = utils.validate_multiple_kw_numbers([kw_number, "BB1B/12345678/9"])
print(f"Multiple validation results: {multi_results}")

# Suggest corrections for invalid KW number
suggestions = utils.suggest_corrections("WA4M/00123456/9")
print(f"Suggestions: {suggestions}")

# --- KWNumber Value Object ---
print("*" * 10, "KWNumber Example", "*" * 10)
kw = KWNumber.from_string("WA4M001234564")
print(f"KWNumber formatted: {kw.formatted}")
print(f"KWNumber compact:   {kw.compact}")
print(f"KWNumber court:     {kw.court_name} ({kw.circuit}, {kw.voivodeship})")
print(f"KWNumber portal URL: {kw.portal_url}")
