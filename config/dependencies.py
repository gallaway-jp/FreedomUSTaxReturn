"""
Dependency Injection Container

Provides centralized dependency management and configuration
for the application. This improves testability and decoupling.
"""

import logging
from pathlib import Path
from typing import Optional
from config.app_config import AppConfig
from config.tax_year_config import get_tax_year_config, TaxYearConfig
from services.encryption_service import EncryptionService
from services.tax_calculation_service import TaxCalculationService
from services.ptin_ero_service import PTINEROService

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Dependency injection container for the application.
    
    This container manages the lifecycle of services and ensures
    consistent configuration across the application.
    """
    
    _instance: Optional['DependencyContainer'] = None
    
    def __init__(self, config: Optional[AppConfig] = None, tax_year: int = 2025):
        """
        Initialize dependency container.
        
        Args:
            config: Application configuration (default: from environment)
            tax_year: Tax year for calculations (default: 2025)
        """
        self.config = config or AppConfig.from_env()
        self.tax_year = tax_year
        self.tax_year_config = get_tax_year_config(tax_year)
        
        # Service instances (lazy-loaded)
        self._encryption_service: Optional[EncryptionService] = None
        self._tax_calculation_service: Optional[TaxCalculationService] = None
        self._ptin_ero_service: Optional[PTINEROService] = None
        
        logger.info(f"Initialized DependencyContainer for tax year {tax_year}")
    
    @classmethod
    def get_instance(cls, config: Optional[AppConfig] = None, tax_year: int = 2025) -> 'DependencyContainer':
        """
        Get singleton instance of the container.
        
        Args:
            config: Application configuration (default: from environment)
            tax_year: Tax year for calculations (default: 2025)
            
        Returns:
            Singleton instance of DependencyContainer
        """
        if cls._instance is None:
            cls._instance = cls(config, tax_year)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for testing)"""
        cls._instance = None
        logger.debug("Reset DependencyContainer instance")
    
    def get_app_config(self) -> AppConfig:
        """Get application configuration"""
        return self.config
    
    def get_tax_year_config(self) -> TaxYearConfig:
        """Get tax year configuration"""
        return self.tax_year_config
    
    def get_encryption_service(self) -> EncryptionService:
        """
        Get encryption service instance.
        
        Returns:
            EncryptionService configured with app key file
        """
        if self._encryption_service is None:
            self._encryption_service = EncryptionService(self.config.key_file)
            logger.debug("Created EncryptionService instance")
        return self._encryption_service
    
    def get_tax_calculation_service(self) -> TaxCalculationService:
        """
        Get tax calculation service instance.
        
        Returns:
            TaxCalculationService configured for the tax year
        """
        if self._tax_calculation_service is None:
            self._tax_calculation_service = TaxCalculationService(self.tax_year)
            logger.debug("Created TaxCalculationService instance")
        return self._tax_calculation_service
    
    def get_ptin_ero_service(self) -> PTINEROService:
        """
        Get PTIN/ERO service instance.
        
        Returns:
            PTINEROService configured with encryption
        """
        if self._ptin_ero_service is None:
            self._ptin_ero_service = PTINEROService(self.config, self.get_encryption_service())
            logger.debug("Created PTINEROService instance")
        return self._ptin_ero_service
    
    def get_tax_data_repository(self):
        """
        Get tax data repository (TaxData instance).
        
        Returns:
            TaxData instance configured with encryption
        """
        from models.tax_data import TaxData
        return TaxData(self.config)
    
    def get_pdf_form_filler(self):
        """
        Get PDF form filler instance.
        
        Returns:
            PDFFormFiller configured with forms directory
        """
        from utils.pdf_form_filler import PDFFormFiller
        forms_dir = self.config.safe_dir.parent / "IRSTaxReturnDocumentation"
        return PDFFormFiller(str(forms_dir))
    
    def configure_logging(self, level: str = "INFO") -> None:
        """
        Configure application-wide logging.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.safe_dir / "logs" / "app.log"),
                logging.StreamHandler()
            ]
        )
        
        logger.info(f"Configured logging at {level} level")


# Convenience function for getting the container
def get_container(config: Optional[AppConfig] = None, tax_year: int = 2025) -> DependencyContainer:
    """
    Get the dependency injection container.
    
    Args:
        config: Application configuration (optional)
        tax_year: Tax year for calculations (default: 2025)
        
    Returns:
        DependencyContainer instance
    """
    return DependencyContainer.get_instance(config, tax_year)
