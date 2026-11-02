import os
import json
import time
import threading
from typing import Any, Dict, Optional, List
from config import settings

class AuditLogger:
    """
    Thread-safe JSONL audit logger.
    Logs every user query, assistant reply, code execution, execution time, and error.
    This fulfills the 'run.jsonl' public log requirement and provides data for the web dashboard.
    """
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or settings.log_file
        self._lock = threading.Lock()
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                pass  # create empty file

    def log(
        self,
        event_type: str,
        chat_id: int | str,
        user_message: str,
        answer: Any,
        code_executed: Optional[str] = None,
        duration_ms: Optional[float] = None,
        tokens_used: Optional[int] = None,
        has_chart: bool = False,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an event to the JSONL log file."""
        event = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": event_type,
            "chat_id": chat_id,
            "user_message": user_message,
            "answer": answer,
            "code_executed": code_executed,
            "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
            "tokens_used": tokens_used,
            "has_chart": has_chart,
            "error": error,
            "metadata": metadata or {},
        }

        line = json.dumps(event, ensure_ascii=False)
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        return event

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch the most recent log entries in reverse chronological order."""
        if not os.path.exists(self.log_path):
            return []

        entries = []
        with self._lock:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except Exception:
                            continue

        return list(reversed(entries[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate stats from the audit log."""
        entries = self.get_recent_logs(limit=1000)
        total_queries = len(entries)
        errors = sum(1 for e in entries if e.get("error"))
        charts_generated = sum(1 for e in entries if e.get("has_chart"))
        
        durations = [e["duration_ms"] for e in entries if e.get("duration_ms") is not None]
        avg_latency = round(sum(durations) / len(durations), 1) if durations else 0.0

        return {
            "total_queries": total_queries,
            "errors": errors,
            "success_rate": round(100 * (1 - errors / total_queries), 1) if total_queries else 100.0,
            "charts_generated": charts_generated,
            "avg_latency_ms": avg_latency,
            "log_file_size_bytes": os.path.getsize(self.log_path) if os.path.exists(self.log_path) else 0,
        }

# Global singleton
audit_logger = AuditLogger()
