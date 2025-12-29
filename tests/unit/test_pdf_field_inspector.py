"""
Tests for utils/pdf_field_inspector.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from utils.pdf_field_inspector import inspect_pdf_fields


class TestPDFFieldInspector:
    """Test PDF field inspection utilities."""
    
    @patch('utils.pdf_field_inspector.PdfReader')
    def test_inspect_pdf_fields_success(self, mock_reader):
        """Test inspecting PDF fields successfully."""
        # Setup mock
        mock_reader_instance = MagicMock()
        mock_reader.return_value = mock_reader_instance
        mock_reader_instance.pages = [Mock(), Mock()]  # 2 pages
        mock_reader_instance.get_fields.return_value = {
            'field1': {'/FT': '/Tx', '/T': 'field1'},
            'field2': {'/FT': '/Tx', '/T': 'field2'}
        }
        
        # Should not raise
        inspect_pdf_fields('fake.pdf')
    
    @patch('utils.pdf_field_inspector.PdfReader')
    def test_inspect_pdf_fields_no_fields(self, mock_reader):
        """Test inspecting PDF with no fillable fields."""
        # Setup mock
        mock_reader_instance = MagicMock()
        mock_reader.return_value = mock_reader_instance
        mock_reader_instance.pages = [Mock()]
        mock_reader_instance.get_fields.return_value = None
        
        # Should handle gracefully
        inspect_pdf_fields('fake.pdf')
    
    @patch('utils.pdf_field_inspector.PdfReader')
    def test_inspect_pdf_fields_verbose(self, mock_reader):
        """Test inspecting PDF with verbose output."""
        # Setup mock
        mock_reader_instance = MagicMock()
        mock_reader.return_value = mock_reader_instance
        mock_reader_instance.pages = [Mock()]
        mock_reader_instance.get_fields.return_value = {
            'field1': {'/FT': '/Tx', '/T': 'field1', '/V': 'value1'}
        }
        
        # Should not raise with verbose=True
        inspect_pdf_fields('fake.pdf', verbose=True)
    
    @patch('utils.pdf_field_inspector.PdfReader')
    def test_inspect_pdf_fields_error(self, mock_reader, capsys):
        mock_reader.side_effect = FileNotFoundError()
        from utils import pdf_field_inspector
        pdf_field_inspector.inspect_pdf_fields('nonexistent.pdf')
        out = capsys.readouterr().out
        assert 'File not found' in out
    
    @patch('utils.pdf_field_inspector.PdfReader')
    def test_inspect_empty_fields(self, mock_reader):
        """Test inspecting PDF with empty field values."""
        # Setup mock
        mock_reader_instance = MagicMock()
        mock_reader.return_value = mock_reader_instance
        mock_reader_instance.pages = [Mock()]
        mock_reader_instance.get_fields.return_value = {
            'field1': {'/FT': '/Tx', '/V': ''},
            'field2': {'/FT': '/Tx'}  # No value
        }
        
        # Should handle empty values
        inspect_pdf_fields('fake.pdf', verbose=True)
    
    @patch('utils.pdf_field_inspector.PdfReader')
    def test_inspect_pdf_fields_prints_fields(self, mock_reader, capsys):
        mock_reader_instance = MagicMock()
        mock_reader.return_value = mock_reader_instance
        mock_reader_instance.pages = [Mock()]
        mock_reader_instance.get_fields.return_value = {
            'Field1': {'/FT': '/Tx', '/V': 'John', '/MaxLen': 20},
            'Field2': {'/FT': '/Btn', '/AS': 'Yes'},
            'Field3': {'/FT': '/Ch'},
        }
        from utils import pdf_field_inspector
        pdf_field_inspector.inspect_pdf_fields('dummy.pdf', verbose=True)
        out = capsys.readouterr().out
        assert 'Field1' in out and 'TEXT' in out
        assert 'Field2' in out and 'CHECKBOX/BUTTON' in out
        assert 'Field3' in out and 'CHOICE' in out
        assert 'Default Value: John' in out
        assert 'Max Length: 20' in out
        assert 'On Value: Yes' in out

    @patch('utils.pdf_field_inspector.PdfReader')
    def test_inspect_pdf_fields_other_exception(self, mock_reader, capsys):
        mock_reader.side_effect = Exception('Boom')
        from utils import pdf_field_inspector
        pdf_field_inspector.inspect_pdf_fields('bad.pdf')
        out = capsys.readouterr().out
        assert 'Error inspecting PDF: Boom' in out

    def test_inspect_common_forms_handles_missing(self, monkeypatch, capsys):
        from utils import pdf_field_inspector
        monkeypatch.setattr('pathlib.Path.exists', lambda self: False)
        pdf_field_inspector.inspect_common_forms()
        out = capsys.readouterr().out
        assert '[WARNING]' in out

    def test_main_inspect_specific(self, monkeypatch):
        from utils import pdf_field_inspector
        monkeypatch.setattr('sys.argv', ['script', 'dummy.pdf'])
        called = {}
        def fake_inspect(pdf_path, verbose):
            called['called'] = (pdf_path, verbose)
        monkeypatch.setattr(pdf_field_inspector, 'inspect_pdf_fields', fake_inspect)
        pdf_field_inspector.main()
        assert called['called'][0] == 'dummy.pdf'
        assert called['called'][1] is False

    def test_main_inspect_common(self, monkeypatch):
        from utils import pdf_field_inspector
        monkeypatch.setattr('sys.argv', ['script'])
        called = {'count': 0}
        def fake_inspect_common():
            called['count'] += 1
        monkeypatch.setattr(pdf_field_inspector, 'inspect_common_forms', fake_inspect_common)
        pdf_field_inspector.main()
        assert called['count'] == 1
