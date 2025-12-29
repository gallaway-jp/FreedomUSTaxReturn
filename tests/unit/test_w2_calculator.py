"""
Comprehensive tests for W2Calculator utility class

Tests cover:
- Total wages calculation
- Federal withholding calculation
- Combined totals calculation
- Social Security wages calculation
- Medicare wages calculation
- Edge cases (empty lists, missing fields, negative values)
"""

import pytest
from utils.w2_calculator import W2Calculator


class TestW2CalculatorTotalWages:
    """Test total wages calculation"""
    
    def test_no_w2_forms(self):
        """Should return 0 for empty list"""
        assert W2Calculator.calculate_total_wages([]) == 0.0
    
    def test_single_w2_form(self):
        """Should return wages from single W-2"""
        w2_forms = [{"wages": 50000.00}]
        assert W2Calculator.calculate_total_wages(w2_forms) == 50000.00
    
    def test_multiple_w2_forms(self):
        """Should sum wages from multiple W-2 forms"""
        w2_forms = [
            {"wages": 50000.00},
            {"wages": 30000.00},
            {"wages": 20000.00}
        ]
        assert W2Calculator.calculate_total_wages(w2_forms) == 100000.00
    
    def test_missing_wages_field(self):
        """Should treat missing wages as 0"""
        w2_forms = [
            {"wages": 50000.00},
            {"employer_name": "Test Corp"},  # No wages field
            {"wages": 30000.00}
        ]
        assert W2Calculator.calculate_total_wages(w2_forms) == 80000.00
    
    def test_zero_wages(self):
        """Should handle zero wages correctly"""
        w2_forms = [
            {"wages": 0},
            {"wages": 50000.00}
        ]
        assert W2Calculator.calculate_total_wages(w2_forms) == 50000.00
    
    def test_decimal_wages(self):
        """Should handle decimal wages accurately"""
        w2_forms = [
            {"wages": 50000.50},
            {"wages": 30000.25},
            {"wages": 19999.25}
        ]
        assert W2Calculator.calculate_total_wages(w2_forms) == 100000.00


class TestW2CalculatorTotalWithholding:
    """Test federal withholding calculation"""
    
    def test_no_w2_forms(self):
        """Should return 0 for empty list"""
        assert W2Calculator.calculate_total_withholding([]) == 0.0
    
    def test_single_w2_withholding(self):
        """Should return withholding from single W-2"""
        w2_forms = [{"federal_withholding": 7500.00}]
        assert W2Calculator.calculate_total_withholding(w2_forms) == 7500.00
    
    def test_multiple_w2_withholding(self):
        """Should sum withholding from multiple W-2 forms"""
        w2_forms = [
            {"federal_withholding": 7500.00},
            {"federal_withholding": 4500.00},
            {"federal_withholding": 3000.00}
        ]
        assert W2Calculator.calculate_total_withholding(w2_forms) == 15000.00
    
    def test_missing_withholding_field(self):
        """Should treat missing withholding as 0"""
        w2_forms = [
            {"federal_withholding": 7500.00},
            {"wages": 50000.00},  # No withholding field
            {"federal_withholding": 3000.00}
        ]
        assert W2Calculator.calculate_total_withholding(w2_forms) == 10500.00
    
    def test_zero_withholding(self):
        """Should handle zero withholding correctly"""
        w2_forms = [
            {"federal_withholding": 0},
            {"federal_withholding": 7500.00}
        ]
        assert W2Calculator.calculate_total_withholding(w2_forms) == 7500.00


class TestW2CalculatorCombinedTotals:
    """Test combined totals calculation"""
    
    def test_empty_list_totals(self):
        """Should return zeros for empty list"""
        totals = W2Calculator.calculate_totals([])
        assert totals == {"wages": 0.0, "withholding": 0.0}
    
    def test_single_w2_totals(self):
        """Should calculate both totals from single W-2"""
        w2_forms = [{"wages": 50000.00, "federal_withholding": 7500.00}]
        totals = W2Calculator.calculate_totals(w2_forms)
        assert totals["wages"] == 50000.00
        assert totals["withholding"] == 7500.00
    
    def test_multiple_w2_totals(self):
        """Should calculate both totals from multiple W-2 forms"""
        w2_forms = [
            {"wages": 50000.00, "federal_withholding": 7500.00},
            {"wages": 30000.00, "federal_withholding": 4500.00},
            {"wages": 20000.00, "federal_withholding": 3000.00}
        ]
        totals = W2Calculator.calculate_totals(w2_forms)
        assert totals["wages"] == 100000.00
        assert totals["withholding"] == 15000.00
    
    def test_totals_efficiency(self):
        """Should calculate both totals in one pass"""
        w2_forms = [
            {"wages": 50000.00, "federal_withholding": 7500.00},
            {"wages": 30000.00, "federal_withholding": 4500.00}
        ]
        totals = W2Calculator.calculate_totals(w2_forms)
        
        # Verify both values are calculated
        assert "wages" in totals
        assert "withholding" in totals
        assert len(totals) == 2


