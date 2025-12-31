"""
Unit tests for Two-Factor Authentication functionality
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from services.authentication_service import AuthenticationService, AuthenticationError
from config.app_config import AppConfig


class TestTwoFactorAuthentication:
    """Unit tests for 2FA functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        return tempfile.mkdtemp()

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration"""
        config = AppConfig()
        config.safe_dir = Path(temp_dir)
        return config

    @pytest.fixture
    def auth_service(self, config):
        """Create authentication service instance"""
        return AuthenticationService(config)

    def test_2fa_not_enabled_by_default(self, auth_service):
        """Test that 2FA is not enabled by default"""
        assert not auth_service.is_2fa_enabled()

    def test_generate_2fa_secret(self, auth_service):
        """Test generating 2FA secret"""
        with patch('pyotp.random_base32', return_value='TESTSECRET123'):
            secret = auth_service.generate_2fa_secret()
            assert secret == 'TESTSECRET123'

    @patch('pyotp.random_base32')
    def test_get_2fa_setup_info(self, mock_random, auth_service, config):
        """Test getting 2FA setup information"""
        # Setup mock
        mock_random.return_value = 'TESTSECRET123'

        # Create a session first
        auth_service.create_master_password("TestPass123!")
        session_token = auth_service.authenticate_master_password("TestPass123!")

        # Get setup info
        setup_info = auth_service.get_2fa_setup_info(session_token)

        assert 'secret' in setup_info
        assert 'uri' in setup_info
        assert 'backup_codes' in setup_info
        assert setup_info['secret'] == 'TESTSECRET123'
        assert 'otpauth://' in setup_info['uri']
        assert len(setup_info['backup_codes']) == 10

    def test_get_2fa_setup_info_invalid_session(self, auth_service):
        """Test getting 2FA setup info with invalid session"""
        with pytest.raises(AuthenticationError, match="Invalid session"):
            auth_service.get_2fa_setup_info("invalid_session")

    @patch('pyotp.TOTP')
    def test_enable_2fa_success(self, mock_totp_class, auth_service, config):
        """Test successfully enabling 2FA"""
        # Setup mocks
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_class.return_value = mock_totp

        # Create password and session
        auth_service.create_master_password("TestPass123!")
        session_token = auth_service.authenticate_master_password("TestPass123!")

        # Enable 2FA
        secret = 'TESTSECRET123'
        success = auth_service.enable_2fa(session_token, secret, '123456')

        assert success
        assert auth_service.is_2fa_enabled()

        # Verify TOTP was called correctly
        mock_totp_class.assert_called_once_with(secret)
        mock_totp.verify.assert_called_once_with('123456')

    @patch('pyotp.TOTP')
    def test_enable_2fa_invalid_code(self, mock_totp_class, auth_service, config):
        """Test enabling 2FA with invalid verification code"""
        # Setup mocks
        mock_totp = Mock()
        mock_totp.verify.return_value = False
        mock_totp_class.return_value = mock_totp

        # Create password and session
        auth_service.create_master_password("TestPass123!")
        session_token = auth_service.authenticate_master_password("TestPass123!")

        # Try to enable 2FA with invalid code
        with pytest.raises(AuthenticationError, match="Invalid verification code"):
            auth_service.enable_2fa(session_token, 'TESTSECRET123', '123456')

    def test_enable_2fa_invalid_session(self, auth_service):
        """Test enabling 2FA with invalid session"""
        with pytest.raises(AuthenticationError, match="Invalid session"):
            auth_service.enable_2fa("invalid_session", 'TESTSECRET123', '123456')

    def test_disable_2fa_success(self, auth_service, config):
        """Test successfully disabling 2FA"""
        # First enable 2FA
        auth_service.create_master_password("TestPass123!")
        session_token = auth_service.authenticate_master_password("TestPass123!")

        # Mock the enable process
        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_data['master']['2fa_secret'] = 'TESTSECRET'
        auth_service._save_auth_data(auth_data)

        # Disable 2FA
        success = auth_service.disable_2fa(session_token, "TestPass123!")

        assert success
        assert not auth_service.is_2fa_enabled()

    def test_disable_2fa_invalid_password(self, auth_service, config):
        """Test disabling 2FA with invalid password"""
        # Enable 2FA first
        auth_service.create_master_password("TestPass123!")
        session_token = auth_service.authenticate_master_password("TestPass123!")

        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_service._save_auth_data(auth_data)

        # Try to disable with wrong password
        with pytest.raises(AuthenticationError):
            auth_service.disable_2fa(session_token, "WrongPass123!")

    def test_verify_2fa_code_when_disabled(self, auth_service):
        """Test verifying 2FA code when 2FA is not enabled"""
        # Should return True when 2FA is not enabled
        assert auth_service.verify_2fa_code('123456')

    @patch('pyotp.TOTP')
    def test_verify_2fa_code_totp_success(self, mock_totp_class, auth_service, config):
        """Test verifying valid TOTP code"""
        # Setup mocks
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_class.return_value = mock_totp

        # Enable 2FA
        auth_service.create_master_password("TestPass123!")
        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_data['master']['2fa_secret'] = 'TESTSECRET'
        auth_service._save_auth_data(auth_data)

        # Verify code
        assert auth_service.verify_2fa_code('123456')
        mock_totp.verify.assert_called_once_with('123456')

    @patch('pyotp.TOTP')
    def test_verify_2fa_code_totp_failure(self, mock_totp_class, auth_service, config):
        """Test verifying invalid TOTP code"""
        # Setup mocks
        mock_totp = Mock()
        mock_totp.verify.return_value = False
        mock_totp_class.return_value = mock_totp

        # Enable 2FA
        auth_service.create_master_password("TestPass123!")
        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_data['master']['2fa_secret'] = 'TESTSECRET'
        auth_service._save_auth_data(auth_data)

        # Verify invalid code
        assert not auth_service.verify_2fa_code('123456')

    def test_verify_2fa_code_backup_code(self, auth_service, config):
        """Test verifying backup code"""
        # Enable 2FA with backup codes
        auth_service.create_master_password("TestPass123!")
        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_data['master']['2fa_secret'] = 'TESTSECRET'
        backup_codes = ['ABC123', 'DEF456', 'GHI789']
        auth_data['master']['2fa_backup_codes'] = backup_codes
        auth_service._save_auth_data(auth_data)

        # Verify backup code
        assert auth_service.verify_2fa_code('DEF456')

        # Check that backup code was removed
        updated_auth_data = auth_service._load_auth_data()
        assert 'DEF456' not in updated_auth_data['master']['2fa_backup_codes']
        assert len(updated_auth_data['master']['2fa_backup_codes']) == 2

    @patch('pyotp.TOTP')
    def test_authenticate_with_2fa_required(self, mock_totp_class, auth_service, config):
        """Test authentication with 2FA required"""
        # Setup mocks
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_class.return_value = mock_totp

        # Create password and enable 2FA
        auth_service.create_master_password("TestPass123!")
        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_data['master']['2fa_secret'] = 'TESTSECRET'
        auth_service._save_auth_data(auth_data)

        # Authenticate with 2FA
        session_token = auth_service.authenticate_with_2fa("TestPass123!", "123456")

        assert session_token is not None
        mock_totp.verify.assert_called_once_with("123456")

    @patch('pyotp.TOTP')
    def test_authenticate_with_2fa_missing_code(self, mock_totp_class, auth_service, config):
        """Test authentication with 2FA required but no code provided"""
        # Enable 2FA
        auth_service.create_master_password("TestPass123!")
        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_data['master']['2fa_secret'] = 'TESTSECRET'
        auth_service._save_auth_data(auth_data)

        # Try to authenticate without 2FA code
        with pytest.raises(AuthenticationError, match="2FA code required"):
            auth_service.authenticate_with_2fa("TestPass123!")

    @patch('pyotp.TOTP')
    def test_authenticate_with_2fa_invalid_code(self, mock_totp_class, auth_service, config):
        """Test authentication with invalid 2FA code"""
        # Setup mocks
        mock_totp = Mock()
        mock_totp.verify.return_value = False
        mock_totp_class.return_value = mock_totp

        # Enable 2FA
        auth_service.create_master_password("TestPass123!")
        auth_data = auth_service._load_auth_data()
        auth_data['master']['2fa_enabled'] = True
        auth_data['master']['2fa_secret'] = 'TESTSECRET'
        auth_service._save_auth_data(auth_data)

        # Try to authenticate with invalid code
        with pytest.raises(AuthenticationError, match="Invalid 2FA code"):
            auth_service.authenticate_with_2fa("TestPass123!", "invalid")

    def test_generate_backup_codes(self, auth_service):
        """Test generating backup codes"""
        codes = auth_service._generate_backup_codes()

        assert len(codes) == 10
        for code in codes:
            assert len(code) == 8  # 4 bytes * 2 hex chars
            assert code.isalnum()
            assert code.isupper()

    @patch('pyotp.TOTP.provisioning_uri')
    def test_2fa_setup_uri_generation(self, mock_provisioning_uri, auth_service, config):
        """Test 2FA setup URI generation"""
        mock_provisioning_uri.return_value = 'otpauth://totp/TestIssuer:TestUser?secret=TESTSECRET&issuer=TestIssuer'

        # Create session
        auth_service.create_master_password("TestPass123!")
        session_token = auth_service.authenticate_master_password("TestPass123!")

        with patch('pyotp.random_base32', return_value='TESTSECRET'):
            setup_info = auth_service.get_2fa_setup_info(session_token)

            # Verify URI was generated
            mock_provisioning_uri.assert_called_once_with(name="FreedomUS Tax Return", issuer_name="FreedomUS")
            assert setup_info['uri'] == 'otpauth://totp/TestIssuer:TestUser?secret=TESTSECRET&issuer=TestIssuer'