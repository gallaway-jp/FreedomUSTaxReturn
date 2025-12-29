"""
Tests for event bus (publish-subscribe pattern).

Tests cover:
- Event creation and serialization
- Subscribe/unsubscribe functionality
- Event publishing and handling
- Event history tracking
- Singleton pattern
"""
import pytest
from datetime import datetime
from utils.event_bus import Event, EventType, EventBus, get_event_bus


class TestEventCreation:
    """Test Event dataclass creation and methods."""
    
    def test_create_event_minimal(self):
        """Test creating event with required fields."""
        event = Event(
            type=EventType.TAX_DATA_CHANGED,
            source="TestComponent"
        )
        assert event.type == EventType.TAX_DATA_CHANGED
        assert event.source == "TestComponent"
        assert event.data is None
        assert isinstance(event.timestamp, datetime)
    
    def test_create_event_with_data(self):
        """Test creating event with data payload."""
        data = {'field': 'ssn', 'value': '123-45-6789'}
        event = Event(
            type=EventType.TAX_DATA_CHANGED,
            source="TaxDataModel",
            data=data
        )
        assert event.data == data
    
    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        data = {'status': 'completed'}
        event = Event(
            type=EventType.CALCULATION_COMPLETED,
            source="Calculator",
            data=data
        )
        
        event_dict = event.to_dict()
        assert event_dict['type'] == 'calculation_completed'
        assert event_dict['source'] == 'Calculator'
        assert event_dict['data'] == data
        assert 'timestamp' in event_dict


class TestEventBusInitialization:
    """Test EventBus initialization and singleton pattern."""
    
    def test_get_instance_creates_singleton(self):
        """Test get_instance returns singleton."""
        EventBus.reset_instance()
        bus1 = EventBus.get_instance()
        bus2 = EventBus.get_instance()
        assert bus1 is bus2
    
    def test_reset_instance(self):
        """Test reset_instance clears singleton."""
        EventBus.reset_instance()
        bus1 = EventBus.get_instance()
        EventBus.reset_instance()
        bus2 = EventBus.get_instance()
        assert bus1 is not bus2
    
    def test_get_event_bus_function(self):
        """Test convenience function returns event bus."""
        EventBus.reset_instance()
        bus = get_event_bus()
        assert isinstance(bus, EventBus)


class TestEventBusSubscription:
    """Test subscribe/unsubscribe functionality."""
    
    def setup_method(self):
        """Reset event bus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus.get_instance()
    
    def test_subscribe_adds_handler(self):
        """Test subscribing adds handler to list."""
        def handler(event):
            pass
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler)
        count = self.bus.get_subscribers_count(EventType.TAX_DATA_CHANGED)
        assert count == 1
    
    def test_subscribe_multiple_handlers(self):
        """Test subscribing multiple handlers."""
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler1)
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler2)
        count = self.bus.get_subscribers_count(EventType.TAX_DATA_CHANGED)
        assert count == 2
    
    def test_subscribe_same_handler_twice(self):
        """Test subscribing same handler twice only adds once."""
        def handler(event):
            pass
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler)
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler)
        count = self.bus.get_subscribers_count(EventType.TAX_DATA_CHANGED)
        assert count == 1
    
    def test_unsubscribe_removes_handler(self):
        """Test unsubscribing removes handler."""
        def handler(event):
            pass
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler)
        self.bus.unsubscribe(EventType.TAX_DATA_CHANGED, handler)
        count = self.bus.get_subscribers_count(EventType.TAX_DATA_CHANGED)
        assert count == 0
    
    def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing handler that wasn't subscribed."""
        def handler(event):
            pass
        
        # Should not raise exception
        self.bus.unsubscribe(EventType.TAX_DATA_CHANGED, handler)


