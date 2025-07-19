from abc import ABC, abstractmethod

from src.yt_download_service.domain.models.history import History


class IHistoryRepository(ABC):
    """Interface for history repository."""

    @abstractmethod
    def create(self, history: History) -> History:
        """Create a new history record."""
        pass
