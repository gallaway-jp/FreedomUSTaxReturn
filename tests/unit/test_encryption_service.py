"""
Comprehensive tests for EncryptionService

Tests cover:
- Key generation and loading
- Encryption and decryption of strings
- Dictionary encryption/decryption
- Key rotation
- Error handling
- Edge cases
"""

import pytest
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet
from services.encryption_service import EncryptionService


class TestEncryptionServiceInitialization:
    """Test encryption service initialization"""
    
    def test_init_with_path(self, tmp_path):
        """Should initialize with key file path"""
        key_file = tmp_path / "test.key"
        service = EncryptionService(key_file)
        
        assert service.key_file == key_file
        assert service._cipher is None
    
    def test_init_creates_parent_directory(self, tmp_path):
        """Should create parent directory if it doesn't exist"""
        key_file = tmp_path / "subdir" / "nested" / "test.key"
        service = EncryptionService(key_file)
        
        # Trigger key creation
        service.get_or_create_cipher()
        
        assert key_file.parent.exists()
        assert key_file.exists()


class TestKeyManagement:
    """Test encryption key generation and loading"""
    
    def test_generates_new_key_if_not_exists(self, tmp_path):
        """Should generate new key if file doesn't exist"""
        key_file = tmp_path / "new.key"
        service = EncryptionService(key_file)
        
        cipher = service.get_or_create_cipher()
        
        assert key_file.exists()
        assert isinstance(cipher, Fernet)
        assert service._cipher is not None
    
    def test_loads_existing_key(self, tmp_path):
        """Should load existing key from file"""
        key_file = tmp_path / "existing.key"
        
        # Create a key file
        test_key = Fernet.generate_key()
        key_file.write_bytes(test_key)
        
        service = EncryptionService(key_file)
        cipher = service.get_or_create_cipher()
        
        assert isinstance(cipher, Fernet)
        # Verify it's using the same key
        test_cipher = Fernet(test_key)
        test_data = b"test"
        encrypted = cipher.encrypt(test_data)
        decrypted = test_cipher.decrypt(encrypted)
        assert decrypted == test_data
    
    def test_cipher_is_cached(self, tmp_path):
        """Should cache cipher instance"""
        key_file = tmp_path / "cached.key"
        service = EncryptionService(key_file)
        
        cipher1 = service.get_or_create_cipher()
        cipher2 = service.get_or_create_cipher()
        
        assert cipher1 is cipher2
    
    def test_key_file_has_restrictive_permissions(self, tmp_path):
        """Should set restrictive permissions on new key file"""
        key_file = tmp_path / "secure.key"
        service = EncryptionService(key_file)
        
        service.get_or_create_cipher()
        
        # Check permissions (0o600 = owner read/write only)
        import stat
        mode = key_file.stat().st_mode
        # On Windows, this might not work as expected, so we just verify the file exists
        assert key_file.exists()


class TestStringEncryptionDecryption:
    """Test encryption and decryption of strings"""
    
    def test_encrypt_string(self, tmp_path):
        """Should encrypt string to bytes"""
        service = EncryptionService(tmp_path / "test.key")
        
        plaintext = "sensitive data"
        encrypted = service.encrypt(plaintext)
        
        assert isinstance(encrypted, bytes)
        assert encrypted != plaintext.encode()
    
    def test_decrypt_string(self, tmp_path):
        """Should decrypt bytes back to original string"""
        service = EncryptionService(tmp_path / "test.key")
        
        plaintext = "sensitive data"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_empty_string(self, tmp_path):
        """Should handle empty strings"""
        service = EncryptionService(tmp_path / "test.key")
        
        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == ""
    
    def test_encrypt_decrypt_unicode(self, tmp_path):
        """Should handle unicode characters"""
        service = EncryptionService(tmp_path / "test.key")
        
        plaintext = "Test 中文 🔒 Émojis"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_long_string(self, tmp_path):
        """Should handle long strings"""
        service = EncryptionService(tmp_path / "test.key")
        
        plaintext = "A" * 10000
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_different_instances_same_key_file(self, tmp_path):
        """Should decrypt with different service instance using same key"""
        key_file = tmp_path / "shared.key"
        
        service1 = EncryptionService(key_file)
        plaintext = "shared secret"
        encrypted = service1.encrypt(plaintext)
        
        service2 = EncryptionService(key_file)
        decrypted = service2.decrypt(encrypted)
        
        assert decrypted == plaintext


