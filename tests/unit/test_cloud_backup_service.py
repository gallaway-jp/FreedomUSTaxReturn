"""
Unit tests for Cloud Backup Service
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from services.cloud_backup_service import (
    CloudBackupService, BackupMetadata, CloudConfig, LocalCloudProvider
)
from config.app_config import AppConfig


class TestCloudBackupService:
    """Unit tests for cloud backup service"""

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
    def backup_service(self, config):
        """Create cloud backup service instance"""
        service = CloudBackupService(config)
        # Clear any existing backups for clean test state
        service.backups = {}
        service._save_backup_metadata()
        return service

    def test_initialization(self, backup_service, config):
        """Test service initialization"""
        assert backup_service.config == config
        assert backup_service.cloud_config.provider == "local"
        assert isinstance(backup_service.cloud_provider, LocalCloudProvider)
        assert backup_service.backups == {}

    def test_configure_cloud_provider(self, backup_service):
        """Test cloud provider configuration"""
        # Test local provider configuration
        success = backup_service.configure_cloud_provider("local", backup_folder="test_folder")
        assert success
        assert backup_service.cloud_config.provider == "local"
        assert backup_service.cloud_config.backup_folder == "test_folder"

    def test_create_backup(self, backup_service, config, tmp_path):
        """Test backup creation"""
        # Create test files
        test_file1 = tmp_path / "test1.json"
        test_file1.write_text('{"test": "data1"}')

        test_file2 = tmp_path / "test2.json"
        test_file2.write_text('{"test": "data2"}')

        # Create backup
        backup_id = backup_service.create_backup([test_file1, test_file2], "Test backup")

        assert backup_id is not None
        assert backup_id in backup_service.backups

        metadata = backup_service.backups[backup_id]
        assert metadata.backup_id == backup_id
        assert metadata.file_count == 2
        assert metadata.description == "Test backup"
        assert metadata.checksum is not None

    def test_restore_backup(self, backup_service, config, tmp_path):
        """Test backup restoration"""
        # Create test files
        test_file1 = tmp_path / "test1.json"
        test_file1.write_text('{"test": "data1"}')

        test_file2 = tmp_path / "test2.json"
        test_file2.write_text('{"test": "data2"}')

        # Create backup
        backup_id = backup_service.create_backup([test_file1, test_file2], "Test backup")
        assert backup_id is not None

        # Restore to different location
        restore_dir = tmp_path / "restore"
        success = backup_service.restore_backup(backup_id, restore_dir)

        assert success

        # Check restored files
        restored_file1 = restore_dir / "test1.json"
        restored_file2 = restore_dir / "test2.json"

        assert restored_file1.exists()
        assert restored_file2.exists()
        assert restored_file1.read_text() == '{"test": "data1"}'
        assert restored_file2.read_text() == '{"test": "data2"}'

    def test_list_backups(self, backup_service, config, tmp_path):
        """Test backup listing"""
        # Create test files
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        # Create multiple backups
        backup_id1 = backup_service.create_backup([test_file], "Backup 1")
        backup_id2 = backup_service.create_backup([test_file], "Backup 2")

        backups = backup_service.list_backups()
        assert len(backups) == 2

        # Check ordering (most recent first)
        assert backups[0].backup_id == backup_id2
        assert backups[1].backup_id == backup_id1

    def test_delete_backup(self, backup_service, config, tmp_path):
        """Test backup deletion"""
        # Create test file and backup
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        backup_id = backup_service.create_backup([test_file], "Test backup")
        assert backup_id in backup_service.backups

        # Delete backup
        success = backup_service.delete_backup(backup_id)
        assert success
        assert backup_id not in backup_service.backups

    def test_get_backup_status(self, backup_service, config, tmp_path):
        """Test backup status retrieval"""
        # Create test file and backup (make it larger so total_size_mb > 0)
        test_file = tmp_path / "test.json"
        test_content = '{"test": "data"}' * 1000  # Make file larger
        test_file.write_text(test_content)

        backup_id = backup_service.create_backup([test_file], "Test backup")

        status = backup_service.get_backup_status()

        assert status['total_backups'] == 1
        assert status['total_size_mb'] > 0
        assert status['cloud_provider'] == 'local'
        assert status['cloud_authenticated'] is True
        assert status['latest_backup'] is not None
        assert status['oldest_backup'] is not None

    def test_backup_metadata_serialization(self, backup_service):
        """Test backup metadata serialization"""
        # Create test metadata
        timestamp = datetime.now(timezone.utc)
        metadata = BackupMetadata(
            backup_id="test_backup_123",
            timestamp=timestamp,
            version="1.0.0",
            file_count=5,
            total_size=1024000,
            checksum="abc123",
            description="Test backup"
        )

        backup_service.backups["test_backup_123"] = metadata
        backup_service._save_backup_metadata()

        # Create new service instance to test loading
        new_service = CloudBackupService(backup_service.config)
        assert "test_backup_123" in new_service.backups

        loaded_metadata = new_service.backups["test_backup_123"]
        assert loaded_metadata.backup_id == metadata.backup_id
        assert loaded_metadata.file_count == metadata.file_count
        assert loaded_metadata.description == metadata.description

    def test_cloud_config_persistence(self, backup_service):
        """Test cloud configuration persistence"""
        # Configure provider
        backup_service.configure_cloud_provider("local", backup_folder="custom_folder")

        # Create new service instance
        new_service = CloudBackupService(backup_service.config)
        assert new_service.cloud_config.backup_folder == "custom_folder"


class TestLocalCloudProvider:
    """Unit tests for local cloud provider"""

    @pytest.fixture
    def config(self):
        """Create test cloud config"""
        return CloudConfig(provider="local", backup_folder="test_backups")

    @pytest.fixture
    def provider(self, config, tmp_path):
        """Create local cloud provider"""
        provider = LocalCloudProvider(config)
        # Override base path for testing
        provider.base_path = tmp_path / "cloud_storage"
        provider.base_path.mkdir(parents=True)
        return provider

    def test_authenticate(self, provider):
        """Test authentication"""
        assert provider.authenticate()

    def test_upload_download_file(self, provider, tmp_path):
        """Test file upload and download"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        # Upload file
        success = provider.upload_file(test_file, "test.txt")
        assert success

        # Download file
        download_path = tmp_path / "downloaded.txt"
        success = provider.download_file("test.txt", download_path)
        assert success

        # Verify content
        assert download_path.read_text() == test_content

    def test_list_files(self, provider, tmp_path):
        """Test file listing"""
        # Create test files
        test_file1 = provider.base_path / "folder1" / "file1.txt"
        test_file1.parent.mkdir(parents=True)
        test_file1.write_text("content1")

        test_file2 = provider.base_path / "folder2" / "file2.txt"
        test_file2.parent.mkdir(parents=True)
        test_file2.write_text("content2")

        files = provider.list_files()
        assert len(files) == 2
        assert "folder1/file1.txt" in files
        assert "folder2/file2.txt" in files

    def test_delete_file(self, provider):
        """Test file deletion"""
        # Create test file
        test_file = provider.base_path / "test.txt"
        test_file.write_text("content")

        # Delete file
        success = provider.delete_file("test.txt")
        assert success
        assert not test_file.exists()


