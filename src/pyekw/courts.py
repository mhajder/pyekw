"""
Court registry for Polish eKW system.
"""

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .courts_data import COURTS


class CourtRegistry:
    """Registry of Polish courts handling land registry (eKW) matters."""

    def __init__(self):
        """Initialize the court registry with complete court data."""
        self._courts_data = self._load_courts()

    def _load_courts(self) -> Dict[str, Dict[str, str]]:
        """Load complete court data from the COURTS constant."""
        return COURTS.copy()

    def is_valid_court(self, court_code: str) -> bool:
        """
        Check if a court code is valid.

        Args:
            court_code: The court code to validate

        Returns:
            True if the court code exists, False otherwise
        """
        return court_code.upper() in self._courts_data

    def get_court_name(self, court_code: str) -> Optional[str]:
        """
        Get the short name of a court by its code.

        Args:
            court_code: The court code

        Returns:
            The court name if found, None otherwise
        """
        court_data = self._courts_data.get(court_code.upper())
        return court_data["name"] if court_data else None

    def get_court_full_name(self, court_code: str) -> Optional[str]:
        """
        Get the full descriptive name of a court by its code.

        Args:
            court_code: The court code

        Returns:
            The court full name if found, None otherwise
        """
        court_data = self._courts_data.get(court_code.upper())
        return court_data["full_name"] if court_data else None

    def get_all_courts(self) -> Dict[str, str]:
        """
        Get all courts as a dictionary.

        Returns:
            Dictionary mapping court codes to court names
        """
        return {code: data["name"] for code, data in self._courts_data.items()}

    def get_all_courts_detailed(self) -> Dict[str, Dict[str, str]]:
        """
        Get all courts with detailed information.

        Returns:
            Dictionary mapping court codes to court data (name and full_name)
        """
        return self._courts_data.copy()

    def search_courts(self, query: str) -> List[Tuple[str, str]]:
        """
        Search for courts by name or code.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of tuples (code, name) matching the query
        """
        query = query.upper()
        results = []

        for code, data in self._courts_data.items():
            name = data["name"]
            full_name = data["full_name"]
            if query in code or query in name.upper() or query in full_name.upper():
                results.append((code, name))

        return results
