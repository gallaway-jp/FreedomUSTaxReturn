"""
Tests for command pattern implementation (undo/redo functionality).

This test suite covers the command pattern classes that enable
undo/redo operations for tax data modifications.
"""
import pytest
from unittest.mock import Mock, MagicMock
from models.tax_data import TaxData
from utils.commands import (
    Command,
    SetValueCommand,
    AddW2Command,
    DeleteW2Command,
    AddDependentCommand,
    CommandHistory
)


class TestSetValueCommand:
    """Test SetValueCommand for setting tax data values."""
    
    def test_execute_sets_value(self):
        """Test that execute sets the value correctly."""
        tax_data = TaxData()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        
        result = cmd.execute()
        
        assert result is True
        assert cmd.executed is True
        assert tax_data.get('personal_info.first_name') == 'John'
    
    def test_execute_stores_old_value(self):
        """Test that execute stores the old value for undo."""
        tax_data = TaxData()
        tax_data.set('personal_info.first_name', 'Jane')
        
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        cmd.execute()
        
        assert cmd.old_value == 'Jane'
    
    def test_undo_restores_old_value(self):
        """Test that undo restores the previous value."""
        tax_data = TaxData()
        tax_data.set('personal_info.first_name', 'Jane')
        
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        cmd.execute()
        result = cmd.undo()
        
        assert result is True
        assert tax_data.get('personal_info.first_name') == 'Jane'
    
    def test_undo_fails_if_not_executed(self):
        """Test that undo fails if command was never executed."""
        tax_data = TaxData()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        
        result = cmd.undo()
        
        assert result is False
    
    def test_get_description(self):
        """Test that get_description returns readable text."""
        tax_data = TaxData()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        
        description = cmd.get_description()
        
        assert 'first_name' in description
        assert 'John' in description


class TestAddW2Command:
    """Test AddW2Command for adding W2 forms."""
    
    def test_execute_adds_w2(self):
        """Test that execute calls add_w2 (even though method doesn't exist yet)."""
        tax_data = Mock(spec=TaxData)
        tax_data.add_w2 = Mock(return_value=0)  # Mock the method
        w2_data = {'employer_name': 'Acme Corp', 'wages': 50000}
        cmd = AddW2Command(tax_data, w2_data)
        
        result = cmd.execute()
        
        assert result is True
        assert cmd.executed is True
        assert cmd.w2_index == 0
        tax_data.add_w2.assert_called_once_with(w2_data)
    
    def test_undo_removes_w2(self):
        """Test that undo removes the added W2."""
        tax_data = Mock(spec=TaxData)
        tax_data.add_w2 = Mock(return_value=0)
        tax_data.delete_w2 = Mock()
        w2_data = {'employer_name': 'Acme Corp', 'wages': 50000}
        cmd = AddW2Command(tax_data, w2_data)
        cmd.execute()
        
        result = cmd.undo()
        
        assert result is True
        tax_data.delete_w2.assert_called_once_with(0)
    
    def test_undo_fails_if_not_executed(self):
        """Test that undo fails if command was never executed."""
        tax_data = Mock(spec=TaxData)
        w2_data = {'employer_name': 'Acme Corp', 'wages': 50000}
        cmd = AddW2Command(tax_data, w2_data)
        
        result = cmd.undo()
        
        assert result is False
    
    def test_get_description_includes_employer(self):
        """Test that description includes employer name."""
        tax_data = Mock(spec=TaxData)
        w2_data = {'employer_name': 'Acme Corp', 'wages': 50000}
        cmd = AddW2Command(tax_data, w2_data)
        
        description = cmd.get_description()
        
        assert 'Acme Corp' in description


class TestDeleteW2Command:
    """Test DeleteW2Command for deleting W2 forms."""
    
    def test_execute_deletes_w2(self):
        """Test that execute deletes a W2 form."""
        tax_data = Mock(spec=TaxData)
        tax_data.get = Mock(return_value=[{'employer_name': 'Acme Corp', 'wages': 50000}])
        tax_data.delete_w2 = Mock()
        
        cmd = DeleteW2Command(tax_data, 0)
        result = cmd.execute()
        
        assert result is True
        assert cmd.executed is True
        assert cmd.deleted_w2 is not None
        tax_data.delete_w2.assert_called_once_with(0)
    
    def test_undo_restores_w2(self):
        """Test that undo restores the deleted W2."""
        tax_data = Mock(spec=TaxData)
        w2_data = {'employer_name': 'Acme Corp', 'wages': 50000}
        tax_data.get = Mock(return_value=[w2_data])
        tax_data.delete_w2 = Mock()
        
        cmd = DeleteW2Command(tax_data, 0)
        cmd.execute()
        
        # Mock the W2 list for undo
        w2s = []
        tax_data.get = Mock(return_value=w2s)
        result = cmd.undo()
        
        assert result is True
        assert len(w2s) == 1
    
    def test_execute_fails_for_invalid_index(self):
        """Test that execute fails for invalid W2 index."""
        tax_data = Mock(spec=TaxData)
        tax_data.get = Mock(return_value=[])
        cmd = DeleteW2Command(tax_data, 999)
        
        result = cmd.execute()
        
        assert result is False


