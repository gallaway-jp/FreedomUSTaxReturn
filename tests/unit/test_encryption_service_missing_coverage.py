"""
Tests to cover missing lines in encryption_service.py

Targets specific uncovered error handling paths:
- Lines 54-56: Exception handling when loading existing key fails
- Lines 67-69: Exception handling when creating new key fails
- Lines 125-129: String/empty value handling in encrypt_dict
- Line 159: Decrypt fallback for non-encrypted values in decrypt_dict
"""
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from services.encryption_service import EncryptionService
from cryptography.fernet import Fernet


class TestKeyLoadingErrors:
    """Test error handling when loading encryption key fails (lines 54-56)."""
    
    def test_load_key_handles_corrupted_key_file(self, tmp_path):
        """Test that loading a corrupted key file raises exception."""
        key_file = tmp_path / "corrupted.key"
        
        # Create a corrupted key file
        key_file.write_bytes(b"not a valid key")
        
        service = EncryptionService(key_file)
        
        # Should raise exception when trying to load corrupted key
        with pytest.raises(Exception):
            service.get_or_create_cipher()
    
    def test_load_key_handles_file_read_permission_error(self, tmp_path):
        """Test that permission errors during key load are propagated."""
        key_file = tmp_path / "secure.key"
        
        # Create valid key file first
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        
        service = EncryptionService(key_file)
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                service.get_or_create_cipher()


class TestKeyCreationErrors:
    """Test error handling when creating new key fails (lines 67-69)."""
    
    def test_create_key_handles_write_permission_error(self, tmp_path):
        """Test that permission errors during key creation are propagated."""
        key_file = tmp_path / "new.key"
        service = EncryptionService(key_file)
        
        # Mock open to raise PermissionError when writing
        m = mock_open()
        m.side_effect = PermissionError("Cannot write")
        
        with patch('builtins.open', m):
            with pytest.raises(PermissionError):
                service.get_or_create_cipher()
    
    def test_create_key_handles_chmod_failure(self, tmp_path):
        """Test that chmod errors during key creation are propagated."""
        key_file = tmp_path / "new.key"
        service = EncryptionService(key_file)
        
        # Mock chmod to raise OSError
        with patch.object(Path, 'chmod', side_effect=OSError("chmod failed")):
            with pytest.raises(OSError):
                service.get_or_create_cipher()


class TestEncryptDictStringHandling:
    """Test string value handling in encrypt_dict (lines 125-129)."""
    
    def test_encrypt_dict_with_empty_string_in_sensitive_field(self, tmp_path):
        """Test that empty strings in sensitive fields are not encrypted (line 126-127)."""
        key_file = tmp_path / "test.key"
        service = EncryptionService(key_file)
        service.get_or_create_cipher()
        
        data = {
            'personal_info': {
                'ssn': '',  # Empty string - should not be encrypted
                'name': 'John Doe'
            }
        }
        
        encrypted = service.encrypt_dict(data)
        
        # Empty string should remain empty
        assert encrypted['personal_info']['ssn'] == ''
    
    def test_encrypt_dict_with_non_string_sensitive_field(self, tmp_path):
        """Test that non-string values are kept as-is (line 129)."""
        key_file = tmp_path / "test.key"
        service = EncryptionService(key_file)
        service.get_or_create_cipher()
        
        data = {
            'personal_info': {
                'ssn': None,  # Non-string value
                'age': 30,    # Non-string value
                'name': 'John Doe'
            }
        }
        
        encrypted = service.encrypt_dict(data)
        
        # Non-string values should remain unchanged
        assert encrypted['personal_info']['ssn'] is None
        assert encrypted['personal_info']['age'] == 30
    
    def test_encrypt_dict_encrypts_non_empty_string_values(self, tmp_path):
        """Test that non-empty string values ARE encrypted when directly matched (line 127)."""
        key_file = tmp_path / "test.key"
        service = EncryptionService(key_file)
        service.get_or_create_cipher()
        
        # Use top-level sensitive field (not nested) to trigger lines 125-127
        data = {
            'personal_info': '123-45-6789',  # Direct string value, not nested
        }
        
        encrypted = service.encrypt_dict(data)
        
        # SSN should be encrypted (different from original)
        assert encrypted['personal_info'] != '123-45-6789'
        assert isinstance(encrypted['personal_info'], str)


class TestDecryptDictNonEncryptedHandling:
    """Test handling of non-encrypted values in decrypt_dict (line 159)."""
    
    def test_decrypt_dict_keeps_non_encrypted_plain_text(self, tmp_path):
        """Test that plain text (non-encrypted) values are kept as-is (line 159)."""
        key_file = tmp_path / "test.key"
        service = EncryptionService(key_file)
        service.get_or_create_cipher()
        
        # Data with plain text that's not encrypted
        data = {
            'other_info': {
                'name': 'John Doe',  # Plain text - not encrypted
                'city': 'New York'
            }
        }
        
        decrypted = service.decrypt_dict(data)
        
        # Plain text should remain unchanged
        assert decrypted['other_info']['name'] == 'John Doe'
        assert decrypted['other_info']['city'] == 'New York'
    
    def test_decrypt_dict_handles_mixed_encrypted_and_plain(self, tmp_path):
        """Test decrypt handles mix of encrypted and plain text."""
        key_file = tmp_path / "test.key"
        service = EncryptionService(key_file)
        service.get_or_create_cipher()
        
        # Encrypt some data
        ssn_encrypted = service.encrypt('123-45-6789').decode('utf-8')
        
        # Create dict with both encrypted and plain text
        data = {
            'personal_info': {
                'ssn': ssn_encrypted,  # Encrypted
                'name': 'John Doe'      # Plain text
            }
        }
        
        decrypted = service.decrypt_dict(data)
        
        # Encrypted value should be decrypted
        assert decrypted['personal_info']['ssn'] == '123-45-6789'
        # Plain text should remain unchanged
        assert decrypted['personal_info']['name'] == 'John Doe'
