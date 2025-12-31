"""
Unit tests for PTIN/ERO Integration Service

Tests PTIN (Practitioner PIN) and ERO (Electronic Return Originator) credential management
for professional tax preparers.
"""

import pytest
import json
from datetime import date, datetime
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from services.ptin_ero_service import (
    PTINEROService, PTINRecord, ERORecord
)
from config.app_config import AppConfig


class TestPTINRecord:
    """Test PTIN record data structure"""

    def test_ptin_record_creation(self):
        """Test creating a PTIN record"""
        record = PTINRecord(
            ptin="P12345678",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            validation_date=date.today()
        )

        assert record.ptin == "P12345678"
        assert record.first_name == "John"
        assert record.last_name == "Doe"
        assert record.email == "john.doe@example.com"
        assert record.status == "active"
        assert record.validation_date == date.today()
        assert isinstance(record.created_at, datetime)
        assert isinstance(record.updated_at, datetime)

    def test_ptin_record_to_dict(self):
        """Test converting PTIN record to dictionary"""
        record = PTINRecord(
            ptin="P12345678",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            validation_date=date(2024, 1, 1)
        )

        data = record.to_dict()
        assert data['ptin'] == "P12345678"
        assert data['first_name'] == "John"
        assert data['validation_date'] == "2024-01-01"
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_ptin_record_from_dict(self):
        """Test creating PTIN record from dictionary"""
        data = {
            'ptin': "P12345678",
            'first_name': "John",
            'last_name': "Doe",
            'email': "john.doe@example.com",
            'validation_date': "2024-01-01",
            'created_at': "2024-01-01T10:00:00",
            'updated_at': "2024-01-01T10:00:00"
        }

        record = PTINRecord.from_dict(data)
        assert record.ptin == "P12345678"
        assert record.first_name == "John"
        assert record.validation_date == date(2024, 1, 1)


class TestERORecord:
    """Test ERO record data structure"""

    def test_ero_record_creation(self):
        """Test creating an ERO record"""
        record = ERORecord(
            ero_number="12345",
            business_name="ABC Tax Services",
            ein="12-3456789",
            ptin="P12345678",
            contact_name="Jane Smith",
            email="jane@abc-tax.com"
        )

        assert record.ero_number == "12345"
        assert record.business_name == "ABC Tax Services"
        assert record.ein == "12-3456789"
        assert record.ptin == "P12345678"
        assert record.contact_name == "Jane Smith"
        assert record.status == "active"

    def test_ero_record_to_dict(self):
        """Test converting ERO record to dictionary"""
        record = ERORecord(
            ero_number="12345",
            business_name="ABC Tax Services",
            ein="12-3456789",
            ptin="P12345678",
            contact_name="Jane Smith",
            email="jane@abc-tax.com",
            validation_date=date(2024, 1, 1)
        )

        data = record.to_dict()
        assert data['ero_number'] == "12345"
        assert data['business_name'] == "ABC Tax Services"
        assert data['validation_date'] == "2024-01-01"

    def test_ero_record_from_dict(self):
        """Test creating ERO record from dictionary"""
        data = {
            'ero_number': "12345",
            'business_name': "ABC Tax Services",
            'ein': "12-3456789",
            'ptin': "P12345678",
            'contact_name': "Jane Smith",
            'email': "jane@abc-tax.com",
            'validation_date': "2024-01-01",
            'created_at': "2024-01-01T10:00:00",
            'updated_at': "2024-01-01T10:00:00"
        }

        record = ERORecord.from_dict(data)
        assert record.ero_number == "12345"
        assert record.business_name == "ABC Tax Services"
        assert record.validation_date == date(2024, 1, 1)


