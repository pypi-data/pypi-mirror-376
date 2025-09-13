"""
Stub file for nameparser module.

This stub provides type information for the nameparser library,
specifically the HumanName class used for parsing human names.
"""

class HumanName:
    """
    A class for parsing human names into their component parts.

    This class takes a full name string and parses it into first name,
    last name, middle name, and other components.
    """

    def __init__(self, full_name: str) -> None:
        """
        Initialize HumanName with a full name string.

        Args:
            full_name: The full name to parse (e.g., "John Michael Smith")
        """
        ...

    @property
    def first(self) -> str:
        """
        The first name component.

        Returns:
            The first name as a string, empty string if not found
        """
        ...

    @property
    def last(self) -> str:
        """
        The last name component.

        Returns:
            The last name as a string, empty string if not found
        """
        ...

    @property
    def middle(self) -> str:
        """
        The middle name component.

        Returns:
            The middle name as a string, empty string if not found
        """
        ...

    @property
    def title(self) -> str:
        """
        The title component (Mr., Mrs., Dr., etc.).

        Returns:
            The title as a string, empty string if not found
        """
        ...

    @property
    def suffix(self) -> str:
        """
        The suffix component (Jr., Sr., III, etc.).

        Returns:
            The suffix as a string, empty string if not found
        """
        ...

    @property
    def nickname(self) -> str:
        """
        The nickname component.

        Returns:
            The nickname as a string, empty string if not found
        """
        ...

    def __str__(self) -> str:
        """
        String representation of the parsed name.

        Returns:
            The full name as a string
        """
        ...

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            A string representation of the HumanName object
        """
        ...
