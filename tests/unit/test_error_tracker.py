"""
Comprehensive tests for error tracking functionality.

Tests cover:
- Error record creation
- Error tracking to JSONL files
- Error summary and aggregation
- Error trends over time
- Old error cleanup
- Global singleton pattern
"""
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from utils.error_tracker import ErrorTracker, ErrorRecord, get_error_tracker


class TestErrorRecordCreation:
    """Test ErrorRecord dataclass creation and attributes."""
    
    def test_create_error_record_minimal(self):
        """Test creating error record with required fields."""
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            severity='ERROR',
            error_type='ValidationError',
            error_message='Test error',
            context={}
        )
        assert record.severity == 'ERROR'
        assert record.error_type == 'ValidationError'
        assert record.error_message == 'Test error'
        assert record.context == {}
        assert record.stack_trace is None
    
    def test_create_error_record_with_context(self):
        """Test creating error record with context dict."""
        context = {'user_id': 'test123', 'action': 'submit'}
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            severity='WARNING',
            error_type='BusinessError',
            error_message='Invalid submission',
            context=context
        )
        assert record.context == context
    
    def test_create_error_record_with_stack_trace(self):
        """Test creating error record with stack trace."""
        stack = "Traceback (most recent call last):\n  File..."
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            severity='CRITICAL',
            error_type='SystemError',
            error_message='Fatal error',
            context={},
            stack_trace=stack
        )
        assert record.stack_trace == stack


class TestErrorTrackerInitialization:
    """Test ErrorTracker initialization and file management."""
    
    def test_init_creates_storage_directory(self, tmp_path):
        """Test that ErrorTracker creates storage directory."""
        storage_dir = tmp_path / "logs"
        tracker = ErrorTracker(storage_dir)
        assert storage_dir.exists()
        assert storage_dir.is_dir()
    
    def test_init_creates_error_file_path(self, tmp_path):
        """Test that error file path is set correctly."""
        storage_dir = tmp_path / "logs"
        tracker = ErrorTracker(storage_dir)
        assert tracker.error_file == storage_dir / "errors.jsonl"
    
    def test_init_with_existing_directory(self, tmp_path):
        """Test initialization with pre-existing directory."""
        storage_dir = tmp_path / "logs"
        storage_dir.mkdir()
        tracker = ErrorTracker(storage_dir)
        assert storage_dir.exists()


