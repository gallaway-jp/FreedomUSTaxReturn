"""
Encryption Service - Handles data encryption and decryption

Extracted from TaxData to follow Single Responsibility Principle.
This service encapsulates all cryptography operations.
"""

import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    
    Uses Fernet (symmetric encryption) for secure data storage.
    Keys are stored in a configurable location.
    """
    
    def __init__(self, key_file: Path):
        """
        Initialize encryption service.
        
        Args:
            key_file: Path to the encryption key file
        """
        self.key_file = Path(key_file)
        self._cipher: Optional[Fernet] = None
    
    def get_or_create_cipher(self) -> Fernet:
        """
        Get cipher instance, creating new key if needed.
        
        Returns:
            Fernet cipher instance for encryption/decryption
        """
        if self._cipher is not None:
            return self._cipher
        
        # Ensure directory exists
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.key_file.exists():
            # Load existing key
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                self._cipher = Fernet(key)
                logger.info("Loaded existing encryption key")
            except Exception as e:
                logger.error(f"Failed to load encryption key: {e}")
                raise
        else:
            # Generate new key
            key = Fernet.generate_key()
            try:
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions (owner read/write only)
                self.key_file.chmod(0o600)
                self._cipher = Fernet(key)
                logger.info("Generated new encryption key")
            except Exception as e:
                logger.error(f"Failed to create encryption key: {e}")
                raise
        
        return self._cipher
    
    def encrypt(self, data: str) -> bytes:
        """
        Encrypt string data.
        
        Args:
            data: String to encrypt
            
        Returns:
            Encrypted bytes
        """
        cipher = self.get_or_create_cipher()
        return cipher.encrypt(data.encode('utf-8'))
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt encrypted bytes.
        
        Args:
            encrypted_data: Encrypted bytes to decrypt
            
        Returns:
            Decrypted string
        """
        cipher = self.get_or_create_cipher()
        return cipher.decrypt(encrypted_data).decode('utf-8')
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt sensitive fields in a dictionary.
        
        Args:
            data: Dictionary with potential sensitive data
            
        Returns:
            Dictionary with encrypted sensitive fields
        """
        import json
        encrypted = {}
        
        # List of sensitive field paths
        sensitive_fields = [
            'personal_info.ssn',
            'spouse_info.ssn',
            'bank_info.account_number',
            'bank_info.routing_number'
        ]
        
        for key, value in data.items():
            if any(key.startswith(field.split('.')[0]) for field in sensitive_fields):
                if isinstance(value, dict):
                    # Recursively encrypt nested dictionaries
                    encrypted[key] = self.encrypt_dict(value)
                elif isinstance(value, str) and value:
                    # Encrypt string values
                    encrypted[key] = self.encrypt(value).decode('utf-8')
                else:
                    encrypted[key] = value
            else:
                encrypted[key] = value
        
        return encrypted
    
    def decrypt_dict(self, data: dict) -> dict:
        """
        Decrypt sensitive fields in a dictionary.
        
        Args:
            data: Dictionary with encrypted sensitive data
            
        Returns:
            Dictionary with decrypted sensitive fields
        """
        decrypted = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively decrypt nested dictionaries
                decrypted[key] = self.decrypt_dict(value)
            elif isinstance(value, str) and value:
                try:
                    # Try to decrypt (will work for encrypted fields)
                    decrypted[key] = self.decrypt(value.encode('utf-8'))
                except Exception:
                    # Not encrypted, keep as is
                    decrypted[key] = value
            else:
                decrypted[key] = value
        
        return decrypted
    
    def rotate_key(self, new_key_file: Path) -> None:
        """
        Rotate encryption key to a new location.
        
        Args:
            new_key_file: Path for the new key file
            
        Note:
            This requires re-encrypting all encrypted data with the new key.
        """
        # Generate new key
        new_key = Fernet.generate_key()
        
        # Save new key
        new_key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(new_key_file, 'wb') as f:
            f.write(new_key)
        new_key_file.chmod(0o600)
        
        logger.info(f"Rotated encryption key to {new_key_file}")
        logger.warning("Existing encrypted data must be re-encrypted with the new key")