class TestPTINEROServiceValidation:
    """Test PTIN/ERO validation methods"""

    def test_validate_ptin_format_valid(self):
        """Test PTIN format validation with valid inputs"""
        assert PTINEROService.validate_ptin_format("P12345678") == True
        assert PTINEROService.validate_ptin_format("p12345678") == True  # case insensitive

    def test_validate_ptin_format_invalid(self):
        """Test PTIN format validation with invalid inputs"""
        assert PTINEROService.validate_ptin_format("") == False
        assert PTINEROService.validate_ptin_format("12345678") == False  # missing P
        assert PTINEROService.validate_ptin_format("P1234567") == False  # too short
        assert PTINEROService.validate_ptin_format("P123456789") == False  # too long
        assert PTINEROService.validate_ptin_format("Q12345678") == False  # wrong prefix
        assert PTINEROService.validate_ptin_format(None) == False

    def test_validate_ero_format_valid(self):
        """Test ERO format validation with valid inputs"""
        assert PTINEROService.validate_ero_format("12345") == True
        assert PTINEROService.validate_ero_format("12345678") == True

    def test_validate_ero_format_invalid(self):
        """Test ERO format validation with invalid inputs"""
        assert PTINEROService.validate_ero_format("") == False
        assert PTINEROService.validate_ero_format("123") == False  # too short
        assert PTINEROService.validate_ero_format("123456789") == False  # too long
        assert PTINEROService.validate_ero_format("abc123") == False  # non-numeric
        assert PTINEROService.validate_ero_format(None) == False

    def test_validate_ein_format_valid(self):
        """Test EIN format validation with valid inputs"""
        assert PTINEROService.validate_ein_format("12-3456789") == True
        assert PTINEROService.validate_ein_format("123456789") == False  # missing hyphen

    def test_validate_ein_format_invalid(self):
        """Test EIN format validation with invalid inputs"""
        assert PTINEROService.validate_ein_format("") == False
        assert PTINEROService.validate_ein_format("12-345678") == False  # too short
        assert PTINEROService.validate_ein_format("12-34567890") == False  # too long
        assert PTINEROService.validate_ein_format("AB-3456789") == False  # non-numeric
        assert PTINEROService.validate_ein_format("123456789") == False  # missing hyphen
        assert PTINEROService.validate_ein_format(None) == False


