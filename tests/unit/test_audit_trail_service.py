"""
Unit tests for Audit Trail Service
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from services.audit_trail_service import AuditTrailService, AuditEntry, AuditSession
from config.app_config import AppConfig
from utils.event_bus import EventType


class TestAuditEntry:
    """Test AuditEntry dataclass"""

    def test_audit_entry_creation(self):
        """Test creating an audit entry"""
        timestamp = datetime.now(timezone.utc)
        entry = AuditEntry(
            id="test_id",
            timestamp=timestamp,
            user_id="test_user",
            action="CREATE",
            entity_type="personal_info",
            entity_id="test_entity",
            field_name="first_name",
            old_value=None,
            new_value="John",
            session_id="session_123",
            ip_address=None,
            user_agent=None,
            metadata={},
            calculation_worksheet=None
        )

        assert entry.id == "test_id"
        assert entry.user_id == "test_user"
        assert entry.action == "CREATE"
        assert entry.entity_type == "personal_info"
        assert entry.new_value == "John"

    def test_audit_entry_to_dict(self):
        """Test converting audit entry to dictionary"""
        timestamp = datetime.now(timezone.utc)
        entry = AuditEntry(
            id="test_id",
            timestamp=timestamp,
            user_id="test_user",
            action="UPDATE",
            entity_type="income",
            entity_id="w2_1",
            field_name="wages",
            old_value=50000,
            new_value=55000,
            session_id="session_123",
            ip_address=None,
            user_agent=None,
            metadata={},
            calculation_worksheet=None
        )

        data = entry.to_dict()
        assert data["id"] == "test_id"
        assert data["action"] == "UPDATE"
        assert data["old_value"] == 50000
        assert data["new_value"] == 55000
        assert "timestamp" in data

    def test_audit_entry_from_dict(self):
        """Test creating audit entry from dictionary"""
        timestamp_str = "2025-01-01T12:00:00+00:00"
        data = {
            "id": "test_id",
            "timestamp": timestamp_str,
            "user_id": "test_user",
            "action": "DELETE",
            "entity_type": "deductions",
            "entity_id": "standard",
            "field_name": None,
            "old_value": "standard",
            "new_value": None,
            "session_id": "session_123",
            "ip_address": None,
            "user_agent": None,
            "metadata": {},
            "calculation_worksheet": None
        }

        entry = AuditEntry.from_dict(data)
        assert entry.id == "test_id"
        assert entry.action == "DELETE"
        assert isinstance(entry.timestamp, datetime)


class TestAuditTrailService:
    """Test AuditTrailService functionality"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        config = AppConfig()
        config.safe_dir = Path(tempfile.mkdtemp())
        return config

    @pytest.fixture
    def audit_service(self, config):
        """Create audit service instance"""
        with patch.object(AuditTrailService, '_load_audit_log'):
            service = AuditTrailService(config)
            yield service
            # Cleanup
            service.end_session()

    def test_initialization(self, config):
        """Test service initialization"""
        service = AuditTrailService(config)
        assert service.config == config
        assert service.current_session is None
        assert service.audit_log == []
        assert service.audit_dir.exists()

    def test_start_session(self, audit_service):
        """Test starting an audit session"""
        session_id = audit_service.start_session("test_user")

        assert audit_service.current_session is not None
        assert audit_service.current_session.session_id == session_id
        assert audit_service.current_session.user_id == "test_user"
        assert audit_service.current_session.actions_count == 1  # SESSION_START logged

    def test_end_session(self, audit_service):
        """Test ending an audit session"""
        audit_service.start_session("test_user")
        audit_service.end_session()

        assert audit_service.current_session is None

    def test_log_action(self, audit_service):
        """Test logging an action"""
        audit_service.start_session("test_user")

        audit_service.log_action(
            action="CREATE",
            entity_type="personal_info",
            entity_id="person_1",
            field_name="first_name",
            new_value="John"
        )

        assert len(audit_service.audit_log) == 2  # SESSION_START + CREATE
        entry = audit_service.audit_log[1]
        assert entry.action == "CREATE"
        assert entry.entity_type == "personal_info"
        assert entry.new_value == "John"

    def test_log_data_change(self, audit_service):
        """Test logging a data change"""
        audit_service.start_session("test_user")

        audit_service.log_data_change(
            entity_type="income",
            entity_id="w2_1",
            field_name="wages",
            old_value=50000,
            new_value=55000
        )

        assert len(audit_service.audit_log) == 2
        entry = audit_service.audit_log[1]
        assert entry.action == "UPDATE"
        assert entry.old_value == 50000
        assert entry.new_value == 55000

    def test_log_calculation(self, audit_service):
        """Test logging a calculation"""
        audit_service.start_session("test_user")

        inputs = {"income": 75000, "deductions": 14000}
        results = {"taxable_income": 61000, "tax": 7949}
        worksheet = {"steps": ["calculate_agi", "apply_deductions", "calculate_tax"]}

        audit_service.log_calculation(
            calculation_type="income_tax",
            inputs=inputs,
            results=results,
            worksheet=worksheet
        )

        assert len(audit_service.audit_log) == 2
        entry = audit_service.audit_log[1]
        assert entry.action == "CALCULATE"
        assert entry.entity_id == "income_tax"
        assert entry.metadata["inputs"] == inputs
        assert entry.metadata["results"] == results
        assert entry.calculation_worksheet == worksheet

    def test_get_audit_history(self, audit_service):
        """Test retrieving audit history"""
        audit_service.start_session("test_user")

        # Add some test entries
        audit_service.log_action("CREATE", "personal_info", "person_1", field_name="first_name", new_value="John")
        audit_service.log_action("UPDATE", "income", "w2_1", field_name="wages", old_value=50000, new_value=55000)
        audit_service.log_action("CALCULATE", "tax_calculation", "income_tax")

        # Get all history
        history = audit_service.get_audit_history()
        assert len(history) == 4  # SESSION_START + 3 actions

        # Filter by entity type
        income_history = audit_service.get_audit_history(entity_type="income")
        assert len(income_history) == 1
        assert income_history[0].entity_type == "income"

        # Filter by date range
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        recent_history = audit_service.get_audit_history(end_date=future_date)
        assert len(recent_history) == 4

    def test_get_calculation_history(self, audit_service):
        """Test retrieving calculation history"""
        audit_service.start_session("test_user")

        audit_service.log_calculation("income_tax", {}, {"tax": 1000})
        audit_service.log_calculation("self_employment_tax", {}, {"tax": 200})
        audit_service.log_action("CREATE", "personal_info", "person_1")  # Non-calculation

        calc_history = audit_service.get_calculation_history()
        assert len(calc_history) == 2
        assert all(entry.action == "CALCULATE" for entry in calc_history)

        # Filter by type
        income_calc_history = audit_service.get_calculation_history("income_tax")
        assert len(income_calc_history) == 1
        assert income_calc_history[0].entity_id == "income_tax"

    def test_export_audit_report(self, audit_service):
        """Test exporting audit report"""
        audit_service.start_session("test_user")

        # Test JSON export
        json_path = audit_service.export_audit_report(format="json")
        assert json_path.endswith(".json")

        with open(json_path, 'r') as f:
            data = json.load(f)
            assert "entries" in data
            assert len(data["entries"]) >= 1

        # Test CSV export
        csv_path = audit_service.export_audit_report(format="csv")
        assert csv_path.endswith(".csv")

        with open(csv_path, 'r') as f:
            content = f.read()
            assert "Timestamp" in content
            assert "SESSION_START" in content

    def test_cleanup_old_logs(self, audit_service, tmp_path):
        """Test cleaning up old audit log files"""
        # Create some test files
        old_file = audit_service.audit_dir / "old_audit.json"
        old_file.write_text("{}")

        # Mock the file as old
        import time
        old_time = time.time() - (100 * 24 * 60 * 60)  # 100 days ago
        os.utime(old_file, (old_time, old_time))

        # Create a recent file
        recent_file = audit_service.audit_dir / "recent_audit.json"
        recent_file.write_text("{}")

        deleted_count = audit_service.cleanup_old_logs(days_to_keep=90)
        assert deleted_count == 1
        assert not old_file.exists()
        assert recent_file.exists()

    @patch('services.audit_trail_service.EventBus')
    def test_event_bus_integration(self, mock_event_bus, config):
        """Test integration with event bus"""
        mock_bus = Mock()
        mock_event_bus.get_instance.return_value = mock_bus

        # Create new service to test event bus subscription
        service = AuditTrailService(config)

        # Verify event bus subscriptions
        mock_bus.subscribe.assert_any_call(EventType.TAX_DATA_CHANGED, service._on_data_changed)
        mock_bus.subscribe.assert_any_call(EventType.CALCULATION_COMPLETED, service._on_calculation_completed)

    def test_on_data_changed_event(self, audit_service):
        """Test handling data changed events"""
        audit_service.start_session("test_user")

        # Mock event
        event = Mock()
        event.type = EventType.TAX_DATA_CHANGED
        event.data = {
            "entity_type": "income",
            "entity_id": "w2_1",
            "field_name": "wages",
            "old_value": 50000,
            "new_value": 55000,
            "metadata": {"source": "ui"}
        }

        audit_service._on_data_changed(event)

        assert len(audit_service.audit_log) == 2  # SESSION_START + data change
        entry = audit_service.audit_log[1]
        assert entry.action == "UPDATE"
        assert entry.entity_type == "income"
        assert entry.new_value == 55000

    def test_on_calculation_completed_event(self, audit_service):
        """Test handling calculation completed events"""
        audit_service.start_session("test_user")

        # Mock event
        event = Mock()
        event.type = EventType.CALCULATION_COMPLETED
        event.data = {
            "calculation_type": "income_tax",
            "inputs": {"income": 75000},
            "results": {"tax": 7949},
            "worksheet": {"steps": ["calculate"]}
        }

        audit_service._on_calculation_completed(event)

        assert len(audit_service.audit_log) == 2  # SESSION_START + calculation
        entry = audit_service.audit_log[1]
        assert entry.action == "CALCULATE"
        assert entry.entity_id == "income_tax"
        assert entry.calculation_worksheet["steps"] == ["calculate"]


class TestAuditSession:
    """Test AuditSession dataclass"""

    def test_audit_session_creation(self):
        """Test creating an audit session"""
        start_time = datetime.now(timezone.utc)
        session = AuditSession(
            session_id="session_123",
            start_time=start_time,
            end_time=None,
            user_id="test_user",
            actions_count=5,
            entities_modified=["personal_info", "income"],
            calculations_performed=["income_tax"]
        )

        assert session.session_id == "session_123"
        assert session.user_id == "test_user"
        assert session.actions_count == 5
        assert "personal_info" in session.entities_modified

    def test_audit_session_to_dict(self):
        """Test converting session to dictionary"""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)

        session = AuditSession(
            session_id="session_123",
            start_time=start_time,
            end_time=end_time,
            user_id="test_user",
            actions_count=10,
            entities_modified=["personal_info"],
            calculations_performed=["income_tax"]
        )

        data = session.to_dict()
        assert data["session_id"] == "session_123"
        assert data["actions_count"] == 10
        assert "start_time" in data
        assert "end_time" in data