class TestBackupMetadata:
    """Unit tests for BackupMetadata dataclass"""

    def test_backup_metadata_creation(self):
        """Test backup metadata creation"""
        timestamp = datetime.now(timezone.utc)
        metadata = BackupMetadata(
            backup_id="test_123",
            timestamp=timestamp,
            version="1.0.0",
            file_count=3,
            total_size=1024,
            checksum="abc123",
            description="Test backup"
        )

        assert metadata.backup_id == "test_123"
        assert metadata.timestamp == timestamp
        assert metadata.version == "1.0.0"
        assert metadata.file_count == 3
        assert metadata.total_size == 1024
        assert metadata.checksum == "abc123"
        assert metadata.description == "Test backup"

    def test_backup_metadata_serialization(self):
        """Test backup metadata JSON serialization"""
        timestamp = datetime.now(timezone.utc)
        metadata = BackupMetadata(
            backup_id="test_123",
            timestamp=timestamp,
            version="1.0.0",
            file_count=3,
            total_size=1024,
            checksum="abc123"
        )

        # Test conversion to dict
        data = {
            'backup_id': metadata.backup_id,
            'timestamp': metadata.timestamp.isoformat(),
            'version': metadata.version,
            'file_count': metadata.file_count,
            'total_size': metadata.total_size,
            'checksum': metadata.checksum,
            'description': metadata.description
        }

        # Test conversion back
        restored = BackupMetadata(**data)
        assert restored.backup_id == metadata.backup_id
        assert restored.file_count == metadata.file_count
        assert restored.description == metadata.description

