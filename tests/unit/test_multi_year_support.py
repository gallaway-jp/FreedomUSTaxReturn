"""
Tests for Multi-Year Support functionality

Tests the tax year service, multi-year tax data model, and year comparison features.
"""

import pytest
import json
from datetime import datetime, date
from unittest.mock import Mock, patch
from services.tax_year_service import TaxYearService, TaxYearConfig, CarryoverItem
from models.tax_data import TaxData
from config.app_config import AppConfig


class TestTaxYearService:
    """Test the TaxYearService functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TaxYearService()

    def test_supported_years(self):
        """Test getting supported tax years"""
        years = self.service.get_supported_years()
        assert isinstance(years, list)
        assert len(years) > 0
        assert all(isinstance(year, int) for year in years)
        # Should be in descending order (most recent first)
        assert years == sorted(years, reverse=True)

    def test_get_tax_year_config(self):
        """Test getting tax year configuration"""
        config = self.service.get_tax_year_config(2024)
        assert isinstance(config, TaxYearConfig)
        assert config.year == 2024
        assert isinstance(config.filing_deadline, date)
        assert isinstance(config.standard_deduction, dict)

    def test_get_current_tax_year(self):
        """Test getting current tax year"""
        current_year = self.service.get_current_tax_year()
        assert isinstance(current_year, int)
        assert current_year >= 2020  # Should be reasonable

    def test_is_tax_year_open(self):
        """Test checking if tax year is open"""
        # Current year should be open
        current_year = self.service.get_current_tax_year()
        assert self.service.is_tax_year_open(current_year)

        # Very old year should not be open
        assert not self.service.is_tax_year_open(2010)

    def test_carryover_items(self):
        """Test carryover item management"""
        tax_year = 2024
        item = CarryoverItem(
            item_type="capital_loss",
            description="Stock losses",
            amount=5000.0,
            tax_year=tax_year
        )

        # Add carryover item
        self.service.add_carryover_item(tax_year, item)

        # Retrieve carryover items
        items = self.service.get_carryover_items(tax_year, "capital_loss")
        assert len(items) == 1
        assert items[0].description == "Stock losses"

        # Use some of the carryover
        success = self.service.use_carryover_amount(tax_year, "capital_loss", 2000.0)
        assert success

        # Check remaining amount
        items = self.service.get_carryover_items(tax_year, "capital_loss")
        assert items[0].used_amount == 2000.0

    def test_year_comparison(self):
        """Test year-over-year comparison"""
        # Create mock tax data
        data1 = {
            "income": {"total_income": 50000},
            "deductions": {"total_deductions": 10000},
            "calculations": {"taxable_income": 40000, "total_tax": 6000}
        }
        data2 = {
            "income": {"total_income": 55000},
            "deductions": {"total_deductions": 12000},
            "calculations": {"taxable_income": 43000, "total_tax": 6500}
        }

        comparison = self.service.get_year_comparison_data(2023, 2024, data1, data2)

        assert "years" in comparison
        assert "summary" in comparison
        assert comparison["years"] == [2023, 2024]

        summary = comparison["summary"]
        assert "total_income" in summary
        assert summary["total_income"]["year1"] == 50000
        assert summary["total_income"]["year2"] == 55000
        assert summary["total_income"]["difference"] == 5000


class TestMultiYearTaxData:
    """Test multi-year tax data functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = AppConfig.from_env()
        self.tax_data = TaxData(self.config)

    def test_initialization(self):
        """Test multi-year data initialization"""
        assert "years" in self.tax_data.data
        assert "metadata" in self.tax_data.data
        assert self.tax_data.get_current_year() == 2025
        assert 2025 in self.tax_data.data["years"]

    def test_year_management(self):
        """Test basic year management"""
        # Test getting current year
        assert self.tax_data.get_current_year() == 2025

        # Test setting current year
        self.tax_data.set_current_year(2024)
        assert self.tax_data.get_current_year() == 2024
        assert 2024 in self.tax_data.data["years"]

        # Test getting available years
        years = self.tax_data.get_available_years()
        assert 2025 in years
        assert 2024 in years

    def test_year_specific_data_access(self):
        """Test accessing data for specific years"""
        # Set data for 2025
        self.tax_data.set("personal_info.first_name", "John", tax_year=2025)
        self.tax_data.set("personal_info.last_name", "Doe", tax_year=2025)

        # Set data for 2024
        self.tax_data.set_current_year(2024)
        self.tax_data.set("personal_info.first_name", "Jane", tax_year=2024)
        self.tax_data.set("personal_info.last_name", "Smith", tax_year=2024)

        # Verify data isolation
        assert self.tax_data.get("personal_info.first_name", tax_year=2025) == "John"
        assert self.tax_data.get("personal_info.last_name", tax_year=2025) == "Doe"
        assert self.tax_data.get("personal_info.first_name", tax_year=2024) == "Jane"
        assert self.tax_data.get("personal_info.last_name", tax_year=2024) == "Smith"

    def test_create_new_year(self):
        """Test creating a new tax year"""
        # Create 2024 based on 2025
        success = self.tax_data.create_new_year(2024, 2025)
        assert success

        # Verify the year was created
        assert 2024 in self.tax_data.data["years"]

        # Verify metadata
        year_data = self.tax_data.get_year_data(2024)
        assert year_data["metadata"]["tax_year"] == 2024
        assert year_data["metadata"]["based_on_year"] == 2025

    def test_copy_personal_info(self):
        """Test copying personal info between years"""
        # Set personal info for 2025
        self.tax_data.set("personal_info.first_name", "John", tax_year=2025)
        self.tax_data.set("personal_info.ssn", "123-45-6789", tax_year=2025)

        # Create 2024 and copy personal info
        self.tax_data.create_new_year(2024, 2025)
        self.tax_data.copy_personal_info_to_year(2025, 2024)

        # Verify copy
        assert self.tax_data.get("personal_info.first_name", tax_year=2024) == "John"
        assert self.tax_data.get("personal_info.ssn", tax_year=2024) == "123456789"  # SSN is cleaned

    def test_delete_year(self):
        """Test deleting a tax year"""
        # Create a year to delete
        self.tax_data.create_new_year(2024, 2025)

        # Try to delete current year (should fail)
        success = self.tax_data.delete_year(2025)
        assert not success

        # Switch to 2024 and try to delete 2025
        self.tax_data.set_current_year(2024)
        success = self.tax_data.delete_year(2025)
        assert success
        assert 2025 not in self.tax_data.data["years"]

    def test_data_validation_across_years(self):
        """Test that validation works across different years"""
        # Test SSN validation - should fail for invalid SSN
        with pytest.raises(ValueError):
            self.tax_data.set("personal_info.ssn", "invalid-ssn", tax_year=2025)

        # Test valid SSN
        self.tax_data.set("personal_info.ssn", "123-45-6789", tax_year=2024)
        assert self.tax_data.get("personal_info.ssn", tax_year=2024) == "123456789"

    def test_get_section_by_year(self):
        """Test getting sections for specific years"""
        # Set data for 2025
        self.tax_data.set("income.w2_forms", [{"wages": 50000}], tax_year=2025)

        # Get section for 2025
        income_2025 = self.tax_data.get_section("income", tax_year=2025)
        assert "w2_forms" in income_2025
        assert len(income_2025["w2_forms"]) == 1

        # Get section for 2024 (should initialize with default structure)
        income_2024 = self.tax_data.get_section("income", tax_year=2024)
        assert "w2_forms" in income_2024  # Should have default structure
        assert income_2024["w2_forms"] == []  # But empty


