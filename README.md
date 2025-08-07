# pyekw - Polish eKW (Land Registry) Utilities

A Python library for working with Polish eKW (Elektroniczne Księgi Wieczyste) land registry numbers.

## Features

- **KW Number Validation**: Validate complete KW numbers including court codes and check digits
- **Check Digit Generation**: Calculate correct check digits for court codes and register numbers
- **Court Registry**: Comprehensive database of Polish courts handling land registry matters
- **Utility Functions**: Normalize, extract, and analyze KW numbers from various sources

## Installation

```sh
uv add "git+https://github.com/mhajder/pyekw.git"
```

## Quick Start

```python
from pyekw import KWValidator, CheckDigitGenerator, CourtRegistry, KWUtils

# Validate a KW number
validator = KWValidator()
is_valid, error = validator.validate_kw_number("WA4M/00123456/4")
print(f"Valid: {is_valid}")  # True

# Generate check digit
generator = CheckDigitGenerator()
check_digit = generator.calculate_check_digit("WA4M", "00123456")
print(f"Check digit: {check_digit}")  # 4

# Work with court registry
registry = CourtRegistry()
court_name = registry.get_court_name("WA4M")
print(f"Court: {court_name}")  # WARSZAWA

# Utility functions
utils = KWUtils()
normalized = utils.normalize_kw_number(" wa4m / 00123456 / 4 ")
print(f"Normalized: {normalized}")  # WA4M/00123456/4
```

## API Documentation

### KWValidator

Class for validating Polish KW numbers.

**Methods:**

- `validate_kw_number(kw_number: str) -> Tuple[bool, Optional[str]]`  
  Validates a complete KW number.  
  **Returns:** `(is_valid, error_message)`

- `parse_kw_number(kw_number: str) -> Tuple[str, str, str]`  
  Parses a KW number into its components: court code, register number, check digit.

- `validate_court_code(court_code: str) -> bool`  
  Checks if the court code is valid.

- `validate_check_digit(court_code: str, register_number: str, check_digit: str) -> bool`  
  Validates the check digit for given court code and register number.

---

### CheckDigitGenerator

Class for generating check digits and full KW numbers.

**Methods:**

- `calculate_check_digit(court_code: str, register_number: str) -> int`  
  Calculates the check digit for a given court code and register number.

- `generate_full_kw_number(court_code: str, register_number: str) -> str`  
  Generates a complete KW number with the correct check digit.

---

### CourtRegistry

Class for working with the court database.

**Methods:**

- `is_valid_court(court_code: str) -> bool`  
  Checks if a court code exists in the registry.

- `get_court_name(court_code: str) -> str`  
  Returns the name of the court for a given code.

- `search_courts(query: str) -> List[Dict]`  
  Searches courts by name or code.

- `get_all_courts() -> Dict[str, str]`  
  Returns a dictionary of all court codes and names.

---

### KWUtils

Utility class for working with KW numbers.

**Methods:**

- `normalize_kw_number(kw_number: str) -> str`  
  Normalizes the format of a KW number.

- `extract_kw_numbers(text: str) -> List[str]`  
  Extracts all KW numbers from a given text.

- `get_kw_info(kw_number: str) -> Dict`  
  Returns detailed information about a KW number.

- `generate_kw_number_variants(court_code: str, start_number: int, count: int) -> List[str]`  
  Generates a series of KW numbers.

- `validate_multiple_kw_numbers(kw_numbers: List[str]) -> List[Tuple[str, bool, Optional[str]]]`  
  Validates multiple KW numbers at once.

- `suggest_corrections(kw_number: str) -> List[str]`  
  Suggests possible corrections for an invalid KW number.

## Examples

You can find example usage of all main functions and classes in the `examples/` directory.

- [`examples/example_all_functions.py`](examples/example_all_functions.py): Demonstrates validation, parsing, check digit generation, court registry operations, and utility functions.

To run the example:

```sh
python examples/example_all_functions.py
```

Feel free to explore and modify the example to fit your use case.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
