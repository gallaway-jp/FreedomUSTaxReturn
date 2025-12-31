"""
Authentication Service - Handles user authentication and access control

Provides password-based authentication, session management, and access control
for the tax preparation application.
"""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

from config.app_config import AppConfig
from services.ptin_ero_service import PTINEROService

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class PasswordPolicyError(Exception):
    """Raised when password doesn't meet policy requirements"""
    pass


class AuthenticationService:
    """
    Service for handling user authentication and session management.

    Features:
    - Password hashing with salt
    - Session token management
    - Password policy enforcement
    - Account lockout protection
    """

    def __init__(self, config: AppConfig, ptin_ero_service: Optional[PTINEROService] = None):
        """
        Initialize authentication service.

        Args:
            config: Application configuration
            ptin_ero_service: Optional PTIN/ERO service for professional authentication
        """
        self.config = config
        self.ptin_ero_service = ptin_ero_service
        self.auth_file = config.safe_dir / "auth.json"
        self.sessions_file = config.safe_dir / "sessions.json"

        # Password policy settings
        self.min_password_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special_chars = True

        # Account lockout settings
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 15

        # Session settings
        self.session_timeout_hours = 24

        # Ensure auth directory exists
        self.config.safe_dir.mkdir(parents=True, exist_ok=True)

    def _load_auth_data(self) -> Dict:
        """Load authentication data from file"""
        if not self.auth_file.exists():
            return {}

        try:
            with open(self.auth_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load auth data: {e}")
            return {}

    def _save_auth_data(self, data: Dict) -> None:
        """Save authentication data to file"""
        try:
            with open(self.auth_file, 'w') as f:
                json.dump(data, f, indent=2)
            # Set restrictive permissions
            self.auth_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save auth data: {e}")
            raise

    def _load_sessions(self) -> Dict:
        """Load session data from file"""
        if not self.sessions_file.exists():
            return {}

        try:
            with open(self.sessions_file, 'r') as f:
                data = json.load(f)
                # Convert string timestamps back to datetime
                for session_id, session in data.items():
                    session['created_at'] = datetime.fromisoformat(session['created_at'])
                    session['last_activity'] = datetime.fromisoformat(session['last_activity'])
                return data
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return {}

    def _save_sessions(self, sessions: Dict) -> None:
        """Save session data to file"""
        try:
            # Convert datetime objects to strings for JSON serialization
            data = {}
            for session_id, session in sessions.items():
                data[session_id] = {
                    **session,
                    'created_at': session['created_at'].isoformat(),
                    'last_activity': session['last_activity'].isoformat()
                }

            with open(self.sessions_file, 'w') as f:
                json.dump(data, f, indent=2)
            # Set restrictive permissions
            self.sessions_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
            raise

    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash password with salt using PBKDF2.

        Args:
            password: Plain text password
            salt: Salt string

        Returns:
            Hex string of hashed password
        """
        # Use PBKDF2 with SHA-256, 100,000 iterations
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return key.hex()

    def _generate_salt(self) -> str:
        """Generate a random salt"""
        return secrets.token_hex(16)

    def _validate_password_policy(self, password: str) -> None:
        """
        Validate password against policy requirements.

        Args:
            password: Password to validate

        Raises:
            PasswordPolicyError: If password doesn't meet requirements
        """
        if len(password) < self.min_password_length:
            raise PasswordPolicyError(f"Password must be at least {self.min_password_length} characters long")

        if self.require_uppercase and not any(c.isupper() for c in password):
            raise PasswordPolicyError("Password must contain at least one uppercase letter")

        if self.require_lowercase and not any(c.islower() for c in password):
            raise PasswordPolicyError("Password must contain at least one lowercase letter")

        if self.require_digits and not any(c.isdigit() for c in password):
            raise PasswordPolicyError("Password must contain at least one digit")

        if self.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise PasswordPolicyError("Password must contain at least one special character")

    def create_master_password(self, password: str) -> None:
        """
        Create the master password for the application.

        Args:
            password: Master password to set

        Raises:
            PasswordPolicyError: If password doesn't meet policy
        """
        self._validate_password_policy(password)

        auth_data = self._load_auth_data()

        # Check if master password already exists
        if 'master' in auth_data:
            raise AuthenticationError("Master password already exists")

        salt = self._generate_salt()
        hashed_password = self._hash_password(password, salt)

        auth_data['master'] = {
            'password_hash': hashed_password,
            'salt': salt,
            'created_at': datetime.now().isoformat(),
            'login_attempts': 0,
            'locked_until': None
        }

        self._save_auth_data(auth_data)
        logger.info("Master password created successfully")

    def authenticate_master_password(self, password: str) -> str:
        """
        Authenticate with master password.

        Args:
            password: Password to authenticate

        Returns:
            Session token on success

        Raises:
            AuthenticationError: If authentication fails
        """
        auth_data = self._load_auth_data()

        if 'master' not in auth_data:
            raise AuthenticationError("Master password not set")

        master_data = auth_data['master']

        # Check if account is locked
        if master_data.get('locked_until'):
            locked_until = datetime.fromisoformat(master_data['locked_until'])
            if datetime.now() < locked_until:
                raise AuthenticationError(f"Account locked until {locked_until}")
            else:
                # Clear lockout
                master_data['locked_until'] = None
                master_data['login_attempts'] = 0

        # Verify password
        hashed_input = self._hash_password(password, master_data['salt'])
        if not hmac.compare_digest(hashed_input, master_data['password_hash']):
            # Increment failed attempts
            master_data['login_attempts'] = master_data.get('login_attempts', 0) + 1

            if master_data['login_attempts'] >= self.max_login_attempts:
                # Lock account
                locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
                master_data['locked_until'] = locked_until.isoformat()
                self._save_auth_data(auth_data)
                raise AuthenticationError(f"Account locked for {self.lockout_duration_minutes} minutes due to too many failed attempts")

            self._save_auth_data(auth_data)
            raise AuthenticationError("Invalid password")

        # Successful authentication
        master_data['login_attempts'] = 0
        master_data['last_login'] = datetime.now().isoformat()
        self._save_auth_data(auth_data)

        # Create session
        session_token = self._create_session('master')
        logger.info("Master password authentication successful")
        return session_token

    def _create_session(self, user_id: str) -> str:
        """
        Create a new session for authenticated user.

        Args:
            user_id: User identifier

        Returns:
            Session token
        """
        sessions = self._load_sessions()

        # Clean expired sessions
        self._clean_expired_sessions(sessions)

        # Generate session token
        session_token = secrets.token_urlsafe(32)
        now = datetime.now()

        sessions[session_token] = {
            'user_id': user_id,
            'created_at': now,
            'last_activity': now
        }

        self._save_sessions(sessions)
        return session_token

    def _clean_expired_sessions(self, sessions: Dict) -> None:
        """Remove expired sessions from the sessions dict"""
        now = datetime.now()
        expired_tokens = []

        for token, session in sessions.items():
            if now - session['last_activity'] > timedelta(hours=self.session_timeout_hours):
                expired_tokens.append(token)

        for token in expired_tokens:
            del sessions[token]

    def validate_session(self, session_token: str) -> Optional[str]:
        """
        Validate session token and return user ID if valid.

        Args:
            session_token: Session token to validate

        Returns:
            User ID if session is valid, None otherwise
        """
        sessions = self._load_sessions()

        if session_token not in sessions:
            return None

        session = sessions[session_token]
        now = datetime.now()

        # Check if session expired
        if now - session['last_activity'] > timedelta(hours=self.session_timeout_hours):
            del sessions[session_token]
            self._save_sessions(sessions)
            return None

        # Update last activity
        session['last_activity'] = now
        self._save_sessions(sessions)

        return session['user_id']

    def logout(self, session_token: str) -> None:
        """
        Logout by removing session.

        Args:
            session_token: Session token to remove
        """
        sessions = self._load_sessions()

        if session_token in sessions:
            del sessions[session_token]
            self._save_sessions(sessions)
            logger.info("Session logged out")

    def change_master_password(self, current_password: str, new_password: str) -> None:
        """
        Change the master password.

        Args:
            current_password: Current password for verification
            new_password: New password to set

        Raises:
            AuthenticationError: If current password is wrong
            PasswordPolicyError: If new password doesn't meet policy
        """
        # First authenticate with current password
        self.authenticate_master_password(current_password)

        # Validate new password
        self._validate_password_policy(new_password)

        auth_data = self._load_auth_data()
        master_data = auth_data['master']

        # Generate new salt and hash
        salt = self._generate_salt()
        hashed_password = self._hash_password(new_password, salt)

        # Update password data
        master_data['password_hash'] = hashed_password
        master_data['salt'] = salt
        master_data['login_attempts'] = 0
        master_data['locked_until'] = None

        self._save_auth_data(auth_data)
        logger.info("Master password changed successfully")

    def is_master_password_set(self) -> bool:
        """Check if master password has been set"""
        auth_data = self._load_auth_data()
        return 'master' in auth_data

    def get_password_policy_requirements(self) -> Dict:
        """Get password policy requirements for UI display"""
        return {
            'min_length': self.min_password_length,
            'require_uppercase': self.require_uppercase,
            'require_lowercase': self.require_lowercase,
            'require_digits': self.require_digits,
            'require_special_chars': self.require_special_chars
        }

    # Two-Factor Authentication (2FA) Methods

    def is_2fa_enabled(self) -> bool:
        """Check if 2FA is enabled for the master account"""
        auth_data = self._load_auth_data()
        master_data = auth_data.get('master', {})
        return master_data.get('2fa_enabled', False)

    def generate_2fa_secret(self) -> str:
        """
        Generate a new TOTP secret for 2FA setup.

        Returns:
            Base32-encoded secret key
        """
        try:
            import pyotp
        except ImportError:
            raise AuthenticationError("2FA dependencies not installed. Please install pyotp.")

        return pyotp.random_base32()

    def enable_2fa(self, session_token: str, secret: str, verification_code: str) -> bool:
        """
        Enable 2FA for the authenticated user.

        Args:
            session_token: Valid session token
            secret: TOTP secret key
            verification_code: Current TOTP code for verification

        Returns:
            True if 2FA was successfully enabled

        Raises:
            AuthenticationError: If session invalid or verification fails
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        try:
            import pyotp
        except ImportError:
            raise AuthenticationError("2FA dependencies not installed. Please install pyotp.")

        # Verify the TOTP code
        totp = pyotp.TOTP(secret)
        if not totp.verify(verification_code):
            raise AuthenticationError("Invalid verification code")

        # Enable 2FA
        auth_data = self._load_auth_data()
        if 'master' not in auth_data:
            raise AuthenticationError("Master password not set")

        master_data = auth_data['master']
        master_data['2fa_enabled'] = True
        master_data['2fa_secret'] = secret
        master_data['2fa_backup_codes'] = self._generate_backup_codes()

        self._save_auth_data(auth_data)
        logger.info("2FA enabled successfully")
        return True

    def disable_2fa(self, session_token: str, password: str) -> bool:
        """
        Disable 2FA for the authenticated user.

        Args:
            session_token: Valid session token
            password: Master password for verification

        Returns:
            True if 2FA was successfully disabled

        Raises:
            AuthenticationError: If session invalid or password wrong
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        # Verify password
        try:
            self.authenticate_master_password(password)
        except AuthenticationError:
            raise AuthenticationError("Invalid password")

        # Disable 2FA
        auth_data = self._load_auth_data()
        master_data = auth_data.get('master', {})
        master_data['2fa_enabled'] = False
        master_data.pop('2fa_secret', None)
        master_data.pop('2fa_backup_codes', None)

        self._save_auth_data(auth_data)
        logger.info("2FA disabled successfully")
        return True

    def verify_2fa_code(self, code: str) -> bool:
        """
        Verify a 2FA code (TOTP or backup code).

        Args:
            code: TOTP code or backup code to verify

        Returns:
            True if code is valid
        """
        if not self.is_2fa_enabled():
            return True  # If 2FA not enabled, any code is "valid"

        auth_data = self._load_auth_data()
        master_data = auth_data.get('master', {})

        # Check if it's a backup code first
        backup_codes = master_data.get('2fa_backup_codes', [])
        if code in backup_codes:
            # Remove used backup code
            backup_codes.remove(code)
            master_data['2fa_backup_codes'] = backup_codes
            self._save_auth_data(auth_data)
            logger.info("2FA verified with backup code")
            return True

        # Check TOTP code
        secret = master_data.get('2fa_secret')
        if not secret:
            return False

        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(code)
            if is_valid:
                logger.info("2FA TOTP code verified successfully")
            return is_valid
        except ImportError:
            logger.error("2FA dependencies not installed")
            return False

    def get_2fa_setup_info(self, session_token: str) -> Dict:
        """
        Get 2FA setup information including QR code URI.

        Args:
            session_token: Valid session token

        Returns:
            Dictionary with setup information

        Raises:
            AuthenticationError: If session invalid
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        try:
            import pyotp
        except ImportError:
            raise AuthenticationError("2FA dependencies not installed. Please install pyotp.")

        secret = self.generate_2fa_secret()

        # Create TOTP URI for QR code
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name="FreedomUS Tax Return", issuer_name="FreedomUS")

        return {
            'secret': secret,
            'uri': uri,
            'backup_codes': self._generate_backup_codes()
        }

    def _generate_backup_codes(self) -> list:
        """Generate backup codes for 2FA recovery"""
        codes = []
        for _ in range(10):  # Generate 10 backup codes
            code = secrets.token_hex(4).upper()  # 8-character hex codes
            codes.append(code)
        return codes

    def authenticate_with_2fa(self, password: str, totp_code: Optional[str] = None) -> str:
        """
        Authenticate with password and optional 2FA code.

        Args:
            password: Master password
            totp_code: TOTP code (required if 2FA enabled)

        Returns:
            Session token on success

        Raises:
            AuthenticationError: If authentication fails
        """
        # First authenticate with password
        session_token = self.authenticate_master_password(password)

        # If 2FA is enabled, verify the code
        if self.is_2fa_enabled():
            if not totp_code:
                raise AuthenticationError("2FA code required")
            if not self.verify_2fa_code(totp_code):
                raise AuthenticationError("Invalid 2FA code")

        return session_token

    # ===== CLIENT MANAGEMENT METHODS =====

    def create_client_account(self, session_token: str, client_name: str, client_email: str,
                            client_ssn: str, password: str) -> str:
        """
        Create a new client account for tax professional management.

        Args:
            session_token: Valid session token of the tax professional
            client_name: Full name of the client
            client_email: Email address of the client
            client_ssn: Last 4 digits of client's SSN (for identification)
            password: Password for client account

        Returns:
            Client ID of the newly created account

        Raises:
            AuthenticationError: If session is invalid or client already exists
            PasswordPolicyError: If password doesn't meet requirements
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        # Validate password policy
        self._validate_password_policy(password)

        auth_data = self._load_auth_data()

        # Initialize clients section if it doesn't exist
        if 'clients' not in auth_data:
            auth_data['clients'] = {}

        # Check if client with this email already exists
        for client_id, client_data in auth_data['clients'].items():
            if client_data['email'] == client_email:
                raise AuthenticationError(f"Client with email {client_email} already exists")

        # Generate unique client ID
        client_id = f"client_{secrets.token_hex(8)}"

        # Hash the password
        salt = self._generate_salt()
        hashed_password = self._hash_password(password, salt)

        # Create client account
        auth_data['clients'][client_id] = {
            'name': client_name,
            'email': client_email,
            'ssn_last4': client_ssn,
            'password_hash': hashed_password,
            'salt': salt,
            'created_at': datetime.now().isoformat(),
            'created_by': user_id,
            'login_attempts': 0,
            'locked_until': None,
            'last_login': None,
            'is_active': True,
            'data_directory': f"client_data_{client_id}"
        }

        self._save_auth_data(auth_data)

        # Create client data directory
        client_data_dir = self.config.safe_dir / auth_data['clients'][client_id]['data_directory']
        client_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Client account created: {client_id} ({client_name})")
        return client_id

    def authenticate_client(self, client_email: str, password: str, totp_code: Optional[str] = None) -> Tuple[str, str]:
        """
        Authenticate a client account.

        Args:
            client_email: Client's email address
            password: Client's password
            totp_code: Optional 2FA code if enabled

        Returns:
            Tuple of (session_token, client_id)

        Raises:
            AuthenticationError: If authentication fails
        """
        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or not auth_data['clients']:
            raise AuthenticationError("No client accounts found")

        # Find client by email
        client_id = None
        client_data = None
        for cid, cdata in auth_data['clients'].items():
            if cdata['email'] == client_email:
                client_id = cid
                client_data = cdata
                break

        if not client_data:
            raise AuthenticationError("Client account not found")

        if not client_data.get('is_active', True):
            raise AuthenticationError("Client account is deactivated")

        # Check if account is locked
        if client_data.get('locked_until'):
            locked_until = datetime.fromisoformat(client_data['locked_until'])
            if datetime.now() < locked_until:
                raise AuthenticationError(f"Account locked until {locked_until}")
            else:
                # Clear lockout
                client_data['locked_until'] = None
                client_data['login_attempts'] = 0

        # Verify password
        hashed_input = self._hash_password(password, client_data['salt'])
        if not hmac.compare_digest(hashed_input, client_data['password_hash']):
            # Increment failed attempts
            client_data['login_attempts'] = client_data.get('login_attempts', 0) + 1

            if client_data['login_attempts'] >= self.max_login_attempts:
                # Lock account
                locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
                client_data['locked_until'] = locked_until.isoformat()

            self._save_auth_data(auth_data)
            raise AuthenticationError("Invalid password")

        # Reset login attempts on successful authentication
        client_data['login_attempts'] = 0
        client_data['last_login'] = datetime.now().isoformat()

        # Check if 2FA is enabled for this client
        if client_data.get('two_factor_enabled', False):
            if not totp_code:
                raise AuthenticationError("2FA code required")
            if not self._verify_client_2fa_code(client_id, totp_code):
                raise AuthenticationError("Invalid 2FA code")

        self._save_auth_data(auth_data)

        # Create session
        session_token = self._create_session(client_id)
        logger.info(f"Client authenticated: {client_id} ({client_data['name']})")

        return session_token, client_id

    def get_client_list(self, session_token: str) -> list:
        """
        Get list of all client accounts (for tax professionals).

        Args:
            session_token: Valid session token

        Returns:
            List of client information dictionaries

        Raises:
            AuthenticationError: If session is invalid
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data:
            return []

        clients = []
        for client_id, client_data in auth_data['clients'].items():
            clients.append({
                'id': client_id,
                'name': client_data['name'],
                'email': client_data['email'],
                'ssn_last4': client_data['ssn_last4'],
                'created_at': client_data['created_at'],
                'last_login': client_data.get('last_login'),
                'is_active': client_data.get('is_active', True),
                'two_factor_enabled': client_data.get('two_factor_enabled', False)
            })

        return clients

    def get_client_data_directory(self, client_id: str) -> Path:
        """
        Get the data directory path for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            Path to client's data directory

        Raises:
            AuthenticationError: If client doesn't exist
        """
        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        client_data = auth_data['clients'][client_id]
        return self.config.safe_dir / client_data['data_directory']

    def update_client_info(self, session_token: str, client_id: str,
                          name: Optional[str] = None, email: Optional[str] = None) -> None:
        """
        Update client account information.

        Args:
            session_token: Valid session token
            client_id: Client to update
            name: New name (optional)
            email: New email (optional)

        Raises:
            AuthenticationError: If session is invalid or client doesn't exist
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        client_data = auth_data['clients'][client_id]

        if name:
            client_data['name'] = name
        if email:
            # Check if email is already used by another client
            for cid, cdata in auth_data['clients'].items():
                if cid != client_id and cdata['email'] == email:
                    raise AuthenticationError(f"Email {email} already in use")
            client_data['email'] = email

        self._save_auth_data(auth_data)
        logger.info(f"Client info updated: {client_id}")

    def deactivate_client(self, session_token: str, client_id: str) -> None:
        """
        Deactivate a client account.

        Args:
            session_token: Valid session token
            client_id: Client to deactivate

        Raises:
            AuthenticationError: If session is invalid or client doesn't exist
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        auth_data['clients'][client_id]['is_active'] = False
        self._save_auth_data(auth_data)
        logger.info(f"Client deactivated: {client_id}")

    def activate_client(self, session_token: str, client_id: str) -> None:
        """
        Reactivate a client account.

        Args:
            session_token: Valid session token
            client_id: Client to activate

        Raises:
            AuthenticationError: If session is invalid or client doesn't exist
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        auth_data['clients'][client_id]['is_active'] = True
        self._save_auth_data(auth_data)
        logger.info(f"Client activated: {client_id}")

    def change_client_password(self, session_token: str, client_id: str, new_password: str) -> None:
        """
        Change a client's password (admin function).

        Args:
            session_token: Valid session token
            client_id: Client whose password to change
            new_password: New password

        Raises:
            AuthenticationError: If session is invalid or client doesn't exist
            PasswordPolicyError: If password doesn't meet requirements
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        # Validate password policy
        self._validate_password_policy(new_password)

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        client_data = auth_data['clients'][client_id]

        # Hash new password
        salt = self._generate_salt()
        hashed_password = self._hash_password(new_password, salt)

        client_data['password_hash'] = hashed_password
        client_data['salt'] = salt
        client_data['login_attempts'] = 0  # Reset failed attempts
        client_data['locked_until'] = None  # Clear any lockout

        self._save_auth_data(auth_data)
        logger.info(f"Client password changed: {client_id}")

    # ===== CLIENT 2FA METHODS =====

    def enable_client_2fa(self, session_token: str, client_id: str, secret: str, verification_code: str) -> bool:
        """
        Enable 2FA for a specific client account.

        Args:
            session_token: Valid session token
            client_id: Client to enable 2FA for
            secret: TOTP secret
            verification_code: Verification code from authenticator

        Returns:
            True if successful

        Raises:
            AuthenticationError: If session is invalid or verification fails
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        # Verify the code
        if not self._verify_client_2fa_setup(secret, verification_code):
            return False

        # Enable 2FA
        client_data = auth_data['clients'][client_id]
        client_data['two_factor_enabled'] = True
        client_data['two_factor_secret'] = secret
        client_data['backup_codes'] = self._generate_backup_codes()

        self._save_auth_data(auth_data)
        logger.info(f"2FA enabled for client: {client_id}")
        return True

    def disable_client_2fa(self, session_token: str, client_id: str) -> bool:
        """
        Disable 2FA for a specific client account.

        Args:
            session_token: Valid session token
            client_id: Client to disable 2FA for

        Returns:
            True if successful

        Raises:
            AuthenticationError: If session is invalid
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        client_data = auth_data['clients'][client_id]
        client_data['two_factor_enabled'] = False
        if 'two_factor_secret' in client_data:
            del client_data['two_factor_secret']
        if 'backup_codes' in client_data:
            del client_data['backup_codes']

        self._save_auth_data(auth_data)
        logger.info(f"2FA disabled for client: {client_id}")
        return True

    def get_client_2fa_setup_info(self, session_token: str, client_id: str) -> Dict[str, str]:
        """
        Get 2FA setup information for a client.

        Args:
            session_token: Valid session token
            client_id: Client to get setup info for

        Returns:
            Dictionary with 'secret' and 'uri' for QR code

        Raises:
            AuthenticationError: If session is invalid or client not found
        """
        # Validate session
        user_id = self.validate_session(session_token)
        if not user_id:
            raise AuthenticationError("Invalid session")

        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            raise AuthenticationError("Client not found")

        client_data = auth_data['clients'][client_id]

        # Generate new secret
        secret = self.generate_2fa_secret()

        # Create URI for QR code
        import pyotp
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=client_data['email'], issuer_name="FreedomUSTaxReturn")

        return {
            'secret': secret,
            'uri': uri
        }

    def _verify_client_2fa_code(self, client_id: str, code: str) -> bool:
        """Verify 2FA code for a client"""
        auth_data = self._load_auth_data()

        if 'clients' not in auth_data or client_id not in auth_data['clients']:
            return False

        client_data = auth_data['clients'][client_id]

        if not client_data.get('two_factor_enabled', False):
            return True  # 2FA not enabled, so any code is "valid"

        secret = client_data.get('two_factor_secret')
        if not secret:
            return False

        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def _verify_client_2fa_setup(self, secret: str, code: str) -> bool:
        """Verify 2FA setup code"""
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def _generate_backup_codes(self) -> list:
        """Generate backup codes for 2FA"""
        codes = []
        for _ in range(10):
            codes.append(secrets.token_hex(4).upper())
        return codes

    # PTIN/ERO Authentication Methods

    def authenticate_with_ptin(self, ptin: str, password: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Authenticate using PTIN credentials.

        Args:
            ptin: PTIN number
            password: Optional password for additional verification

        Returns:
            Tuple of (session_token, user_info)

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.ptin_ero_service:
            raise AuthenticationError("PTIN/ERO service not available")

        # Validate PTIN format
        if not self.ptin_ero_service.validate_ptin_format(ptin):
            raise AuthenticationError("Invalid PTIN format")

        # Get PTIN record
        ptin_record = self.ptin_ero_service.get_ptin_record(ptin)
        if not ptin_record:
            raise AuthenticationError("PTIN not found or not registered")

        # Check if PTIN is active
        if ptin_record.status != "active":
            raise AuthenticationError(f"PTIN is {ptin_record.status}")

        # If password is provided, validate it (optional additional security)
        if password:
            # For PTIN authentication, we could implement a separate password
            # or use the PTIN itself as a form of authentication
            # For now, we'll just validate the PTIN record exists and is active
            pass

        # Create session
        session_token = self._create_session({
            'user_type': 'professional',
            'ptin': ptin,
            'name': f"{ptin_record.first_name} {ptin_record.last_name}",
            'email': ptin_record.email,
            'role': 'tax_preparer'
        })

        user_info = {
            'user_type': 'professional',
            'ptin': ptin,
            'name': f"{ptin_record.first_name} {ptin_record.last_name}",
            'email': ptin_record.email,
            'role': 'tax_preparer'
        }

        return session_token, user_info

    def authenticate_with_ero(self, ero_number: str, ptin: str, password: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Authenticate using ERO credentials.

        Args:
            ero_number: ERO number
            ptin: Associated PTIN number
            password: Optional password for additional verification

        Returns:
            Tuple of (session_token, user_info)

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.ptin_ero_service:
            raise AuthenticationError("PTIN/ERO service not available")

        # Validate ERO format
        if not self.ptin_ero_service.validate_ero_format(ero_number):
            raise AuthenticationError("Invalid ERO number format")

        # Validate PTIN format
        if not self.ptin_ero_service.validate_ptin_format(ptin):
            raise AuthenticationError("Invalid PTIN format")

        # Get ERO record
        ero_record = self.ptin_ero_service.get_ero_record(ero_number)
        if not ero_record:
            raise AuthenticationError("ERO number not found or not registered")

        # Verify PTIN matches
        if ero_record.ptin.upper() != ptin.upper():
            raise AuthenticationError("PTIN does not match ERO record")

        # Check if ERO is active
        if ero_record.status != "active":
            raise AuthenticationError(f"ERO is {ero_record.status}")

        # Get associated PTIN record
        ptin_record = self.ptin_ero_service.get_ptin_record(ptin)
        if not ptin_record or ptin_record.status != "active":
            raise AuthenticationError("Associated PTIN is not active")

        # If password is provided, validate it (optional additional security)
        if password:
            # For ERO authentication, we could implement a separate password
            # For now, we'll just validate the ERO and PTIN records exist and are active
            pass

        # Create session
        session_token = self._create_session({
            'user_type': 'ero',
            'ero_number': ero_number,
            'ptin': ptin,
            'business_name': ero_record.business_name,
            'contact_name': ero_record.contact_name,
            'email': ero_record.email,
            'role': 'ero_administrator'
        })

        user_info = {
            'user_type': 'ero',
            'ero_number': ero_number,
            'ptin': ptin,
            'business_name': ero_record.business_name,
            'contact_name': ero_record.contact_name,
            'email': ero_record.email,
            'role': 'ero_administrator'
        }

        return session_token, user_info

    def validate_professional_credentials(self, ptin: Optional[str] = None, ero_number: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate professional credentials without creating a session.

        Args:
            ptin: PTIN number to validate
            ero_number: ERO number to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if not self.ptin_ero_service:
            return False, "PTIN/ERO service not available"

        try:
            if ptin:
                if not self.ptin_ero_service.validate_ptin_format(ptin):
                    return False, "Invalid PTIN format"

                ptin_record = self.ptin_ero_service.get_ptin_record(ptin)
                if not ptin_record:
                    return False, "PTIN not registered"

                if ptin_record.status != "active":
                    return False, f"PTIN is {ptin_record.status}"

            if ero_number:
                if not self.ptin_ero_service.validate_ero_format(ero_number):
                    return False, "Invalid ERO number format"

                ero_record = self.ptin_ero_service.get_ero_record(ero_number)
                if not ero_record:
                    return False, "ERO number not registered"

                if ero_record.status != "active":
                    return False, f"ERO is {ero_record.status}"

                # If both PTIN and ERO are provided, verify they match
                if ptin and ero_record.ptin.upper() != ptin.upper():
                    return False, "PTIN does not match ERO record"

            return True, "Credentials are valid"

        except Exception as e:
            return False, f"Validation error: {str(e)}"