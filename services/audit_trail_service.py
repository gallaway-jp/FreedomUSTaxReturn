"""
Audit Trail Service - Tracks all changes and calculations for compliance and debugging

This service provides comprehensive audit logging for:
- Data entry changes with timestamps
- Calculation results and worksheets
- User actions and navigation
- Supporting document references
- Change history for compliance
"""

import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from config.app_config import AppConfig
from utils.event_bus import EventBus, Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Single audit log entry"""

    id: str
    timestamp: datetime
    user_id: str  # For future multi-user support
    action: str  # 'CREATE', 'UPDATE', 'DELETE', 'CALCULATE', 'VIEW', etc.
    entity_type: str  # 'personal_info', 'income', 'deductions', etc.
    entity_id: Optional[str]  # Specific record ID if applicable
    field_name: Optional[str]  # Specific field that changed
    old_value: Any  # Previous value (None for CREATE)
    new_value: Any  # New value (None for DELETE)
    session_id: str  # Session identifier
    ip_address: Optional[str]  # For future network logging
    user_agent: Optional[str]  # For future web/mobile support
    metadata: Dict[str, Any]  # Additional context
    calculation_worksheet: Optional[Dict[str, Any]]  # For calculation actions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        def serialize_value(value: Any) -> Any:
            """Safely serialize a value for JSON"""
            if value is None:
                return None
            elif isinstance(value, (str, int, float, bool)):
                return value
            elif isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            else:
                # For any other type, convert to string
                return str(value)

        data = asdict(self)
        # Convert datetime to ISO format
        data['timestamp'] = self.timestamp.isoformat()
        # Safely serialize all values
        for key, value in data.items():
            data[key] = serialize_value(value)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEntry':
        """Create from dictionary"""
        # Convert ISO timestamp back to datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class AuditSession:
    """Audit session information"""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    user_id: str
    actions_count: int
    entities_modified: List[str]
    calculations_performed: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data


class AuditTrailService:
    """
    Comprehensive audit trail service for tracking all application activities.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize audit trail service.

        Args:
            config: Application configuration
        """
        self.config = config or AppConfig()
        self.current_session: Optional[AuditSession] = None
        self.audit_log: List[AuditEntry] = []
        self.event_bus = EventBus.get_instance()

        # Ensure audit directory exists
        self.audit_dir = Path(self.config.safe_dir) / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Load existing audit log from disk
        self._load_audit_log()

        # Subscribe to data change events
        self.event_bus.subscribe(EventType.TAX_DATA_CHANGED, self._on_data_changed)
        self.event_bus.subscribe(EventType.CALCULATION_COMPLETED, self._on_calculation_completed)

        logger.info(f"Initialized AuditTrailService with audit directory: {self.audit_dir}")

    def start_session(self, user_id: str = "default_user") -> str:
        """
        Start a new audit session.

        Args:
            user_id: Identifier for the user/session

        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{user_id}"

        self.current_session = AuditSession(
            session_id=session_id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
            user_id=user_id,
            actions_count=0,
            entities_modified=[],
            calculations_performed=[]
        )

        # Log session start
        self.log_action(
            action="SESSION_START",
            entity_type="session",
            entity_id=session_id,
            metadata={"user_id": user_id}
        )

        logger.info(f"Started audit session: {session_id}")
        return session_id

    def end_session(self) -> None:
        """End the current audit session"""
        if self.current_session:
            self.current_session.end_time = datetime.now(timezone.utc)

            # Log session end
            self.log_action(
                action="SESSION_END",
                entity_type="session",
                entity_id=self.current_session.session_id,
                metadata={
                    "duration_seconds": (self.current_session.end_time - self.current_session.start_time).total_seconds(),
                    "actions_count": self.current_session.actions_count
                }
            )

            # Save session summary
            self._save_session_summary()

            # Save audit log to persist all entries
            self._save_audit_log()

            logger.info(f"Ended audit session: {self.current_session.session_id}")
            self.current_session = None

    def log_action(self, action: str, entity_type: str, entity_id: Optional[str] = None,
                  field_name: Optional[str] = None, old_value: Any = None,
                  new_value: Any = None, metadata: Optional[Dict[str, Any]] = None,
                  calculation_worksheet: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an audit action.

        Args:
            action: Action type ('CREATE', 'UPDATE', 'DELETE', etc.)
            entity_type: Type of entity being acted upon
            entity_id: Specific entity identifier
            field_name: Field that was changed
            old_value: Previous value
            new_value: New value
            metadata: Additional context
            calculation_worksheet: Calculation details for CALCULATE actions
        """
        entry = AuditEntry(
            id=f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}",
            timestamp=datetime.now(timezone.utc),
            user_id=self.current_session.user_id if self.current_session else "unknown",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            session_id=self.current_session.session_id if self.current_session else "no_session",
            ip_address=None,  # Not applicable for desktop app
            user_agent=None,  # Not applicable for desktop app
            metadata=metadata or {},
            calculation_worksheet=calculation_worksheet
        )

        self.audit_log.append(entry)

        # Update session counters
        if self.current_session:
            self.current_session.actions_count += 1
            if entity_type not in self.current_session.entities_modified:
                self.current_session.entities_modified.append(entity_type)

        # Auto-save periodically (every 10 actions)
        if len(self.audit_log) % 10 == 0:
            self._save_audit_log()

        logger.debug(f"Audit logged: {action} on {entity_type}")

    def log_data_change(self, entity_type: str, entity_id: str, field_name: str,
                       old_value: Any, new_value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a data field change.

        Args:
            entity_type: Type of data entity
            entity_id: Entity identifier
            field_name: Field that changed
            old_value: Previous value
            new_value: New value
            metadata: Additional context
        """
        action = "CREATE" if old_value is None else "UPDATE" if new_value is not None else "DELETE"

        self.log_action(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata
        )

    def log_calculation(self, calculation_type: str, inputs: Dict[str, Any],
                       results: Dict[str, Any], worksheet: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a tax calculation.

        Args:
            calculation_type: Type of calculation performed
            inputs: Calculation inputs
            results: Calculation results
            worksheet: Detailed calculation steps
        """
        self.log_action(
            action="CALCULATE",
            entity_type="calculation",
            entity_id=calculation_type,
            metadata={
                "calculation_type": calculation_type,
                "inputs": inputs,
                "results": results
            },
            calculation_worksheet=worksheet
        )

        # Update session calculations
        if self.current_session and calculation_type not in self.current_session.calculations_performed:
            self.current_session.calculations_performed.append(calculation_type)

    def get_audit_history(self, entity_type: Optional[str] = None,
                         entity_id: Optional[str] = None,
                         action: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[AuditEntry]:
        """
        Retrieve audit history with optional filtering.

        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of entries to return

        Returns:
            List of matching audit entries
        """
        filtered_entries = self.audit_log

        if entity_type:
            filtered_entries = [e for e in filtered_entries if e.entity_type == entity_type]

        if entity_id:
            filtered_entries = [e for e in filtered_entries if e.entity_id == entity_id]

        if action:
            filtered_entries = [e for e in filtered_entries if e.action == action]

        if start_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp >= start_date]

        if end_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp <= end_date]

        # Sort by timestamp descending (most recent first)
        filtered_entries.sort(key=lambda e: e.timestamp, reverse=True)

        return filtered_entries[:limit]

    def get_calculation_history(self, calculation_type: Optional[str] = None,
                               limit: int = 50) -> List[AuditEntry]:
        """
        Get calculation history.

        Args:
            calculation_type: Filter by calculation type
            limit: Maximum entries to return

        Returns:
            List of calculation audit entries
        """
        calculations = [e for e in self.audit_log if e.action == "CALCULATE"]

        if calculation_type:
            calculations = [e for e in calculations if e.entity_id == calculation_type]

        calculations.sort(key=lambda e: e.timestamp, reverse=True)
        return calculations[:limit]

    def export_audit_report(self, format: str = "json",
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> str:
        """
        Export audit report for a date range.

        Args:
            format: Export format ('json' or 'csv')
            start_date: Start date for report
            end_date: End date for report

        Returns:
            Path to exported file
        """
        entries = self.get_audit_history(start_date=start_date, end_date=end_date, limit=10000)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_report_{timestamp}.{format}"
        filepath = self.audit_dir / filename

        if format == "json":
            data = {
                "export_date": datetime.now(timezone.utc).isoformat(),
                "total_entries": len(entries),
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "entries": [entry.to_dict() for entry in entries]
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        elif format == "csv":
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'ID', 'Timestamp', 'User ID', 'Action', 'Entity Type',
                    'Entity ID', 'Field Name', 'Old Value', 'New Value', 'Session ID'
                ])

                for entry in entries:
                    writer.writerow([
                        entry.id,
                        entry.timestamp.isoformat(),
                        entry.user_id,
                        entry.action,
                        entry.entity_type,
                        entry.entity_id or '',
                        entry.field_name or '',
                        str(entry.old_value) if entry.old_value is not None else '',
                        str(entry.new_value) if entry.new_value is not None else '',
                        entry.session_id
                    ])

        logger.info(f"Exported audit report to: {filepath}")
        return str(filepath)

    def _on_data_changed(self, event: Event) -> None:
        """Handle data change events from the event bus"""
        if event.type == EventType.TAX_DATA_CHANGED:
            data = event.data
            self.log_data_change(
                entity_type=data.get('entity_type', 'unknown'),
                entity_id=data.get('entity_id', 'unknown'),
                field_name=data.get('field_name'),
                old_value=data.get('old_value'),
                new_value=data.get('new_value'),
                metadata=data.get('metadata', {})
            )

    def _on_calculation_completed(self, event: Event) -> None:
        """Handle calculation completion events"""
        if event.type == EventType.CALCULATION_COMPLETED:
            data = event.data
            self.log_calculation(
                calculation_type=data.get('calculation_type', 'unknown'),
                inputs=data.get('inputs', {}),
                results=data.get('results', {}),
                worksheet=data.get('worksheet')
            )

    def _save_audit_log(self) -> None:
        """Save current audit log to disk"""
        if not self.audit_log:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_log_{timestamp}.json"
        filepath = self.audit_dir / filename

        data = {
            "session_id": self.current_session.session_id if self.current_session else "unknown",
            "export_time": datetime.now(timezone.utc).isoformat(),
            "entries": [entry.to_dict() for entry in self.audit_log[-100:]]  # Last 100 entries
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    def _save_session_summary(self) -> None:
        """Save session summary"""
        if not self.current_session:
            return

        filename = f"session_{self.current_session.session_id}.json"
        filepath = self.audit_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save session summary: {e}")

    def _load_audit_log(self) -> None:
        """Load audit log from the most recent saved file"""
        try:
            # Find all audit log files
            audit_files = list(self.audit_dir.glob("audit_log_*.json"))
            if not audit_files:
                logger.info("No existing audit log files found")
                return

            # Sort by modification time, most recent first
            audit_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            loaded_entries = []

            # Try to load from the most recent files (up to 3 attempts)
            for filepath in audit_files[:3]:
                try:
                    logger.info(f"Loading audit log from: {filepath}")

                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Load audit entries
                    for entry_data in data.get('entries', []):
                        try:
                            entry = AuditEntry.from_dict(entry_data)
                            loaded_entries.append(entry)
                        except Exception as e:
                            logger.warning(f"Failed to load audit entry: {e}")

                    # If we successfully loaded entries, break
                    if loaded_entries:
                        break

                except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                    logger.warning(f"Failed to load audit log from {filepath}: {e}")
                    continue

            self.audit_log = loaded_entries
            logger.info(f"Loaded {len(self.audit_log)} audit entries from disk")

        except Exception as e:
            logger.error(f"Failed to load audit log: {e}")
            self.audit_log = []

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clean up old audit log files.

        Args:
            days_to_keep: Number of days of logs to keep

        Returns:
            Number of files deleted
        """
        import time
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0

        for filepath in self.audit_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete old audit log {filepath}: {e}")

        logger.info(f"Cleaned up {deleted_count} old audit log files")
        return deleted_count