"""Audit trail system for DeFi Sentinel.

Records all agent decisions, executions, and portfolio state changes
for monitoring, debugging, and compliance.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    # Agent lifecycle
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"

    # Portfolio
    PORTFOLIO_SNAPSHOT = "portfolio_snapshot"
    PORTFOLIO_REBALANCED = "portfolio_rebalanced"

    # Decisions
    DECISION_MADE = "decision_made"
    DECISION_EXECUTED = "decision_executed"
    DECISION_FAILED = "decision_failed"

    # Onchain
    TRANSACTION_SENT = "transaction_sent"
    TRANSACTION_CONFIRMED = "transaction_confirmed"
    TRANSACTION_FAILED = "transaction_failed"

    # Alerts
    ALERT_TRIGGERED = "alert_triggered"
    LIQUIDATION_RISK = "liquidation_risk"
    YIELD_OPPORTUNITY = "yield_opportunity"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    event_type: AuditEventType
    timestamp: float
    source: str  # which strategy/module generated this
    data: dict
    entry_id: str = ""
    correlation_id: str = ""  # link related events

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "data": self.data,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class AuditTrail:
    """Persistent audit trail for all agent activities."""

    def __init__(self, log_dir: str = "logs"):
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[AuditEntry] = []
        self._max_entries = 10000
        self._entry_counter = 0

    def log(
        self,
        event_type: AuditEventType,
        source: str,
        data: dict,
        correlation_id: Optional[str] = None,
    ) -> AuditEntry:
        """Log an audit entry."""
        self._entry_counter += 1
        entry = AuditEntry(
            event_type=event_type,
            timestamp=time.time(),
            source=source,
            data=data,
            entry_id=f"evt_{self._entry_counter:06d}",
            correlation_id=correlation_id or "",
        )

        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

        # Write to file
        self._write_entry(entry)

        # Also log to application logger
        level = logging.DEBUG
        if event_type in (
            AuditEventType.AGENT_ERROR,
            AuditEventType.TRANSACTION_FAILED,
            AuditEventType.DECISION_FAILED,
            AuditEventType.LIQUIDATION_RISK,
        ):
            level = logging.WARNING
        elif event_type in (
            AuditEventType.AGENT_STARTED,
            AuditEventType.AGENT_STOPPED,
        ):
            level = logging.INFO

        logger.log(level, f"AUDIT: {entry.to_json()}")

        return entry

    def _write_entry(self, entry: AuditEntry):
        """Write entry to audit log file."""
        audit_file = self._log_dir / "audit.jsonl"
        with open(audit_file, "a") as f:
            f.write(entry.to_json() + "\n")

    def get_entries(
        self,
        event_type: Optional[AuditEventType] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query audit entries."""
        entries = self._entries

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        if source:
            entries = [e for e in entries if e.source == source]

        return entries[-limit:]

    def get_summary(self) -> dict:
        """Get audit trail summary."""
        type_counts: dict[str, int] = {}
        for entry in self._entries:
            type_counts[entry.event_type.value] = (
                type_counts.get(entry.event_type.value, 0) + 1
            )

        return {
            "total_entries": len(self._entries),
            "event_type_counts": type_counts,
            "latest_entry": (
                self._entries[-1].to_dict() if self._entries else None
            ),
        }

    def export_json(self, output_path: Optional[str] = None) -> str:
        """Export all entries as JSON."""
        data = {
            "total_entries": len(self._entries),
            "entries": [e.to_dict() for e in self._entries],
        }
        json_str = json.dumps(data, indent=2, default=str)

        if output_path:
            Path(output_path).write_text(json_str)

        return json_str