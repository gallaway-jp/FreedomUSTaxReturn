"""
Performance benchmarks for PDF generation and tax calculations.

Uses pytest-benchmark to establish performance baselines.
"""
import pytest
from pathlib import Path
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService
from utils.pdf.form_filler import PDFFormFiller


@pytest.fixture
def sample_tax_data():
    """Create sample tax data for benchmarking."""
    data = TaxData()
    data.set('personal_info.first_name', 'John')
    data.set('personal_info.last_name', 'Doe')
    data.set('personal_info.ssn', '123-45-6789')
    data.set('filing_info.filing_status', 'single')
    data.set('income.w2[0].employer', 'Test Corp')
    data.set('income.w2[0].wages', 75000)
    data.set('income.w2[0].federal_withholding', 12000)
    return data


@pytest.fixture
def tax_calculator():
    """Create tax calculator service."""
    return TaxCalculationService()


class TestTaxCalculationPerformance:
    """Benchmark tax calculations."""
    
    def test_benchmark_complete_tax_calculation(self, benchmark, sample_tax_data, tax_calculator):
        """Benchmark complete tax return calculation."""
        result = benchmark(tax_calculator.calculate_complete_return, sample_tax_data)
        assert result is not None
        assert hasattr(result, 'total_tax')
    
    def test_benchmark_taxable_income_calculation(self, benchmark, sample_tax_data, tax_calculator):
        """Benchmark taxable income calculation."""
        # Benchmark the complete calculation and extract taxable income
        result = benchmark(tax_calculator.calculate_complete_return, sample_tax_data)
        assert result.taxable_income >= 0
    
    def test_benchmark_tax_with_credits(self, benchmark, tax_calculator):
        """Benchmark tax calculation with credits."""
        data = TaxData()
        data.set('personal_info.first_name', 'Jane')
        data.set('personal_info.last_name', 'Doe')
        data.set('filing_info.filing_status', 'married_filing_jointly')
        data.set('income.w2[0].wages', 50000)
        
        # Set dependents using array format
        dependents = [
            {'age': 8, 'qualifying_child': True},
            {'age': 5, 'qualifying_child': True}
        ]
        data.set('dependents', dependents)
        
        result = benchmark(tax_calculator.calculate_complete_return, data.data)
        assert result is not None


class TestPDFGenerationPerformance:
    """Benchmark PDF generation operations."""
    
    def test_benchmark_form_filler_init(self, benchmark, tmp_path):
        """Benchmark PDFFormFiller initialization."""
        template_path = tmp_path / "test_form.pdf"
        # Create minimal PDF for testing
        template_path.write_bytes(b'%PDF-1.4\n%%EOF')
        
        def create_filler():
            return PDFFormFiller(str(template_path))
        
        result = benchmark(create_filler)
        assert result is not None


class TestDataModelPerformance:
    """Benchmark TaxData model operations."""
    
    def test_benchmark_tax_data_creation(self, benchmark):
        """Benchmark creating TaxData instance."""
        result = benchmark(TaxData)
        assert result is not None
    
    def test_benchmark_tax_data_set_operations(self, benchmark):
        """Benchmark set operations on TaxData."""
        data = TaxData()
        
        def set_multiple_fields():
            data.set('personal_info.first_name', 'Test')
            data.set('personal_info.last_name', 'User')
            data.set('personal_info.ssn', '123-45-6789')
            data.set('income.w2[0].wages', 50000)
            return data
        
        result = benchmark(set_multiple_fields)
        assert result.get('personal_info.first_name') == 'Test'
    
    def test_benchmark_tax_data_get_operations(self, benchmark):
        """Benchmark get operations on TaxData."""
        data = TaxData()
        data.set('personal_info.first_name', 'Test')
        data.set('income.w2[0].wages', 50000)
        
        def get_multiple_fields():
            return (
                data.get('personal_info.first_name'),
                data.get('income.w2[0].wages'),
                data.get('filing_info.filing_status')
            )
        
        result = benchmark(get_multiple_fields)
        assert result[0] == 'Test'
    
    def test_benchmark_tax_data_to_dict(self, benchmark, sample_tax_data):
        """Benchmark converting TaxData to dictionary."""
        result = benchmark(sample_tax_data.to_dict)
        assert isinstance(result, dict)
