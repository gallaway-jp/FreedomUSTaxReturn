"""
Unit tests for Multi-Client Management functionality

Tests client account creation, authentication, management, and 2FA features.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from config.app_config import AppConfig
from services.authentication_service import AuthenticationService, AuthenticationError, PasswordPolicyError


class TestMultiClientManagement:
    """Test suite for multi-client management features"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AppConfig()
        self.config.safe_dir = self.temp_dir
        self.auth_service = AuthenticationService(self.config)
        
        # Create master session for testing
        self.auth_service.create_master_password("TestPass123!")
        self.master_session = self.auth_service.authenticate_master_password("TestPass123!")

    def teardown_method(self):
        """Clean up test fixtures"""
        # Clean up any files created during tests
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)



    def test_create_client_account_success(self):
        """Test successful client account creation"""
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        assert client_id.startswith("client_")
        assert len(client_id) > 10  # Should be longer than just "client_"

        # Verify client was created
        clients = self.auth_service.get_client_list(self.master_session)
        assert len(clients) == 1
        assert clients[0]['name'] == "John Doe"
        assert clients[0]['email'] == "john@example.com"
        assert clients[0]['ssn_last4'] == "1234"
        assert clients[0]['is_active'] is True

        # Verify data directory was created
        client_dir = self.auth_service.get_client_data_directory(client_id)
        assert client_dir.exists()
        assert client_dir.is_dir()

    def test_create_client_account_duplicate_email(self):
        """Test creating client with duplicate email fails"""
        # Create first client
        self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Try to create second client with same email
        with pytest.raises(AuthenticationError, match="already exists"):
            self.auth_service.create_client_account(
                self.master_session, "Jane Doe", "john@example.com", "5678", "ClientPass456!"
            )

    def test_create_client_account_invalid_session(self):
        """Test creating client with invalid session fails"""
        with pytest.raises(AuthenticationError, match="Invalid session"):
            self.auth_service.create_client_account(
                "invalid_session", "John Doe", "john@example.com", "1234", "ClientPass123!"
            )

    def test_create_client_account_weak_password(self):
        """Test creating client with weak password fails"""
        with pytest.raises(PasswordPolicyError):
            self.auth_service.create_client_account(
                self.master_session, "John Doe", "john@example.com", "1234", "weak"
            )

    def test_authenticate_client_success(self):
        """Test successful client authentication"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Authenticate client
        session_token, authenticated_client_id = self.auth_service.authenticate_client(
            "john@example.com", "ClientPass123!"
        )

        assert session_token is not None
        assert authenticated_client_id == client_id

        # Verify session is valid
        validated_user = self.auth_service.validate_session(session_token)
        assert validated_user == client_id

    def test_authenticate_client_wrong_password(self):
        """Test client authentication with wrong password"""
        # Create client
        self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Try to authenticate with wrong password
        with pytest.raises(AuthenticationError, match="Invalid password"):
            self.auth_service.authenticate_client("john@example.com", "WrongPass123!")

    def test_authenticate_client_nonexistent(self):
        """Test authentication of non-existent client when no clients exist"""
        with pytest.raises(AuthenticationError, match="No client accounts found"):
            self.auth_service.authenticate_client("nonexistent@example.com", "SomePass123!")

    def test_authenticate_client_wrong_email(self):
        """Test authentication with wrong email when clients exist"""
        # Create a client
        self.auth_service.create_client_account(
            self.master_session, "John Doe", "unique@example.com", "1234", "ClientPass123!"
        )

        # Try to authenticate with non-existent email
        with pytest.raises(AuthenticationError, match="Client account not found"):
            self.auth_service.authenticate_client("wrong@example.com", "ClientPass123!")
        """Test authentication of deactivated client fails"""
        # Create and deactivate client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )
        self.auth_service.deactivate_client(self.master_session, client_id)

        # Try to authenticate
        with pytest.raises(AuthenticationError, match="Client account is deactivated"):
            self.auth_service.authenticate_client("john@example.com", "ClientPass123!")

    def test_get_client_list(self):
        """Test retrieving client list"""
        # Create multiple clients
        client1_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )
        client2_id = self.auth_service.create_client_account(
            self.master_session, "Jane Smith", "jane@example.com", "5678", "ClientPass456!"
        )

        clients = self.auth_service.get_client_list(self.master_session)

        assert len(clients) == 2

        # Check client details
        john_client = next(c for c in clients if c['id'] == client1_id)
        assert john_client['name'] == "John Doe"
        assert john_client['email'] == "john@example.com"
        assert john_client['ssn_last4'] == "1234"
        assert john_client['is_active'] is True

        jane_client = next(c for c in clients if c['id'] == client2_id)
        assert jane_client['name'] == "Jane Smith"
        assert jane_client['email'] == "jane@example.com"
        assert jane_client['ssn_last4'] == "5678"
        assert jane_client['is_active'] is True

    def test_update_client_info(self):
        """Test updating client information"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Update client info
        self.auth_service.update_client_info(self.master_session, client_id, "John Smith", "johnsmith@example.com")

        # Verify update
        clients = self.auth_service.get_client_list(self.master_session)
        client = next(c for c in clients if c['id'] == client_id)
        assert client['name'] == "John Smith"
        assert client['email'] == "johnsmith@example.com"

    def test_update_client_info_duplicate_email(self):
        """Test updating client email to existing email fails"""
        # Create two clients
        client1_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )
        client2_id = self.auth_service.create_client_account(
            self.master_session, "Jane Smith", "jane@example.com", "5678", "ClientPass456!"
        )

        # Try to update client1 email to client2's email
        with pytest.raises(AuthenticationError, match="already in use"):
            self.auth_service.update_client_info(self.master_session, client1_id, email="jane@example.com")

    def test_deactivate_activate_client(self):
        """Test deactivating and reactivating client accounts"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Deactivate
        self.auth_service.deactivate_client(self.master_session, client_id)
        clients = self.auth_service.get_client_list(self.master_session)
        client = next(c for c in clients if c['id'] == client_id)
        assert client['is_active'] is False

        # Reactivate
        self.auth_service.activate_client(self.master_session, client_id)
        clients = self.auth_service.get_client_list(self.master_session)
        client = next(c for c in clients if c['id'] == client_id)
        assert client['is_active'] is True

    def test_change_client_password(self):
        """Test changing client password"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Change password
        self.auth_service.change_client_password(self.master_session, client_id, "NewPass456!")

        # Verify old password doesn't work
        with pytest.raises(AuthenticationError):
            self.auth_service.authenticate_client("john@example.com", "ClientPass123!")

        # Verify new password works
        session_token, authenticated_client_id = self.auth_service.authenticate_client(
            "john@example.com", "NewPass456!"
        )
        assert authenticated_client_id == client_id

    def test_client_2fa_enable_disable(self):
        """Test enabling and disabling 2FA for clients"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Get 2FA setup info
        setup_info = self.auth_service.get_client_2fa_setup_info(self.master_session, client_id)
        assert 'secret' in setup_info
        assert 'uri' in setup_info

        # Mock TOTP verification for testing
        with patch('pyotp.TOTP.verify', return_value=True):
            # Enable 2FA
            success = self.auth_service.enable_client_2fa(self.master_session, client_id, setup_info['secret'], "123456")
            assert success is True

        # Verify 2FA is enabled
        clients = self.auth_service.get_client_list(self.master_session)
        client = next(c for c in clients if c['id'] == client_id)
        assert client['two_factor_enabled'] is True

        # Disable 2FA
        success = self.auth_service.disable_client_2fa(self.master_session, client_id)
        assert success is True

        # Verify 2FA is disabled
        clients = self.auth_service.get_client_list(self.master_session)
        client = next(c for c in clients if c['id'] == client_id)
        assert client['two_factor_enabled'] is False

    def test_client_2fa_authentication(self):
        """Test client authentication with 2FA enabled"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Enable 2FA
        setup_info = self.auth_service.get_client_2fa_setup_info(self.master_session, client_id)
        with patch('pyotp.TOTP.verify', return_value=True):
            self.auth_service.enable_client_2fa(self.master_session, client_id, setup_info['secret'], "123456")

        # Try to authenticate without 2FA code (should fail)
        with pytest.raises(AuthenticationError, match="2FA code required"):
            self.auth_service.authenticate_client("john@example.com", "ClientPass123!")

        # Authenticate with valid 2FA code (mocked)
        with patch.object(self.auth_service, '_verify_client_2fa_code', return_value=True):
            session_token, authenticated_client_id = self.auth_service.authenticate_client(
                "john@example.com", "ClientPass123!", "123456"
            )
            assert authenticated_client_id == client_id

    def test_client_account_lockout(self):
        """Test client account lockout after failed attempts"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Simulate multiple failed login attempts
        for _ in range(5):
            with pytest.raises(AuthenticationError):
                self.auth_service.authenticate_client("john@example.com", "WrongPass123!")

        # Account should be locked
        with pytest.raises(AuthenticationError, match="Account locked"):
            self.auth_service.authenticate_client("john@example.com", "ClientPass123!")

    def test_get_client_data_directory(self):
        """Test getting client data directory"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Get data directory
        data_dir = self.auth_service.get_client_data_directory(client_id)
        assert data_dir.exists()
        assert data_dir.is_dir()
        assert f"client_data_{client_id}" in str(data_dir)

    def test_get_client_data_directory_nonexistent(self):
        """Test getting data directory for non-existent client fails"""
        with pytest.raises(AuthenticationError, match="Client not found"):
            self.auth_service.get_client_data_directory("nonexistent_client")

    def test_client_operations_invalid_session(self):
        """Test that client operations require valid session"""
        # Create client
        client_id = self.auth_service.create_client_account(
            self.master_session, "John Doe", "john@example.com", "1234", "ClientPass123!"
        )

        # Try operations with invalid session
        invalid_session = "invalid_session_token"

        with pytest.raises(AuthenticationError, match="Invalid session"):
            self.auth_service.get_client_list(invalid_session)

        with pytest.raises(AuthenticationError, match="Invalid session"):
            self.auth_service.update_client_info(invalid_session, client_id, "New Name")

        with pytest.raises(AuthenticationError, match="Invalid session"):
            self.auth_service.deactivate_client(invalid_session, client_id)

        with pytest.raises(AuthenticationError, match="Invalid session"):
            self.auth_service.change_client_password(invalid_session, client_id, "NewPass123!")

    def test_client_data_isolation(self):
        """Test that client data directories are properly isolated"""
        # Create multiple clients
        client1_id = self.auth_service.create_client_account(
            self.master_session, "Client One", "client1@example.com", "1111", "Pass123!"
        )
        client2_id = self.auth_service.create_client_account(
            self.master_session, "Client Two", "client2@example.com", "2222", "Pass456!"
        )

        # Get data directories
        dir1 = self.auth_service.get_client_data_directory(client1_id)
        dir2 = self.auth_service.get_client_data_directory(client2_id)

        # Directories should be different
        assert dir1 != dir2
        assert client1_id in str(dir1)
        assert client2_id in str(dir2)

        # Each directory should exist and be unique
        assert dir1.exists()
        assert dir2.exists()
        assert dir1 != dir2