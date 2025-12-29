"""
Plugin System for Tax Schedules

This module provides a plugin architecture for extensible tax schedule support.
New schedules can be added as plugins without modifying core code.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
import logging
import importlib
import inspect
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a schedule plugin"""
    name: str
    version: str
    description: str
    schedule_name: str  # e.g., "Schedule C", "Schedule A"
    irs_form: str  # e.g., "f1040sc.pdf"
    author: str = "Unknown"
    requires: List[str] = None  # Required dependencies
    
    def __post_init__(self):
        if self.requires is None:
            self.requires = []


class ISchedulePlugin(ABC):
    """Interface that all schedule plugins must implement"""
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    def validate_data(self, tax_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that the tax data contains required fields for this schedule
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def calculate(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform schedule-specific calculations
        
        Returns:
            Dictionary with calculated values
        """
        pass
    
    @abstractmethod
    def map_to_pdf_fields(self, tax_data: Dict[str, Any], calculated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map tax data and calculated results to PDF form fields
        
        Returns:
            Dictionary mapping PDF field names to values
        """
        pass
    
    def is_applicable(self, tax_data: Dict[str, Any]) -> bool:
        """
        Determine if this schedule applies to the given tax return
        
        Default implementation checks if validation passes
        """
        is_valid, _ = self.validate_data(tax_data)
        return is_valid


class PluginRegistry:
    """Registry for managing schedule plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, ISchedulePlugin] = {}
        self._plugin_classes: Dict[str, Type[ISchedulePlugin]] = {}
    
    def register(self, plugin: ISchedulePlugin):
        """Register a plugin instance"""
        metadata = plugin.get_metadata()
        schedule_name = metadata.schedule_name
        
        if schedule_name in self._plugins:
            logger.warning(f"Plugin for {schedule_name} already registered. Replacing.")
        
        self._plugins[schedule_name] = plugin
        logger.info(f"Registered plugin: {metadata.name} v{metadata.version} ({schedule_name})")
    
    def register_class(self, plugin_class: Type[ISchedulePlugin]):
        """Register a plugin class (will be instantiated on demand)"""
        # Instantiate to get metadata
        temp_instance = plugin_class()
        metadata = temp_instance.get_metadata()
        schedule_name = metadata.schedule_name
        
        self._plugin_classes[schedule_name] = plugin_class
        logger.info(f"Registered plugin class: {metadata.name} ({schedule_name})")
    
    def get_plugin(self, schedule_name: str) -> Optional[ISchedulePlugin]:
        """Get a plugin by schedule name"""
        # Check instances first
        if schedule_name in self._plugins:
            return self._plugins[schedule_name]
        
        # Instantiate from class if available
        if schedule_name in self._plugin_classes:
            plugin = self._plugin_classes[schedule_name]()
            self._plugins[schedule_name] = plugin
            return plugin
        
        logger.warning(f"No plugin found for {schedule_name}")
        return None
    
    def get_all_plugins(self) -> List[ISchedulePlugin]:
        """Get all registered plugins"""
        # Instantiate any class-based plugins that haven't been instantiated yet
        for schedule_name, plugin_class in self._plugin_classes.items():
            if schedule_name not in self._plugins:
                self._plugins[schedule_name] = plugin_class()
        
        return list(self._plugins.values())
    
    def get_applicable_plugins(self, tax_data: Dict[str, Any]) -> List[ISchedulePlugin]:
        """Get all plugins that apply to the given tax data"""
        applicable = []
        for plugin in self.get_all_plugins():
            if plugin.is_applicable(tax_data):
                applicable.append(plugin)
        return applicable
    
    def unregister(self, schedule_name: str):
        """Unregister a plugin"""
        if schedule_name in self._plugins:
            del self._plugins[schedule_name]
            logger.info(f"Unregistered plugin: {schedule_name}")
        if schedule_name in self._plugin_classes:
            del self._plugin_classes[schedule_name]
    
    def clear(self):
        """Clear all registered plugins"""
        self._plugins.clear()
        self._plugin_classes.clear()
        logger.info("Cleared all plugins")


class PluginLoader:
    """Loads plugins from files or directories"""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
    
    def load_from_directory(self, directory: Path):
        """
        Load all plugins from a directory
        
        Searches for Python files containing ISchedulePlugin implementations
        """
        if not directory.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return
        
        plugin_files = list(directory.glob("*.py"))
        logger.info(f"Scanning {len(plugin_files)} files in {directory}")
        
        for file_path in plugin_files:
            if file_path.name.startswith("_"):
                continue  # Skip __init__.py and private modules
            
            try:
                self.load_from_file(file_path)
            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")
    
    def load_from_file(self, file_path: Path):
        """Load plugins from a single Python file"""
        module_name = file_path.stem
        
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load module spec from {file_path}")
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all ISchedulePlugin implementations
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, ISchedulePlugin) and 
                    obj is not ISchedulePlugin):
                    
                    # Register the plugin class
                    self.registry.register_class(obj)
                    logger.info(f"Loaded plugin class {name} from {file_path}")
        
        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {e}")
            raise


# Global plugin registry
_global_registry = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry (singleton)"""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry
