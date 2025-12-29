"""
Application configuration with environment variable support

This module centralizes all configuration settings to improve maintainability
and make it easier to adjust settings for different environments.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """
    Application configuration settings.
    
    Can be customized via environment variables:
    - TAX_SAFE_DIR: Directory for storing tax returns
    - TAX_KEY_FILE: Path to encryption key file
    - TAX_YEAR: Current tax year
    - WINDOW_WIDTH: Application window width
    - WINDOW_HEIGHT: Application window height
    - ENCRYPTION_ENABLED: Enable/disable encryption (true/false)
    """
    
    # File storage paths
    safe_dir: Path = Path.home() / "Documents" / "TaxReturns"
    key_file: Path = Path.home() / ".tax_encryption_key"
    log_dir: Optional[Path] = None  # Defaults to safe_dir/logs
    
    # UI Settings
    window_width: int = 1200
    window_height: int = 800
    window_title: str = "Freedom US Tax Return - Free Tax Preparation"
    
    # Tax Year Settings
    tax_year: int = 2025
    
    # Security
    encryption_enabled: bool = True
    
    # Performance
    cache_calculations: bool = True
    cache_size: int = 128
    
    def __post_init__(self):
        """Set default log directory if not specified"""
        if self.log_dir is None:
            self.log_dir = self.safe_dir / "logs"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            AppConfig instance with settings from environment
            
        Example:
            >>> os.environ['TAX_YEAR'] = '2024'
            >>> config = AppConfig.from_env()
            >>> config.tax_year
            2024
        """
        return cls(
            safe_dir=Path(os.getenv("TAX_SAFE_DIR", cls.safe_dir)),
            key_file=Path(os.getenv("TAX_KEY_FILE", cls.key_file)),
            tax_year=int(os.getenv("TAX_YEAR", cls.tax_year)),
            window_width=int(os.getenv("WINDOW_WIDTH", cls.window_width)),
            window_height=int(os.getenv("WINDOW_HEIGHT", cls.window_height)),
            encryption_enabled=os.getenv("ENCRYPTION_ENABLED", "true").lower() == "true",
        )
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.safe_dir.mkdir(parents=True, exist_ok=True)
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)


# Global config instance (can be overridden for testing)
config = AppConfig.from_env()