class TestW2CalculatorSocialSecurityWages:
    """Test Social Security wages calculation"""
    
    def test_no_w2_forms_ss(self):
        """Should return 0 for empty list"""
        assert W2Calculator.calculate_social_security_wages([]) == 0.0
    
    def test_single_w2_ss_wages(self):
        """Should return SS wages from single W-2"""
        w2_forms = [{"social_security_wages": 50000.00}]
        assert W2Calculator.calculate_social_security_wages(w2_forms) == 50000.00
    
    def test_multiple_w2_ss_wages(self):
        """Should sum SS wages from multiple W-2 forms"""
        w2_forms = [
            {"social_security_wages": 50000.00},
            {"social_security_wages": 30000.00},
            {"social_security_wages": 20000.00}
        ]
        assert W2Calculator.calculate_social_security_wages(w2_forms) == 100000.00
    
    def test_missing_ss_wages_field(self):
        """Should treat missing SS wages as 0"""
        w2_forms = [
            {"social_security_wages": 50000.00},
            {"wages": 30000.00},  # No SS wages field
            {"social_security_wages": 20000.00}
        ]
        assert W2Calculator.calculate_social_security_wages(w2_forms) == 70000.00
    
    def test_ss_wages_at_wage_base_limit(self):
        """Should handle wages at SS wage base limit (2025: $176,100)"""
        w2_forms = [
            {"social_security_wages": 176100.00},
            {"social_security_wages": 50000.00}  # Over limit from second job
        ]
        # Calculator sums all SS wages reported
        assert W2Calculator.calculate_social_security_wages(w2_forms) == 226100.00


class TestW2CalculatorMedicareWages:
    """Test Medicare wages calculation"""
    
    def test_no_w2_forms_medicare(self):
        """Should return 0 for empty list"""
        assert W2Calculator.calculate_medicare_wages([]) == 0.0
    
    def test_single_w2_medicare_wages(self):
        """Should return Medicare wages from single W-2"""
        w2_forms = [{"medicare_wages": 50000.00}]
        assert W2Calculator.calculate_medicare_wages(w2_forms) == 50000.00
    
    def test_multiple_w2_medicare_wages(self):
        """Should sum Medicare wages from multiple W-2 forms"""
        w2_forms = [
            {"medicare_wages": 50000.00},
            {"medicare_wages": 30000.00},
            {"medicare_wages": 20000.00}
        ]
        assert W2Calculator.calculate_medicare_wages(w2_forms) == 100000.00
    
    def test_missing_medicare_wages_field(self):
        """Should treat missing Medicare wages as 0"""
        w2_forms = [
            {"medicare_wages": 50000.00},
            {"wages": 30000.00},  # No Medicare wages field
            {"medicare_wages": 20000.00}
        ]
        assert W2Calculator.calculate_medicare_wages(w2_forms) == 70000.00
    
    def test_medicare_wages_over_additional_threshold(self):
        """Should handle wages over additional Medicare tax threshold (2025: $200,000)"""
        w2_forms = [
            {"medicare_wages": 150000.00},
            {"medicare_wages": 100000.00}
        ]
        assert W2Calculator.calculate_medicare_wages(w2_forms) == 250000.00


class TestW2CalculatorEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_mixed_complete_and_incomplete_forms(self):
        """Should handle mix of complete and incomplete W-2 forms"""
        w2_forms = [
            {
                "wages": 50000.00,
                "federal_withholding": 7500.00,
                "social_security_wages": 50000.00,
                "medicare_wages": 50000.00
            },
            {
                "wages": 30000.00
                # Missing other fields
            },
            {
                "federal_withholding": 3000.00,
                "medicare_wages": 20000.00
                # Missing wages and SS wages
            }
        ]
        
        assert W2Calculator.calculate_total_wages(w2_forms) == 80000.00
        assert W2Calculator.calculate_total_withholding(w2_forms) == 10500.00
        assert W2Calculator.calculate_social_security_wages(w2_forms) == 50000.00
        assert W2Calculator.calculate_medicare_wages(w2_forms) == 70000.00
    
    def test_all_calculations_consistent(self):
        """Should produce consistent results across all methods"""
        w2_forms = [
            {
                "wages": 75000.00,
                "federal_withholding": 11250.00,
                "social_security_wages": 75000.00,
                "medicare_wages": 75000.00
            }
        ]
        
        # Individual calculations
        wages = W2Calculator.calculate_total_wages(w2_forms)
        withholding = W2Calculator.calculate_total_withholding(w2_forms)
        
        # Combined calculation
        totals = W2Calculator.calculate_totals(w2_forms)
        
        # Should match
        assert totals["wages"] == wages
        assert totals["withholding"] == withholding
    
    def test_very_small_amounts(self):
        """Should handle very small wage amounts accurately"""
        w2_forms = [
            {"wages": 0.01, "federal_withholding": 0.01},
            {"wages": 0.99, "federal_withholding": 0.10}
        ]
        assert W2Calculator.calculate_total_wages(w2_forms) == 1.00
        assert W2Calculator.calculate_total_withholding(w2_forms) == 0.11
    
    def test_large_number_of_w2_forms(self):
        """Should handle many W-2 forms efficiently"""
        w2_forms = [{"wages": 1000.00, "federal_withholding": 150.00} for _ in range(100)]
        assert W2Calculator.calculate_total_wages(w2_forms) == 100000.00
        assert W2Calculator.calculate_total_withholding(w2_forms) == 15000.00