class TestErrorTracking:
    """Test error tracking to JSONL file."""
    
    def test_track_error_creates_file(self, tmp_path):
        """Test that tracking an error creates the file."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.track_error(ValueError('Test error'))
        assert tracker.error_file.exists()
    
    def test_track_error_writes_json_line(self, tmp_path):
        """Test that error is written as JSON line."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.track_error(ValueError('Test message'))
        
        with open(tracker.error_file, 'r', encoding='utf-8') as f:
            line = f.readline()
            data = json.loads(line)
            assert data['severity'] == 'ERROR'
            assert data['error_type'] == 'ValueError'
            assert data['error_message'] == 'Test message'
    
    def test_track_error_with_context(self, tmp_path):
        """Test tracking error with context dict."""
        tracker = ErrorTracker(tmp_path / "logs")
        context = {'file': 'test.py', 'line': 42}
        tracker.track_error(
            RuntimeError('Parse failed'),
            context=context,
            severity='WARNING'
        )
        
        with open(tracker.error_file, 'r', encoding='utf-8') as f:
            data = json.loads(f.readline())
            assert data['context'] == context
    
    def test_track_error_with_exception(self, tmp_path):
        """Test tracking error with exception object."""
        tracker = ErrorTracker(tmp_path / "logs")
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            tracker.track_error(e, severity='ERROR')
        
        with open(tracker.error_file, 'r', encoding='utf-8') as f:
            data = json.loads(f.readline())
            assert 'stack_trace' in data
            assert 'ValueError: Test exception' in data['stack_trace']
    
    def test_track_multiple_errors(self, tmp_path):
        """Test tracking multiple errors appends to file."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.track_error(ValueError('Message 1'), severity='ERROR')
        tracker.track_error(TypeError('Message 2'), severity='WARNING')
        tracker.track_error(RuntimeError('Message 3'), severity='INFO')
        
        with open(tracker.error_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 3
            data1 = json.loads(lines[0])
            data2 = json.loads(lines[1])
            data3 = json.loads(lines[2])
            assert data1['error_type'] == 'ValueError'
            assert data2['error_type'] == 'TypeError'
            assert data3['error_type'] == 'RuntimeError'


class TestErrorSummary:
    """Test error summary and aggregation."""
    
    def test_get_error_summary_empty_file(self, tmp_path):
        """Test summary with no errors tracked."""
        tracker = ErrorTracker(tmp_path / "logs")
        summary = tracker.get_error_summary(hours=24)
        assert summary['total_errors'] == 0
        assert summary['by_type'] == {}
        assert summary['by_severity'] == {}
        assert summary['recent_errors'] == []
    
    def test_get_error_summary_counts_by_type(self, tmp_path):
        """Test summary counts errors by type."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.track_error(TypeError('Type error 1'))
        tracker.track_error(TypeError('Type error 2'))
        tracker.track_error(ValueError('Value error'))
        
        summary = tracker.get_error_summary(hours=24)
        assert summary['total_errors'] == 3
        assert summary['by_type']['TypeError'] == 2
        assert summary['by_type']['ValueError'] == 1
    
    def test_get_error_summary_counts_by_severity(self, tmp_path):
        """Test summary counts errors by severity."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.track_error(ValueError('Error1'), severity='ERROR')
        tracker.track_error(TypeError('Error2'), severity='ERROR')
        tracker.track_error(RuntimeError('Error3'), severity='WARNING')
        tracker.track_error(KeyError('Error4'), severity='CRITICAL')
        
        summary = tracker.get_error_summary(hours=24)
        assert summary['by_severity']['ERROR'] == 2
        assert summary['by_severity']['WARNING'] == 1
        assert summary['by_severity']['CRITICAL'] == 1
    
    def test_get_error_summary_returns_recent_errors(self, tmp_path):
        """Test summary returns list of recent errors."""
        tracker = ErrorTracker(tmp_path / "logs")
        for i in range(15):
            tracker.track_error(ValueError(f'Message {i}'))
        
        summary = tracker.get_error_summary(hours=24)
        recent = summary['recent_errors']
        assert len(recent) == 10  # Last 10 errors
        # Recent errors are ErrorRecord objects
        assert recent[0].error_type == 'ValueError'
        assert recent[-1].error_message == 'Message 14'
    
    def test_get_error_summary_filters_by_time(self, tmp_path):
        """Test summary filters errors by time window."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Create old error by manually writing timestamp
        old_time = datetime.now() - timedelta(hours=25)
        old_record = {
            'timestamp': old_time.isoformat(),
            'severity': 'ERROR',
            'error_type': 'OldError',
            'error_message': 'Old message',
            'context': {},
            'user_message': None,
            'stack_trace': None
        }
        with open(tracker.error_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(old_record) + '\n')
        
        # Track new error
        tracker.track_error(ValueError('New message'))
        
        summary = tracker.get_error_summary(hours=24)
        assert summary['total_errors'] == 1  # Only new error counted
        assert 'ValueError' in summary['by_type']
        assert 'OldError' not in summary['by_type']


class TestErrorTrends:
    """Test error trends over time."""
    
    def test_get_error_trends_empty(self, tmp_path):
        """Test trends with no errors."""
        tracker = ErrorTracker(tmp_path / "logs")
        trends = tracker.get_error_trends(days=7)
        assert trends == {}
    
    def test_get_error_trends_groups_by_date(self, tmp_path):
        """Test trends groups errors by date."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Create errors for different days
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # Write errors with different dates
        errors = [
            {
                'timestamp': today.isoformat(),
                'severity': 'ERROR',
                'error_type': 'TypeError',
                'error_message': 'Today error',
                'context': {},
                'user_message': None,
                'stack_trace': None
            },
            {
                'timestamp': yesterday.isoformat(),
                'severity': 'ERROR',
                'error_type': 'TypeError',
                'error_message': 'Yesterday error',
                'context': {},
                'user_message': None,
                'stack_trace': None
            }
        ]
        
        with open(tracker.error_file, 'w', encoding='utf-8') as f:
            for error in errors:
                f.write(json.dumps(error) + '\n')
        
        trends = tracker.get_error_trends(days=7)
        assert 'TypeError' in trends
        assert len(trends['TypeError']) == 2  # Two different dates
    
    def test_get_error_trends_counts_per_day(self, tmp_path):
        """Test trends counts errors per day."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        today = datetime.now()
        today_key = today.strftime('%Y-%m-%d')
        
        # Create multiple errors for today
        for i in range(5):
            error = {
                'timestamp': today.isoformat(),
                'severity': 'ERROR',
                'error_type': 'ValidationError',
                'error_message': f'Error {i}',
                'context': {},
                'user_message': None,
                'stack_trace': None
            }
            with open(tracker.error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error) + '\n')
        
        trends = tracker.get_error_trends(days=7)
        assert trends['ValidationError'][today_key] == 5


