## v0.3.0 (2026-10-23)

### Feat

- add pyekw command-line interface
- **utils**: return typed results from get_kw_info and validate_multiple_kw_numbers
- add pyekw.__version__
- add py.typed marker for type checkers

### Fix

- **courts**: correct the OL1L court name
- **utils**: suggest similar known courts for unknown court codes
- **utils**: extract KW numbers with spaces around separators
- require 4-character court codes, also with check_court=False
- **validator**: reject non-ASCII digits in KW numbers

## v0.2.0 (2025-12-18)

### Feat

- **dependencies**: add commitizen for conventional commits support

### Fix

- **publish**: trigger on version tags, update actions and better uv sync
- add permissions to test workflow

## v0.1.0 (2025-08-07)
