"""
Modern Tax Interview Page - Multi-step interview with navigation

A page-based interview system that guides users through tax form selection
with forward/backward navigation, ability to skip, and integrate with tax forms page.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any, List
import threading

from config.app_config import AppConfig
from services.tax_interview_service import TaxInterviewService, InterviewQuestion, QuestionType, FormCategory
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernRadioGroup,
    ModernCheckBox, ModernEntry, show_info_message, show_error_message,
    show_confirmation, ModernProgressBar
)


class ModernTaxInterviewPage(ctk.CTkScrollableFrame):
    """
    Modern tax interview page with multi-step navigation.

    Features:
    - Progressive question-based interview
    - Forward/backward navigation
    - Skip interview option
    - Form recommendations based on answers
    - Integration with tax forms selection
    """

    def __init__(
        self,
        parent,
        config: AppConfig,
        accessibility_service: Optional[AccessibilityService] = None,
        on_complete: Optional[Callable] = None,
        on_skip: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the tax interview page.

        Args:
            parent: Parent widget
            config: Application configuration
            accessibility_service: Accessibility service
            on_complete: Callback when interview completes with recommendations
            on_skip: Callback when user skips interview
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.config = config
        self.accessibility_service = accessibility_service
        self.on_complete = on_complete
        self.on_skip = on_skip

        # Initialize interview service
        self.interview_service = TaxInterviewService(config)
        self.current_questions: List[InterviewQuestion] = []
        self.current_question_index = 0
        self.answers: Dict[str, Any] = {}
        self.form_recommendations: List[Dict[str, Any]] = []

        # UI components
        self.progress_bar: Optional[ModernProgressBar] = None
        self.question_container: Optional[ctk.CTkFrame] = None
        self.input_widget = None
        self.button_container: Optional[ctk.CTkFrame] = None

        # Start interview
        self._start_interview()
        self._setup_ui()

    def _start_interview(self):
        """Initialize the interview with starting questions"""
        try:
            # Get initial questions from service
            initial_questions = self.interview_service.start_interview()
            if not initial_questions:
                show_error_message("Error", "Failed to load interview questions")
                return
            
            # Convert to list for navigation
            self.current_questions = list(initial_questions)
        except Exception as e:
            show_error_message("Error", f"Failed to start interview: {str(e)}")

    def _setup_ui(self):
        """Setup the interview page UI"""
        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with skip option
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ModernLabel(
            header_frame,
            text="Tax Interview",
            font=ctk.CTkFont(size=24)
        )
        title_label.pack(side="left", fill="x", expand=True)

        skip_button = ModernButton(
            header_frame,
            text="⊗ Skip Interview",
            command=self._skip_interview,
            button_type="secondary",
            width=120,
            accessibility_service=self.accessibility_service
        )
        skip_button.pack(side="right")

        # Progress bar
        self.progress_bar = ModernProgressBar(
            content_frame,
            label_text="Progress"
        )
        self.progress_bar.pack(fill="x", pady=(0, 20))

        # Question container
        self.question_container = ModernFrame(content_frame)
        self.question_container.pack(fill="both", expand=True, pady=(0, 20))

        # Navigation buttons
        self.button_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.button_container.pack(fill="x", pady=(20, 0))

        self.back_button = ModernButton(
            self.button_container,
            text="← Back",
            command=self._go_back,
            button_type="secondary",
            width=100,
            accessibility_service=self.accessibility_service
        )
        self.back_button.pack(side="left", padx=(0, 10))

        self.next_button = ModernButton(
            self.button_container,
            text="Next →",
            command=self._go_next,
            button_type="primary",
            width=100,
            accessibility_service=self.accessibility_service
        )
        self.next_button.pack(side="right")

        # Display first question
        self._display_question()

    def _display_question(self):
        """Display the current question"""
        # Clear previous widgets
        for widget in self.question_container.winfo_children():
            widget.destroy()

        if not self.current_questions or self.current_question_index >= len(self.current_questions):
            self._show_recommendations()
            return

        question = self.current_questions[self.current_question_index]

        # Update progress
        progress = (self.current_question_index + 1) / len(self.current_questions)
        if self.progress_bar:
            self.progress_bar.set_progress(progress)

        # Question text
        question_label = ModernLabel(
            self.question_container,
            text=question.text,
            font=ctk.CTkFont(size=14),
            wraplength=500
        )
        question_label.pack(pady=(0, 10), anchor="w")

        # Help text
        if question.help_text:
            help_label = ModernLabel(
                self.question_container,
                text=question.help_text,
                font=ctk.CTkFont(size=11),
                text_color="gray60",
                wraplength=500
            )
            help_label.pack(pady=(0, 15), anchor="w")

        # Input widget based on question type
        self._create_input_widget(question)

        # Update button states
        self.back_button.configure(
            state="normal" if self.current_question_index > 0 else "disabled"
        )

    def _create_input_widget(self, question: InterviewQuestion):
        """Create appropriate input widget based on question type"""
        if question.question_type == QuestionType.YES_NO:
            self._create_yes_no_input(question)
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            self._create_multiple_choice_input(question)
        elif question.question_type == QuestionType.NUMERIC:
            self._create_numeric_input(question)
        elif question.question_type == QuestionType.TEXT:
            self._create_text_input(question)
        elif question.question_type == QuestionType.DATE:
            self._create_date_input(question)

    def _create_yes_no_input(self, question: InterviewQuestion):
        """Create yes/no radio input"""
        current_answer = self.answers.get(question.id, None)

        input_frame = ModernFrame(self.question_container)
        input_frame.pack(fill="x", pady=10)

        # Yes option
        yes_var = ctk.StringVar(value="yes" if current_answer == "yes" else "")
        yes_radio = ctk.CTkRadioButton(
            input_frame,
            text="Yes",
            variable=yes_var,
            value="yes",
            command=lambda: self._update_answer(question.id, "yes", yes_var)
        )
        yes_radio.pack(anchor="w", pady=5)

        # No option
        no_var = ctk.StringVar(value="no" if current_answer == "no" else "")
        no_radio = ctk.CTkRadioButton(
            input_frame,
            text="No",
            variable=no_var,
            value="no",
            command=lambda: self._update_answer(question.id, "no", no_var)
        )
        no_radio.pack(anchor="w", pady=5)

    def _create_multiple_choice_input(self, question: InterviewQuestion):
        """Create multiple choice input"""
        current_answer = self.answers.get(question.id, None)

        input_frame = ModernFrame(self.question_container)
        input_frame.pack(fill="x", pady=10)

        for option in question.options or []:
            var = ctk.StringVar(value=option if current_answer == option else "")
            radio = ctk.CTkRadioButton(
                input_frame,
                text=option,
                variable=var,
                value=option,
                command=lambda opt=option: self._update_answer(question.id, opt, var)
            )
            radio.pack(anchor="w", pady=5)

    def _create_numeric_input(self, question: InterviewQuestion):
        """Create numeric input"""
        input_frame = ModernFrame(self.question_container)
        input_frame.pack(fill="x", pady=10)

        entry = ModernEntry(input_frame)
        entry.pack(fill="x")

        current_answer = self.answers.get(question.id, "")
        if current_answer:
            entry.insert(0, str(current_answer))

        entry.bind("<KeyRelease>", lambda e: self._update_answer(question.id, entry.get(), None))

    def _create_text_input(self, question: InterviewQuestion):
        """Create text input"""
        input_frame = ModernFrame(self.question_container)
        input_frame.pack(fill="x", pady=10)

        entry = ModernEntry(input_frame)
        entry.pack(fill="x")

        current_answer = self.answers.get(question.id, "")
        if current_answer:
            entry.insert(0, str(current_answer))

        entry.bind("<KeyRelease>", lambda e: self._update_answer(question.id, entry.get(), None))

    def _create_date_input(self, question: InterviewQuestion):
        """Create date input"""
        input_frame = ModernFrame(self.question_container)
        input_frame.pack(fill="x", pady=10)

        entry = ModernEntry(input_frame, placeholder="YYYY-MM-DD")
        entry.pack(fill="x")

        current_answer = self.answers.get(question.id, "")
        if current_answer:
            entry.insert(0, str(current_answer))

        entry.bind("<KeyRelease>", lambda e: self._update_answer(question.id, entry.get(), None))

    def _update_answer(self, question_id: str, answer: Any, var=None):
        """Update the answer for a question"""
        self.answers[question_id] = answer
        # Also record in the service
        try:
            self.interview_service.answer_question(question_id, answer)
        except Exception as e:
            print(f"Error recording answer: {e}")
        if var:
            var.set(answer)

    def _go_back(self):
        """Go to previous question"""
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self._display_question()

    def _go_next(self):
        """Go to next question or complete interview"""
        question = self.current_questions[self.current_question_index]

        # Validate required fields
        if question.required and question.id not in self.answers:
            show_error_message("Required Field", f"Please answer this question to continue")
            return

        # Record the answer and get next questions
        try:
            result = self.interview_service.answer_question(question.id, self.answers.get(question.id))
            next_questions = result.get('next_questions', [])
            
            # If there are next questions, add them to our list
            if next_questions:
                # Replace remaining questions with new ones
                self.current_questions = self.current_questions[:self.current_question_index + 1]
                self.current_questions.extend(next_questions)
            
            # Check if interview is completed
            if result.get('completed', False):
                self.current_question_index = len(self.current_questions)  # Go past last question
                self._show_recommendations()
            else:
                self.current_question_index += 1
                self._display_question()
        except Exception as e:
            show_error_message("Error", f"Failed to process answer: {str(e)}")

    def _skip_interview(self):
        """Skip the interview and go to form selection"""
        # Clear question display and show message
        for widget in self.question_container.winfo_children():
            widget.destroy()

        skip_label = ModernLabel(
            self.question_container,
            text="Interview skipped. You can now select tax forms to file.",
            font=ctk.CTkFont(size=14),
            wraplength=500
        )
        skip_label.pack(pady=20)

        # Hide navigation buttons
        self.button_container.pack_forget()

        # Call callback
        if self.on_skip:
            self.on_skip()

    def _show_recommendations(self):
        """Show interview recommendations"""
        # Get recommendations from service
        try:
            self.form_recommendations = self.interview_service.recommendations
        except Exception as e:
            show_error_message("Error", f"Failed to generate recommendations: {str(e)}")
            self.form_recommendations = []

        # Clear question display
        for widget in self.question_container.winfo_children():
            widget.destroy()

        # Show recommendations
        recommendations_label = ModernLabel(
            self.question_container,
            text=f"Interview Complete!",
            font=ctk.CTkFont(size=18)
        )
        recommendations_label.pack(pady=(0, 10))

        summary_text = f"Based on your answers, we recommend {len(self.form_recommendations)} tax forms."
        summary_label = ModernLabel(
            self.question_container,
            text=summary_text,
            font=ctk.CTkFont(size=12),
            wraplength=500
        )
        summary_label.pack(pady=(0, 20))

        # Forms list
        if self.form_recommendations:
            forms_label = ModernLabel(
                self.question_container,
                text="Recommended Forms:",
                font=ctk.CTkFont(size=12)
            )
            forms_label.pack(anchor="w", pady=(0, 10))

            for rec in self.form_recommendations[:10]:
                form_name = rec.form_name
                reason = rec.reason
                form_text = f"• {form_name}"
                if reason:
                    form_text += f" - {reason}"

                form_label = ModernLabel(
                    self.question_container,
                    text=form_text,
                    font=ctk.CTkFont(size=11),
                    wraplength=500,
                    justify="left"
                )
                form_label.pack(anchor="w", pady=2)

        # Update buttons
        self.back_button.configure(state="normal")
        self.next_button.configure(text="Finish")
        self.button_container.pack(fill="x", pady=(20, 0))

        # Complete callback
        if self.on_complete:
            # Update to complete state
            self.next_button.configure(
                command=lambda: self._finish_interview()
            )

    def _finish_interview(self):
        """Finish the interview and call completion callback"""
        if self.on_complete:
            # Convert FormRecommendation objects to dict format for callback
            recommendations_list = []
            for rec in self.form_recommendations:
                recommendations_list.append({
                    'form': rec.form_name,
                    'reason': rec.reason,
                    'priority': rec.priority,
                    'estimated_time': rec.estimated_time
                })
            self.on_complete(recommendations_list)
