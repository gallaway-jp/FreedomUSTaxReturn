"""
Tax Interview Service - Intelligent question-based tax form guidance

Provides a conversational interface to determine which tax forms and information
a user needs to report, guiding them through the tax preparation process.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from services.exceptions import (
    InvalidInputException,
    DataValidationException,
    ServiceExecutionException
)
from services.error_logger import get_error_logger


class QuestionType(Enum):
    """Types of questions that can be asked"""
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERIC = "numeric"
    TEXT = "text"
    DATE = "date"


class FormCategory(Enum):
    """Categories of tax forms"""
    PERSONAL_INFO = "personal_info"
    FILING_STATUS = "filing_status"
    DEPENDENTS = "dependents"
    INCOME = "income"
    DEDUCTIONS = "deductions"
    CREDITS = "credits"
    PAYMENTS = "payments"
    BUSINESS = "business"
    INVESTMENTS = "investments"
    FOREIGN = "foreign"
    ESTATE_TRUST = "estate_trust"
    CRYPTO = "crypto"
    AMENDMENT = "amendment"


@dataclass
class InterviewQuestion:
    """Represents a single question in the tax interview"""
    id: str
    text: str
    question_type: QuestionType
    category: FormCategory
    options: Optional[List[str]] = None
    help_text: Optional[str] = None
    required: bool = True
    conditional_logic: Optional[Dict[str, Any]] = None
    follow_up_questions: Optional[List[str]] = None


@dataclass
class InterviewAnswer:
    """Represents an answer to an interview question"""
    question_id: str
    answer: Any
    timestamp: str
    confidence: float = 1.0


@dataclass
class FormRecommendation:
    """Recommendation for a specific tax form"""
    form_name: str
    category: FormCategory
    priority: int  # 1-10, higher = more important
    reason: str
    required_fields: List[str]
    estimated_time: int  # minutes to complete
    help_resources: List[str]


class TaxInterviewService:
    """
    Service for conducting intelligent tax interviews to determine
    which forms and information a user needs to report.
    """

    def __init__(self, config: 'AppConfig'):
        """
        Initialize the tax interview service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.questions = self._load_questions()
        self.answers: Dict[str, InterviewAnswer] = {}
        self.recommendations: List[FormRecommendation] = []

    def _load_questions(self) -> Dict[str, InterviewQuestion]:
        """Load interview questions from data file"""
        questions_file = Path(__file__).parent.parent / "data" / "tax_interview_questions.json"

        if not questions_file.exists():
            return self._get_default_questions()

        try:
            with open(questions_file, 'r') as f:
                data = json.load(f)

            questions = {}
            for q_data in data.get('questions', []):
                question = InterviewQuestion(
                    id=q_data['id'],
                    text=q_data['text'],
                    question_type=QuestionType(q_data['type']),
                    category=FormCategory(q_data['category']),
                    options=q_data.get('options'),
                    help_text=q_data.get('help_text'),
                    required=q_data.get('required', True),
                    conditional_logic=q_data.get('conditional_logic'),
                    follow_up_questions=q_data.get('follow_up_questions', [])
                )
                questions[q_data['id']] = question

            return questions

        except Exception as e:
            print(f"Error loading questions: {e}")
            return self._get_default_questions()

    def _get_default_questions(self) -> Dict[str, InterviewQuestion]:
        """Get default interview questions if file doesn't exist"""
        return {
            "income_employment": InterviewQuestion(
                id="income_employment",
                text="Did you receive a W-2 form from an employer this year?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.INCOME,
                help_text="A W-2 is the form your employer sends showing your wages and taxes withheld. Check your mail or your employer's payroll website.",
                follow_up_questions=["income_multiple_jobs"]
            ),
            "income_multiple_jobs": InterviewQuestion(
                id="income_multiple_jobs",
                text="How many W-2 forms did you receive?",
                question_type=QuestionType.NUMERIC,
                category=FormCategory.INCOME,
                conditional_logic={"depends_on": "income_employment", "value": True}
            ),
            "income_business": InterviewQuestion(
                id="income_business",
                text="Did you have self-employment income (Schedule C business)?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.BUSINESS,
                help_text="This includes income from freelancing, consulting, or running your own business. You'll need records of your business expenses."
            ),
            "income_investments": InterviewQuestion(
                id="income_investments",
                text="Did you receive any investment income (interest, dividends, capital gains)?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.INVESTMENTS,
                help_text="This includes 1099-INT (interest), 1099-DIV (dividends), or 1099-B (stock sales). Check statements from banks, brokerages, or mutual funds."
            ),
            "income_crypto": InterviewQuestion(
                id="income_crypto",
                text="Did you buy, sell, or trade cryptocurrency this year?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.CRYPTO,
                help_text="This includes Bitcoin, Ethereum, and other digital currencies. You'll need records of all transactions."
            ),
            "income_foreign": InterviewQuestion(
                id="income_foreign",
                text="Did you have any foreign income or foreign bank accounts?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.FOREIGN,
                help_text="This includes income earned outside the US or accounts in foreign banks. Foreign accounts over $10,000 must be reported on FBAR."
            ),
            "deductions_home": InterviewQuestion(
                id="deductions_home",
                text="Did you own a home or pay mortgage interest?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.DEDUCTIONS,
                help_text="Mortgage interest and property taxes may be deductible. You'll need Form 1098 from your lender."
            ),
            "deductions_medical": InterviewQuestion(
                id="deductions_medical",
                text="Did you have significant medical expenses?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.DEDUCTIONS,
                help_text="Medical expenses are deductible if they exceed 7.5% of your adjusted gross income. Keep receipts for doctor visits, prescriptions, etc."
            ),
            "deductions_charity": InterviewQuestion(
                id="deductions_charity",
                text="Did you make charitable donations?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.DEDUCTIONS,
                help_text="Cash donations and non-cash donations may be deductible. Keep receipts for donations over $250."
            ),
            "credits_children": InterviewQuestion(
                id="credits_children",
                text="Do you have children under 17 years old?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.CREDITS,
                help_text="You may qualify for the Child Tax Credit if you have qualifying children. You'll need their Social Security numbers."
            ),
            "credits_education": InterviewQuestion(
                id="credits_education",
                text="Did you or your dependents attend college?",
                question_type=QuestionType.YES_NO,
                category=FormCategory.CREDITS,
                help_text="You may qualify for education credits like the American Opportunity Credit. You'll need Form 1098-T from the school."
            )
        }

    def start_interview(self) -> List[InterviewQuestion]:
        """
        Start a new tax interview and return initial questions.

        Returns:
            List of initial questions to ask
        """
        self.answers.clear()
        self.recommendations.clear()

        # Return questions that don't have conditional logic
        initial_questions = []
        for question in self.questions.values():
            if not question.conditional_logic:
                initial_questions.append(question)

        return initial_questions

    def answer_question(self, question_id: str, answer: Any) -> Dict[str, Any]:
        """
        Record an answer and return next questions or recommendations.

        Args:
            question_id: ID of the question being answered
            answer: The user's answer

        Returns:
            Dict containing next questions and any form recommendations
        """
        from datetime import datetime

        # Record the answer
        interview_answer = InterviewAnswer(
            question_id=question_id,
            answer=answer,
            timestamp=datetime.now().isoformat(),
            confidence=1.0
        )
        self.answers[question_id] = interview_answer

        # Get follow-up questions
        next_questions = []
        if question_id in self.questions:
            question = self.questions[question_id]
            if question.follow_up_questions:
                for follow_up_id in question.follow_up_questions:
                    if follow_up_id in self.questions:
                        follow_up = self.questions[follow_up_id]
                        # Check conditional logic
                        if self._check_conditional_logic(follow_up):
                            next_questions.append(follow_up)

        # Generate recommendations based on answers
        self._update_recommendations()

        return {
            "next_questions": next_questions,
            "recommendations": self.recommendations,
            "completed": len(next_questions) == 0 and len(self.recommendations) > 0
        }

    def _check_conditional_logic(self, question: InterviewQuestion) -> bool:
        """Check if a question's conditional logic is satisfied"""
        if not question.conditional_logic:
            return True

        depends_on = question.conditional_logic.get("depends_on")
        required_value = question.conditional_logic.get("value")

        if depends_on in self.answers:
            return self.answers[depends_on].answer == required_value

        return False

    def _update_recommendations(self):
        """Update form recommendations based on current answers"""
        self.recommendations.clear()

        # Basic Form 1040 is always needed
        self.recommendations.append(FormRecommendation(
            form_name="Form 1040",
            category=FormCategory.PERSONAL_INFO,
            priority=10,
            reason="Main individual income tax return",
            required_fields=["personal_info", "filing_status"],
            estimated_time=30,
            help_resources=["IRS Publication 17", "Form 1040 Instructions"]
        ))

        # Check for W-2 income
        if self.answers.get("income_employment") and self.answers["income_employment"].answer:
            self.recommendations.append(FormRecommendation(
                form_name="W-2 Income",
                category=FormCategory.INCOME,
                priority=9,
                reason="You reported receiving W-2 forms from employers",
                required_fields=["w2_forms"],
                estimated_time=15,
                help_resources=["W-2 Instructions", "Where to find W-2"]
            ))

        # Check for business income
        if self.answers.get("income_business") and self.answers["income_business"].answer:
            self.recommendations.append(FormRecommendation(
                form_name="Schedule C",
                category=FormCategory.BUSINESS,
                priority=8,
                reason="You reported self-employment income",
                required_fields=["business_income", "business_expenses"],
                estimated_time=45,
                help_resources=["Schedule C Instructions", "IRS Publication 334"]
            ))

        # Check for investments
        if self.answers.get("income_investments") and self.answers["income_investments"].answer:
            self.recommendations.append(FormRecommendation(
                form_name="Schedule B",
                category=FormCategory.INVESTMENTS,
                priority=7,
                reason="You reported investment income",
                required_fields=["interest_income", "dividend_income"],
                estimated_time=20,
                help_resources=["Schedule B Instructions", "1099 Forms"]
            ))

        # Check for crypto
        if self.answers.get("income_crypto") and self.answers["income_crypto"].answer:
            self.recommendations.append(FormRecommendation(
                form_name="Form 8949",
                category=FormCategory.CRYPTO,
                priority=6,
                reason="You reported cryptocurrency transactions",
                required_fields=["crypto_transactions"],
                estimated_time=60,
                help_resources=["IRS Crypto Tax Guide", "Form 8949 Instructions"]
            ))

        # Check for foreign accounts
        if self.answers.get("income_foreign") and self.answers["income_foreign"].answer:
            self.recommendations.append(FormRecommendation(
                form_name="FBAR",
                category=FormCategory.FOREIGN,
                priority=5,
                reason="You reported foreign bank accounts",
                required_fields=["foreign_accounts"],
                estimated_time=30,
                help_resources=["FBAR Instructions", "FinCEN Form 114"]
            ))

        # Check for deductions
        deduction_count = 0
        if self.answers.get("deductions_home") and self.answers["deductions_home"].answer:
            deduction_count += 1
        if self.answers.get("deductions_medical") and self.answers["deductions_medical"].answer:
            deduction_count += 1
        if self.answers.get("deductions_charity") and self.answers["deductions_charity"].answer:
            deduction_count += 1

        if deduction_count > 0:
            self.recommendations.append(FormRecommendation(
                form_name="Schedule A",
                category=FormCategory.DEDUCTIONS,
                priority=7,
                reason=f"You reported {deduction_count} types of deductions",
                required_fields=["itemized_deductions"],
                estimated_time=25,
                help_resources=["Schedule A Instructions"]
            ))

        # Check for credits
        if self.answers.get("credits_children") and self.answers["credits_children"].answer:
            self.recommendations.append(FormRecommendation(
                form_name="Child Tax Credit",
                category=FormCategory.CREDITS,
                priority=8,
                reason="You have children under 17",
                required_fields=["dependents", "child_tax_credit"],
                estimated_time=10,
                help_resources=["Child Tax Credit Information"]
            ))

        if self.answers.get("credits_education") and self.answers["credits_education"].answer:
            self.recommendations.append(FormRecommendation(
                form_name="Education Credits",
                category=FormCategory.CREDITS,
                priority=6,
                reason="You or dependents attended college",
                required_fields=["education_expenses"],
                estimated_time=15,
                help_resources=["Education Credit Information"]
            ))

        # Sort by priority
        self.recommendations.sort(key=lambda x: x.priority, reverse=True)

    def get_progress_percentage(self) -> float:
        """
        Get the completion percentage of the interview.

        Returns:
            Percentage complete (0-100)
        """
        total_questions = len(self.questions)
        answered_questions = len(self.answers)

        if total_questions == 0:
            return 100.0

        return min(100.0, (answered_questions / total_questions) * 100.0)

    def get_answers_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all answers given.

        Returns:
            Dict containing answer summary
        """
        total_estimated_time = sum(rec.estimated_time for rec in self.recommendations)

        return {
            "total_questions_answered": len(self.answers),
            "total_recommendations": len(self.recommendations),
            "estimated_total_time": total_estimated_time,
            "progress_percentage": self.get_progress_percentage(),
            "answers": {qid: answer.answer for qid, answer in self.answers.items()},
            "recommendations": [
                {
                    "form": rec.form_name,
                    "category": rec.category.value,
                    "priority": rec.priority,
                    "reason": rec.reason
                }
                for rec in self.recommendations
            ]
        }

    def reset_interview(self):
        """Reset the interview to start over"""
        self.answers.clear()
        self.recommendations.clear()