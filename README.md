<div align="center">

# pyekw

**Validate, generate and analyze Polish land registry (eKW) numbers in Python**

[![PyPI](https://img.shields.io/pypi/v/pyekw?logo=pypi&logoColor=white)](https://pypi.org/project/pyekw/)
[![Python](https://img.shields.io/pypi/pyversions/pyekw?logo=python&logoColor=white)](https://pypi.org/project/pyekw/)
[![License](https://img.shields.io/github/license/mhajder/pyekw)](https://github.com/mhajder/pyekw/blob/main/LICENSE)

[![Pre-commit Checks](https://github.com/mhajder/pyekw/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/mhajder/pyekw/actions/workflows/pre-commit.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

[Installation](https://github.com/mhajder/pyekw#-installation) · [Quick Start](https://github.com/mhajder/pyekw#-quick-start) · [Command Line](https://github.com/mhajder/pyekw#-command-line) · [API Reference](https://github.com/mhajder/pyekw#-api-reference) · [Development](https://github.com/mhajder/pyekw#-development)

</div>

pyekw is a dependency-free Python library for working with Polish eKW (Elektroniczne Księgi Wieczyste) land registry numbers. It validates KW numbers against the official check digit algorithm and court code list, generates correct check digits, extracts KW numbers from free text and suggests corrections for mistyped ones.

A KW number has three parts:

```text
WA4M / 00123456 / 4
│      │          └── check digit (0-9)
│      └───────────── 8-digit register number
└──────────────────── 4-character court code
```

## ✨ Features

- **KW number validation**: check format, court code and check digit, with a readable error message
- **Check digit generation**: calculate check digits and build complete KW numbers
- **First-class KWNumber object**: typed, immutable value object with formats, equality, sorting and Pydantic V2 support
- **Court registry**: built-in database of 350+ Polish courts with Regional Court circuit and Voivodeship mapping
- **Text & legacy utilities**: normalize, extract, batch-validate, auto-pad, convert legacy book formats, and generate official portal links
- **Error correction**: suggest valid KW numbers for an invalid input
- **Command-line tool**: validate, inspect, extract, generate, and search courts without writing Python
- **Pre-commit hook**: fail commits that add invalid KW numbers to documents and fixtures
- **Zero dependencies**: pure Python, fully typed, nothing else to install

## 🚀 Installation

### Prerequisites

- Python 3.10 to 3.15

### Install from PyPI

```sh
# Using UV (recommended)
uv add pyekw

# Or using pip
pip install pyekw
```

### Install from Source

```sh
uv add "git+https://github.com/mhajder/pyekw.git"
```

## ⚡ Quick Start

```pycon
>>> from pyekw import CheckDigitGenerator, CourtRegistry, KWUtils, KWValidator

>>> # Validate a KW number
>>> validator = KWValidator()
>>> validator.validate_kw_number("WA4M/00123456/4")
(True, None)
>>> validator.validate_kw_number("WA4M/00123456/5")
(False, 'Invalid check digit: expected 4, got 5')

>>> # Generate a check digit or a complete KW number
>>> CheckDigitGenerator.calculate_check_digit("WA4M", "00123456")
4
>>> CheckDigitGenerator.generate_full_kw_number("KR1P", "00012345")
'KR1P/00012345/2'

>>> # Look up courts
>>> registry = CourtRegistry()
>>> registry.get_court_name("WA4M")
'WARSZAWA (X)'
>>> registry.search_courts("Kraków")
[('KR1P', 'KRAKÓW')]

>>> # Work with KW numbers in text
>>> utils = KWUtils()
>>> utils.normalize_kw_number(" wa4m / 00123456 / 4 ")
'WA4M/00123456/4'
>>> utils.extract_kw_numbers("Nieruchomość WA4M/00123456/4 oraz KR1P/00012345/2.")
['WA4M/00123456/4', 'KR1P/00012345/2']
>>> utils.suggest_corrections("WA4M/00123456/5")
['WA4M/00123456/4']

```

More examples are in [`examples/example_all_functions.py`](https://github.com/mhajder/pyekw/blob/main/examples/example_all_functions.py):

```sh
uv run python examples/example_all_functions.py
```

## 💻 Command Line

Run it without installing using `uvx`, or as `pyekw` after `pip install pyekw`:

```sh
# Validate one or more KW numbers (exit code 1 if any is invalid)
uvx pyekw validate WA4M/00123456/4 WA4M/00123456/5
# WA4M/00123456/4: valid
# WA4M/00123456/5: invalid (Invalid check digit: expected 4, got 5)
#   did you mean: WA4M/00123456/4

# Auto-pad register numbers shorter than 8 digits
uvx pyekw validate --auto-pad WA4M/123456/4

# Show court, circuit, voivodeship and register details
uvx pyekw info WA4M/00123456/4

# Generate complete KW numbers with calculated check digits
uvx pyekw generate WA4M 12345
# WA4M/00012345/2
uvx pyekw generate WA4M 12345 --count 3 --compact
# WA4M000123452
# WA4M000123469
# WA4M000123476

# Search land registry courts by code, name or city, or filter by region
uvx pyekw courts "Kraków"
uvx pyekw courts --voivodeship "mazowieckie"
uvx pyekw courts --circuit "Warszawie"

# Find KW numbers in text files, or in standard input
uvx pyekw extract contract.txt
pdftotext contract.pdf - | uvx pyekw extract --valid-only --include-compact

# Lint files: print invalid KW numbers and exit with 1 if any is found
uvx pyekw extract --check docs/*.md
```

Every command supports `--json` for machine-readable output. Run `uvx pyekw --help` for all options.

## 📚 API Reference

### `KWNumber`

Immutable, typed value object representing a validated Polish land registry (eKW) number.

```python
from pyekw import KWNumber

kw = KWNumber.from_string("WA4M001234564")
print(kw.formatted)  # WA4M/00123456/4
print(kw.compact)  # WA4M001234564
print(kw.court_name)  # WARSZAWA (X)
print(kw.circuit)  # Sąd Okręgowy w Warszawie
print(kw.voivodeship)  # mazowieckie
# https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW
print(kw.portal_url)
```

| Method / Property | Returns | Description |
|-------------------|---------|-------------|
| `KWNumber.from_string(kw_str, auto_pad=False, check_court=True)` | `KWNumber` | Parse and validate from standard or compact string |
| `KWNumber.from_parts(court, number, auto_pad=True, check_court=True)` | `KWNumber` | Build from court and register number, calculating check digit |
| `KWNumber.from_legacy(court, legacy_number, check_court=True)` | `KWNumber` | Convert legacy number (e.g. `'KW 12345'`) |
| `kw.formatted` / `str(kw)` | `str` | Standard string format `COURT/REGISTER/CHECK` |
| `kw.compact` | `str` | Compact 13-character string `COURTREGISTERCHECK` |
| `kw.spaced` | `str` | Spaced format `COURT / REGISTER / CHECK` |
| `kw.court_name` | `str \| None` | Short court name |
| `kw.court_full_name` | `str \| None` | Full descriptive court name |
| `kw.circuit` | `str \| None` | Regional Court circuit (Sąd Okręgowy) |
| `kw.voivodeship` | `str \| None` | Voivodeship (*województwo*) name |
| `kw.portal_url` / `kw.portal_params` | `str` / `dict` | Official Ministry of Justice portal link and parameters |
| `kw.to_dict()` / `kw.to_json()` | `KWInfo` / `str` | Export as dictionary or JSON string |

`KWNumber` supports equality with other `KWNumber` instances (compare `str(kw)` to match a string), sorting, hashing (can be used in sets or dict keys), and automatic validation in **Pydantic V2** models.

### `KWValidator`

Validates Polish KW numbers.

| Method | Returns | Description |
|--------|---------|-------------|
| `validate_kw_number(kw_number, check_court=True, auto_pad=False, allow_compact=False)` | `tuple[bool, str \| None]` | Validate a complete KW number, returns `(is_valid, error_message)` |
| `is_valid_kw_number(kw_number, check_court=True, auto_pad=False, allow_compact=False)` | `bool` | Same as above, but returns only the result |
| `parse_kw_number(kw_number, auto_pad=False, allow_compact=False)` | `tuple[str, str, str]` | Split a KW number into court code, register number and check digit |
| `validate_court_code(court_code)` | `bool` | Check if the court code exists |
| `validate_check_digit(court_code, register_number, check_digit)` | `bool` | Check if the check digit is correct |

### `CheckDigitGenerator`

Generates check digits and complete KW numbers. All methods are static.

| Method | Returns | Description |
|--------|---------|-------------|
| `calculate_check_digit(court_code, register_number)` | `int` | Calculate the check digit |
| `generate_full_kw_number(court_code, register_number)` | `str` | Build a complete KW number with the correct check digit |

### `CourtRegistry`

Built-in database of Polish land registry courts with circuit and regional mapping.

| Method | Returns | Description |
|--------|---------|-------------|
| `is_valid_court(court_code)` | `bool` | Check if a court code exists |
| `get_court_name(court_code)` | `str \| None` | Short court name |
| `get_court_full_name(court_code)` | `str \| None` | Full court name with its territorial jurisdiction |
| `get_court_circuit(court_code)` | `str \| None` | Regional Court circuit (Sąd Okręgowy) |
| `get_court_voivodeship(court_code)` | `str \| None` | Voivodeship (*województwo*) |
| `get_courts_by_voivodeship(voivodeship)` | `list[tuple[str, str]]` | All courts in a voivodeship |
| `get_courts_by_circuit(circuit)` | `list[tuple[str, str]]` | All courts in a circuit |
| `get_all_circuits()` | `dict[str, dict[str, str]]` | All 47 circuits with voivodeships |
| `search_courts(query)` | `list[tuple[str, str]]` | Search courts by code, name or full name |
| `get_all_courts()` | `dict[str, str]` | All court codes with short names |
| `get_all_courts_detailed()` | `dict[str, dict[str, str]]` | All court codes with short, full, circuit and voivodeship names |
| `get_official_url()` / `get_official_search_params(...)` | `str` / `dict` | Official search portal URL and parameters |

### `KWUtils`

Helpers for working with KW numbers in real-world data.

| Method | Returns | Description |
|--------|---------|-------------|
| `normalize_kw_number(kw_number, auto_pad=False, compact=False)` | `str` | Normalize spacing, letter case, separators, or compact format |
| `from_legacy(court_code, legacy_number, check_court=True)` | `str` | Convert legacy number (e.g. `'KW 12345'`) to complete eKW number |
| `extract_kw_numbers(text, include_compact=False)` | `list[str]` | Find all KW numbers in a text (standard or compact) |
| `get_kw_info(kw_number, auto_pad=False)` | `KWInfo \| None` | Court, circuit, voivodeship, register, check digit, and url |
| `validate_multiple_kw_numbers(kw_numbers, check_court=True, auto_pad=False)` | `dict[str, KWValidationResult]` | Validate many KW numbers at once |
| `generate_kw_number_variants(court_code, base_number, count=10)` | `list[str]` | Generate a series of consecutive valid KW numbers |
| `suggest_corrections(kw_number, check_court=True)` | `list[str]` | Suggest valid KW numbers for an invalid input |

### Result types

`KWInfo` and `KWValidationResult` are `TypedDict`s exported from `pyekw`, so type checkers and editors know every key of the returned dicts. In `KWValidationResult`, the court and register keys are only present when the KW number is valid.

The installed version is available as `pyekw.__version__`.

## 🪝 Pre-commit Hook

You can use `pyekw` in `.pre-commit-config.yaml` of other repositories to validate KW numbers in docs and fixtures. The hook fails if a file contains an invalid KW number; files without KW numbers pass:

```yaml
repos:
  - repo: https://github.com/mhajder/pyekw
    rev: v0.4.0
    hooks:
      - id: pyekw-validate
```

## 🔨 Development

```sh
# Clone and install with development dependencies
git clone https://github.com/mhajder/pyekw.git
cd pyekw
uv sync --group dev

# Run tests, README examples and the 100% coverage check
uv run pytest

# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Run type checking
uv run ty check .

# Setup prek hooks
uv run prek install
```

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) and are checked by [commitizen](https://commitizen-tools.github.io/commitizen/).

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](https://github.com/mhajder/pyekw/blob/main/CONTRIBUTING.md) for the dev setup, checks and commit message format, and use the [issue templates](https://github.com/mhajder/pyekw/issues/new/choose) for bugs and feature requests.

Found a security problem? Please report it privately as described in [SECURITY.md](https://github.com/mhajder/pyekw/blob/main/SECURITY.md).

## 📜 License

MIT License - see [LICENSE](https://github.com/mhajder/pyekw/blob/main/LICENSE) for details.
