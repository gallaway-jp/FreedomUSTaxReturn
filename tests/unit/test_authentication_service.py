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
from config.app_config import AppConfig


class TestAuthenticationService:
    """Test cases for AuthenticationService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AppConfig()
        self.config.safe_dir = self.temp_dir
        self.auth_service = AuthenticationService(self.config)

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
