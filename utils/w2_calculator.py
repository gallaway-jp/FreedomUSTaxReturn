"""
W-2 Form Calculator - Centralized calculations for W-2 forms
Eliminates code duplication across the codebase
"""

from typing import List, Dict


class W2Calculator:
    """Centralized W-2 calculations following DRY principle"""
    
    @staticmethod
    def calculate_total_wages(w2_forms: List[Dict]) -> float:
        """
        Calculate total wages from all W-2 forms
        
        Args:
            w2_forms: List of W-2 form dictionaries
            
        Returns:
            Total wages across all W-2 forms
        """
        if not w2_forms:
            return 0.0
        return sum(w2.get("wages", 0) for w2 in w2_forms)
    
    @staticmethod
    def calculate_total_withholding(w2_forms: List[Dict]) -> float:
        """
        Calculate total federal withholding from all W-2 forms
        
        Args:
            w2_forms: List of W-2 form dictionaries
            
        Returns:
            Total federal withholding across all W-2 forms
        """
        if not w2_forms:
            return 0.0
        return sum(w2.get("federal_withholding", 0) for w2 in w2_forms)
    
    @staticmethod
    def calculate_totals(w2_forms: List[Dict]) -> Dict[str, float]:
        """
        Calculate all W-2 totals at once for efficiency
        
        Args:
            w2_forms: List of W-2 form dictionaries
            
        Returns:
            Dictionary with 'wages' and 'withholding' totals
        """
        return {
            "wages": W2Calculator.calculate_total_wages(w2_forms),
            "withholding": W2Calculator.calculate_total_withholding(w2_forms)
        }
    
    @staticmethod
    def calculate_social_security_wages(w2_forms: List[Dict]) -> float:
        """
        Calculate total Social Security wages from all W-2 forms
        
        Args:
            w2_forms: List of W-2 form dictionaries
            
        Returns:
            Total Social Security wages
        """
        if not w2_forms:
            return 0.0
        return sum(w2.get("social_security_wages", 0) for w2 in w2_forms)
    
    @staticmethod
    def calculate_medicare_wages(w2_forms: List[Dict]) -> float:
        """
        Calculate total Medicare wages from all W-2 forms
        
        Args:
            w2_forms: List of W-2 form dictionaries
            
        Returns:
            Total Medicare wages
        """
        if not w2_forms:
            return 0.0
        return sum(w2.get("medicare_wages", 0) for w2 in w2_forms)