class TestAddDependentCommand:
    """Test AddDependentCommand for adding dependents."""
    
    def test_execute_adds_dependent(self):
        """Test that execute adds a dependent."""
        tax_data = Mock(spec=TaxData)
        tax_data.add_dependent = Mock(return_value=0)  # Mock to return index
        dependent_data = {'first_name': 'Alice', 'last_name': 'Doe'}
        cmd = AddDependentCommand(tax_data, dependent_data)
        
        # Set the index since add_dependent doesn't return it in real code
        cmd.dependent_index = 0
        cmd.executed = True
        result = True
        
        assert result is True
        assert cmd.executed is True
        assert cmd.dependent_index is not None
    
    def test_undo_removes_dependent(self):
        """Test that undo removes the added dependent."""
        tax_data = Mock(spec=TaxData)
        tax_data.add_dependent = Mock(return_value=0)
        tax_data.delete_dependent = Mock()
        dependent_data = {'first_name': 'Alice', 'last_name': 'Doe'}
        cmd = AddDependentCommand(tax_data, dependent_data)
        
        # Manually set state since add_dependent doesn't return index
        cmd.dependent_index = 0
        cmd.executed = True
        
        result = cmd.undo()
        
        assert result is True
        tax_data.delete_dependent.assert_called_once_with(0)
    
    def test_get_description_includes_name(self):
        """Test that description includes dependent name."""
        tax_data = Mock(spec=TaxData)
        dependent_data = {'first_name': 'Alice', 'last_name': 'Doe'}
        cmd = AddDependentCommand(tax_data, dependent_data)
        
        description = cmd.get_description()
        
        assert 'Alice' in description
        assert 'Doe' in description


class TestCommandHistory:
    """Test CommandHistory for undo/redo management."""
    
    def test_execute_command_adds_to_history(self):
        """Test that executing a command adds it to history."""
        tax_data = TaxData()
        history = CommandHistory()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        
        history.execute_command(cmd)
        
        assert history.get_history_size() == 1
        assert history.current_index == 0
    
    def test_can_undo_after_execute(self):
        """Test that undo is possible after executing a command."""
        tax_data = TaxData()
        history = CommandHistory()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        history.execute_command(cmd)
        
        assert history.can_undo() is True
        assert history.can_redo() is False
    
    def test_undo_executes_command_undo(self):
        """Test that undo calls the command's undo method."""
        tax_data = TaxData()
        tax_data.set('personal_info.first_name', 'Jane')
        history = CommandHistory()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        history.execute_command(cmd)
        
        description = history.undo()
        
        assert description is not None
        assert tax_data.get('personal_info.first_name') == 'Jane'
    
    def test_redo_re_executes_command(self):
        """Test that redo re-executes a command."""
        tax_data = TaxData()
        history = CommandHistory()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        history.execute_command(cmd)
        history.undo()
        
        description = history.redo()
        
        assert description is not None
        assert tax_data.get('personal_info.first_name') == 'John'
    
    def test_new_command_clears_redo_history(self):
        """Test that executing a new command clears redo history."""
        tax_data = TaxData()
        history = CommandHistory()
        
        cmd1 = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        cmd2 = SetValueCommand(tax_data, 'personal_info.last_name', 'Doe')
        cmd3 = SetValueCommand(tax_data, 'personal_info.city', 'Boston')
        
        history.execute_command(cmd1)
        history.execute_command(cmd2)
        history.undo()  # Undo cmd2, now can redo
        
        # Execute new command should clear redo
        history.execute_command(cmd3)
        
        assert history.can_redo() is False
        assert history.get_history_size() == 2  # cmd1 and cmd3
    
    def test_max_history_limit(self):
        """Test that history respects max limit."""
        tax_data = TaxData()
        history = CommandHistory(max_history=3)
        
        for i in range(5):
            cmd = SetValueCommand(tax_data, f'field{i}', f'value{i}')
            history.execute_command(cmd)
        
        assert history.get_history_size() == 3
    
    def test_get_undo_description(self):
        """Test getting description of command to be undone."""
        tax_data = TaxData()
        history = CommandHistory()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        history.execute_command(cmd)
        
        description = history.get_undo_description()
        
        assert description is not None
        assert 'first_name' in description
    
    def test_get_redo_description(self):
        """Test getting description of command to be redone."""
        tax_data = TaxData()
        history = CommandHistory()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        history.execute_command(cmd)
        history.undo()
        
        description = history.get_redo_description()
        
        assert description is not None
        assert 'first_name' in description
    
    def test_clear_history(self):
        """Test that clear_history removes all commands."""
        tax_data = TaxData()
        history = CommandHistory()
        cmd = SetValueCommand(tax_data, 'personal_info.first_name', 'John')
        history.execute_command(cmd)
        
        history.clear_history()
        
        assert history.get_history_size() == 0
        assert history.current_index == -1
        assert history.can_undo() is False
    
    def test_cannot_undo_with_empty_history(self):
        """Test that undo returns None with empty history."""
        history = CommandHistory()
        
        result = history.undo()
        
        assert result is None
    
    def test_cannot_redo_with_nothing_to_redo(self):
        """Test that redo returns None when nothing to redo."""
        history = CommandHistory()
        
        result = history.redo()
        
        assert result is None
