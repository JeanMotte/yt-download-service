from enum import Enum, unique


@unique
class ROLE(str, Enum):
    """Enumeration for user roles."""

    ADMIN = "admin"
    STANDARD = "standard"

    @staticmethod
    def values() -> list[str]:
        """Return a list of all role values."""
        return [c.value for c in ROLE]
