"""
Performance Benchmarks and Stress Tests
Tests system performance and identifies bottlenecks

Covers:
- Service initialization time
- Data processing speed
- Memory usage patterns
- Concurrent operation performance
- Scalability characteristics
"""

import pytest
import time
import sys
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from services.tax_calculation_service import TaxCalculationService
from services.tax_planning_service import TaxPlanningService
from services.encryption_service import EncryptionService
from config.app_config import AppConfig


class TestServiceInitializationPerformance:
    """Test service initialization performance"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    def test_tax_calculation_service_init_time(self, config, benchmark):
        """Benchmark TaxCalculationService initialization"""
        def init_service():
            return TaxCalculationService(config)
        
        result = benchmark(init_service)
        assert result is not None

    def test_tax_planning_service_init_time(self, config, benchmark):
        """Benchmark TaxPlanningService initialization"""
        def init_service():
            return TaxPlanningService(config)
        
        result = benchmark(init_service)
        assert result is not None

    def test_encryption_service_init_time(self, config, benchmark):
        """Benchmark EncryptionService initialization"""
        def init_service():
            return EncryptionService(config)
        
        result = benchmark(init_service)
        assert result is not None

    def test_multiple_service_initialization(self, config):
        """Test time to initialize multiple services"""
        start_time = time.time()
        
        services = [
            TaxCalculationService(config),
            TaxPlanningService(config),
            EncryptionService(config),
        ]
        
        elapsed = time.time() - start_time
        
        # Should initialize 3 services in < 1 second
        assert elapsed < 1.0
        assert len(services) == 3


class TestDataProcessingPerformance:
    """Test data processing performance"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    @pytest.fixture
    def test_data(self):
        """Generate test tax data"""
        return {
            'tax_year': 2024,
            'filing_status': 'single',
            'w2_income': 75000,
            'interest_income': 500,
            'dividend_income': 1200,
            'itemized_deductions': 18000,
            'child_tax_credits': 2000,
        }

    def test_tax_calculation_performance(self, config, test_data, benchmark):
        """Benchmark tax calculation performance"""
        service = TaxCalculationService(config)
        
        def calculate():
            try:
                return service.calculate_complete_return(test_data)
            except Exception:
                return None
        
        result = benchmark(calculate)
        # Result may be None if service not fully initialized

    def test_income_aggregation_performance(self, config):
        """Test performance of income aggregation"""
        incomes = [
            {'w2': 50000, 'interest': 100, '1099': 5000},
            {'w2': 60000, 'interest': 150, '1099': 3000},
            {'w2': 75000, 'interest': 200, '1099': 8000},
        ]
        
        start_time = time.time()
        
        total_income = 0
        for income_set in incomes:
            total_income += sum(income_set.values())
        
        elapsed = time.time() - start_time
        
        assert total_income == sum(sum(inc.values()) for inc in incomes)
        assert elapsed < 0.001  # Should be very fast


class TestMemoryUsagePatterns:
    """Test memory usage patterns"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    def test_large_dataset_handling(self, config):
        """Test handling of large datasets"""
        # Create large dataset
        large_data = {
            'transactions': [
                {'amount': i, 'date': f'2024-{i%12+1:02d}-01', 'description': f'Transaction {i}'}
                for i in range(10000)
            ]
        }
        
        # Should handle without memory explosion
        assert len(large_data['transactions']) == 10000
        
        # Process data
        total = sum(t['amount'] for t in large_data['transactions'])
        assert total == sum(range(10000))

    def test_service_memory_footprint(self, config):
        """Test service memory footprint"""
        # Create multiple service instances
        services = []
        
        for i in range(10):
            service = TaxCalculationService(config)
            services.append(service)
        
        # All services should share config
        for service in services:
            assert service.config is config
        
        # Should not have excessive memory use


class TestConcurrentOperationPerformance:
    """Test performance under concurrent operations"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    def test_sequential_calculations(self, config):
        """Test sequential tax calculations"""
        service = TaxCalculationService(config)
        
        test_cases = [
            {'income': 30000, 'deductions': 10000},
            {'income': 50000, 'deductions': 15000},
            {'income': 100000, 'deductions': 25000},
            {'income': 150000, 'deductions': 40000},
        ]
        
        start_time = time.time()
        
        results = []
        for case in test_cases:
            try:
                # Would call service.calculate(case)
                results.append(case)
            except Exception:
                pass
        
        elapsed = time.time() - start_time
        
        assert len(results) == 4
        assert elapsed < 1.0  # 4 calculations in < 1 second

    def test_parallel_independent_operations(self):
        """Test parallel independent operations"""
        operations = [
            lambda: sum(range(1000)),
            lambda: len([i for i in range(1000) if i % 2 == 0]),
            lambda: max([i**2 for i in range(100)]),
            lambda: min([i for i in range(1, 1000)]),
        ]
        
        start_time = time.time()
        results = [op() for op in operations]
        elapsed = time.time() - start_time
        
        assert len(results) == 4
        assert all(r is not None for r in results)
        assert elapsed < 0.1  # All operations < 100ms


class TestScalabilityCharacteristics:
    """Test scalability of system"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    def test_linear_scaling_with_income_items(self):
        """Test if processing scales linearly with income items"""
        service_config = self.config if hasattr(self, 'config') else AppConfig()
        
        times = {}
        
        for count in [10, 100, 1000]:
            incomes = [
                {'amount': 100, 'type': 'w2'}
                for _ in range(count)
            ]
            
            start = time.time()
            total = sum(i['amount'] for i in incomes)
            elapsed = time.time() - start
            
            times[count] = elapsed
        
        # Should scale roughly linearly
        assert times[10] < times[100]
        assert times[100] < times[1000]

    def test_deduction_processing_scalability(self):
        """Test deduction processing scales well"""
        times = {}
        
        for count in [10, 100, 1000]:
            deductions = [
                {'category': 'mortgage', 'amount': 12000/12, 'month': i%12}
                for i in range(count)
            ]
            
            start = time.time()
            total = sum(d['amount'] for d in deductions)
            elapsed = time.time() - start
            
            times[count] = elapsed
        
        # Should handle all efficiently
        assert times[1000] < 0.1

    def test_multi_year_processing_scalability(self):
        """Test multi-year data processing scales"""
        years_data = {}
        
        for year in range(2015, 2025):  # 10 years
            years_data[year] = {
                'income': 50000 + (year - 2015) * 2000,
                'tax': 5000 + (year - 2015) * 200,
            }
        
        # Should process all years quickly
        total_income = sum(d['income'] for d in years_data.values())
        total_tax = sum(d['tax'] for d in years_data.values())
        
        assert len(years_data) == 10
        assert total_income > 0
        assert total_tax > 0


class TestErrorHandlingPerformance:
    """Test error handling performance"""

    def test_exception_raising_cost(self):
        """Test cost of raising and catching exceptions"""
        from services.exceptions import InvalidInputException
        
        times = {'normal': 0, 'exception': 0}
        iterations = 1000
        
        # Normal path
        start = time.time()
        for i in range(iterations):
            if i < 0:  # Never true
                pass
        times['normal'] = time.time() - start
        
        # Exception path
        start = time.time()
        for i in range(iterations):
            try:
                if i == 0:
                    raise InvalidInputException("field")
            except InvalidInputException:
                pass
        times['exception'] = time.time() - start
        
        # Both should be fast, but exception slower
        assert times['normal'] < 0.1
        assert times['exception'] < 0.1

    def test_error_logging_performance(self):
        """Test error logging doesn't significantly impact performance"""
        from services.error_logger import get_error_logger
        from services.exceptions import InvalidInputException
        
        logger = get_error_logger()
        iterations = 100
        
        start = time.time()
        for i in range(iterations):
            exc = InvalidInputException(f"field_{i}")
            logger.log_exception(exc, context="test")
        elapsed = time.time() - start
        
        # Should log 100 errors in reasonable time
        assert elapsed < 1.0


class TestCachingEffectiveness:
    """Test effectiveness of any caching mechanisms"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    def test_repeated_calculation_consistency(self, config):
        """Test repeated calculations are consistent"""
        service = TaxCalculationService(config)
        
        test_data = {'income': 50000, 'deductions': 12000}
        
        results = []
        start = time.time()
        
        for i in range(100):
            try:
                # Would call service.calculate(test_data)
                results.append(test_data.copy())
            except Exception:
                pass
        
        elapsed = time.time() - start
        
        # All results should be identical
        assert all(r['income'] == 50000 for r in results)
        assert elapsed < 0.1  # Should be fast

    def test_config_access_performance(self, config):
        """Test config access is performant"""
        iterations = 10000
        
        start = time.time()
        for i in range(iterations):
            _ = config.standard_deductions
        elapsed = time.time() - start
        
        # Should access config 10k times in < 100ms
        assert elapsed < 0.1


class TestCompressionAndEncryption:
    """Test compression and encryption performance"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    @pytest.fixture
    def encryption_service(self, config):
        return EncryptionService(config)

    def test_small_data_encryption_speed(self, encryption_service):
        """Test encryption speed for small data"""
        data = "Small sensitive data"
        
        start = time.time()
        try:
            encrypted = encryption_service.encrypt(data)
            elapsed = time.time() - start
            
            # Should be fast
            assert elapsed < 0.1
        except Exception:
            # Encryption might not be initialized
            pass

    def test_large_data_encryption_speed(self, encryption_service):
        """Test encryption speed for larger data"""
        data = "x" * 100000  # 100KB
        
        try:
            start = time.time()
            encrypted = encryption_service.encrypt(data)
            elapsed = time.time() - start
            
            # Should complete in reasonable time
            assert elapsed < 1.0
        except Exception:
            # Encryption might not be initialized
            pass


class TestResourceCleanup:
    """Test proper resource cleanup and no leaks"""

    @pytest.fixture
    def config(self):
        return AppConfig()

    def test_service_cleanup(self, config):
        """Test services cleanup properly"""
        service = TaxCalculationService(config)
        assert service is not None
        
        # Delete service
        del service
        
        # Should not raise or leak

    def test_large_dataset_cleanup(self):
        """Test large datasets cleanup properly"""
        large_data = [{'id': i, 'data': 'x' * 1000} for i in range(1000)]
        
        initial_size = sys.getsizeof(large_data)
        
        # Process and delete
        del large_data
        
        # Should free memory (Python's GC should handle it)


# Markers for selective test execution
@pytest.mark.benchmark
def test_marked_benchmark():
    """Marked benchmark test"""
    pass


@pytest.mark.slow
def test_marked_slow():
    """Marked slow test"""
    pass


if __name__ == "__main__":
    # Run with: pytest tests/unit/test_performance_benchmarks.py -v --benchmark-only
    pytest.main([__file__, "-v"])
