from yt_download_service.app.interfaces.history_service import IHistoryService
from yt_download_service.domain.models.history import History


class HistoryService(IHistoryService):
    """Repository for managing history records."""

    def __init__(self):
        # This will be implemented later
        self.history = []

    def create(self, history: History) -> History:
        """Create a new history record."""
        self.history.append(history)
        return history
