"""
Tests for config/dependencies.py
"""
import pytest
from config.dependencies import DependencyContainer, get_container
from services.tax_calculation_service import TaxCalculationService
from services.encryption_service import EncryptionService


class TestDependencyContainer:
    """Test dependency injection container."""
    
    def setup_method(self):
        """Reset container before each test."""
        DependencyContainer.reset_instance()
    
    def test_get_tax_calculation_service(self):
        """Test retrieving tax calculation service."""
        container = DependencyContainer()
        service = container.get_tax_calculation_service()
        
        assert isinstance(service, TaxCalculationService)
        assert service.tax_year == 2025
    
    def test_get_tax_calculation_service_custom_year(self):
        """Test retrieving tax calculation service with custom year."""
        container = DependencyContainer(tax_year=2023)
        service = container.get_tax_calculation_service()
        
        assert isinstance(service, TaxCalculationService)
        assert service.tax_year == 2023
    
    def test_get_encryption_service(self):
        """Test retrieving encryption service."""
        container = DependencyContainer()
        service = container.get_encryption_service()
        
        assert isinstance(service, EncryptionService)
    
    def test_singleton_pattern_within_container(self):
        """Test that services are singletons within a container."""
        container = DependencyContainer()
        
        service1 = container.get_tax_calculation_service()
        service2 = container.get_tax_calculation_service()
        
        assert service1 is service2
    
    def test_encryption_service_singleton(self):
        """Test encryption service is singleton within container."""
        container = DependencyContainer()
        
        service1 = container.get_encryption_service()
        service2 = container.get_encryption_service()
        
        assert service1 is service2
    
    def test_container_reset(self):
        """Test resetting singleton container."""
        container1 = DependencyContainer.get_instance()
        DependencyContainer.reset_instance()
        container2 = DependencyContainer.get_instance()
        
        assert container1 is not container2
    
    def test_multiple_containers_independent(self):
        """Test multiple containers are independent."""
        DependencyContainer.reset_instance()
        container1 = DependencyContainer()
        container2 = DependencyContainer()
        
        service1 = container1.get_tax_calculation_service()
        service2 = container2.get_tax_calculation_service()
        
        # Different containers should have different service instances
        assert service1 is not service2
    
    def test_get_container_function(self):
        """Test convenience function for getting container."""
        DependencyContainer.reset_instance()
        container = get_container()
        
        assert isinstance(container, DependencyContainer)
        assert container.tax_year == 2025
    
    def test_get_container_custom_year(self):
        """Test get_container with custom year."""
        DependencyContainer.reset_instance()
        container = get_container(tax_year=2023)
        
        assert container.tax_year == 2023