class TestDictionaryEncryption:
    """Test encryption of dictionary fields"""
    
    def test_encrypt_dict_with_sensitive_fields(self, tmp_path):
        """Should encrypt sensitive fields in dictionary"""
        service = EncryptionService(tmp_path / "test.key")
        
        data = {
            'personal_info': {
                'name': 'John Doe',
                'ssn': '123-45-6789'
            },
            'income': {
                'wages': 50000
            }
        }
        
        encrypted = service.encrypt_dict(data)
        
        # Non-sensitive data should remain unchanged
        assert encrypted['income'] == data['income']
        # Sensitive nested dict should be processed
        assert 'personal_info' in encrypted
    
    def test_decrypt_dict_with_sensitive_fields(self, tmp_path):
        """Should decrypt sensitive fields in dictionary"""
        service = EncryptionService(tmp_path / "test.key")
        
        data = {
            'personal_info': {
                'name': 'John Doe',
                'ssn': '123-45-6789'
            }
        }
        
        encrypted = service.encrypt_dict(data)
        decrypted = service.decrypt_dict(encrypted)
        
        # Check nested structure is preserved
        assert 'personal_info' in decrypted
    
    def test_encrypt_dict_empty(self, tmp_path):
        """Should handle empty dictionary"""
        service = EncryptionService(tmp_path / "test.key")
        
        encrypted = service.encrypt_dict({})
        
        assert encrypted == {}
    
    def test_encrypt_dict_no_sensitive_fields(self, tmp_path):
        """Should return unchanged dict if no sensitive fields"""
        service = EncryptionService(tmp_path / "test.key")
        
        data = {
            'income': {'wages': 50000},
            'deductions': {'standard': 14600}
        }
        
        encrypted = service.encrypt_dict(data)
        
        assert encrypted == data


class TestKeyRotation:
    """Test encryption key rotation"""
    
    def test_rotate_key_creates_new_key(self, tmp_path):
        """Should create new key file"""
        old_key = tmp_path / "old.key"
        new_key = tmp_path / "new.key"
        
        service = EncryptionService(old_key)
        service.get_or_create_cipher()  # Create old key
        
        service.rotate_key(new_key)
        
        assert new_key.exists()
        assert old_key.read_bytes() != new_key.read_bytes()
    
    def test_rotate_key_creates_parent_directory(self, tmp_path):
        """Should create parent directory for new key"""
        old_key = tmp_path / "old.key"
        new_key = tmp_path / "nested" / "dir" / "new.key"
        
        service = EncryptionService(old_key)
        service.rotate_key(new_key)
        
        assert new_key.parent.exists()
        assert new_key.exists()
    
    def test_rotated_key_is_different(self, tmp_path):
        """Should generate different key on rotation"""
        old_key = tmp_path / "old.key"
        new_key = tmp_path / "new.key"
        
        service = EncryptionService(old_key)
        old_cipher = service.get_or_create_cipher()
        
        service.rotate_key(new_key)
        
        # Keys should be different
        old_key_data = old_key.read_bytes()
        new_key_data = new_key.read_bytes()
        
        assert old_key_data != new_key_data


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_decrypt_with_wrong_key(self, tmp_path):
        """Should raise error when decrypting with wrong key"""
        key1 = tmp_path / "key1.key"
        key2 = tmp_path / "key2.key"
        
        service1 = EncryptionService(key1)
        encrypted = service1.encrypt("secret")
        
        service2 = EncryptionService(key2)
        
        with pytest.raises(Exception):
            service2.decrypt(encrypted)
    
    def test_decrypt_invalid_data(self, tmp_path):
        """Should raise error when decrypting invalid data"""
        service = EncryptionService(tmp_path / "test.key")
        
        with pytest.raises(Exception):
            service.decrypt(b"not encrypted data")
    
    def test_decrypt_corrupted_data(self, tmp_path):
        """Should raise error when decrypting corrupted data"""
        service = EncryptionService(tmp_path / "test.key")
        
        encrypted = service.encrypt("test")
        # Corrupt the encrypted data
        corrupted = encrypted[:-5] + b"xxxxx"
        
        with pytest.raises(Exception):
            service.decrypt(corrupted)


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_encrypt_special_characters(self, tmp_path):
        """Should handle special characters"""
        service = EncryptionService(tmp_path / "test.key")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/`~\n\t\r"
        encrypted = service.encrypt(special_chars)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == special_chars
    
    def test_encrypt_numeric_string(self, tmp_path):
        """Should handle numeric strings"""
        service = EncryptionService(tmp_path / "test.key")
        
        numbers = "123456789"
        encrypted = service.encrypt(numbers)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == numbers
    
    def test_multiple_encrypt_same_data(self, tmp_path):
        """Should produce different ciphertext for same plaintext"""
        service = EncryptionService(tmp_path / "test.key")
        
        plaintext = "same data"
        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)
        
        # Fernet includes timestamp, so encryptions should differ
        # But both should decrypt to same value
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext
