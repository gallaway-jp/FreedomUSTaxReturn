"""
Event Bus - Centralized event system for component communication

This module provides a publish-subscribe pattern for decoupled
communication between GUI components and business logic.
"""

import logging
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types for the application"""
    
    # Data events
    TAX_DATA_CHANGED = "tax_data_changed"
    TAX_DATA_LOADED = "tax_data_loaded"
    TAX_DATA_SAVED = "tax_data_saved"
    
    # Calculation events
    CALCULATION_STARTED = "calculation_started"
    CALCULATION_COMPLETED = "calculation_completed"
    CALCULATION_FAILED = "calculation_failed"
    
    # Validation events
    VALIDATION_STARTED = "validation_started"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    
    # PDF events
    PDF_EXPORT_STARTED = "pdf_export_started"
    PDF_EXPORT_COMPLETED = "pdf_export_completed"
    PDF_EXPORT_FAILED = "pdf_export_failed"
    
    # UI events
    PAGE_CHANGED = "page_changed"
    FORM_SUBMITTED = "form_submitted"
    
    # Error events
    ERROR_OCCURRED = "error_occurred"
    WARNING_OCCURRED = "warning_occurred"


@dataclass
class Event:
    """
    Event object containing event data.
    
    Attributes:
        type: Type of event (EventType enum)
        source: Source component that triggered the event
        data: Event-specific data payload
        timestamp: When the event occurred
    """
    type: EventType
    source: str
    data: Any = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'type': self.type.value,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }


class EventBus:
    """
    Centralized event bus for publish-subscribe pattern.
    
    Allows components to communicate without direct coupling.
    Subscribers register handlers for specific event types.
    Publishers emit events that are delivered to all subscribers.
    
    Example:
        >>> bus = EventBus.get_instance()
        >>> bus.subscribe(EventType.TAX_DATA_CHANGED, my_handler)
        >>> bus.publish(Event(EventType.TAX_DATA_CHANGED, 'TaxData', {'field': 'ssn'}))
    """
    
    _instance: 'EventBus' = None
    
    def __init__(self):
        """Initialize event bus with empty subscriber lists"""
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 100
        logger.info("EventBus initialized")
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        """
        Get singleton instance of the event bus.
        
        Returns:
            Singleton EventBus instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for testing)"""
        cls._instance = None
        logger.debug("EventBus instance reset")
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed {handler.__name__} from {event_type.value}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify subscribers
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)
        
        logger.debug(f"Published event: {event.type.value} from {event.source}")
    
    def get_subscribers_count(self, event_type: EventType) -> int:
        """
        Get number of subscribers for an event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))
    
    def get_event_history(self, event_type: EventType = None, limit: int = 10) -> List[Event]:
        """
        Get recent event history.
        
        Args:
            event_type: Filter by event type (None = all events)
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()
        logger.debug("Event history cleared")


# Convenience function
def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    return EventBus.get_instance()
