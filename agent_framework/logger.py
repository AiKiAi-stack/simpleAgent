import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from .config import settings


def setup_logger(name: str = "agent") -> logging.Logger:
    """
    Setup logger with file and console handlers.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create log directory
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(exist_ok=True)

    # File handler
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class LogManager:
    """Manage agent execution logs."""

    def __init__(self):
        """Initialize log manager."""
        self.log_dir = Path(settings.log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.logger = setup_logger()

    def save_session_log(self, session_id: str, logs: List[Dict[str, Any]]) -> str:
        """
        Save session logs to file.

        Args:
            session_id: Unique session identifier
            logs: List of log entries

        Returns:
            Path to saved log file
        """
        log_file = self.log_dir / f"session_{session_id}.json"

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "logs": logs,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        self.logger.info(f"Saved session log: {log_file}")
        return str(log_file)

    def get_session_log(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session log by ID.

        Args:
            session_id: Session identifier to look up

        Returns:
            Session log data or None if not found
        """
        log_file = self.log_dir / f"session_{session_id}.json"

        if not log_file.exists():
            return None

        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent session logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of session metadata (id, timestamp, log_path)
        """
        log_files = sorted(
            self.log_dir.glob("session_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:limit]

        sessions = []
        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions.append(
                    {
                        "session_id": data["session_id"],
                        "timestamp": data["timestamp"],
                        "log_path": str(log_file),
                    }
                )

        return sessions
