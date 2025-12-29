"""
Command Pattern Implementation for Undo/Redo Functionality

This module implements the command pattern to support undo and redo
operations for tax data modifications. Each command encapsulates an
operation and knows how to reverse it.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(ABC):
    """Base class for all commands"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.executed = False
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True if successful."""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get a human-readable description of the command"""
        pass


class SetValueCommand(Command):
    """Command to set a value in TaxData"""
    
    def __init__(self, tax_data, path: str, new_value: Any):
        super().__init__()
        self.tax_data = tax_data
        self.path = path
        self.new_value = new_value
        self.old_value = None
    
    def execute(self) -> bool:
        """Execute the set operation"""
        try:
            # Store old value before changing
            self.old_value = self.tax_data.get(self.path)
            self.tax_data.set(self.path, self.new_value)
            self.executed = True
            logger.info(f"Executed SetValueCommand: {self.path} = {self.new_value}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute SetValueCommand: {e}")
            return False
    
    def undo(self) -> bool:
        """Undo the set operation"""
        if not self.executed:
            logger.warning("Cannot undo command that was never executed")
            return False
        
        try:
            self.tax_data.set(self.path, self.old_value)
            logger.info(f"Undone SetValueCommand: {self.path} = {self.old_value}")
            return True
        except Exception as e:
            logger.error(f"Failed to undo SetValueCommand: {e}")
            return False
    
    def get_description(self) -> str:
        field_name = self.path.split('.')[-1]
        return f"Set {field_name} to {self.new_value}"


class AddW2Command(Command):
    """Command to add a W2 form"""
    
    def __init__(self, tax_data, w2_data: dict):
        super().__init__()
        self.tax_data = tax_data
        self.w2_data = w2_data
        self.w2_index = None
    
    def execute(self) -> bool:
        """Execute the add W2 operation"""
        try:
            self.w2_index = self.tax_data.add_w2(self.w2_data)
            self.executed = True
            logger.info(f"Executed AddW2Command: index {self.w2_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute AddW2Command: {e}")
            return False
    
    def undo(self) -> bool:
        """Undo the add W2 operation"""
        if not self.executed or self.w2_index is None:
            logger.warning("Cannot undo AddW2Command that was never executed")
            return False
        
        try:
            self.tax_data.delete_w2(self.w2_index)
            logger.info(f"Undone AddW2Command: deleted index {self.w2_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to undo AddW2Command: {e}")
            return False
    
    def get_description(self) -> str:
        employer = self.w2_data.get('employer_name', 'Unknown')
        return f"Add W2 from {employer}"


class DeleteW2Command(Command):
    """Command to delete a W2 form"""
    
    def __init__(self, tax_data, w2_index: int):
        super().__init__()
        self.tax_data = tax_data
        self.w2_index = w2_index
        self.deleted_w2 = None
    
    def execute(self) -> bool:
        """Execute the delete W2 operation"""
        try:
            # Store the W2 before deleting
            w2s = self.tax_data.get('income.w2_forms')
            if w2s and self.w2_index < len(w2s):
                self.deleted_w2 = w2s[self.w2_index].copy()
                self.tax_data.delete_w2(self.w2_index)
                self.executed = True
                logger.info(f"Executed DeleteW2Command: index {self.w2_index}")
                return True
            else:
                logger.error(f"W2 index {self.w2_index} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to execute DeleteW2Command: {e}")
            return False
    
    def undo(self) -> bool:
        """Undo the delete W2 operation"""
        if not self.executed or self.deleted_w2 is None:
            logger.warning("Cannot undo DeleteW2Command that was never executed")
            return False
        
        try:
            # Add the deleted W2 back at the same position
            w2s = self.tax_data.get('income.w2_forms')
            w2s.insert(self.w2_index, self.deleted_w2)
            logger.info(f"Undone DeleteW2Command: restored index {self.w2_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to undo DeleteW2Command: {e}")
            return False
    
    def get_description(self) -> str:
        if self.deleted_w2:
            employer = self.deleted_w2.get('employer_name', 'Unknown')
            return f"Delete W2 from {employer}"
        return f"Delete W2 at index {self.w2_index}"


class AddDependentCommand(Command):
    """Command to add a dependent"""
    
    def __init__(self, tax_data, dependent_data: dict):
        super().__init__()
        self.tax_data = tax_data
        self.dependent_data = dependent_data
        self.dependent_index = None
    
    def execute(self) -> bool:
        """Execute the add dependent operation"""
        try:
            self.dependent_index = self.tax_data.add_dependent(self.dependent_data)
            self.executed = True
            logger.info(f"Executed AddDependentCommand: index {self.dependent_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute AddDependentCommand: {e}")
            return False
    
    def undo(self) -> bool:
        """Undo the add dependent operation"""
        if not self.executed or self.dependent_index is None:
            logger.warning("Cannot undo AddDependentCommand that was never executed")
            return False
        
        try:
            self.tax_data.delete_dependent(self.dependent_index)
            logger.info(f"Undone AddDependentCommand: deleted index {self.dependent_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to undo AddDependentCommand: {e}")
            return False
    
    def get_description(self) -> str:
        name = f"{self.dependent_data.get('first_name', '')} {self.dependent_data.get('last_name', '')}".strip()
        return f"Add dependent {name}" if name else "Add dependent"


class CommandHistory:
    """Manages command history for undo/redo operations"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[Command] = []
        self.current_index = -1
    
    def execute_command(self, command: Command) -> bool:
        """Execute a command and add it to history"""
        if command.execute():
            # Remove any commands after current index (redo history)
            self.history = self.history[:self.current_index + 1]
            
            # Add new command
            self.history.append(command)
            self.current_index += 1
            
            # Enforce max history limit
            if len(self.history) > self.max_history:
                self.history.pop(0)
                self.current_index -= 1
            
            logger.info(f"Command executed and added to history: {command.get_description()}")
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_index < len(self.history) - 1
    
    def undo(self) -> Optional[str]:
        """Undo the last command. Returns description of undone command or None"""
        if not self.can_undo():
            logger.warning("Cannot undo: no commands in history")
            return None
        
        command = self.history[self.current_index]
        if command.undo():
            self.current_index -= 1
            description = command.get_description()
            logger.info(f"Undo successful: {description}")
            return description
        else:
            logger.error("Undo failed")
            return None
    
    def redo(self) -> Optional[str]:
        """Redo the next command. Returns description of redone command or None"""
        if not self.can_redo():
            logger.warning("Cannot redo: no commands to redo")
            return None
        
        self.current_index += 1
        command = self.history[self.current_index]
        if command.execute():
            description = command.get_description()
            logger.info(f"Redo successful: {description}")
            return description
        else:
            logger.error("Redo failed")
            self.current_index -= 1
            return None
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of the command that would be undone"""
        if self.can_undo():
            return self.history[self.current_index].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of the command that would be redone"""
        if self.can_redo():
            return self.history[self.current_index + 1].get_description()
        return None
    
    def clear_history(self):
        """Clear all command history"""
        self.history.clear()
        self.current_index = -1
        logger.info("Command history cleared")
    
    def get_history_size(self) -> int:
        """Get the current size of the history"""
        return len(self.history)
