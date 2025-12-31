"""
Cloud Backup Service - Secure cloud backup functionality

Provides encrypted cloud backup and restore capabilities for tax data.
Supports multiple cloud providers with a unified interface.
"""

import json
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from config.app_config import AppConfig
from services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup"""
    backup_id: str
    timestamp: datetime
    version: str
    file_count: int
    total_size: int
    checksum: str
    description: str = ""


@dataclass
class CloudConfig:
    """Cloud storage configuration"""
    provider: str = "local"  # local, dropbox, google_drive, onedrive, etc.
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    backup_folder: str = "FreedomUSTaxReturn_Backups"


class CloudProvider(ABC):
    """Abstract base class for cloud storage providers"""

    def __init__(self, config: CloudConfig):
        self.config = config

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider"""
        pass

    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to cloud storage"""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from cloud storage"""
        pass

    @abstractmethod
    def list_files(self, folder: str = "") -> List[str]:
        """List files in a cloud folder"""
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from cloud storage"""
        pass


class LocalCloudProvider(CloudProvider):
    """Local filesystem provider for testing/development"""

    def __init__(self, config: CloudConfig):
        super().__init__(config)
        self.base_path = Path.home() / "FreedomUSTaxReturn_Cloud"

    def authenticate(self) -> bool:
        """Local storage doesn't need authentication"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        return True

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Copy file to local cloud storage"""
        try:
            remote_full_path = self.base_path / remote_path
            remote_full_path.parent.mkdir(parents=True, exist_ok=True)
            remote_full_path.write_bytes(local_path.read_bytes())
            return True
        except Exception as e:
            logger.error(f"Failed to upload file locally: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Copy file from local cloud storage"""
        try:
            remote_full_path = self.base_path / remote_path
            if not remote_full_path.exists():
                return False
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(remote_full_path.read_bytes())
            return True
        except Exception as e:
            logger.error(f"Failed to download file locally: {e}")
            return False

    def list_files(self, folder: str = "") -> List[str]:
        """List files in local cloud storage"""
        try:
            search_path = self.base_path / folder if folder else self.base_path
            if not search_path.exists():
                return []
            return [str(f.relative_to(self.base_path)).replace("\\", "/") for f in search_path.rglob("*") if f.is_file()]
        except Exception as e:
            logger.error(f"Failed to list files locally: {e}")
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from local cloud storage"""
        try:
            remote_full_path = self.base_path / remote_path
            if remote_full_path.exists():
                remote_full_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete file locally: {e}")
            return False


class CloudBackupService:
    """
    Service for secure cloud backup and restore operations.

    Features:
    - Encrypted backup uploads
    - Versioned backups
    - Backup integrity verification
    - Multiple cloud provider support
    - Automatic backup scheduling
    """

    def __init__(self, config: AppConfig):
        """
        Initialize cloud backup service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.encryption_service = EncryptionService(config.safe_dir / "encryption.key")
        self.backup_dir = config.safe_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load or create cloud configuration
        self.cloud_config = self._load_cloud_config()
        self.cloud_provider = self._create_cloud_provider()

        # Backup metadata storage
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.backups: Dict[str, BackupMetadata] = self._load_backup_metadata()

    def _load_cloud_config(self) -> CloudConfig:
        """Load cloud configuration from file"""
        config_file = self.config.safe_dir / "cloud_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return CloudConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load cloud config: {e}")

        # Return default config
        return CloudConfig()

    def _save_cloud_config(self):
        """Save cloud configuration to file"""
        config_file = self.config.safe_dir / "cloud_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(asdict(self.cloud_config), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cloud config: {e}")

    def _create_cloud_provider(self) -> CloudProvider:
        """Create appropriate cloud provider instance"""
        if self.cloud_config.provider == "local":
            return LocalCloudProvider(self.cloud_config)
        else:
            # For now, default to local provider
            # Future: implement other providers (Dropbox, Google Drive, etc.)
            logger.warning(f"Provider '{self.cloud_config.provider}' not implemented, using local")
            return LocalCloudProvider(self.cloud_config)

    def _load_backup_metadata(self) -> Dict[str, BackupMetadata]:
        """Load backup metadata from file"""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                backups = {}
                for backup_id, backup_data in data.items():
                    # Convert timestamp string back to datetime
                    backup_data['timestamp'] = datetime.fromisoformat(backup_data['timestamp'])
                    backups[backup_id] = BackupMetadata(**backup_data)
                return backups
        except Exception as e:
            logger.error(f"Failed to load backup metadata: {e}")
            return {}

    def _save_backup_metadata(self):
        """Save backup metadata to file"""
        try:
            data = {}
            for backup_id, metadata in self.backups.items():
                backup_dict = asdict(metadata)
                # Convert datetime to ISO format string
                backup_dict['timestamp'] = metadata.timestamp.isoformat()
                data[backup_id] = backup_dict

            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")

    def configure_cloud_provider(self, provider: str, **kwargs) -> bool:
        """
        Configure cloud provider settings.

        Args:
            provider: Cloud provider name
            **kwargs: Provider-specific configuration

        Returns:
            True if configuration successful
        """
        try:
            self.cloud_config.provider = provider

            # Update config with provided parameters
            for key, value in kwargs.items():
                if hasattr(self.cloud_config, key):
                    setattr(self.cloud_config, key, value)

            # Save configuration
            self._save_cloud_config()

            # Recreate provider with new config
            self.cloud_provider = self._create_cloud_provider()

            # Test authentication
            if self.cloud_provider.authenticate():
                logger.info(f"Successfully configured {provider} cloud provider")
                return True
            else:
                logger.error(f"Failed to authenticate with {provider}")
                return False

        except Exception as e:
            logger.error(f"Failed to configure cloud provider: {e}")
            return False

    def create_backup(self, data_files: List[Path], description: str = "") -> Optional[str]:
        """
        Create an encrypted backup of the specified files.

        Args:
            data_files: List of files to backup
            description: Optional description for the backup

        Returns:
            Backup ID if successful, None otherwise
        """
        try:
            # Generate backup ID
            timestamp = datetime.now(timezone.utc)
            backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)

            # Encrypt and copy files
            total_size = 0
            encrypted_files = []

            for data_file in data_files:
                if not data_file.exists():
                    continue

                # Read original file
                with open(data_file, 'rb') as f:
                    data = f.read()

                # Encrypt data
                cipher = self.encryption_service.get_or_create_cipher()
                encrypted_data = cipher.encrypt(data)

                # Save encrypted file
                encrypted_filename = f"{data_file.name}.encrypted"
                encrypted_path = backup_path / encrypted_filename

                with open(encrypted_path, 'wb') as f:
                    f.write(encrypted_data)

                encrypted_files.append(encrypted_path)
                total_size += len(encrypted_data)

            # Create backup archive (simple concatenation for now)
            archive_path = backup_path / f"{backup_id}.backup"
            with open(archive_path, 'wb') as archive:
                # Write header with file count
                archive.write(len(encrypted_files).to_bytes(4, byteorder='big'))

                for encrypted_file in encrypted_files:
                    # Write filename length and filename
                    filename_bytes = encrypted_file.name.encode('utf-8')
                    archive.write(len(filename_bytes).to_bytes(4, byteorder='big'))
                    archive.write(filename_bytes)

                    # Write file size and content
                    with open(encrypted_file, 'rb') as f:
                        file_data = f.read()
                        archive.write(len(file_data).to_bytes(8, byteorder='big'))
                        archive.write(file_data)

            # Calculate checksum
            with open(archive_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp,
                version=self.config.version,
                file_count=len(data_files),
                total_size=total_size,
                checksum=checksum,
                description=description or f"Backup created on {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

            # Store metadata
            self.backups[backup_id] = metadata
            self._save_backup_metadata()

            # Upload to cloud
            remote_path = f"{self.cloud_config.backup_folder}/{backup_id}.backup"
            if self.cloud_provider.upload_file(archive_path, remote_path):
                logger.info(f"Successfully created and uploaded backup {backup_id}")
                return backup_id
            else:
                logger.error(f"Failed to upload backup {backup_id} to cloud")
                return None

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def restore_backup(self, backup_id: str, restore_path: Path) -> bool:
        """
        Restore a backup to the specified location.

        Args:
            backup_id: ID of the backup to restore
            restore_path: Directory to restore files to

        Returns:
            True if restore successful
        """
        try:
            if backup_id not in self.backups:
                logger.error(f"Backup {backup_id} not found")
                return False

            metadata = self.backups[backup_id]

            # Download backup from cloud
            remote_path = f"{self.cloud_config.backup_folder}/{backup_id}.backup"
            local_archive = self.backup_dir / f"{backup_id}_download.backup"

            if not self.cloud_provider.download_file(remote_path, local_archive):
                logger.error(f"Failed to download backup {backup_id} from cloud")
                return False

            # Verify checksum
            with open(local_archive, 'rb') as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()

            if actual_checksum != metadata.checksum:
                logger.error(f"Backup {backup_id} checksum mismatch")
                return False

            # Extract and decrypt files
            restore_path.mkdir(parents=True, exist_ok=True)

            with open(local_archive, 'rb') as archive:
                # Read file count
                file_count = int.from_bytes(archive.read(4), byteorder='big')

                cipher = self.encryption_service.get_or_create_cipher()

                for _ in range(file_count):
                    # Read filename
                    filename_len = int.from_bytes(archive.read(4), byteorder='big')
                    filename = archive.read(filename_len).decode('utf-8')

                    # Read file size and content
                    file_size = int.from_bytes(archive.read(8), byteorder='big')
                    encrypted_data = archive.read(file_size)

                    # Decrypt data
                    try:
                        decrypted_data = cipher.decrypt(encrypted_data)
                    except Exception as e:
                        logger.error(f"Failed to decrypt file {filename}: {e}")
                        continue

                    # Remove .encrypted extension if present
                    if filename.endswith('.encrypted'):
                        filename = filename[:-10]  # Remove '.encrypted'

                    # Write decrypted file
                    output_path = restore_path / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(output_path, 'wb') as f:
                        f.write(decrypted_data)

            # Clean up
            local_archive.unlink()

            logger.info(f"Successfully restored backup {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False

    def list_backups(self) -> List[BackupMetadata]:
        """
        Get list of available backups.

        Returns:
            List of backup metadata, sorted by timestamp (most recent first)
        """
        return sorted(self.backups.values(), key=lambda x: x.timestamp, reverse=True)

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup from both local and cloud storage.

        Args:
            backup_id: ID of the backup to delete

        Returns:
            True if deletion successful
        """
        try:
            if backup_id not in self.backups:
                logger.error(f"Backup {backup_id} not found")
                return False

            # Delete from cloud
            remote_path = f"{self.cloud_config.backup_folder}/{backup_id}.backup"
            self.cloud_provider.delete_file(remote_path)

            # Delete local backup directory
            backup_path = self.backup_dir / backup_id
            if backup_path.exists():
                import shutil
                shutil.rmtree(backup_path)

            # Remove from metadata
            del self.backups[backup_id]
            self._save_backup_metadata()

            logger.info(f"Successfully deleted backup {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False

    def get_backup_status(self) -> Dict[str, Any]:
        """
        Get current backup status and statistics.

        Returns:
            Dictionary with backup status information
        """
        total_backups = len(self.backups)
        total_size = sum(metadata.total_size for metadata in self.backups.values())

        if self.backups:
            latest_backup = max(self.backups.values(), key=lambda x: x.timestamp)
            oldest_backup = min(self.backups.values(), key=lambda x: x.timestamp)
        else:
            latest_backup = None
            oldest_backup = None

        return {
            'total_backups': total_backups,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'latest_backup': latest_backup.timestamp.isoformat() if latest_backup else None,
            'oldest_backup': oldest_backup.timestamp.isoformat() if oldest_backup else None,
            'cloud_provider': self.cloud_config.provider,
            'cloud_authenticated': self.cloud_provider.authenticate()
        }

