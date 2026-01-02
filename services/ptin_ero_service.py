"""
PTIN/ERO Integration Service

Handles Professional Tax Preparer authentication and Electronic Return Originator (ERO) support
for IRS e-filing compliance. Manages PTIN validation, ERO credentials, and professional
authentication workflows.
"""

import re
import json
import hashlib
from typing import Dict, Optional, List, Tuple
from datetime import datetime, date
from dataclasses import dataclass, asdict
from pathlib import Path

from config.app_config import AppConfig
from services.encryption_service import EncryptionService
from utils.error_tracker import get_error_tracker
from services.exceptions import (
    InvalidInputException,
    DataValidationException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger


@dataclass
class PTINRecord:
    """Represents a validated PTIN record"""
    ptin: str
    first_name: str
    last_name: str
    middle_initial: Optional[str] = None
    suffix: Optional[str] = None
    address: Dict[str, str] = None
    phone: Optional[str] = None
    email: str = ""
    status: str = "active"  # active, inactive, expired
    validation_date: Optional[date] = None
    expiration_date: Optional[date] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.address is None:
            self.address = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert dates to ISO format strings
        if self.validation_date:
            data['validation_date'] = self.validation_date.isoformat()
        if self.expiration_date:
            data['expiration_date'] = self.expiration_date.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'PTINRecord':
        """Create from dictionary"""
        # Convert ISO date strings back to date objects
        if 'validation_date' in data and data['validation_date']:
            data['validation_date'] = date.fromisoformat(data['validation_date'])
        if 'expiration_date' in data and data['expiration_date']:
            data['expiration_date'] = date.fromisoformat(data['expiration_date'])
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class ERORecord:
    """Represents an Electronic Return Originator record"""
    ero_number: str
    business_name: str
    ein: str  # Employer Identification Number
    ptin: str  # Associated PTIN
    address: Dict[str, str] = None
    phone: str = ""
    email: str = ""
    contact_name: str = ""
    contact_title: Optional[str] = None
    status: str = "active"  # active, inactive, suspended
    validation_date: Optional[date] = None
    expiration_date: Optional[date] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.address is None:
            self.address = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert dates to ISO format strings
        if self.validation_date:
            data['validation_date'] = self.validation_date.isoformat()
        if self.expiration_date:
            data['expiration_date'] = self.expiration_date.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'ERORecord':
        """Create from dictionary"""
        # Convert ISO date strings back to date objects
        if 'validation_date' in data and data['validation_date']:
            data['validation_date'] = date.fromisoformat(data['validation_date'])
        if 'expiration_date' in data and data['expiration_date']:
            data['expiration_date'] = date.fromisoformat(data['expiration_date'])
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class PTINEROService:
    """
    Service for managing PTIN (Practitioner PIN) and ERO (Electronic Return Originator)
    credentials for professional tax preparers.
    """

    def __init__(self, config: AppConfig, encryption_service: EncryptionService):
        """
        Initialize the PTIN/ERO service.

        Args:
            config: Application configuration
            encryption_service: Service for encrypting sensitive data
        """
        self.config = config
        self.encryption = encryption_service
        self.error_tracker = get_error_tracker()

        # Storage paths
        self.data_dir = Path(config.safe_dir) / "ptin_ero"
        self.ptin_file = self.data_dir / "ptin_records.json"
        self.ero_file = self.data_dir / "ero_records.json"

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory caches
        self._ptin_cache: Dict[str, PTINRecord] = {}
        self._ero_cache: Dict[str, ERORecord] = {}

        # Load existing data
        self._load_ptin_records()
        self._load_ero_records()

    def _load_ptin_records(self) -> None:
        """Load PTIN records from encrypted storage"""
        if not self.ptin_file.exists():
            return

        try:
            with open(self.ptin_file, 'rb') as f:
                encrypted_data = f.read()

            if encrypted_data:
                decrypted_data = self.encryption.decrypt(encrypted_data)
                records_data = json.loads(decrypted_data)

                for record_data in records_data:
                    record = PTINRecord.from_dict(record_data)
                    self._ptin_cache[record.ptin] = record

        except Exception as e:
            # Log the error but don't crash - just start with empty cache
            self.error_tracker.track_error(
                error=e,
                context={"file": str(self.ptin_file), "action": "loading PTIN records"}
            )
            # Clear any partial data and start fresh
            self._ptin_cache.clear()

    def _save_ptin_records(self) -> None:
        """Save PTIN records to encrypted storage"""
        try:
            records_data = [record.to_dict() for record in self._ptin_cache.values()]
            json_data = json.dumps(records_data, indent=2, ensure_ascii=False)
            encrypted_data = self.encryption.encrypt(json_data)

            with open(self.ptin_file, 'wb') as f:
                f.write(encrypted_data)

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"file": str(self.ptin_file)}
            )
            raise

    def _load_ero_records(self) -> None:
        """Load ERO records from encrypted storage"""
        if not self.ero_file.exists():
            return

        try:
            with open(self.ero_file, 'rb') as f:
                encrypted_data = f.read()

            if encrypted_data:
                decrypted_data = self.encryption.decrypt(encrypted_data)
                records_data = json.loads(decrypted_data)

                for record_data in records_data:
                    record = ERORecord.from_dict(record_data)
                    self._ero_cache[record.ero_number] = record

        except Exception as e:
            # Log the error but don't crash - just start with empty cache
            self.error_tracker.track_error(
                error=e,
                context={"file": str(self.ero_file), "action": "loading ERO records"}
            )
            # Clear any partial data and start fresh
            self._ero_cache.clear()

    def _save_ero_records(self) -> None:
        """Save ERO records to encrypted storage"""
        try:
            records_data = [record.to_dict() for record in self._ero_cache.values()]
            json_data = json.dumps(records_data, indent=2, ensure_ascii=False)
            encrypted_data = self.encryption.encrypt(json_data)

            with open(self.ero_file, 'wb') as f:
                f.write(encrypted_data)

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"file": str(self.ero_file)}
            )
            raise

    @staticmethod
    def validate_ptin_format(ptin: str) -> bool:
        """
        Validate PTIN format.

        PTIN format: P followed by 8 digits (e.g., P12345678)

        Args:
            ptin: PTIN to validate

        Returns:
            True if format is valid
        """
        if not ptin or not isinstance(ptin, str):
            return False

        # PTIN pattern: P followed by exactly 8 digits
        pattern = r'^P\d{8}$'
        return bool(re.match(pattern, ptin.strip().upper()))

    @staticmethod
    def validate_ero_format(ero_number: str) -> bool:
        """
        Validate ERO number format.

        ERO format: Typically 6 digits, but can vary by state/tax authority

        Args:
            ero_number: ERO number to validate

        Returns:
            True if format is valid
        """
        if not ero_number or not isinstance(ero_number, str):
            return False

        # ERO pattern: 4-8 digits (can vary by jurisdiction)
        pattern = r'^\d{4,8}$'
        return bool(re.match(pattern, ero_number.strip()))

    @staticmethod
    def validate_ein_format(ein: str) -> bool:
        """
        Validate EIN (Employer Identification Number) format.

        EIN format: XX-XXXXXXX

        Args:
            ein: EIN to validate

        Returns:
            True if format is valid
        """
        if not ein or not isinstance(ein, str):
            return False

        # Remove hyphens and spaces for validation
        clean_ein = re.sub(r'[- ]', '', ein.strip())

        # EIN pattern: exactly 9 digits
        if not re.match(r'^\d{9}$', clean_ein):
            return False

        # Format should be XX-XXXXXXX
        formatted = f"{clean_ein[:2]}-{clean_ein[2:]}"
        return formatted == ein.strip()

    def register_ptin(self, ptin_data: Dict) -> PTINRecord:
        """
        Register a new PTIN record.

        Args:
            ptin_data: Dictionary containing PTIN information

        Returns:
            Created PTINRecord

        Raises:
            ValueError: If PTIN format is invalid or already exists
        """
        ptin = ptin_data.get('ptin', '').strip().upper()

        if not self.validate_ptin_format(ptin):
            raise ValueError(f"Invalid PTIN format: {ptin}")

        if ptin in self._ptin_cache:
            raise ValueError(f"PTIN already registered: {ptin}")

        # Create PTIN record
        record = PTINRecord(
            ptin=ptin,
            first_name=ptin_data.get('first_name', '').strip(),
            last_name=ptin_data.get('last_name', '').strip(),
            middle_initial=ptin_data.get('middle_initial', '').strip() or None,
            suffix=ptin_data.get('suffix', '').strip() or None,
            address=ptin_data.get('address', {}),
            phone=ptin_data.get('phone', '').strip() or None,
            email=ptin_data.get('email', '').strip(),
            validation_date=date.today()
        )

        # Validate required fields
        if not record.first_name or not record.last_name or not record.email:
            raise ValueError("First name, last name, and email are required")

        # Store in cache and save
        self._ptin_cache[ptin] = record
        self._save_ptin_records()

        return record

    def get_ptin_record(self, ptin: str) -> Optional[PTINRecord]:
        """
        Get PTIN record by PTIN number.

        Args:
            ptin: PTIN to look up

        Returns:
            PTINRecord if found, None otherwise
        """
        return self._ptin_cache.get(ptin.strip().upper())

    def update_ptin_record(self, ptin: str, updates: Dict) -> PTINRecord:
        """
        Update an existing PTIN record.

        Args:
            ptin: PTIN to update
            updates: Dictionary of fields to update

        Returns:
            Updated PTINRecord

        Raises:
            ValueError: If PTIN not found
        """
        ptin = ptin.strip().upper()
        record = self._ptin_cache.get(ptin)

        if not record:
            raise ValueError(f"PTIN not found: {ptin}")

        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'middle_initial', 'suffix',
                         'address', 'phone', 'email', 'status']

        for field, value in updates.items():
            if field in allowed_fields:
                if field in ['first_name', 'last_name', 'email']:
                    value = value.strip() if value else ""
                    if not value:
                        raise ValueError(f"{field} cannot be empty")
                elif field in ['middle_initial', 'suffix', 'phone']:
                    value = value.strip() if value else None
                setattr(record, field, value)

        record.updated_at = datetime.now()

        # Save changes
        self._save_ptin_records()

        return record

    def deactivate_ptin(self, ptin: str) -> None:
        """
        Deactivate a PTIN record.

        Args:
            ptin: PTIN to deactivate

        Raises:
            ValueError: If PTIN not found
        """
        ptin = ptin.strip().upper()
        record = self._ptin_cache.get(ptin)

        if not record:
            raise ValueError(f"PTIN not found: {ptin}")

        record.status = "inactive"
        record.updated_at = datetime.now()

        self._save_ptin_records()

    def get_all_ptins(self) -> List[PTINRecord]:
        """
        Get all PTIN records.

        Returns:
            List of all PTIN records
        """
        return list(self._ptin_cache.values())

    def register_ero(self, ero_data: Dict) -> ERORecord:
        """
        Register a new ERO record.

        Args:
            ero_data: Dictionary containing ERO information

        Returns:
            Created ERORecord

        Raises:
            ValueError: If ERO format is invalid or already exists
        """
        ero_number = ero_data.get('ero_number', '').strip()
        ein = ero_data.get('ein', '').strip()
        ptin = ero_data.get('ptin', '').strip().upper()

        if not self.validate_ero_format(ero_number):
            raise ValueError(f"Invalid ERO number format: {ero_number}")

        if not self.validate_ein_format(ein):
            raise ValueError(f"Invalid EIN format: {ein}")

        if not self.validate_ptin_format(ptin):
            raise ValueError(f"Invalid PTIN format: {ptin}")

        if ero_number in self._ero_cache:
            raise ValueError(f"ERO number already registered: {ero_number}")

        # Verify PTIN exists
        if ptin not in self._ptin_cache:
            raise ValueError(f"Associated PTIN not found: {ptin}")

        # Create ERO record
        record = ERORecord(
            ero_number=ero_number,
            business_name=ero_data.get('business_name', '').strip(),
            ein=ein,
            ptin=ptin,
            address=ero_data.get('address', {}),
            phone=ero_data.get('phone', '').strip(),
            email=ero_data.get('email', '').strip(),
            contact_name=ero_data.get('contact_name', '').strip(),
            contact_title=ero_data.get('contact_title', '').strip() or None,
            validation_date=date.today()
        )

        # Validate required fields
        if not record.business_name or not record.contact_name or not record.email:
            raise ValueError("Business name, contact name, and email are required")

        # Store in cache and save
        self._ero_cache[ero_number] = record
        self._save_ero_records()

        return record

    def get_ero_record(self, ero_number: str) -> Optional[ERORecord]:
        """
        Get ERO record by ERO number.

        Args:
            ero_number: ERO number to look up

        Returns:
            ERORecord if found, None otherwise
        """
        return self._ero_cache.get(ero_number.strip())

    def update_ero_record(self, ero_number: str, updates: Dict) -> ERORecord:
        """
        Update an existing ERO record.

        Args:
            ero_number: ERO number to update
            updates: Dictionary of fields to update

        Returns:
            Updated ERORecord

        Raises:
            ValueError: If ERO not found
        """
        ero_number = ero_number.strip()
        record = self._ero_cache.get(ero_number)

        if not record:
            raise ValueError(f"ERO not found: {ero_number}")

        # Update allowed fields
        allowed_fields = ['business_name', 'ein', 'ptin', 'address', 'phone',
                         'email', 'contact_name', 'contact_title', 'status']

        for field, value in updates.items():
            if field in allowed_fields:
                if field in ['business_name', 'contact_name', 'email']:
                    value = value.strip() if value else ""
                    if not value:
                        raise ValueError(f"{field} cannot be empty")
                elif field in ['contact_title', 'phone']:
                    value = value.strip() if value else None
                elif field == 'ein':
                    if not self.validate_ein_format(value):
                        raise ValueError(f"Invalid EIN format: {value}")
                elif field == 'ptin':
                    value = value.strip().upper()
                    if not self.validate_ptin_format(value):
                        raise ValueError(f"Invalid PTIN format: {value}")
                    if value not in self._ptin_cache:
                        raise ValueError(f"PTIN not found: {value}")
                setattr(record, field, value)

        record.updated_at = datetime.now()

        # Save changes
        self._save_ero_records()

        return record

    def deactivate_ero(self, ero_number: str) -> None:
        """
        Deactivate an ERO record.

        Args:
            ero_number: ERO number to deactivate

        Raises:
            ValueError: If ERO not found
        """
        ero_number = ero_number.strip()
        record = self._ero_cache.get(ero_number)

        if not record:
            raise ValueError(f"ERO not found: {ero_number}")

        record.status = "inactive"
        record.updated_at = datetime.now()

        self._save_ero_records()

    def get_all_eros(self) -> List[ERORecord]:
        """
        Get all ERO records.

        Returns:
            List of all ERO records
        """
        return list(self._ero_cache.values())

    def get_eros_by_ptin(self, ptin: str) -> List[ERORecord]:
        """
        Get all ERO records associated with a PTIN.

        Args:
            ptin: PTIN to search for

        Returns:
            List of ERO records associated with the PTIN
        """
        ptin = ptin.strip().upper()
        return [ero for ero in self._ero_cache.values() if ero.ptin == ptin]

    def validate_professional_credentials(self, ptin: str, ero_number: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate professional credentials for e-filing.

        Args:
            ptin: PTIN to validate
            ero_number: Optional ERO number to validate

        Returns:
            Tuple of (is_valid, message)
        """
        ptin = ptin.strip().upper() if ptin else ""

        # Validate PTIN
        if not self.validate_ptin_format(ptin):
            return False, f"Invalid PTIN format: {ptin}"

        ptin_record = self._ptin_cache.get(ptin)
        if not ptin_record:
            return False, f"PTIN not registered: {ptin}"

        if ptin_record.status != "active":
            return False, f"PTIN is not active: {ptin}"

        # Check expiration if set
        if ptin_record.expiration_date and ptin_record.expiration_date < date.today():
            return False, f"PTIN has expired: {ptin}"

        # Validate ERO if provided
        if ero_number:
            ero_number = ero_number.strip()
            if not self.validate_ero_format(ero_number):
                return False, f"Invalid ERO number format: {ero_number}"

            ero_record = self._ero_cache.get(ero_number)
            if not ero_record:
                return False, f"ERO number not registered: {ero_number}"

            if ero_record.status != "active":
                return False, f"ERO is not active: {ero_number}"

            if ero_record.ptin != ptin:
                return False, f"ERO {ero_number} is not associated with PTIN {ptin}"

            # Check expiration if set
            if ero_record.expiration_date and ero_record.expiration_date < date.today():
                return False, f"ERO has expired: {ero_number}"

        return True, "Professional credentials are valid"

    def get_professional_info(self, ptin: str) -> Optional[Dict]:
        """
        Get complete professional information for a PTIN.

        Args:
            ptin: PTIN to look up

        Returns:
            Dictionary with PTIN and associated ERO information, or None if not found
        """
        ptin = ptin.strip().upper() if ptin else ""
        ptin_record = self._ptin_cache.get(ptin)

        if not ptin_record:
            return None

        # Get associated EROs
        eros = self.get_eros_by_ptin(ptin)

        return {
            'ptin': ptin_record.to_dict(),
            'eros': [ero.to_dict() for ero in eros]
        }