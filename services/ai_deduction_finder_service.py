"""
AI-Powered Deduction Finder Service

This service uses intelligent analysis to identify potential tax deductions
that users might have missed based on their income, expenses, and lifestyle data.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService
from utils.error_tracker import get_error_tracker

logger = logging.getLogger(__name__)


class DeductionCategory(Enum):
    """Categories of potential deductions"""
    MEDICAL = "medical"
    CHARITABLE = "charitable"
    BUSINESS = "business"
    EDUCATION = "education"
    HOME_OFFICE = "home_office"
    VEHICLE = "vehicle"
    RETIREMENT = "retirement"
    ENERGY = "energy"
    STATE_LOCAL = "state_local"
    MISCELLANEOUS = "miscellaneous"


class ConfidenceLevel(Enum):
    """Confidence levels for deduction suggestions"""
    HIGH = "high"      # Very likely deduction available
    MEDIUM = "medium"  # Possible deduction, needs verification
    LOW = "low"        # Speculative, requires more information


@dataclass
class DeductionSuggestion:
    """A potential tax deduction suggestion"""

    category: DeductionCategory
    title: str
    description: str
    potential_savings: float
    confidence: ConfidenceLevel
    requirements: List[str]
    evidence: List[str]
    form_reference: str
    priority: int  # 1-10, higher is more important
    suggested_action: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'category': self.category.value,
            'title': self.title,
            'description': self.description,
            'potential_savings': self.potential_savings,
            'confidence': self.confidence.value,
            'requirements': self.requirements,
            'evidence': self.evidence,
            'form_reference': self.form_reference,
            'priority': self.priority,
            'suggested_action': self.suggested_action
        }


@dataclass
class DeductionAnalysisResult:
    """Complete analysis result with all suggestions"""

    tax_year: int
    total_potential_savings: float
    suggestions: List[DeductionSuggestion]
    analyzed_categories: List[str]
    analysis_date: datetime
    data_completeness_score: float  # 0-100, how complete the user's data is

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'tax_year': self.tax_year,
            'total_potential_savings': self.total_potential_savings,
            'suggestions': [s.to_dict() for s in self.suggestions],
            'analyzed_categories': self.analyzed_categories,
            'analysis_date': self.analysis_date.isoformat(),
            'data_completeness_score': self.data_completeness_score
        }


class AIDeductionFinderService:
    """
    AI-powered service to find potential tax deductions.

    Uses intelligent analysis of tax data, income sources, expenses,
    and lifestyle indicators to suggest deductions that users might
    have missed.
    """

    def __init__(self, config: AppConfig, tax_calculation_service: TaxCalculationService):
        """
        Initialize the AI deduction finder service.

        Args:
            config: Application configuration
            tax_calculation_service: Service for tax calculations
        """
        self.config = config
        self.tax_calculation = tax_calculation_service
        self.error_tracker = get_error_tracker()

    def analyze_deductions(self, tax_data: TaxData) -> DeductionAnalysisResult:
        """
        Perform comprehensive deduction analysis on tax data.

        Args:
            tax_data: Complete tax data to analyze

        Returns:
            Analysis result with potential deductions
        """
        try:
            suggestions = []
            analyzed_categories = []

            # Calculate data completeness score
            completeness_score = self._calculate_data_completeness(tax_data)

            # Analyze different categories of deductions
            suggestions.extend(self._analyze_medical_deductions(tax_data))
            analyzed_categories.append("medical")

            suggestions.extend(self._analyze_charitable_deductions(tax_data))
            analyzed_categories.append("charitable")

            suggestions.extend(self._analyze_business_deductions(tax_data))
            analyzed_categories.append("business")

            suggestions.extend(self._analyze_education_deductions(tax_data))
            analyzed_categories.append("education")

            suggestions.extend(self._analyze_home_office_deductions(tax_data))
            analyzed_categories.append("home_office")

            suggestions.extend(self._analyze_vehicle_deductions(tax_data))
            analyzed_categories.append("vehicle")

            suggestions.extend(self._analyze_retirement_deductions(tax_data))
            analyzed_categories.append("retirement")

            suggestions.extend(self._analyze_energy_deductions(tax_data))
            analyzed_categories.append("energy")

            suggestions.extend(self._analyze_state_local_deductions(tax_data))
            analyzed_categories.append("state_local")

            # Sort suggestions by priority and potential savings
            suggestions.sort(key=lambda x: (x.priority, x.potential_savings), reverse=True)

            # Calculate total potential savings
            total_savings = sum(s.potential_savings for s in suggestions)

            return DeductionAnalysisResult(
                tax_year=tax_data.get_current_year(),
                total_potential_savings=total_savings,
                suggestions=suggestions,
                analyzed_categories=analyzed_categories,
                analysis_date=datetime.now(),
                data_completeness_score=completeness_score
            )

        except Exception as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "analyze_deductions", "tax_year": tax_data.get_current_year()}
            )
            # Return empty result on error
            return DeductionAnalysisResult(
                tax_year=tax_data.get_current_year(),
                total_potential_savings=0.0,
                suggestions=[],
                analyzed_categories=[],
                analysis_date=datetime.now(),
                data_completeness_score=0.0
            )

    def _calculate_data_completeness(self, tax_data: TaxData) -> float:
        """
        Calculate how complete the user's tax data is (0-100).

        Args:
            tax_data: Tax data to evaluate

        Returns:
            Completeness score as percentage
        """
        score = 0.0
        max_score = 0.0

        # Personal info (20 points)
        personal_info = tax_data.get('personal_info', {})
        if personal_info.get('first_name'): score += 5
        if personal_info.get('last_name'): score += 5
        if personal_info.get('ssn'): score += 5
        if personal_info.get('address'): score += 5
        max_score += 20

        # Filing status (10 points)
        filing_status = tax_data.get('filing_status', {})
        if filing_status.get('status'): score += 10
        max_score += 10

        # Income data (30 points)
        income = tax_data.get('income', {})
        if income.get('w2_forms'): score += 10
        if income.get('interest_income') or income.get('dividend_income'): score += 10
        if income.get('business_income') or income.get('self_employment'): score += 10
        max_score += 30

        # Deductions (20 points)
        deductions = tax_data.get('deductions', {})
        if deductions.get('method'): score += 10
        if deductions.get('medical_expenses') or deductions.get('charitable_contributions'): score += 10
        max_score += 20

        # Credits (10 points)
        credits = tax_data.get('credits', {})
        if credits.get('child_tax_credit') or credits.get('earned_income_credit'): score += 10
        max_score += 10

        # Dependents (10 points)
        if tax_data.get('dependents'): score += 10
        max_score += 10

        return (score / max_score) * 100 if max_score > 0 else 0.0

    def _analyze_medical_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential medical expense deductions.

        Medical expenses are deductible if they exceed 7.5% of AGI.
        """
        suggestions = []

        # Get current medical expenses
        deductions = tax_data.get('deductions', {})
        current_medical = deductions.get('medical_expenses', 0)

        # Calculate AGI to determine threshold
        agi = tax_data.calculate_agi()
        threshold = agi * Decimal('0.075')

        # Check if user has dependents (children often have medical expenses)
        dependents = tax_data.get('dependents', [])
        has_children = any(d.get('relationship') in ['child', 'son', 'daughter'] for d in dependents)

        if has_children and current_medical < threshold:
            # Suggest checking for unreported medical expenses
            potential_savings = min(threshold * Decimal('0.5'), Decimal('2000'))  # Estimate based on common expenses

            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.MEDICAL,
                title="Medical Expense Deduction",
                description="You may be able to deduct medical expenses that exceed 7.5% of your adjusted gross income.",
                potential_savings=potential_savings,
                confidence=ConfidenceLevel.MEDIUM,
                requirements=[
                    "Medical expenses must exceed 7.5% of AGI",
                    "Expenses must be for prevention, treatment, or rehabilitation",
                    "Keep detailed records and receipts"
                ],
                evidence=[
                    f"You have {len([d for d in dependents if d.get('relationship') in ['child', 'son', 'daughter']])} dependent children",
                    f"Your AGI is ${agi:,.0f}, threshold is ${threshold:,.0f}",
                    f"Currently reported medical expenses: ${current_medical:,.0f}"
                ],
                form_reference="Schedule A (Form 1040)",
                priority=8,
                suggested_action="Review medical bills, prescriptions, and insurance payments from the past year"
            ))

        return suggestions

    def _analyze_charitable_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential charitable contribution deductions.
        """
        suggestions = []

        # Get current charitable contributions
        deductions = tax_data.get('deductions', {})
        current_charitable = deductions.get('charitable_contributions', 0)

        # Get income level to estimate potential donations
        total_income = tax_data.calculate_total_income()

        # People with higher incomes often make charitable contributions
        if total_income > 50000 and current_charitable < total_income * Decimal('0.02'):
            # Suggest checking for unreported charitable contributions
            potential_savings = min(total_income * Decimal('0.03'), Decimal('5000'))  # Estimate 3% of income

            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.CHARITABLE,
                title="Charitable Contributions",
                description="Cash and non-cash donations to qualified charities may be tax deductible.",
                potential_savings=potential_savings,
                confidence=ConfidenceLevel.MEDIUM,
                requirements=[
                    "Donations must be to qualified 501(c)(3) organizations",
                    "Keep receipts for cash donations over $250",
                    "Get appraisals for non-cash donations over $500"
                ],
                evidence=[
                    f"Your income level suggests potential for charitable giving",
                    f"Currently reported charitable contributions: ${current_charitable:,.0f}"
                ],
                form_reference="Schedule A (Form 1040)",
                priority=7,
                suggested_action="Review bank statements and credit card records for charitable donations"
            ))

        return suggestions

    def _analyze_business_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential business expense deductions.
        """
        suggestions = []

        # Check if user has any self-employment or business income
        income = tax_data.get('income', {})
        has_business_income = bool(income.get('self_employment') or income.get('business_income'))

        if has_business_income:
            # Check for home office deduction
            business_data = income.get('self_employment', [{}])[0] if income.get('self_employment') else {}
            has_home_office = business_data.get('home_office_percentage', 0) > 0

            if not has_home_office:
                # Suggest home office deduction if they work from home
                potential_savings = 2000  # Estimate based on average home office deduction

                suggestions.append(DeductionSuggestion(
                    category=DeductionCategory.HOME_OFFICE,
                    title="Home Office Deduction",
                    description="Self-employed individuals can deduct a portion of home expenses for space used exclusively for business.",
                    potential_savings=potential_savings,
                    confidence=ConfidenceLevel.MEDIUM,
                    requirements=[
                        "Space must be used exclusively and regularly for business",
                        "Space must be the principal place of business or used for meeting clients",
                        "Calculate square footage percentage accurately"
                    ],
                    evidence=[
                        "You have self-employment or business income",
                        "No home office deduction currently claimed"
                    ],
                    form_reference="Schedule C (Form 1040)",
                    priority=9,
                    suggested_action="Measure the square footage used for business and calculate the percentage of your home"
                ))

            # Check for vehicle expenses
            has_vehicle_expenses = business_data.get('vehicle_expenses', 0) > 0

            if not has_vehicle_expenses:
                suggestions.append(DeductionSuggestion(
                    category=DeductionCategory.VEHICLE,
                    title="Business Vehicle Expenses",
                    description="Mileage, gas, maintenance, and depreciation for business use of personal vehicles.",
                    potential_savings=1500,
                    confidence=ConfidenceLevel.LOW,
                    requirements=[
                        "Keep detailed mileage logs",
                        "Track business vs. personal use",
                        "Choose standard mileage rate OR actual expenses (not both)"
                    ],
                    evidence=[
                        "Self-employed individuals often use vehicles for business",
                        "No vehicle expenses currently reported"
                    ],
                    form_reference="Schedule C (Form 1040)",
                    priority=6,
                    suggested_action="Track business mileage for one month to establish usage patterns"
                ))

        return suggestions

    def _analyze_education_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential education-related deductions and credits.
        """
        suggestions = []

        # Check for student loan interest
        adjustments = tax_data.get('adjustments', {})
        student_loan_interest = adjustments.get('student_loan_interest', 0)

        # Check if user might have student loans (based on age and income patterns)
        personal_info = tax_data.get('personal_info', {})
        age = self._calculate_age(personal_info.get('date_of_birth', ''))

        if age and 25 <= age <= 45 and student_loan_interest == 0:
            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.EDUCATION,
                title="Student Loan Interest Deduction",
                description="Deduct up to $2,500 of interest paid on qualified student loans.",
                potential_savings=2500,
                confidence=ConfidenceLevel.LOW,
                requirements=[
                    "Loans must be for qualified education expenses",
                    "You must be legally obligated to repay the loan",
                    "Income phase-out limits apply"
                ],
                evidence=[
                    f"Age {age} suggests possible student loan debt",
                    "No student loan interest currently reported"
                ],
                form_reference="Schedule 1 (Form 1040)",
                priority=5,
                suggested_action="Check 1098-E forms from lenders for interest paid"
            ))

        return suggestions

    def _analyze_home_office_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential home office deductions for employees.
        """
        suggestions = []

        # Check if user is W-2 employee (not self-employed)
        income = tax_data.get('income', {})
        w2_forms = income.get('w2_forms', [])
        has_w2_income = len(w2_forms) > 0

        # Check if they might work from home
        personal_info = tax_data.get('personal_info', {})
        # This is speculative - in a real implementation, we'd ask about work-from-home status

        if has_w2_income:
            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.HOME_OFFICE,
                title="Employee Home Office (Unreimbursed)",
                description="Employees can deduct unreimbursed home office expenses if they work from home for employer's convenience.",
                potential_savings=800,
                confidence=ConfidenceLevel.LOW,
                requirements=[
                    "Home office must be for employer's convenience",
                    "Not available if you receive employer reimbursement",
                    "Simplified method: $5 per square foot up to 300 sq ft"
                ],
                evidence=[
                    "You have W-2 employment income",
                    "Many employees now work from home"
                ],
                form_reference="Schedule 1 (Form 1040)",
                priority=4,
                suggested_action="Confirm if you work from home for your employer's convenience"
            ))

        return suggestions

    def _analyze_vehicle_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential vehicle-related deductions.
        """
        suggestions = []

        # Check for medical vehicle use
        deductions = tax_data.get('deductions', {})
        medical_expenses = deductions.get('medical_expenses', 0)

        if medical_expenses > 0:
            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.MEDICAL,
                title="Medical Transportation Expenses",
                description="Mileage for medical appointments may be deductible as medical expenses.",
                potential_savings=500,
                confidence=ConfidenceLevel.LOW,
                requirements=[
                    "Transportation must be primarily for medical care",
                    "Use standard medical mileage rate (65.5 cents per mile in 2023)",
                    "Keep detailed records of trips"
                ],
                evidence=[
                    f"You have ${medical_expenses:,.0f} in medical expenses",
                    "Medical transportation is often overlooked"
                ],
                form_reference="Schedule A (Form 1040)",
                priority=3,
                suggested_action="Track mileage for doctor visits, hospital trips, and pharmacy runs"
            ))

        return suggestions

    def _analyze_retirement_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential retirement contribution deductions.
        """
        suggestions = []

        # Check current retirement contributions
        adjustments = tax_data.get('adjustments', {})
        ira_deduction = adjustments.get('ira_deduction', 0)

        # Get income and filing status
        total_income = tax_data.calculate_total_income()
        filing_status = tax_data.get('filing_status', {}).get('status', 'Single')

        # Estimate potential IRA contribution limit
        if filing_status == 'Single':
            ira_limit = 7000 if total_income < 100000 else 0  # Simplified
        else:
            ira_limit = 14000 if total_income < 100000 else 0  # Simplified

        if ira_limit > 0 and ira_deduction < ira_limit * Decimal('0.5'):
            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.RETIREMENT,
                title="Traditional IRA Deduction",
                description="Contributions to a Traditional IRA may be tax deductible.",
                potential_savings=min(ira_limit, 3000),
                confidence=ConfidenceLevel.MEDIUM,
                requirements=[
                    "Must have earned income",
                    "Contributions must be made by tax filing deadline",
                    "Income limits apply for deductibility"
                ],
                evidence=[
                    f"Income level suggests IRA eligibility",
                    f"Currently reported IRA deduction: ${ira_deduction:,.0f}"
                ],
                form_reference="Schedule 1 (Form 1040)",
                priority=7,
                suggested_action="Check if you contributed to a Traditional IRA this year"
            ))

        return suggestions

    def _analyze_energy_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential energy efficiency deductions/credits.
        """
        suggestions = []

        # Check if user has residential energy credits
        credits = tax_data.get('credits', {})
        energy_credit = credits.get('residential_energy', {}).get('amount', 0)

        if energy_credit == 0:
            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.ENERGY,
                title="Energy Efficient Home Improvements",
                description="Tax credits available for solar panels, energy-efficient windows, and electrical upgrades.",
                potential_savings=2000,
                confidence=ConfidenceLevel.LOW,
                requirements=[
                    "Must be your primary residence",
                    "Improvements must meet energy efficiency standards",
                    "Keep receipts and certifications"
                ],
                evidence=[
                    "Many homeowners qualify for energy credits",
                    "No energy credits currently claimed"
                ],
                form_reference="Form 5695",
                priority=4,
                suggested_action="Check if you installed solar panels, new windows, or electrical upgrades"
            ))

        return suggestions

    def _analyze_state_local_deductions(self, tax_data: TaxData) -> List[DeductionSuggestion]:
        """
        Analyze potential state and local tax deductions.
        """
        suggestions = []

        # Check current state/local taxes paid
        deductions = tax_data.get('deductions', {})
        state_local_taxes = deductions.get('state_local_taxes', 0)

        # SALT deduction limit is $10,000 for single filers
        salt_limit = 10000
        filing_status = tax_data.get('filing_status', {}).get('status', 'Single')

        if filing_status in ['Married Filing Jointly', 'Qualifying Surviving Spouse']:
            salt_limit = 20000

        if state_local_taxes < salt_limit * Decimal('0.8'):  # If reporting less than 80% of limit
            potential_additional = min(salt_limit - state_local_taxes, 2000)

            suggestions.append(DeductionSuggestion(
                category=DeductionCategory.STATE_LOCAL,
                title="State and Local Taxes (SALT)",
                description="Deduct state income taxes, property taxes, and local taxes up to $10,000 ($20,000 for joint filers).",
                potential_savings=potential_additional,
                confidence=ConfidenceLevel.MEDIUM,
                requirements=[
                    f"Deduction limited to ${salt_limit:,.0f} for your filing status",
                    "Includes state income tax, property tax, and local taxes",
                    "Does not include sales tax (alternative option)"
                ],
                evidence=[
                    f"Your filing status allows up to ${salt_limit:,.0f} SALT deduction",
                    f"Currently reported: ${state_local_taxes:,.0f}"
                ],
                form_reference="Schedule A (Form 1040)",
                priority=6,
                suggested_action="Review state tax returns and property tax bills for additional deductions"
            ))

        return suggestions

    def _calculate_age(self, birth_date_str: str) -> Optional[int]:
        """
        Calculate age from birth date string.

        Args:
            birth_date_str: Date string in format MM/DD/YYYY

        Returns:
            Age in years, or None if invalid date
        """
        try:
            if not birth_date_str:
                return None
            birth_date = datetime.strptime(birth_date_str, '%m/%d/%Y').date()
            today = date.today()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
        except ValueError:
            return None