class TestYearComparisonIntegration:
    """Test year comparison integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = AppConfig.from_env()
        self.tax_data = TaxData(self.config)
        self.service = TaxYearService()

        # Create test data for two years
        self._setup_test_data()

    def _setup_test_data(self):
        """Set up test data for comparison"""
        # 2024 data
        self.tax_data.set("income.total_income", 60000, tax_year=2024)
        self.tax_data.set("deductions.total_deductions", 15000, tax_year=2024)
        self.tax_data.set("calculations.taxable_income", 45000, tax_year=2024)
        self.tax_data.set("calculations.total_tax", 6750, tax_year=2024)
        self.tax_data.set("credits.total_credits", 2000, tax_year=2024)

        # 2025 data
        self.tax_data.set("income.total_income", 65000, tax_year=2025)
        self.tax_data.set("deductions.total_deductions", 16000, tax_year=2025)
        self.tax_data.set("calculations.taxable_income", 49000, tax_year=2025)
        self.tax_data.set("calculations.total_tax", 7350, tax_year=2025)
        self.tax_data.set("credits.total_credits", 2500, tax_year=2025)

    def test_year_comparison_data(self):
        """Test generating comparison data"""
        data_2024 = self.tax_data.get_year_data(2024)
        data_2025 = self.tax_data.get_year_data(2025)

        comparison = self.service.get_year_comparison_data(2024, 2025, data_2024, data_2025)

        assert comparison["years"] == [2024, 2025]

        summary = comparison["summary"]
        assert summary["total_income"]["year1"] == 60000
        assert summary["total_income"]["year2"] == 65000
        assert summary["total_income"]["difference"] == 5000
        assert summary["total_income"]["percent_change"] == pytest.approx(8.33, rel=0.01)

    def test_comparison_with_missing_data(self):
        """Test comparison when some data is missing"""
        # Create year with minimal data
        self.tax_data.create_new_year(2023, 2024)

        data_2023 = self.tax_data.get_year_data(2023)
        data_2024 = self.tax_data.get_year_data(2024)

        comparison = self.service.get_year_comparison_data(2023, 2024, data_2023, data_2024)

        # Should handle missing data gracefully
        assert comparison["years"] == [2023, 2024]
        assert "summary" in comparison

    @pytest.mark.skip(reason="Matplotlib not installed")
    def test_chart_generation_logic(self, mock_show):
        """Test that chart data can be generated (without actually showing plots)"""
        data_2024 = self.tax_data.get_year_data(2024)
        data_2025 = self.tax_data.get_year_data(2025)

        comparison = self.service.get_year_comparison_data(2024, 2025, data_2024, data_2025)

        # Verify comparison has the data needed for charts
        assert "summary" in comparison
        summary = comparison["summary"]

        # Check that all expected metrics are present
        expected_metrics = ["total_income", "total_deductions", "taxable_income", "total_tax", "total_credits"]
        for metric in expected_metrics:
            assert metric in summary
            assert "year1" in summary[metric]
            assert "year2" in summary[metric]
            assert "difference" in summary[metric]
            assert "percent_change" in summary[metric]


if __name__ == "__main__":
    pytest.main([__file__])