"""
Tax data model - stores all tax return information
"""

import json
import os
import stat
import hmac
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from functools import lru_cache, wraps
from cryptography.fernet import Fernet
from config.app_config import AppConfig
from services.encryption_service import EncryptionService
from utils.event_bus import EventBus, Event, EventType
from utils.resilience import retry
from utils.error_tracker import get_error_tracker
from utils.tax_calculations import (
    calculate_standard_deduction,
    calculate_income_tax,
    calculate_self_employment_tax,
    calculate_child_tax_credit,
    calculate_earned_income_credit,
    calculate_retirement_savings_credit,
    calculate_child_dependent_care_credit,
    calculate_residential_energy_credit,
    calculate_premium_tax_credit
)
from utils.w2_calculator import W2Calculator

# Performance: Cache decorator for expensive calculations
def invalidate_cache_on_change(func):
    """Decorator to invalidate cache when data changes"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Clear cache if data has been modified
        if hasattr(self, '_calculation_cache'):
            cache_time = getattr(self, '_cache_timestamp', None)
            last_modified = self.data.get('metadata', {}).get('last_modified', '')
            if cache_time != last_modified:
                self._calculation_cache = {}
                self._cache_timestamp = last_modified
        else:
            self._calculation_cache = {}
            self._cache_timestamp = self.data.get('metadata', {}).get('last_modified', '')
        
        # Check cache
        cache_key = f"{func.__name__}_{args}_{kwargs}"
        if cache_key in self._calculation_cache:
            return self._calculation_cache[cache_key]
        
        # Calculate and cache
        result = func(self, *args, **kwargs)
        self._calculation_cache[cache_key] = result
        return result
    return wrapper
from utils.validation import (
    validate_ssn,
    validate_email,
    validate_zip_code,
    validate_phone,
    validate_ein,
    validate_currency
)

# Configure security logging
def setup_logging():
    """Setup security logging with proper directory creation"""
    log_dir = Path.home() / "Documents" / "TaxReturns" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        filename=str(log_dir / "security.log"),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

class TaxData:
    """Central data model for tax return information"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize tax data model with optional configuration.
        
        Args:
            config: Application configuration (uses default if None)
        """
        # Use provided config or create default
        self.config = config or AppConfig.from_env()
        
        # Field validators
        self.VALIDATORS = {
            'personal_info.ssn': validate_ssn,
            'spouse_info.ssn': validate_ssn,
            'personal_info.email': validate_email,
            'personal_info.zip_code': validate_zip_code,
            'personal_info.phone': validate_phone,
        }
        
        # Input length limits
        self.MAX_LENGTHS = {
            'first_name': 50,
            'last_name': 50,
            'address': 100,
            'city': 50,
            'email': 100,
        }
        
        # Initialize empty tax data with encryption
        # Ensure safe directory exists
        self.config.ensure_directories()
        
        # Initialize encryption service
        self.encryption = EncryptionService(self.config.key_file)
        
        # Get event bus for publishing data changes
        self.event_bus = EventBus.get_instance()
        
        self.data = {
            # Personal Information
            "personal_info": {
                "first_name": "",
                "middle_initial": "",
                "last_name": "",
                "ssn": "",
                "date_of_birth": "",
                "occupation": "",
                "address": "",
                "city": "",
                "state": "",
                "zip_code": "",
                "email": "",
                "phone": "",
            },
            
            # Spouse Information (if married filing jointly)
            "spouse_info": {
                "first_name": "",
                "middle_initial": "",
                "last_name": "",
                "ssn": "",
                "date_of_birth": "",
                "occupation": "",
            },
            
            # Dependents
            "dependents": [],
            
            # Filing Status
            "filing_status": {
                "status": "Single",  # Single, MFJ, MFS, HOH, QW
                "is_dependent": False,
                "can_be_claimed": False,
            },
            
            # Income
            "income": {
                "w2_forms": [],
                "interest_income": [],
                "dividend_income": [],
                "self_employment": [],
                "retirement_distributions": [],
                "social_security": [],
                "capital_gains": [],
                "rental_income": [],
                "business_income": [],
                "unemployment": [],
                "other_income": [],
            },
            
            # Adjustments to Income
            "adjustments": {
                "educator_expenses": 0,
                "hsa_deduction": 0,
                "self_employment_tax": 0,
                "self_employed_sep": 0,
                "self_employed_health": 0,
                "student_loan_interest": 0,
                "ira_deduction": 0,
                "other_adjustments": [],
            },
            
            # Deductions
            "deductions": {
                "method": "standard",  # standard or itemized
                "medical_expenses": 0,
                "state_local_taxes": 0,
                "mortgage_interest": 0,
                "charitable_contributions": 0,
                "other_itemized": [],
            },
            
            # Credits
            "credits": {
                "child_tax_credit": {
                    "qualifying_children": [],
                    "other_dependents": [],
                },
                "earned_income_credit": {
                    "qualifying_children": [],
                },
                "education_credits": {
                    "american_opportunity": [],
                    "lifetime_learning": [],
                },
                "retirement_savings_credit": 0,
                "child_dependent_care": {
                    "expenses": 0,
                },
                "residential_energy": {
                    "amount": 0,
                },
                "premium_tax_credit": {
                    "amount": 0,
                },
                "other_credits": [],
            },
            
            # Other Taxes
            "other_taxes": {
                "self_employment_tax": 0,
                "additional_medicare": 0,
                "household_employment": 0,
                "other": [],
            },
            
            # Payments
            "payments": {
                "federal_withholding": 0,
                "estimated_payments": [],
                "prior_year_overpayment": 0,
                "eic_payments": 0,
                "other_payments": [],
            },
            
            # Metadata
            "metadata": {
                "tax_year": 2025,  # Default to 2025 tax year
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "version": "1.0",
            }
        }
    
    def get(self, path: str, default=None) -> Any:
        """
        Get value from nested dictionary using dot notation
        Example: tax_data.get("personal_info.first_name")
        """
        keys = path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value
    
    def set(self, path: str, value: Any):
        """
        Set value in nested dictionary using dot notation with validation
        Example: tax_data.set("personal_info.first_name", "John")
        """
        # Store old value for event
        old_value = self.get(path)
        
        # Validate using field-specific validators
        if path in self.VALIDATORS:
            is_valid, validated_value = self.VALIDATORS[path](value)
            if not is_valid:
                logger.warning(f"Validation failed for {path}: {validated_value}")
                raise ValueError(f"Invalid value for {path}: {validated_value}")
            value = validated_value
        
        # Check length limits for string fields
        field_name = path.split('.')[-1]
        if field_name in self.MAX_LENGTHS and isinstance(value, str):
            max_len = self.MAX_LENGTHS[field_name]
            if len(value) > max_len:
                raise ValueError(f"{field_name} exceeds maximum length of {max_len} characters")
        
        # Validate currency values
        if 'amount' in field_name.lower() or field_name in ['wages', 'withholding', 'income']:
            if isinstance(value, (int, float)):
                if value < 0:
                    raise ValueError(f"{field_name} cannot be negative")
                if value > 999999999.99:
                    raise ValueError(f"{field_name} exceeds maximum allowed value")
        
        keys = path.split('.')
        data = self.data
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value
        self.data["metadata"]["last_modified"] = datetime.now().isoformat()
        
        logger.info(f"Data modified - Field: {path}")
        
        # Publish event for data change
        self.event_bus.publish(Event(
            type=EventType.TAX_DATA_CHANGED,
            source='TaxData',
            data={'path': path, 'old_value': old_value, 'new_value': value}
        ))
    
    def get_section(self, section: str) -> Dict:
        """Get entire section of data"""
        return self.data.get(section, {})
    
    def set_section(self, section: str, data: Dict):
        """Set entire section of data"""
        self.data[section] = data
        self.data["metadata"]["last_modified"] = datetime.now().isoformat()
    
    def add_to_list(self, path: str, item: Any):
        """Add item to a list in the data structure"""
        current_list = self.get(path, [])
        if not isinstance(current_list, list):
            current_list = []
        current_list.append(item)
        self.set(path, current_list)
    
    def remove_from_list(self, path: str, index: int):
        """Remove item from list by index"""
        current_list = self.get(path, [])
        if isinstance(current_list, list) and 0 <= index < len(current_list):
            current_list.pop(index)
            self.set(path, current_list)
    
    def update_in_list(self, path: str, index: int, new_item: Any):
        """Update item in list by index"""
        current_list = self.get(path, [])
        if isinstance(current_list, list) and 0 <= index < len(current_list):
            current_list[index] = new_item
            self.set(path, current_list)
    
    def get_required_forms(self) -> List[str]:
        """Determine which forms are required based on entered data"""
        forms = ["Form 1040"]  # Always required
        
        # Check filing status
        filing_status = self.get("filing_status.status")
        
        # Check income types
        income = self.get_section("income")
        
        # W-2 income doesn't require additional forms (included in 1040)
        
        # Schedule 1 - Additional Income and Adjustments
        if (income.get("unemployment") or 
            income.get("other_income") or
            self.get_section("adjustments")):
            forms.append("Schedule 1")
        
        # Schedule 2 - Additional Taxes
        other_taxes = self.get_section("other_taxes")
        if any(other_taxes.values()):
            forms.append("Schedule 2")
        
        # Schedule 3 - Additional Credits and Payments
        credits = self.get_section("credits")
        if any(credits.values()):
            forms.append("Schedule 3")
        
        # Schedule A - Itemized Deductions
        if self.get("deductions.method") == "itemized":
            forms.append("Schedule A")
        
        # Schedule B - Interest and Dividend Income
        if income.get("interest_income") or income.get("dividend_income"):
            interest_total = sum(i.get("amount", 0) for i in income.get("interest_income", []))
            dividend_total = sum(d.get("amount", 0) for d in income.get("dividend_income", []))
            if interest_total > 1500 or dividend_total > 1500:
                forms.append("Schedule B")
        
        # Schedule C - Business Income
        if income.get("business_income"):
            forms.append("Schedule C")
        
        # Schedule D - Capital Gains
        if income.get("capital_gains"):
            forms.append("Schedule D")
        
        # Schedule E - Rental/Royalty Income
        # (Would need to add rental income tracking)
        
        # Schedule SE - Self-Employment Tax
        if income.get("business_income"):
            forms.append("Schedule SE")
        
        # Schedule EIC - Earned Income Credit
        eic_children = self.get("credits.earned_income_credit.qualifying_children", [])
        if eic_children:
            forms.append("Schedule EIC")
        
        # Schedule 8812 - Child Tax Credit
        ctc_children = self.get("credits.child_tax_credit.qualifying_children", [])
        if ctc_children:
            forms.append("Schedule 8812")
        
        # Form 8863 - Education Credits
        aotc = self.get("credits.education_credits.american_opportunity", [])
        llc = self.get("credits.education_credits.lifetime_learning", [])
        if aotc or llc:
            forms.append("Form 8863")
        
        return sorted(forms)
    
    def calculate_totals(self) -> Dict[str, float]:
        """Calculate key totals for the tax return using focused helper methods"""
        income = self.get_section("income")
        
        totals = {
            "total_income": self._calculate_total_income(income),
            "adjusted_gross_income": 0,
            "taxable_income": 0,
            "total_tax": 0,
            "total_payments": 0,
            "refund_or_owe": 0,
        }
        
        # Calculate AGI
        totals["adjusted_gross_income"] = self._calculate_agi(totals["total_income"])
        
        # Calculate taxable income
        totals["taxable_income"] = self._calculate_taxable_income(totals["adjusted_gross_income"])
        
        # Calculate total tax
        tax_year = self.data.get("metadata", {}).get("tax_year", 2025)
        filing_status = self.get("filing_status.status")
        totals["total_tax"] = self._calculate_total_tax(
            totals["taxable_income"],
            filing_status,
            tax_year,
            income
        )
        
        # Subtract credits
        credits = self.calculate_credits(totals["adjusted_gross_income"])
        totals["total_tax"] = max(0, totals["total_tax"] - credits["total_credits"])
        
        # Add individual credits to result
        totals.update(credits)
        
        # Calculate payments and final result
        payments = self.get_section("payments")
        totals["total_payments"] = self._calculate_total_payments(payments)
        totals["amount_owed"] = max(0, totals["total_tax"] - totals["total_payments"])
        totals["refund"] = max(0, totals["total_payments"] - totals["total_tax"])
        totals["refund_or_owe"] = totals["refund"] - totals["amount_owed"]
        
        return totals
    
    def _calculate_total_income(self, income: Dict[str, Any]) -> float:
        """Calculate total income from all sources"""
        total = 0
        
        # W-2 wages
        w2_forms = income.get("w2_forms", [])
        total += W2Calculator.calculate_total_wages(w2_forms)
        
        # Interest and dividend income
        total += sum(item.get("amount", 0) for item in income.get("interest_income", []))
        total += sum(item.get("amount", 0) for item in income.get("dividend_income", []))
        
        # Self-employment income
        total += sum(item.get("net_profit", 0) for item in income.get("self_employment", []))
        
        # Retirement distributions
        total += sum(item.get("amount", 0) for item in income.get("retirement_distributions", []))
        
        # Social Security benefits
        total += sum(item.get("amount", 0) for item in income.get("social_security", []))
        
        # Capital gains/losses (only gains are taxable)
        for item in income.get("capital_gains", []):
            gain = item.get("gain_loss", 0)
            if gain > 0:  # Only add positive gains
                total += gain
        
        # Rental income
        total += sum(item.get("amount", 0) for item in income.get("rental_income", []))
        
        # Business income (legacy - may be deprecated in favor of self-employment)
        total += sum(business.get("net_profit", 0) for business in income.get("business_income", []))
        
        # Unemployment income
        total += self._calculate_unemployment_income(income.get("unemployment", 0))
        
        # Other income
        total += sum(other.get("amount", 0) for other in income.get("other_income", []))
        
        return total
    
    def _calculate_unemployment_income(self, unemployment: Union[int, float, List]) -> float:
        """Calculate unemployment income (handles both old and new formats)"""
        if isinstance(unemployment, (int, float)):
            return unemployment
        elif isinstance(unemployment, list):
            return sum(
                unemp.get("amount", 0) if isinstance(unemp, dict) else unemp
                for unemp in unemployment
            )
        return 0
    
    def _calculate_agi(self, total_income: float) -> float:
        """Calculate Adjusted Gross Income"""
        adjustments = self.get_section("adjustments")
        adjustment_keys = (
            "educator_expenses", "hsa_deduction", "self_employment_tax",
            "self_employed_sep", "self_employed_health", "student_loan_interest", "ira_deduction"
        )
        total_adjustments = sum(adjustments.get(key, 0) for key in adjustment_keys)
        return total_income - total_adjustments
    
    def _calculate_taxable_income(self, agi: float) -> float:
        """Calculate taxable income after deductions"""
        deductions = self.get_section("deductions")
        filing_status = self.get("filing_status.status")
        tax_year = self.data.get("metadata", {}).get("tax_year", 2025)
        
        if deductions.get("method") == "standard":
            deduction_amount = calculate_standard_deduction(filing_status, tax_year)
        else:
            # Itemized deductions
            itemized_keys = ("medical_expenses", "state_local_taxes", "mortgage_interest", "charitable_contributions")
            deduction_amount = sum(deductions.get(key, 0) for key in itemized_keys)
        
        return max(0, agi - deduction_amount)
    
    def _calculate_total_tax(self, taxable_income: float, filing_status: str, tax_year: int, income: Dict[str, Any]) -> float:
        """Calculate total tax including income tax and self-employment tax"""
        # Regular income tax
        income_tax = calculate_income_tax(taxable_income, filing_status, tax_year)
        
        # Self-employment tax (if applicable)
        business_income = income.get("business_income", [])
        se_tax = 0
        if business_income:
            # Sum all business income
            total_se_income = sum(biz.get("net_profit", 0) for biz in business_income) if isinstance(business_income, list) else business_income
            if total_se_income > 0:
                se_tax = calculate_self_employment_tax(total_se_income)
        
        return income_tax + se_tax
    
    def _calculate_total_payments(self, payments: Dict[str, Any]) -> float:
        """Calculate total payments from all sources"""
        total = 0
        
        # Federal withholding from W-2s
        w2_forms = self.get("income.w2_forms", [])
        total += sum(w2.get("federal_withholding", 0) for w2 in w2_forms)
        
        # Estimated payments
        estimated = payments.get("estimated_payments", [])
        if isinstance(estimated, list):
            total += sum(payment.get("amount", 0) for payment in estimated)
        else:
            total += estimated
        
        # Other payments
        total += payments.get("prior_year_overpayment", 0)
        total += payments.get("eic_payments", 0)
        
        return total
    
    @invalidate_cache_on_change
    def calculate_credits(self, agi: float) -> Dict[str, float]:
        """
        Calculate all tax credits (cached for performance)
        """
        credits = {
            "child_tax_credit": 0,
            "earned_income_credit": 0,
            "education_credits": 0,
            "retirement_savings_credit": 0,
            "child_dependent_care_credit": 0,
            "residential_energy_credit": 0,
            "premium_tax_credit": 0,
            "other_credits": 0,
            "total_credits": 0
        }
        
        # Performance: Direct access to nested data
        filing_status = self.data.get("filing_status", {}).get("status", "Single")
        
        # Child Tax Credit - automatically determine from dependents
        dependents = self.get("dependents", [])
        qualifying_children = []
        other_dependents = []
        
        for dependent in dependents:
            relationship = dependent.get("relationship", "").lower()
            birth_date = dependent.get("birth_date", "")
            months_lived = dependent.get("months_lived_in_home", 0)
            
            # Simple qualifying child logic (age < 17, lived with taxpayer more than half year)
            if relationship in ["son", "daughter", "child"] and months_lived >= 6:
                try:
                    # Parse birth date and check age (simplified)
                    birth_year = int(birth_date.split("/")[-1]) if "/" in birth_date else 2000
                    current_year = self.data.get("metadata", {}).get("tax_year", 2025)
                    age = current_year - birth_year
                    if age < 17:
                        qualifying_children.append(dependent)
                    else:
                        other_dependents.append(dependent)
                except:
                    other_dependents.append(dependent)
            else:
                other_dependents.append(dependent)
        
        if qualifying_children or other_dependents:
            credits["child_tax_credit"] = calculate_child_tax_credit(
                len(qualifying_children),
                len(other_dependents),
                agi,
                filing_status
            )
        
        # Performance: Earned Income Credit with optimized data access
        if qualifying_children:
            # Use centralized W2Calculator
            w2_forms = self.data.get("income", {}).get("w2_forms", [])
            earned_income = W2Calculator.calculate_total_wages(w2_forms)
            
            if earned_income > 0:
                credits["earned_income_credit"] = calculate_earned_income_credit(
                    earned_income,
                    agi,
                    len(qualifying_children),
                    filing_status
                )
        
        # Retirement Savings Credit
        retire_contrib = self.get("credits.retirement_savings_credit", 0)
        if retire_contrib > 0:
            credits["retirement_savings_credit"] = calculate_retirement_savings_credit(
                retire_contrib, agi, filing_status
            )
        
        # Child and Dependent Care Credit
        care_expenses = self.get("credits.child_dependent_care.expenses", 0)
        if care_expenses > 0:
            credits["child_dependent_care_credit"] = calculate_child_dependent_care_credit(
                care_expenses, agi, filing_status
            )
        
        # Residential Energy Credit
        energy_amount = self.get("credits.residential_energy.amount", 0)
        if energy_amount > 0:
            credits["residential_energy_credit"] = calculate_residential_energy_credit(energy_amount)
        
        # Premium Tax Credit
        premium_amount = self.get("credits.premium_tax_credit.amount", 0)
        if premium_amount > 0:
            credits["premium_tax_credit"] = calculate_premium_tax_credit(premium_amount)
        
        # Sum all credits
        credits["total_credits"] = sum([
            credits["child_tax_credit"],
            credits["earned_income_credit"],
            credits["education_credits"],
            credits["retirement_savings_credit"],
            credits["child_dependent_care_credit"],
            credits["residential_energy_credit"],
            credits["premium_tax_credit"],
            credits["other_credits"]
        ])
        
        return credits
    
    # Helper methods for common operations
    
    def add_w2_form(self, w2_data: Dict):
        """Add a W-2 form to income"""
        self.add_to_list("income.w2_forms", w2_data)
    
    def update_w2_form(self, index: int, w2_data: Dict):
        """Update an existing W-2 form"""
        w2_forms = self.get("income.w2_forms", [])
        if 0 <= index < len(w2_forms):
            w2_forms[index] = w2_data
            self.set("income.w2_forms", w2_forms)
    
    def delete_w2_form(self, index: int):
        """Delete a W-2 form"""
        self.remove_from_list("income.w2_forms", index)
    
    def add_dependent(self, dependent_data: Dict):
        """Add a dependent"""
        dependents = self.get("dependents", [])
        dependents.append(dependent_data)
        self.set("dependents", dependents)
    
    def update_dependent(self, index: int, dependent_data: Dict):
        """Update an existing dependent"""
        dependents = self.get("dependents", [])
        if 0 <= index < len(dependents):
            dependents[index] = dependent_data
            self.set("dependents", dependents)
    
    def delete_dependent(self, index: int):
        """Delete a dependent"""
        dependents = self.get("dependents", [])
        if 0 <= index < len(dependents):
            dependents.pop(index)
            self.set("dependents", dependents)
    
    # Encryption is now handled by EncryptionService
    # Legacy method removed - use self.encryption instead
    
    def _get_integrity_key(self) -> bytes:
        """Get key for HMAC integrity verification"""
        # Derive separate key from encryption key for HMAC
        key_material = self.config.key_file.read_bytes() if self.config.key_file.exists() else b'default_key'
        return hashlib.sha256(key_material + b'_integrity').digest()
    
    def _validate_path(self, filename: str) -> Path:
        """Validate file path to prevent directory traversal"""
        # Resolve to absolute path
        file_path = (self.config.safe_dir / filename).resolve()
        
        # Ensure path is within safe directory
        if not str(file_path).startswith(str(self.config.safe_dir.resolve())):
            logger.warning(f"Path traversal attempt detected: {filename}")
            raise ValueError("Invalid file path - must be within TaxReturns directory")
        
        return file_path
    
    @retry(max_attempts=3, delay=0.5, exceptions=(IOError, PermissionError, OSError))
    def save_to_file(self, filename: str = None) -> str:
        """Save encrypted tax data to file with integrity protection"""
        error_tracker = get_error_tracker()
        try:
            if filename is None:
                tax_year = self.get("metadata.tax_year")
                last_name = self.get("personal_info.last_name", "Unknown")
                filename = f"tax_return_{tax_year}_{last_name}.enc"
            
            # Validate and resolve path
            file_path = self._validate_path(filename)
            
            # Serialize data to JSON
            json_data = json.dumps(self.data, indent=2, sort_keys=True)
            
            # Calculate HMAC for integrity verification
            integrity_key = self._get_integrity_key()
            mac = hmac.new(integrity_key, json_data.encode(), hashlib.sha256).hexdigest()
            
            # Create data package with MAC
            data_package = {
                'data': self.data,
                'mac': mac,
                'version': '2.0'  # Encrypted version
            }
            
            # Encrypt entire package
            package_json = json.dumps(data_package)
            encrypted_data = self.encryption.encrypt(package_json)
            
            # Write encrypted data
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive file permissions (owner read/write only)
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
            
            logger.info(f"Saved encrypted tax return: {file_path.name}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save tax return: {e}")
            error_tracker.track_error(
                error=e,
                context={"operation": "save_file", "filename": filename},
                severity="ERROR",
                user_message="Could not save your tax return. Please check disk space and permissions."
            )
            raise
    
    @retry(max_attempts=3, delay=0.5, exceptions=(IOError, OSError))
    def load_from_file(self, filename: str):
        """Load and decrypt tax data from file with integrity verification"""
        error_tracker = get_error_tracker()
        try:
            file_path = self._resolve_file_path(filename)
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Try loading in order: encrypted with MAC, encrypted without MAC, plaintext
            self.data = self._load_file_data(file_data, file_path.name)
            self.data["metadata"]["last_modified"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Failed to load tax return: {e}")
            error_tracker.track_error(
                error=e,
                context={"operation": "load_file", "filename": filename},
                severity="ERROR",
                user_message="Could not load your tax return. The file may be corrupted or encrypted with a different key."
            )
            raise
    
    def _resolve_file_path(self, filename: str) -> Path:
        """Resolve and validate file path"""
        file_path = Path(filename)
        if not file_path.is_absolute():
            file_path = self._validate_path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Tax return file not found: {filename}")
        
        return file_path
    
    def _load_file_data(self, encrypted_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Load data from file, trying different formats.
        
        Tries in order:
        1. Encrypted format with MAC integrity check
        2. Encrypted format without MAC (legacy)
        3. Plaintext JSON (legacy)
        """
        try:
            return self._load_encrypted_data(encrypted_data, filename)
        except Exception as decrypt_error:
            return self._load_plaintext_fallback(encrypted_data, filename, decrypt_error)
    
    def _load_encrypted_data(self, encrypted_data: bytes, filename: str) -> Dict[str, Any]:
        """Load and decrypt encrypted tax data"""
        decrypted_data = self.encryption.decrypt(encrypted_data)
        data_package = json.loads(decrypted_data)
        
        if 'mac' in data_package and 'data' in data_package:
            # Verify integrity with MAC
            self._verify_data_integrity(data_package)
            logger.info(f"Loaded encrypted tax return with integrity check: {filename}")
            return data_package['data']
        else:
            # Old encrypted format without MAC
            logger.warning(f"Loaded encrypted file without integrity check: {filename}")
            return data_package
    
    def _verify_data_integrity(self, data_package: Dict[str, Any]):
        """Verify data integrity using HMAC"""
        json_data = json.dumps(data_package['data'], indent=2, sort_keys=True)
        integrity_key = self._get_integrity_key()
        expected_mac = hmac.new(integrity_key, json_data.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(expected_mac, data_package['mac']):
            logger.error("Data integrity check failed")
            raise ValueError("Data integrity verification failed - file may be corrupted or tampered")
    
    def _load_plaintext_fallback(self, file_data: bytes, filename: str, decrypt_error: Exception) -> Dict[str, Any]:
        """Try loading as plaintext JSON (legacy format)"""
        try:
            data = json.loads(file_data.decode('utf-8'))
            logger.warning(f"Loaded legacy plaintext file: {filename} - Consider re-saving with encryption")
            return data
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as e:
            # Plaintext load also failed - re-raise original decryption error
            logger.debug(f"Plaintext load failed: {e}")
            raise decrypt_error from e
    
    def to_dict(self) -> Dict:
        """Export data as dictionary"""
        return self.data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaxData':
        """Create TaxData object from dictionary"""
        instance = cls()
        instance.data = data.copy()
        # Ensure metadata exists
        if "metadata" not in instance.data:
            instance.data["metadata"] = {
                "tax_year": datetime.now().year - 1,
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "version": "1.0",
            }
        else:
            instance.data["metadata"]["last_modified"] = datetime.now().isoformat()
        return instance
    
    def detect_wash_sales(self) -> List[Dict]:
        """
        Detect potential wash sales in capital gains transactions.
        
        A wash sale occurs when you sell a security at a loss and buy the same or 
        substantially identical security within 30 days before or after the sale.
        
        Returns:
            List of dictionaries containing wash sale information
        """
        wash_sales = []
        capital_gains = self.get("income.capital_gains", [])
        
        for i, sale in enumerate(capital_gains):
            if sale.get('gain_loss', 0) >= 0:  # Only check losses
                continue
                
            sale_date = self._parse_date(sale.get('date_sold', ''))
            if not sale_date:
                continue
                
            description = sale.get('description', '').lower()
            
            # Check 30 days before and after sale
            start_date = sale_date - timedelta(days=30)
            end_date = sale_date + timedelta(days=30)
            
            for j, purchase in enumerate(capital_gains):
                if i == j:  # Don't compare with itself
                    continue
                    
                purchase_date = self._parse_date(purchase.get('date_acquired', ''))
                if not purchase_date:
                    continue
                    
                # Check if purchase is within 30-day window
                if start_date <= purchase_date <= end_date:
                    # Check if descriptions are similar (basic check)
                    purchase_desc = purchase.get('description', '').lower()
                    if self._are_similar_securities(description, purchase_desc):
                        wash_sales.append({
                            'sale_index': i,
                            'purchase_index': j,
                            'sale_description': sale.get('description'),
                            'purchase_description': purchase.get('description'),
                            'sale_date': sale.get('date_sold'),
                            'purchase_date': purchase.get('date_acquired'),
                            'loss_amount': abs(sale.get('gain_loss', 0)),
                            'days_between': abs((purchase_date - sale_date).days)
                        })
        
        return wash_sales
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        if not date_str:
            return None
        try:
            # Try MM/DD/YYYY format
            return datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            try:
                # Try YYYY-MM-DD format
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return None
    
    def _are_similar_securities(self, desc1: str, desc2: str) -> bool:
        """
        Check if two security descriptions represent substantially identical securities.
        For wash sale purposes, securities are considered identical if they represent
        the same company and same type of security (common stock, preferred, etc.).
        """
        if not desc1 or not desc2:
            return False
            
        # Normalize descriptions
        desc1_norm = desc1.lower().strip()
        desc2_norm = desc2.lower().strip()
        
        # Exact match
        if desc1_norm == desc2_norm:
            return True
            
        # Extract company name and security type
        def extract_company_and_type(desc: str) -> tuple:
            """Extract (company_name, security_type) from description"""
            # Common security type indicators
            security_types = ['common stock', 'preferred stock', 'bond', 'note', 'debenture']
            
            desc_lower = desc.lower()
            
            # Find security type
            security_type = None
            for st in security_types:
                if st in desc_lower:
                    security_type = st
                    # Remove security type from description to get company name
                    company_part = desc_lower.replace(st, '').strip()
                    break
            
            if not security_type:
                # If no security type found, assume it's common stock and use whole description as company
                company_part = desc_lower
                security_type = 'common stock'
            
            # Clean up company name - remove extra spaces, punctuation, and class designations
            company_part = ' '.join(company_part.split())  # normalize spaces
            company_part = company_part.replace(',', '').replace('.', '').strip()
            
            # Remove class designations (Class A, Class B, Series A, etc.) as they don't affect wash sale similarity
            import re
            company_part = re.sub(r'\bclass\s+[a-zA-Z0-9]+\b', '', company_part, flags=re.IGNORECASE)
            company_part = re.sub(r'\bseries\s+[a-zA-Z0-9]+\b', '', company_part, flags=re.IGNORECASE)
            company_part = ' '.join(company_part.split())  # normalize spaces again
            
            return company_part, security_type
        
        company1, type1 = extract_company_and_type(desc1_norm)
        company2, type2 = extract_company_and_type(desc2_norm)
        
        # Must be same security type
        if type1 != type2:
            return False
            
        # Company names must be very similar (allowing for minor differences)
        # For simplicity, check if one contains the other or they differ by only common variations
        if company1 == company2:
            return True
            
        # Check if one is substring of the other (handles abbreviations, etc.)
        if company1 in company2 or company2 in company1:
            return True
            
        # Handle common variations (Inc vs Inc., Corp vs Corporation, etc.)
        variations = {
            'inc': ['inc.', 'incorporated'],
            'corp': ['corp.', 'corporation'],
            'ltd': ['ltd.', 'limited'],
            'co': ['co.', 'company']
        }
        
        for base, variants in variations.items():
            for variant in variants:
                if base in company1 and variant in company2:
                    # Replace variant with base and compare
                    c1_normalized = company1.replace(base, '').replace(variant, '').strip()
                    c2_normalized = company2.replace(base, '').replace(variant, '').strip()
                    if c1_normalized == c2_normalized:
                        return True
                if variant in company1 and base in company2:
                    c1_normalized = company1.replace(variant, '').replace(base, '').strip()
                    c2_normalized = company2.replace(variant, '').replace(base, '').strip()
                    if c1_normalized == c2_normalized:
                        return True
        
        return False
    
    def save(self, filename: str):
        """Save tax data to file (alias for save_to_file)"""
        return self.save_to_file(filename)
    
    @classmethod
    def load(cls, filename: str) -> 'TaxData':
        """Load tax data from file"""
        instance = cls()
        instance.load_from_file(filename)
        return instance
