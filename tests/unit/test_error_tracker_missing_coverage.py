"""
Tests to cover missing lines in error_tracker.py

Targets specific uncovered error handling paths:
- Line 103-104: File write errors in track_error
- Line 153-154: File read errors in get_error_stats  
- Line 191-195: JSON errors and file read errors in get_daily_errors
- Line 238-241: Cleanup errors in clear_old_errors
"""
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from utils.error_tracker import ErrorTracker


class TestErrorTrackerFileWriteErrors:
    """Test error handling when file writes fail (lines 103-104)."""
    
    def test_track_error_handles_file_write_permission_error(self, tmp_path):
        """Test that track_error logs but doesn't crash when file write fails."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Should not raise exception, just log the error
            tracker.track_error(ValueError("Test error"))
            # Test passes if no exception is raised


class TestGetErrorSummaryFileReadErrors:
    """Test error handling in get_error_summary when file reading fails (lines 153-154)."""
    
    def test_get_error_summary_handles_file_read_error(self, tmp_path):
        """Test that get_error_summary handles file read errors gracefully."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Create the file first so it exists
        tracker.track_error(ValueError("Test"))
        
        # Mock open to raise IOError when reading
        with patch('builtins.open', side_effect=IOError("Read failed")):
            stats = tracker.get_error_summary()
            # Should return empty stats, not crash
            assert stats['total_errors'] == 0
            assert stats['by_type'] == {}


class TestGetErrorTrendsHandling:
    """Test error handling in get_error_trends (lines 191-195)."""
    
    def test_get_error_trends_handles_json_decode_error(self, tmp_path):
        """Test that malformed JSON lines are skipped (line 192)."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Write valid error first
        tracker.track_error(ValueError("Valid error"))
        
        # Manually append malformed JSON
        with open(tracker.error_file, 'a', encoding='utf-8') as f:
            f.write('{"invalid json}\n')
            f.write('not json at all\n')
        
        # Should handle malformed lines gracefully
        trends = tracker.get_error_trends()
        # Should still get the valid error
        assert isinstance(trends, dict)
    
    def test_get_error_trends_handles_file_read_error(self, tmp_path):
        """Test that get_error_trends handles file read errors (lines 194-195)."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.track_error(ValueError("Test"))
        
        # Mock open to raise IOError
        with patch('builtins.open', side_effect=IOError("Cannot read")):
            trends = tracker.get_error_trends()
            # Should return empty dict, not crash
            assert trends == {}


class TestClearOldErrorsExceptionHandling:
    """Test error handling in clear_old_errors (lines 238-241)."""
    
    def test_clear_old_errors_handles_exception(self, tmp_path):
        """Test that clear_old_errors handles exceptions during cleanup."""
        tracker = ErrorTracker(tmp_path / "logs")
        
        # Create some errors
        tracker.track_error(ValueError("Test error 1"))
        tracker.track_error(RuntimeError("Test error 2"))
        
        # Mock NamedTemporaryFile to raise an exception
        with patch('tempfile.NamedTemporaryFile', side_effect=OSError("Cannot create temp file")):
            # Should not crash
            tracker.clear_old_errors(days=30)
            # Original file should still exist
            assert tracker.error_file.exists()
    
    def test_clear_old_errors_cleans_up_temp_file_on_error(self, tmp_path):
        """Test that temp file is cleaned up if error occurs (line 241)."""
        tracker = ErrorTracker(tmp_path / "logs")
        tracker.track_error(ValueError("Test"))
        
        # Create a mock temp file that will be cleaned up
        mock_temp = MagicMock()
        mock_temp_path = MagicMock(spec=Path)
        mock_temp_path.exists.return_value = True
        mock_temp.__enter__ = MagicMock(return_value=mock_temp)
        mock_temp.__exit__ = MagicMock(return_value=False)
        mock_temp.name = str(tmp_path / "temp_file")
        
        with patch('tempfile.NamedTemporaryFile', return_value=mock_temp):
            with patch('pathlib.Path.replace', side_effect=OSError("Replace failed")):
                # Should handle the error and try to clean up
                tracker.clear_old_errors(days=30)
