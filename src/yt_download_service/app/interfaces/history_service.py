from abc import ABC, abstractmethod

from src.yt_download_service.domain.models.history import History


class IHistoryService(ABC):
    """Interface for history service."""

    @abstractmethod
    def create(self, history: History) -> History:
        """Create a new history record."""
        pass
