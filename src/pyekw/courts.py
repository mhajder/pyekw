"""
Court registry for Polish eKW system.
"""

from .constants import EKW_PORTAL_URL
from .courts_data import CIRCUITS
from .courts_data import COURTS


class CourtRegistry:
    """Registry of Polish courts handling land registry (eKW) matters."""

    def __init__(self):
        """Initialize the court registry with complete court data."""
        self._courts_data = self._load_courts()

    def _load_courts(self) -> dict[str, dict[str, str]]:
        """Load complete court data from the COURTS and CIRCUITS constants."""
        loaded: dict[str, dict[str, str]] = {}
        for code, data in COURTS.items():
            prefix = code[:2]
            circuit_data = CIRCUITS.get(prefix, {})
            entry = data.copy()
            entry["circuit"] = circuit_data.get("circuit", "")
            entry["voivodeship"] = circuit_data.get("voivodeship", "")
            loaded[code] = entry
        return loaded

    def is_valid_court(self, court_code: str) -> bool:
        """
        Check if a court code is valid.

        Args:
            court_code: The court code to validate

        Returns:
            True if the court code exists, False otherwise
        """
        return court_code.upper() in self._courts_data

    def get_court_name(self, court_code: str) -> str | None:
        """
        Get the short name of a court by its code.

        Args:
            court_code: The court code

        Returns:
            The court name if found, None otherwise
        """
        court_data = self._courts_data.get(court_code.upper())
        return court_data["name"] if court_data else None

    def get_court_full_name(self, court_code: str) -> str | None:
        """
        Get the full descriptive name of a court by its code.

        Args:
            court_code: The court code

        Returns:
            The court full name if found, None otherwise
        """
        court_data = self._courts_data.get(court_code.upper())
        return court_data["full_name"] if court_data else None

    def get_court_circuit(self, court_code: str) -> str | None:
        """
        Get the Regional Court circuit (Sąd Okręgowy) for a court code.

        Args:
            court_code: The court code

        Returns:
            The regional court circuit name, or None if the court is unknown
        """
        court_data = self._courts_data.get(court_code.upper())
        return court_data["circuit"] if court_data and court_data["circuit"] else None

    def get_court_voivodeship(self, court_code: str) -> str | None:
        """
        Get the Voivodeship (województwo) for a court code.

        Args:
            court_code: The court code

        Returns:
            The voivodeship name in Polish, or None if the court is unknown
        """
        court_data = self._courts_data.get(court_code.upper())
        return (
            court_data["voivodeship"]
            if court_data and court_data["voivodeship"]
            else None
        )

    def get_all_circuits(self) -> dict[str, dict[str, str]]:
        """
        Get all regional court circuits and their voivodeships.

        Returns:
            Dictionary mapping 2-letter prefixes to circuit and voivodeship
        """
        return {prefix: data.copy() for prefix, data in CIRCUITS.items()}

    def get_courts_by_voivodeship(self, voivodeship: str) -> list[tuple[str, str]]:
        """
        Get all courts located in a given voivodeship.

        Args:
            voivodeship: Voivodeship name (case-insensitive, e.g. 'mazowieckie' or 'województwo mazowieckie')

        Returns:
            List of tuples (code, name) in the voivodeship
        """
        voiv_clean = voivodeship.strip().lower().removeprefix("województwo").strip()
        return [
            (code, data["name"])
            for code, data in self._courts_data.items()
            if data.get("voivodeship", "").lower() == voiv_clean
        ]

    def get_courts_by_circuit(self, circuit: str) -> list[tuple[str, str]]:
        """
        Get all courts belonging to a given regional court circuit.

        Args:
            circuit: Regional court circuit name or query (case-insensitive)

        Returns:
            List of tuples (code, name) in the circuit
        """
        query = circuit.strip().lower()
        if not query:
            return []
        return [
            (code, data["name"])
            for code, data in self._courts_data.items()
            if query in data.get("circuit", "").lower()
        ]

    def get_all_courts(self) -> dict[str, str]:
        """
        Get all courts as a dictionary.

        Returns:
            Dictionary mapping court codes to court names
        """
        return {code: data["name"] for code, data in self._courts_data.items()}

    def get_all_courts_detailed(self) -> dict[str, dict[str, str]]:
        """
        Get all courts with detailed information.

        Returns:
            Dictionary mapping court codes to court data (name, full_name, circuit, voivodeship)
        """
        return {code: data.copy() for code, data in self._courts_data.items()}

    def search_courts(self, query: str) -> list[tuple[str, str]]:
        """
        Search for courts by code, name or full name.

        Use get_courts_by_circuit() or get_courts_by_voivodeship() to filter by region.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of tuples (code, name) matching the query
        """
        query = query.upper()
        return [
            (code, data["name"])
            for code, data in self._courts_data.items()
            if query in code
            or query in data["name"].upper()
            or query in data["full_name"].upper()
        ]

    @staticmethod
    def get_official_url() -> str:
        """
        Get the URL to the official Ministry of Justice eKW search portal.

        Returns:
            Portal search URL
        """
        return EKW_PORTAL_URL

    @staticmethod
    def get_official_search_params(
        court_code: str, register_number: str, check_digit: int | str
    ) -> dict[str, str]:
        """
        Get form parameters expected by the official Ministry of Justice eKW portal.

        Args:
            court_code: 4-character court code
            register_number: 8-digit register number
            check_digit: 1-digit check digit

        Returns:
            Dictionary with portal parameter names and values
        """
        return {
            "kodWydzialu": court_code.upper(),
            "numerKw": str(register_number),
            "cyfraKontrolna": str(check_digit),
        }
