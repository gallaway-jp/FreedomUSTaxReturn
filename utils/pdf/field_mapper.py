"""
Field Mapper Utilities

Provides helper classes for accessing nested data structures
used in tax data and PDF field mapping.
"""

from typing import Dict, Any


class DotDict:
    """
    Wrapper that allows dot-notation access to nested dictionaries.
    
    This helper class simplifies accessing deeply nested data structures
    commonly found in tax data (e.g., 'personal_info.first_name').
    
    Example:
        >>> data = {'personal_info': {'first_name': 'John'}}
        >>> dd = DotDict(data)
        >>> dd.get('personal_info.first_name')
        'John'
    """
    
    def __init__(self, data: Dict):
        """
        Initialize DotDict wrapper.
        
        Args:
            data: Dictionary to wrap
        """
        self.data = data
    
    def get(self, path: str, default=None) -> Any:
        """
        Get value using dot notation (e.g., 'personal_info.first_name').
        
        Args:
            path: Dot-separated path to the value
            default: Default value if path not found
            
        Returns:
            Value at the path, or default if not found
        """
        # If it's already in the dict as a dotted key, return it
        if path in self.data:
            return self.data[path]
        
        # Otherwise, traverse the path
        keys = path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