class TestPTINEROService:
    """Test PTIN/ERO service functionality"""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration"""
        config = AppConfig()
        config.data_dir = str(tmp_path / "data")
        config.safe_dir = tmp_path / "data" / "safe"
        config.key_file = tmp_path / "data" / "safe" / "key.bin"
        return config

    @pytest.fixture
    def encryption_service(self):
        """Create mock encryption service"""
        mock_encryption = MagicMock()
        mock_encryption.encrypt.return_value = b"encrypted_data"
        mock_encryption.decrypt.return_value = '{"test": "data"}'
        return mock_encryption

    @pytest.fixture
    def ptin_ero_service(self, config, encryption_service):
        """Create PTIN/ERO service instance"""
        return PTINEROService(config, encryption_service)

    def test_initialization(self, ptin_ero_service, config):
        """Test service initialization"""
        assert ptin_ero_service.config == config
        assert ptin_ero_service.data_dir == Path(config.safe_dir) / "ptin_ero"
        assert ptin_ero_service.ptin_file == ptin_ero_service.data_dir / "ptin_records.json"
        assert ptin_ero_service.ero_file == ptin_ero_service.data_dir / "ero_records.json"
        assert isinstance(ptin_ero_service._ptin_cache, dict)
        assert isinstance(ptin_ero_service._ero_cache, dict)

    @patch('pathlib.Path.mkdir')
    def test_register_ptin_success(self, mock_mkdir, ptin_ero_service, encryption_service):
        """Test successful PTIN registration"""
        mock_mkdir.return_value = None
        encryption_service.encrypt_string.return_value = "encrypted"

        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }

        record = ptin_ero_service.register_ptin(ptin_data)

        assert record.ptin == 'P12345678'
        assert record.first_name == 'John'
        assert record.last_name == 'Doe'
        assert record.email == 'john.doe@example.com'
        assert record.status == 'active'
        assert record in ptin_ero_service._ptin_cache.values()

    def test_register_ptin_invalid_format(self, ptin_ero_service):
        """Test PTIN registration with invalid format"""
        ptin_data = {
            'ptin': '12345678',  # Missing P prefix
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }

        with pytest.raises(ValueError, match="Invalid PTIN format"):
            ptin_ero_service.register_ptin(ptin_data)

    def test_register_ptin_duplicate(self, ptin_ero_service):
        """Test registering duplicate PTIN"""
        # First registration
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Duplicate registration
        with pytest.raises(ValueError, match="PTIN already registered"):
            ptin_ero_service.register_ptin(ptin_data)

    def test_register_ptin_missing_required_fields(self, ptin_ero_service):
        """Test PTIN registration with missing required fields"""
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            # Missing last_name
            'email': 'john.doe@example.com'
        }

        with pytest.raises(ValueError, match="First name, last name, and email are required"):
            ptin_ero_service.register_ptin(ptin_data)

    def test_get_ptin_record(self, ptin_ero_service):
        """Test retrieving PTIN record"""
        # Register a PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Retrieve it
        record = ptin_ero_service.get_ptin_record('P12345678')
        assert record is not None
        assert record.ptin == 'P12345678'

        # Try to get non-existent PTIN
        record = ptin_ero_service.get_ptin_record('P87654321')
        assert record is None

    def test_update_ptin_record(self, ptin_ero_service):
        """Test updating PTIN record"""
        # Register a PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Update it
        updates = {
            'first_name': 'Jane',
            'phone': '555-1234'
        }
        updated_record = ptin_ero_service.update_ptin_record('P12345678', updates)

        assert updated_record.first_name == 'Jane'
        assert updated_record.phone == '555-1234'
        assert updated_record.last_name == 'Doe'  # Unchanged

    def test_update_ptin_record_not_found(self, ptin_ero_service):
        """Test updating non-existent PTIN record"""
        updates = {'first_name': 'Jane'}

        with pytest.raises(ValueError, match="PTIN not found"):
            ptin_ero_service.update_ptin_record('P12345678', updates)

    def test_deactivate_ptin(self, ptin_ero_service):
        """Test deactivating PTIN"""
        # Register a PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Deactivate it
        ptin_ero_service.deactivate_ptin('P12345678')

        record = ptin_ero_service.get_ptin_record('P12345678')
        assert record.status == 'inactive'

    def test_deactivate_ptin_not_found(self, ptin_ero_service):
        """Test deactivating non-existent PTIN"""
        with pytest.raises(ValueError, match="PTIN not found"):
            ptin_ero_service.deactivate_ptin('P12345678')

    def test_get_all_ptins(self, ptin_ero_service):
        """Test getting all PTIN records"""
        # Register multiple PTINs
        ptins_data = [
            {
                'ptin': 'P12345678',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com'
            },
            {
                'ptin': 'P87654321',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com'
            }
        ]

        for ptin_data in ptins_data:
            ptin_ero_service.register_ptin(ptin_data)

        all_ptins = ptin_ero_service.get_all_ptins()
        assert len(all_ptins) == 2
        ptin_numbers = [ptin.ptin for ptin in all_ptins]
        assert 'P12345678' in ptin_numbers
        assert 'P87654321' in ptin_numbers

    def test_register_ero_success(self, ptin_ero_service):
        """Test successful ERO registration"""
        # Register PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Register ERO
        ero_data = {
            'ero_number': '12345',
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }

        record = ptin_ero_service.register_ero(ero_data)

        assert record.ero_number == '12345'
        assert record.business_name == 'ABC Tax Services'
        assert record.ptin == 'P12345678'
        assert record in ptin_ero_service._ero_cache.values()

    def test_register_ero_invalid_formats(self, ptin_ero_service):
        """Test ERO registration with invalid formats"""
        # Register PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Test invalid ERO number
        ero_data = {
            'ero_number': '123',  # Too short
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }

        with pytest.raises(ValueError, match="Invalid ERO number format"):
            ptin_ero_service.register_ero(ero_data)

        # Test invalid EIN
        ero_data['ero_number'] = '12345'
        ero_data['ein'] = '123456789'  # Missing hyphen

        with pytest.raises(ValueError, match="Invalid EIN format"):
            ptin_ero_service.register_ero(ero_data)

    def test_register_ero_ptin_not_found(self, ptin_ero_service):
        """Test ERO registration with non-existent PTIN"""
        ero_data = {
            'ero_number': '12345',
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P12345678',  # Doesn't exist
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }

        with pytest.raises(ValueError, match="Associated PTIN not found"):
            ptin_ero_service.register_ero(ero_data)

    def test_register_ero_duplicate(self, ptin_ero_service):
        """Test registering duplicate ERO"""
        # Register PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Register ERO
        ero_data = {
            'ero_number': '12345',
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }
        ptin_ero_service.register_ero(ero_data)

        # Try to register duplicate
        with pytest.raises(ValueError, match="ERO number already registered"):
            ptin_ero_service.register_ero(ero_data)

    def test_get_eros_by_ptin(self, ptin_ero_service):
        """Test getting EROs by PTIN"""
        # Register PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Register multiple EROs for same PTIN
        ero_data1 = {
            'ero_number': '12345',
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }

        ero_data2 = {
            'ero_number': '67890',
            'business_name': 'XYZ Accounting',
            'ein': '98-7654321',
            'ptin': 'P12345678',
            'contact_name': 'Bob Johnson',
            'email': 'bob@xyz-accounting.com'
        }

        ptin_ero_service.register_ero(ero_data1)
        ptin_ero_service.register_ero(ero_data2)

        # Get EROs by PTIN
        eros = ptin_ero_service.get_eros_by_ptin('P12345678')
        assert len(eros) == 2
        ero_numbers = [ero.ero_number for ero in eros]
        assert '12345' in ero_numbers
        assert '67890' in ero_numbers

        # Get EROs for non-existent PTIN
        eros = ptin_ero_service.get_eros_by_ptin('P99999999')
        assert len(eros) == 0

    def test_validate_professional_credentials_valid_ptin_only(self, ptin_ero_service):
        """Test validating professional credentials with valid PTIN only"""
        # Register PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        is_valid, message = ptin_ero_service.validate_professional_credentials('P12345678')
        assert is_valid == True
        assert "valid" in message.lower()

    def test_validate_professional_credentials_invalid_ptin(self, ptin_ero_service):
        """Test validating professional credentials with invalid PTIN"""
        is_valid, message = ptin_ero_service.validate_professional_credentials('P12345678')
        assert is_valid == False
        assert "not registered" in message

    def test_validate_professional_credentials_inactive_ptin(self, ptin_ero_service):
        """Test validating professional credentials with inactive PTIN"""
        # Register and deactivate PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)
        ptin_ero_service.deactivate_ptin('P12345678')

        is_valid, message = ptin_ero_service.validate_professional_credentials('P12345678')
        assert is_valid == False
        assert "not active" in message

    def test_validate_professional_credentials_with_ero(self, ptin_ero_service):
        """Test validating professional credentials with PTIN and ERO"""
        # Register PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Register ERO
        ero_data = {
            'ero_number': '12345',
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }
        ptin_ero_service.register_ero(ero_data)

        is_valid, message = ptin_ero_service.validate_professional_credentials('P12345678', '12345')
        assert is_valid == True
        assert "valid" in message.lower()

    def test_validate_professional_credentials_ero_not_associated(self, ptin_ero_service):
        """Test validating credentials where ERO is not associated with PTIN"""
        # Register PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Register ERO with different PTIN (but don't register that PTIN)
        ero_data = {
            'ero_number': '12345',
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P87654321',  # Different PTIN that doesn't exist
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }

        # This should fail because the PTIN doesn't exist
        with pytest.raises(ValueError, match="Associated PTIN not found"):
            ptin_ero_service.register_ero(ero_data)

    def test_get_professional_info(self, ptin_ero_service):
        """Test getting complete professional information"""
        # Register PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        ptin_ero_service.register_ptin(ptin_data)

        # Register ERO
        ero_data = {
            'ero_number': '12345',
            'business_name': 'ABC Tax Services',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@abc-tax.com'
        }
        ptin_ero_service.register_ero(ero_data)

        info = ptin_ero_service.get_professional_info('P12345678')
        assert info is not None
        assert 'ptin' in info
        assert 'eros' in info
        assert len(info['eros']) == 1
        assert info['eros'][0]['ero_number'] == '12345'

        # Test with non-existent PTIN
        info = ptin_ero_service.get_professional_info('P99999999')
        assert info is None