class TestEventBusPublishing:
    """Test event publishing and handler invocation."""
    
    def setup_method(self):
        """Reset event bus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus.get_instance()
    
    def test_publish_calls_handler(self):
        """Test publishing event calls subscribed handler."""
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler)
        event = Event(EventType.TAX_DATA_CHANGED, "Test")
        self.bus.publish(event)
        
        assert len(received_events) == 1
        assert received_events[0] is event
    
    def test_publish_calls_multiple_handlers(self):
        """Test publishing calls all subscribed handlers."""
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event):
            handler1_calls.append(event)
        
        def handler2(event):
            handler2_calls.append(event)
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler1)
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler2)
        
        event = Event(EventType.TAX_DATA_CHANGED, "Test")
        self.bus.publish(event)
        
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
    
    def test_publish_only_calls_matching_type(self):
        """Test publishing only calls handlers for matching event type."""
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event):
            handler1_calls.append(event)
        
        def handler2(event):
            handler2_calls.append(event)
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler1)
        self.bus.subscribe(EventType.CALCULATION_COMPLETED, handler2)
        
        event = Event(EventType.TAX_DATA_CHANGED, "Test")
        self.bus.publish(event)
        
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 0
    
    def test_publish_with_no_subscribers(self):
        """Test publishing event with no subscribers doesn't crash."""
        event = Event(EventType.TAX_DATA_CHANGED, "Test")
        self.bus.publish(event)  # Should not raise
    
    def test_publish_handles_handler_exception(self):
        """Test publishing continues if handler raises exception."""
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event):
            raise ValueError("Handler error")
        
        def handler2(event):
            handler2_calls.append(event)
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler1)
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler2)
        
        event = Event(EventType.TAX_DATA_CHANGED, "Test")
        self.bus.publish(event)
        
        # Handler2 should still be called despite handler1 error
        assert len(handler2_calls) == 1


class TestEventHistory:
    """Test event history tracking."""
    
    def setup_method(self):
        """Reset event bus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus.get_instance()
    
    def test_publish_adds_to_history(self):
        """Test publishing adds event to history."""
        event = Event(EventType.TAX_DATA_CHANGED, "Test")
        self.bus.publish(event)
        
        history = self.bus.get_event_history()
        assert len(history) == 1
        assert history[0] is event
    
    def test_get_event_history_limit(self):
        """Test event history respects limit."""
        for i in range(20):
            event = Event(EventType.TAX_DATA_CHANGED, f"Test{i}")
            self.bus.publish(event)
        
        history = self.bus.get_event_history(limit=5)
        assert len(history) == 5
    
    def test_get_event_history_filter_by_type(self):
        """Test filtering event history by type."""
        self.bus.publish(Event(EventType.TAX_DATA_CHANGED, "Test1"))
        self.bus.publish(Event(EventType.CALCULATION_COMPLETED, "Test2"))
        self.bus.publish(Event(EventType.TAX_DATA_CHANGED, "Test3"))
        
        history = self.bus.get_event_history(event_type=EventType.TAX_DATA_CHANGED)
        assert len(history) == 2
        assert all(e.type == EventType.TAX_DATA_CHANGED for e in history)
    
    def test_clear_history(self):
        """Test clearing event history."""
        for i in range(5):
            self.bus.publish(Event(EventType.TAX_DATA_CHANGED, f"Test{i}"))
        
        self.bus.clear_history()
        history = self.bus.get_event_history()
        assert len(history) == 0
    
    def test_history_max_size(self):
        """Test event history doesn't grow beyond max size."""
        # Publish more than max_history (100) events
        for i in range(150):
            self.bus.publish(Event(EventType.TAX_DATA_CHANGED, f"Test{i}"))
        
        # Should only keep last 100
        history = self.bus.get_event_history(limit=200)
        assert len(history) <= 100


class TestGetSubscribersCount:
    """Test getting subscriber counts."""
    
    def setup_method(self):
        """Reset event bus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus.get_instance()
    
    def test_subscribers_count_empty(self):
        """Test count is 0 for event type with no subscribers."""
        count = self.bus.get_subscribers_count(EventType.TAX_DATA_CHANGED)
        assert count == 0
    
    def test_subscribers_count_after_subscribe(self):
        """Test count increases after subscribing."""
        def handler(event):
            pass
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler)
        count = self.bus.get_subscribers_count(EventType.TAX_DATA_CHANGED)
        assert count == 1
    
    def test_subscribers_count_after_unsubscribe(self):
        """Test count decreases after unsubscribing."""
        def handler(event):
            pass
        
        self.bus.subscribe(EventType.TAX_DATA_CHANGED, handler)
        self.bus.unsubscribe(EventType.TAX_DATA_CHANGED, handler)
        count = self.bus.get_subscribers_count(EventType.TAX_DATA_CHANGED)
        assert count == 0
