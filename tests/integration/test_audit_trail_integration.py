"""
Integration tests for Audit Trail feature
"""

import pytest
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch
from services.audit_trail_service import AuditTrailService
from gui.audit_trail_window import AuditTrailWindow
from gui.main_window import MainWindow
from config.app_config import AppConfig
from utils.event_bus import EventType


class TestAuditTrailIntegration:
    """Integration tests for audit trail functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        return tempfile.mkdtemp()

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration"""
        config = AppConfig()
        config.safe_dir = Path(temp_dir)
        return config

    @pytest.fixture
    def audit_service(self, config):
        """Create audit service"""
        service = AuditTrailService(config)
        service.start_session("test_user")
        yield service
        service.end_session()

    def test_audit_service_persistence(self, audit_service):
        """Test that audit entries persist across service restarts"""
        # Log some actions
        audit_service.log_action("CREATE", "personal_info", "person_1", field_name="first_name", new_value="John")
        audit_service.log_action("UPDATE", "income", "w2_1", field_name="wages", old_value=50000, new_value=55000)

        initial_count = len(audit_service.audit_log)

        # Force save the audit log before creating new service
        audit_service._save_audit_log()

        # Simulate service restart by creating new instance
        new_service = AuditTrailService(audit_service.config)
        new_service.start_session("test_user")

        # Should load previous entries
        assert len(new_service.audit_log) >= initial_count

        new_service.end_session()

    def test_audit_data_export_import(self, audit_service, tmp_path):
        """Test exporting and importing audit data"""
        # Add some test data
        audit_service.log_calculation(
            "income_tax",
            {"income": 75000, "deductions": 14000},
            {"tax": 7949},
            {"steps": ["calculate_agi", "apply_deductions"]}
        )

        # Export to JSON
        export_path = audit_service.export_audit_report("json")
        assert export_path.endswith(".json")

        # Verify exported data
        with open(export_path, 'r') as f:
            exported_data = json.load(f)

        assert "entries" in exported_data
        assert len(exported_data["entries"]) >= 1

        # Find the calculation entry
        calc_entries = [e for e in exported_data["entries"] if e.get("action") == "CALCULATE"]
        assert len(calc_entries) == 1

        calc_entry = calc_entries[0]
        assert calc_entry["entity_id"] == "income_tax"
        assert calc_entry["metadata"]["results"]["tax"] == 7949

    def test_audit_session_tracking(self, audit_service):
        """Test session tracking across multiple operations"""
        session_id = audit_service.current_session.session_id

        # Perform various operations
        audit_service.log_action("CREATE", "personal_info", "person_1", new_value="John")
        audit_service.log_data_change("income", "w2_1", "wages", 0, 50000)
        audit_service.log_calculation("income_tax", {}, {"tax": 1000})

        # Check all entries have the same session ID
        for entry in audit_service.audit_log[1:]:  # Skip SESSION_START
            assert entry.session_id == session_id

        # End session
        audit_service.end_session()

        # Verify session end was logged
        last_entry = audit_service.audit_log[-1]
        assert last_entry.action == "SESSION_END"
        assert last_entry.session_id == session_id

    def test_audit_filtering_integration(self, audit_service):
        """Test filtering works across different data types"""
        # Add diverse test data
        audit_service.log_action("CREATE", "personal_info", "person_1", field_name="first_name", new_value="John")
        audit_service.log_action("CREATE", "personal_info", "person_1", field_name="last_name", new_value="Doe")
        audit_service.log_action("UPDATE", "income", "w2_1", field_name="wages", old_value=0, new_value=50000)
        audit_service.log_action("UPDATE", "income", "1099", field_name="income", old_value=0, new_value=25000)
        audit_service.log_calculation("income_tax", {}, {"tax": 7949})
        audit_service.log_calculation("self_employment_tax", {}, {"tax": 200})

        # Test filtering by entity type
        personal_history = audit_service.get_audit_history(entity_type="personal_info")
        assert len(personal_history) == 2
        assert all(entry.entity_type == "personal_info" for entry in personal_history)

        income_history = audit_service.get_audit_history(entity_type="income")
        assert len(income_history) == 2
        assert all(entry.entity_type == "income" for entry in income_history)

        # Test filtering by action
        create_history = audit_service.get_audit_history(action="CREATE")
        assert len(create_history) == 2
        assert all(entry.action == "CREATE" for entry in create_history)

        # Test calculation filtering
        calc_history = audit_service.get_calculation_history()
        assert len(calc_history) == 2
        assert all(entry.action == "CALCULATE" for entry in calc_history)

        income_tax_calcs = audit_service.get_calculation_history("income_tax")
        assert len(income_tax_calcs) == 1
        assert income_tax_calcs[0].entity_id == "income_tax"

    def test_audit_window_integration(self, audit_service):
        """Test audit window integrates with service"""
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()

        try:
            # Create audit window
            window = AuditTrailWindow(root, audit_service)

            # Verify window loads data
            items = window.audit_tree.get_children()
            assert len(items) >= 1  # At least SESSION_START

            # Test filtering integration
            window.action_var.set("SESSION_START")
            window._apply_filters()

            filtered_items = window.audit_tree.get_children()
            # Should have at least the session start entry
            assert len(filtered_items) >= 1

            window.destroy()

        finally:
            root.destroy()

    @patch('services.audit_trail_service.EventBus')
    def test_event_bus_integration(self, mock_event_bus, config):
        """Test event bus integration for automatic audit logging"""
        mock_bus = Mock()
        mock_event_bus.get_instance.return_value = mock_bus

        service = AuditTrailService(config)
        service.start_session("test_user")

        # Simulate data changed event
        data_event = Mock()
        data_event.type = EventType.TAX_DATA_CHANGED
        data_event.data = {
            "entity_type": "income",
            "entity_id": "w2_1",
            "field_name": "wages",
            "old_value": 50000,
            "new_value": 55000
        }

        service._on_data_changed(data_event)

        # Verify audit entry was created
        assert len(service.audit_log) == 2  # SESSION_START + data change
        entry = service.audit_log[1]
        assert entry.action == "UPDATE"
        assert entry.new_value == 55000

        # Simulate calculation completed event
        calc_event = Mock()
        calc_event.type = EventType.CALCULATION_COMPLETED
        calc_event.data = {
            "calculation_type": "income_tax",
            "inputs": {"income": 75000},
            "results": {"tax": 7949}
        }

        service._on_calculation_completed(calc_event)

        # Verify calculation audit entry
        assert len(service.audit_log) == 3
        calc_entry = service.audit_log[2]
        assert calc_entry.action == "CALCULATE"
        assert calc_entry.entity_id == "income_tax"

        service.end_session()

    def test_main_window_audit_integration(self, config):
        """Test main window integration with audit trail"""
        import tkinter as tk
        from services.authentication_service import AuthenticationService

        root = tk.Tk()
        root.withdraw()

        # Set up authentication service with a test password
        auth_service = AuthenticationService(config)
        test_password = "TestPassword123!"
        auth_service.create_master_password(test_password)

        # Mock the authentication dialogs to avoid GUI interaction
        with patch('gui.password_dialogs.AuthenticateDialog') as mock_auth_dialog:
            mock_auth_dialog.return_value.show.return_value = "test_session_token"
            
            # Create main window with audit service
            main_window = MainWindow(root, config)

            # Verify audit service is initialized
            assert hasattr(main_window, 'audit_service')
            assert main_window.audit_service is not None

            # Verify session started
            assert main_window.audit_service.current_session is not None

            # Verify the method exists
            assert hasattr(main_window, '_open_audit_trail')
            assert callable(getattr(main_window, '_open_audit_trail'))

            # Test opening audit trail window
            with patch('gui.main_window.AuditTrailWindow') as mock_window:
                main_window._open_audit_trail()
                mock_window.assert_called_once_with(root, main_window.audit_service)

            main_window.root.destroy()

    def test_audit_log_cleanup_integration(self, audit_service, tmp_path):
        """Test audit log cleanup integration"""
        import os
        import time

        # Create some old log files
        old_log = audit_service.audit_dir / "old_audit_20240101.json"
        old_log.write_text('{"entries": []}')

        # Make it appear old
        old_time = time.time() - (100 * 24 * 60 * 60)  # 100 days ago
        os.utime(old_log, (old_time, old_time))

        # Create recent log
        recent_log = audit_service.audit_dir / "recent_audit_20241201.json"
        recent_log.write_text('{"entries": []}')

        # Run cleanup
        deleted_count = audit_service.cleanup_old_logs(days_to_keep=90)

        # Verify old file deleted, recent file kept
        assert deleted_count == 1
        assert not old_log.exists()
        assert recent_log.exists()

    def test_audit_export_formats(self, audit_service):
        """Test different export formats"""
        # Add test data
        audit_service.log_action("CREATE", "personal_info", "person_1", new_value="John")
        audit_service.log_calculation("income_tax", {}, {"tax": 1000})

        # Test JSON export
        json_path = audit_service.export_audit_report("json")
        assert json_path.endswith(".json")

        with open(json_path, 'r') as f:
            json_data = json.load(f)
            assert "entries" in json_data
            assert len(json_data["entries"]) >= 2

        # Test CSV export
        csv_path = audit_service.export_audit_report("csv")
        assert csv_path.endswith(".csv")

        with open(csv_path, 'r') as f:
            csv_content = f.read()
            lines = csv_content.strip().split('\n')
            assert len(lines) >= 3  # Header + 2 data rows
            assert "Timestamp" in lines[0]
            assert "CREATE" in csv_content or "CALCULATE" in csv_content

    def test_audit_performance_large_dataset(self, audit_service):
        """Test audit performance with large dataset"""
        import time

        # Add many entries
        start_time = time.time()
        for i in range(1000):
            audit_service.log_action(
                "CREATE",
                "test_entity",
                f"entity_{i}",
                field_name="test_field",
                new_value=f"value_{i}"
            )

        # Verify all entries added
        assert len(audit_service.audit_log) == 1001  # 1000 + SESSION_START

        # Test filtering performance
        filter_start = time.time()
        filtered = audit_service.get_audit_history(action="CREATE", limit=10000)
        filter_time = time.time() - filter_start

        assert len(filtered) == 1000
        # Should filter quickly (less than 1 second for 1000 entries)
        assert filter_time < 1.0

    def test_audit_data_validation(self, audit_service):
        """Test audit data validation and integrity"""
        # Test with various data types
        test_cases = [
            {"action": "CREATE", "entity_type": "personal_info", "new_value": "John"},
            {"action": "UPDATE", "entity_type": "income", "old_value": 50000, "new_value": 55000},
            {"action": "DELETE", "entity_type": "deductions", "old_value": "standard"},
            {"action": "CALCULATE", "entity_type": "calculation", "metadata": {"complex": True}},
        ]

        for case in test_cases:
            audit_service.log_action(**case)

        # Verify all entries are valid
        for entry in audit_service.audit_log[1:]:  # Skip SESSION_START
            assert entry.id is not None
            assert entry.timestamp is not None
            assert entry.user_id == "test_user"
            assert entry.session_id == audit_service.current_session.session_id
            assert entry.action in ["CREATE", "UPDATE", "DELETE", "CALCULATE"]

        # Test export/import integrity
        export_path = audit_service.export_audit_report("json")

        with open(export_path, 'r') as f:
            imported_data = json.load(f)

        # Verify round-trip conversion
        for original, imported in zip(audit_service.audit_log, imported_data["entries"]):
            assert original.id == imported["id"]
            assert original.action == imported["action"]
            assert original.user_id == imported["user_id"]