class TestErrorCleanup:
    """Test cleaning old errors."""
    
    def test_clear_old_errors_no_file(self, tmp_path):
        """Test cleanup when no error file exists."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.clear_old_errors(days=30)  # Should not raise error
    
    def test_clear_old_errors_removes_old_records(self, tmp_path):
        """Test that old errors are removed."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Create old and new errors
        old_time = datetime.now() - timedelta(days=35)
        new_time = datetime.now() - timedelta(days=10)
        
        errors = [
            {
                'timestamp': old_time.isoformat(),
                'severity': 'ERROR',
                'error_type': 'OldError',
                'message': 'Old',
                'context': {},
                'stack_trace': None
            },
            {
                'timestamp': new_time.isoformat(),
                'severity': 'ERROR',
                'error_type': 'NewError',
                'message': 'New',
                'context': {},
                'stack_trace': None
            }
        ]
        
        with open(tracker.error_file, 'w', encoding='utf-8') as f:
            for error in errors:
                f.write(json.dumps(error) + '\n')
        
        tracker.clear_old_errors(days=30)
        
        # Read remaining errors
        with open(tracker.error_file, 'r', encoding='utf-8') as f:
            remaining = [json.loads(line) for line in f]
        
        assert len(remaining) == 1
        assert remaining[0]['error_type'] == 'NewError'
    
    def test_clear_old_errors_keeps_recent_records(self, tmp_path):
        """Test that recent errors are kept."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Create several recent errors
        for i in range(10):
            tracker.track_error('ERROR', f'Error{i}', f'Message {i}')
        
        tracker.clear_old_errors(days=30)
        
        # All errors should still be there
        with open(tracker.error_file, 'r', encoding='utf-8') as f:
            remaining = [json.loads(line) for line in f]
        
        assert len(remaining) == 10
    
    def test_clear_old_errors_handles_malformed_records(self, tmp_path):
        """Test cleanup keeps malformed records to avoid data loss."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Write malformed JSON
        with open(tracker.error_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid json\n')
            f.write(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'severity': 'ERROR',
                'error_type': 'ValidError',
                'message': 'Valid',
                'context': {},
                'stack_trace': None
            }) + '\n')
        
        tracker.clear_old_errors(days=30)
        
        # Both records should be kept
        with open(tracker.error_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 2


class TestGlobalSingleton:
    """Test global error tracker singleton."""
    
    def test_get_error_tracker_creates_instance(self, tmp_path):
        """Test get_error_tracker creates instance."""
        tracker = get_error_tracker(tmp_path / "logs")
        assert isinstance(tracker, ErrorTracker)
    
    def test_get_error_tracker_returns_same_instance(self, tmp_path):
        """Test get_error_tracker returns singleton."""
        # Reset global tracker
        import utils.error_tracker
        utils.error_tracker._global_tracker = None
        
        tracker1 = get_error_tracker(tmp_path / "logs")
        tracker2 = get_error_tracker()
        assert tracker1 is tracker2
    
    def test_get_error_tracker_default_directory(self):
        """Test get_error_tracker uses default directory."""
        import utils.error_tracker
        utils.error_tracker._global_tracker = None
        
        tracker = get_error_tracker()
        expected_dir = Path.home() / "Documents" / "TaxReturns" / "logs"
        assert tracker.storage_dir == expected_dir


class TestErrorHandling:
    """Test error handling edge cases."""
    
    def test_track_error_with_file_write_error(self, tmp_path, monkeypatch):
        """Test tracking error when file write fails."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Make directory read-only to cause write error
        tracker.error_file.parent.chmod(0o444)
        
        try:
            # Should not raise exception
            tracker.track_error(ValueError('Test error'))
        finally:
            # Restore permissions
            tracker.error_file.parent.chmod(0o755)
    
    def test_get_summary_handles_corrupted_file(self, tmp_path):
        """Test summary handles corrupted JSON file."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Write corrupted data
        with open(tracker.error_file, 'w', encoding='utf-8') as f:
            f.write('{"corrupted": json\n')
            f.write(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'severity': 'ERROR',
                'error_type': 'ValidError',
                'error_message': 'Valid',
                'context': {},
                'user_message': None,
                'stack_trace': None
            }) + '\n')
        
        summary = tracker.get_error_summary(hours=24)
        assert summary['total_errors'] == 1  # Only valid record counted
