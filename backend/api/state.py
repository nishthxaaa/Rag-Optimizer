from typing import Optional
from enum import Enum
import threading

class OptimizationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"

class AppState:
    """
    Single shared state object for the FastAPI app.
    Holds optimization status and the active winning RAG chain.
    Thread-safe for background task updates.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.status: OptimizationStatus = OptimizationStatus.IDLE
        self.current_doc_id: Optional[str] = None
        self.winner_chain = None          # The active RAG chain after optimization
        self.winner_config: Optional[dict] = None
        self.progress_message: str = ""
        self.error_message: str = ""
        self.scoreboard: Optional[dict] = None

    def set_running(self, doc_id: str, message: str = "Optimization started..."):
        with self._lock:
            self.status = OptimizationStatus.RUNNING
            self.current_doc_id = doc_id
            self.progress_message = message
            self.winner_chain = None
            self.winner_config = None
            self.error_message = ""

    def set_progress(self, message: str):
        with self._lock:
            self.progress_message = message

    def set_complete(self, winner_variant: dict):
        with self._lock:
            self.status = OptimizationStatus.COMPLETE
            self.winner_chain = winner_variant["chain"]
            self.winner_config = {
                k: v for k, v in winner_variant["config"].items()
                if k not in ("chain", "retriever", "scoreboard")
            }
            self.scoreboard = winner_variant["config"].get("scoreboard")
            self.progress_message = "Optimization complete."

    def set_failed(self, error: str):
        with self._lock:
            self.status = OptimizationStatus.FAILED
            self.error_message = error
            self.progress_message = ""

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "status": self.status,
                "doc_id": self.current_doc_id,
                "message": self.progress_message,
                "error": self.error_message,
                "winner_config": self.winner_config,
            }

# Single global instance — imported by all route modules
app_state = AppState()