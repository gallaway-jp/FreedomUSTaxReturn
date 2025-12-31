"""
Unit tests for Authentication Service
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from services.authentication_service import (
    AuthenticationService,
    AuthenticationError,
    PasswordPolicyError
)
from services.ptin_ero_service import PTINEROService
from services.encryption_service import EncryptionService
from config.app_config import AppConfig


class TestAuthenticationService:
    """Test cases for AuthenticationService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AppConfig()
        self.config.safe_dir = self.temp_dir
        
        # Initialize encryption service
        self.encryption_service = EncryptionService(self.config.key_file)
        
        # Initialize PTIN/ERO service
        self.ptin_ero_service = PTINEROService(self.config, self.encryption_service)
        
        # Initialize authentication service
        self.auth_service = AuthenticationService(self.config, self.ptin_ero_service)

    def teardown_method(self):
        """Clean up test fixtures"""
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initial_state(self):
        """Test initial state of authentication service"""
        assert not self.auth_service.is_master_password_set()
        policy = self.auth_service.get_password_policy_requirements()
        assert policy['min_length'] == 8
        assert policy['require_uppercase'] is True
        assert policy['require_lowercase'] is True
        assert policy['require_digits'] is True
        assert policy['require_special_chars'] is True

    def test_password_policy_validation(self):
        """Test password policy validation"""
        # Valid password
        self.auth_service._validate_password_policy("ValidPass123!")

        # Too short
        with pytest.raises(PasswordPolicyError, match="at least 8 characters"):
            self.auth_service._validate_password_policy("Short1!")

        # No uppercase
        with pytest.raises(PasswordPolicyError, match="uppercase letter"):
            self.auth_service._validate_password_policy("validpass123!")

        # No lowercase
        with pytest.raises(PasswordPolicyError, match="lowercase letter"):
            self.auth_service._validate_password_policy("VALIDPASS123!")

        # No digits
        with pytest.raises(PasswordPolicyError, match="at least one digit"):
            self.auth_service._validate_password_policy("ValidPass!")

        # No special chars
        with pytest.raises(PasswordPolicyError, match="special character"):
            self.auth_service._validate_password_policy("ValidPass123")

    def test_create_master_password(self):
        """Test creating master password"""
        password = "TestPass123!"

        self.auth_service.create_master_password(password)
        assert self.auth_service.is_master_password_set()

        # Try to create again - should fail
        with pytest.raises(AuthenticationError, match="already exists"):
            self.auth_service.create_master_password("AnotherPass123!")

    def test_authenticate_master_password(self):
        """Test authenticating with master password"""
        password = "TestPass123!"

        # Create password first
        self.auth_service.create_master_password(password)

        # Successful authentication
        session_token = self.auth_service.authenticate_master_password(password)
        assert session_token is not None
        assert isinstance(session_token, str)

        # Validate session
        user_id = self.auth_service.validate_session(session_token)
        assert user_id == "master"

        # Invalid password
        with pytest.raises(AuthenticationError, match="Invalid password"):
            self.auth_service.authenticate_master_password("WrongPass123!")

    def test_account_lockout(self):
        """Test account lockout after failed attempts"""
        password = "TestPass123!"
        self.auth_service.create_master_password(password)

        # Simulate failed attempts
        for i in range(self.auth_service.max_login_attempts):
            with pytest.raises(AuthenticationError):
                self.auth_service.authenticate_master_password("WrongPass123!")

        # Next attempt should mention lockout
        with pytest.raises(AuthenticationError, match="locked"):
            self.auth_service.authenticate_master_password("WrongPass123!")

    def test_session_management(self):
        """Test session token management"""
        password = "TestPass123!"
        self.auth_service.create_master_password(password)

        # Create session
        token1 = self.auth_service.authenticate_master_password(password)
        token2 = self.auth_service.authenticate_master_password(password)

        # Both tokens should be valid
        assert self.auth_service.validate_session(token1) == "master"
        assert self.auth_service.validate_session(token2) == "master"

        # Logout one session
        self.auth_service.logout(token1)
        assert self.auth_service.validate_session(token1) is None
        assert self.auth_service.validate_session(token2) == "master"

    def test_change_master_password(self):
        """Test changing master password"""
        old_password = "OldPass123!"
        new_password = "NewPass456!"

        # Create initial password
        self.auth_service.create_master_password(old_password)

        # Change password
        self.auth_service.change_master_password(old_password, new_password)

        # Old password should no longer work
        with pytest.raises(AuthenticationError):
            self.auth_service.authenticate_master_password(old_password)

        # New password should work
        session_token = self.auth_service.authenticate_master_password(new_password)
        assert session_token is not None

    def test_session_timeout(self):
        """Test session timeout"""
        password = "TestPass123!"
        self.auth_service.create_master_password(password)

        # Create session
        token = self.auth_service.authenticate_master_password(password)

        # Mock session creation time to be expired
        sessions = self.auth_service._load_sessions()
        expired_time = datetime.now() - timedelta(hours=self.auth_service.session_timeout_hours + 1)
        sessions[token]['created_at'] = expired_time
        sessions[token]['last_activity'] = expired_time
        self.auth_service._save_sessions(sessions)

        # Session should be invalid
        assert self.auth_service.validate_session(token) is None

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPass123!"
        salt = self.auth_service._generate_salt()

        # Hash password
        hash1 = self.auth_service._hash_password(password, salt)
        hash2 = self.auth_service._hash_password(password, salt)

        # Same password + salt should produce same hash
        assert hash1 == hash2

        # Different salt should produce different hash
        salt2 = self.auth_service._generate_salt()
        hash3 = self.auth_service._hash_password(password, salt2)
        assert hash1 != hash3

    # PTIN/ERO Authentication Tests

    def test_authenticate_with_ptin_success(self):
        """Test successful PTIN authentication"""
        # Register a PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)

        # Authenticate with PTIN
        session_token, user_info = self.auth_service.authenticate_with_ptin('P12345678')

        # Verify session was created
        assert session_token
        assert self.auth_service.validate_session(session_token) is not None

        # Verify user info
        assert user_info['user_type'] == 'professional'
        assert user_info['ptin'] == 'P12345678'
        assert user_info['name'] == 'John Doe'
        assert user_info['email'] == 'john.doe@example.com'
        assert user_info['role'] == 'tax_preparer'

    def test_authenticate_with_ptin_invalid_format(self):
        """Test PTIN authentication with invalid format"""
        with pytest.raises(AuthenticationError, match="Invalid PTIN format"):
            self.auth_service.authenticate_with_ptin('INVALID')

    def test_authenticate_with_ptin_not_found(self):
        """Test PTIN authentication with unregistered PTIN"""
        with pytest.raises(AuthenticationError, match="PTIN not found"):
            self.auth_service.authenticate_with_ptin('P12345678')

    def test_authenticate_with_ptin_inactive(self):
        """Test PTIN authentication with inactive PTIN"""
        # Register and then deactivate PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)
        self.ptin_ero_service.deactivate_ptin('P12345678')

        with pytest.raises(AuthenticationError, match="PTIN is inactive"):
            self.auth_service.authenticate_with_ptin('P12345678')

    def test_authenticate_with_ero_success(self):
        """Test successful ERO authentication"""
        # Register PTIN first
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)

        # Register ERO
        ero_data = {
            'ero_number': '12345',
            'business_name': 'Tax Services Inc',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@taxservices.com'
        }
        self.ptin_ero_service.register_ero(ero_data)

        # Authenticate with ERO
        session_token, user_info = self.auth_service.authenticate_with_ero('12345', 'P12345678')

        # Verify session was created
        assert session_token
        assert self.auth_service.validate_session(session_token) is not None

        # Verify user info
        assert user_info['user_type'] == 'ero'
        assert user_info['ero_number'] == '12345'
        assert user_info['ptin'] == 'P12345678'
        assert user_info['business_name'] == 'Tax Services Inc'
        assert user_info['contact_name'] == 'Jane Smith'
        assert user_info['role'] == 'ero_administrator'

    def test_authenticate_with_ero_invalid_ero_format(self):
        """Test ERO authentication with invalid ERO format"""
        with pytest.raises(AuthenticationError, match="Invalid ERO number format"):
            self.auth_service.authenticate_with_ero('INVALID', 'P12345678')

    def test_authenticate_with_ero_ptin_mismatch(self):
        """Test ERO authentication with mismatched PTIN"""
        # Register PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)

        # Register ERO with different PTIN
        ptin_data2 = {
            'ptin': 'P87654321',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data2)

        ero_data = {
            'ero_number': '12345',
            'business_name': 'Tax Services Inc',
            'ein': '12-3456789',
            'ptin': 'P87654321',
            'contact_name': 'Jane Smith',
            'email': 'jane@taxservices.com'
        }
        self.ptin_ero_service.register_ero(ero_data)

        # Try to authenticate with wrong PTIN
        with pytest.raises(AuthenticationError, match="PTIN does not match ERO record"):
            self.auth_service.authenticate_with_ero('12345', 'P12345678')

    def test_validate_professional_credentials_ptin_only(self):
        """Test credential validation for PTIN only"""
        # Register PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)

        # Validate credentials
        is_valid, message = self.auth_service.validate_professional_credentials(ptin='P12345678')
        assert is_valid
        assert message == "Credentials are valid"

    def test_validate_professional_credentials_ero_only(self):
        """Test credential validation for ERO only"""
        # Register PTIN and ERO
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)

        ero_data = {
            'ero_number': '12345',
            'business_name': 'Tax Services Inc',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@taxservices.com'
        }
        self.ptin_ero_service.register_ero(ero_data)

        # Validate credentials
        is_valid, message = self.auth_service.validate_professional_credentials(ero_number='12345')
        assert is_valid
        assert message == "Credentials are valid"

    def test_validate_professional_credentials_both(self):
        """Test credential validation for both PTIN and ERO"""
        # Register PTIN and ERO
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)

        ero_data = {
            'ero_number': '12345',
            'business_name': 'Tax Services Inc',
            'ein': '12-3456789',
            'ptin': 'P12345678',
            'contact_name': 'Jane Smith',
            'email': 'jane@taxservices.com'
        }
        self.ptin_ero_service.register_ero(ero_data)

        # Validate both credentials
        is_valid, message = self.auth_service.validate_professional_credentials(
            ptin='P12345678', ero_number='12345'
        )
        assert is_valid
        assert message == "Credentials are valid"

    def test_validate_professional_credentials_mismatch(self):
        """Test credential validation with PTIN/ERO mismatch"""
        # Register PTIN and ERO with different PTIN
        ptin_data = {
            'ptin': 'P12345678',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data)

        ptin_data2 = {
            'ptin': 'P87654321',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com'
        }
        self.ptin_ero_service.register_ptin(ptin_data2)

        ero_data = {
            'ero_number': '12345',
            'business_name': 'Tax Services Inc',
            'ein': '12-3456789',
            'ptin': 'P87654321',
            'contact_name': 'Jane Smith',
            'email': 'jane@taxservices.com'
        }
        self.ptin_ero_service.register_ero(ero_data)

        # Try to validate with mismatched PTIN
        is_valid, message = self.auth_service.validate_professional_credentials(
            ptin='P12345678', ero_number='12345'
        )
        assert not is_valid
        assert "PTIN does not match ERO record" in message
