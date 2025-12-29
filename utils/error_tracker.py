"""
Error Tracking Service

This module provides centralized error tracking and aggregation
for monitoring application health and troubleshooting issues.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    timestamp: str
    severity: str
    error_type: str
    error_message: str
    context: Dict[str, Any]
    user_message: Optional[str] = None
    stack_trace: Optional[str] = None


class ErrorTracker:
    """
    Centralized error tracking and aggregation service.
    
    Tracks errors to a JSON Lines file for later analysis.
    Provides error summary and statistics.
    
    Example:
        tracker = ErrorTracker(Path("logs"))
        
        try:
            risky_operation()
        except Exception as e:
            tracker.track_error(
                error=e,
                context={"operation": "save_file", "filename": "tax_return.enc"},
                severity="ERROR",
                user_message="Could not save your tax return."
            )
            raise
    """
    
    def __init__(self, storage_dir: Path):
        """
        Initialize error tracker.
        
        Args:
            storage_dir: Directory to store error log files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.error_file = self.storage_dir / "errors.jsonl"
        self.logger = logging.getLogger(__name__)
    
    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR",
        user_message: Optional[str] = None,
        include_stack_trace: bool = True
    ) -> ErrorRecord:
        """
        Track an error with context.
        
        Args:
            error: Exception that occurred
            context: Additional context (user action, data state, etc.)
            severity: ERROR, WARNING, or CRITICAL
            user_message: User-friendly message (if different from technical)
            include_stack_trace: Whether to include full stack trace
            
        Returns:
            ErrorRecord that was created
        """
        import traceback
        
        # Create error record
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            severity=severity,
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {},
            user_message=user_message,
            stack_trace=traceback.format_exc() if include_stack_trace else None
        )
        
        # Append to error log file
        try:
            with open(self.error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(record)) + '\n')
        except Exception as log_error:
            self.logger.error(f"Failed to write error log: {log_error}")
        
        # Log to standard logger
        self.logger.error(
            f"{severity}: {record.error_type} - {record.error_message}",
            exc_info=include_stack_trace
        )
        
        return record
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for the last N hours.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with error statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        error_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        recent_errors: List[ErrorRecord] = []
        
        if not self.error_file.exists():
            return {
                'total_errors': 0,
                'by_type': {},
                'by_severity': {},
                'recent_errors': []
            }
        
        try:
            with open(self.error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record_dict = json.loads(line)
                        record_time = datetime.fromisoformat(record_dict['timestamp'])
                        
                        if record_time >= cutoff_time:
                            error_counts[record_dict['error_type']] += 1
                            severity_counts[record_dict['severity']] += 1
                            recent_errors.append(ErrorRecord(**record_dict))
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        self.logger.warning(f"Failed to parse error record: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Failed to read error log: {e}")
        
        return {
            'total_errors': sum(error_counts.values()),
            'by_type': dict(error_counts),
            'by_severity': dict(severity_counts),
            'recent_errors': recent_errors[-10:],  # Last 10 errors
            'hours_analyzed': hours
        }
    
    def get_error_trends(self, days: int = 7) -> Dict[str, List[int]]:
        """
        Get error trends over the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary mapping error types to daily counts
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        daily_errors = defaultdict(lambda: defaultdict(int))
        
        if not self.error_file.exists():
            return {}
        
        try:
            with open(self.error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record_dict = json.loads(line)
                        record_time = datetime.fromisoformat(record_dict['timestamp'])
                        
                        if record_time >= cutoff_time:
                            date_key = record_time.strftime('%Y-%m-%d')
                            error_type = record_dict['error_type']
                            daily_errors[error_type][date_key] += 1
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        
        except Exception as e:
            self.logger.error(f"Failed to read error log: {e}")
        
        return dict(daily_errors)
    
    def clear_old_errors(self, days: int = 30):
        """
        Remove error records older than N days.
        
        Args:
            days: Keep errors from last N days
        """
        if not self.error_file.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(days=days)
        temp_file = self.error_file.with_suffix('.tmp')
        kept_count = 0
        removed_count = 0
        
        try:
            with open(self.error_file, 'r', encoding='utf-8') as input_f:
                with open(temp_file, 'w', encoding='utf-8') as output_f:
                    for line in input_f:
                        try:
                            record_dict = json.loads(line)
                            record_time = datetime.fromisoformat(record_dict['timestamp'])
                            
                            if record_time >= cutoff_time:
                                output_f.write(line)
                                kept_count += 1
                            else:
                                removed_count += 1
                        except (json.JSONDecodeError, KeyError, ValueError):
                            # Keep malformed records to avoid data loss
                            output_f.write(line)
                            kept_count += 1
            
            # Replace original file with cleaned version
            temp_file.replace(self.error_file)
            self.logger.info(
                f"Cleaned error log: kept {kept_count}, removed {removed_count} old records"
            )
        
        except Exception as e:
            self.logger.error(f"Failed to clean error log: {e}")
            if temp_file.exists():
                temp_file.unlink()


# Global error tracker instance
_global_tracker: Optional[ErrorTracker] = None


def get_error_tracker(storage_dir: Optional[Path] = None) -> ErrorTracker:
    """
    Get global error tracker instance (singleton).
    
    Args:
        storage_dir: Directory for error logs (only used on first call)
        
    Returns:
        Global ErrorTracker instance
    """
    global _global_tracker
    
    if _global_tracker is None:
        if storage_dir is None:
            storage_dir = Path.home() / "Documents" / "TaxReturns" / "logs"
        _global_tracker = ErrorTracker(storage_dir)
    
    return _global_tracker
