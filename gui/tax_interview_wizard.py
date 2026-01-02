"""
Tax Interview Wizard - Guided question-based tax preparation

A modal dialog that walks users through intelligent questions to determine
which tax forms they need, providing contextual help and guidance.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List, Callable
import threading

from services.tax_interview_service import TaxInterviewService, InterviewQuestion, FormRecommendation
from gui.modern_ui_components import (
    ModernDialog, ModernFrame, ModernLabel, ModernButton,
    ModernRadioGroup, ModernCheckBox, ModernProgressBar,
    ModernTextBox, show_info_message, show_error_message
)


class TaxInterviewWizard(ModernDialog):
    """
    Interactive tax interview wizard that guides users through
    determining which forms they need to file.
    """

    def __init__(self, master, config, on_complete: Optional[Callable] = None):
        """
        Initialize the tax interview wizard.

        Args:
            master: Parent window
            config: Application configuration
            on_complete: Callback when interview completes
        """
        super().__init__(master, title="Tax Interview Wizard")
        self.config = config
        self.on_complete = on_complete

        # Initialize interview service
        self.interview_service = TaxInterviewService(config)
        self.current_questions: List[InterviewQuestion] = []
        self.current_question_index = 0
        self.answers: Dict[str, Any] = {}

        # UI components
        self.progress_bar: Optional[ModernProgressBar] = None
        self.question_frame: Optional[ModernFrame] = None
        self.question_label: Optional[ModernLabel] = None
        self.input_widget = None
        self.help_text_label: Optional[ModernLabel] = None
        self.navigation_frame: Optional[ModernFrame] = None

        self._setup_ui()
        self._start_interview()

    def _setup_ui(self):
        """Setup the wizard user interface"""
        # Main container
        main_frame = ModernFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_label = ModernLabel(
            main_frame,
            text="Tax Interview Wizard",
            font=ctk.CTkFont(size=20)
        )
        header_label.pack(pady=(0, 10))

        subtitle_label = ModernLabel(
            main_frame,
            text="Answer a few questions to determine which tax forms you need",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 20))

        # Progress bar
        self.progress_bar = ModernProgressBar(
            main_frame,
            label_text="Interview Progress"
        )
        self.progress_bar.pack(fill="x", pady=(0, 20))

        # Question container
        self.question_frame = ModernFrame(main_frame)
        self.question_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Question label
        self.question_label = ModernLabel(
            self.question_frame,
            text="",
            font=ctk.CTkFont(size=14),
            wraplength=500
        )
        self.question_label.pack(pady=(20, 10), padx=20, anchor="w")

        # Help text
        self.help_text_label = ModernLabel(
            self.question_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=500
        )
        self.help_text_label.pack(pady=(0, 20), padx=20, anchor="w")

        # Navigation buttons
        self.navigation_frame = ModernFrame(main_frame)
        self.navigation_frame.pack(fill="x", pady=(20, 0))

        # Button frame for alignment
        button_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)

        # Back button (initially disabled)
        self.back_button = ModernButton(
            button_frame,
            text="← Back",
            command=self._go_back,
            button_type="secondary",
            state="disabled"
        )
        self.back_button.pack(side="left", padx=(0, 10))

        # Next button
        self.next_button = ModernButton(
            button_frame,
            text="Next →",
            command=self._go_next,
            button_type="primary"
        )
        self.next_button.pack(side="right")

        # Skip button (for optional questions)
        self.skip_button = ModernButton(
            button_frame,
            text="Skip",
            command=self._skip_question,
            button_type="secondary"
        )
        self.skip_button.pack(side="right", padx=(0, 10))

    def _start_interview(self):
        """Start the tax interview"""
        try:
            self.current_questions = self.interview_service.start_interview()
            self.current_question_index = 0
            self._display_current_question()
            self._update_progress()
        except Exception as e:
            show_error_message("Interview Error", f"Failed to start interview: {e}")
            self.destroy()

    def _display_current_question(self):
        """Display the current question"""
        if self.current_question_index >= len(self.current_questions):
            self._complete_interview()
            return

        question = self.current_questions[self.current_question_index]

        # Update question text
        self.question_label.configure(text=f"Question {self.current_question_index + 1}: {question.text}")

        # Update help text
        help_text = question.help_text or "Select the option that best describes your situation."
        self.help_text_label.configure(text=help_text)

        # Remove previous input widget
        if self.input_widget:
            self.input_widget.destroy()

        # Create appropriate input widget based on question type
        if question.question_type.value == "yes_no":
            self.input_widget = ModernRadioGroup(
                self.question_frame,
                options=["Yes", "No"],
                required=question.required
            )
        elif question.question_type.value == "multiple_choice":
            self.input_widget = ModernRadioGroup(
                self.question_frame,
                options=question.options or [],
                required=question.required
            )
        elif question.question_type.value == "numeric":
            self.input_widget = ctk.CTkEntry(
                self.question_frame,
                placeholder_text="Enter a number"
            )
        elif question.question_type.value == "text":
            self.input_widget = ctk.CTkEntry(
                self.question_frame,
                placeholder_text="Enter your answer"
            )
        else:
            self.input_widget = ModernRadioGroup(
                self.question_frame,
                options=["Not implemented"],
                required=False
            )

        self.input_widget.pack(pady=(0, 20), padx=20, anchor="w")

        # Update navigation buttons
        self.back_button.configure(
            state="normal" if self.current_question_index > 0 else "disabled"
        )
        self.skip_button.configure(
            state="normal" if not question.required else "disabled"
        )

    def _go_next(self):
        """Go to the next question"""
        if not self.input_widget:
            return

        # Get answer from current input widget
        answer = self._get_answer_from_widget()

        if answer is None:
            show_error_message("Invalid Answer", "Please provide an answer to continue.")
            return

        # Record the answer
        current_question = self.current_questions[self.current_question_index]
        result = self.interview_service.answer_question(current_question.id, answer)

        # Store answer
        self.answers[current_question.id] = answer

        # Handle follow-up questions
        if result["next_questions"]:
            # Insert follow-up questions
            for follow_up in result["next_questions"]:
                if follow_up not in self.current_questions:
                    insert_index = self.current_question_index + 1
                    self.current_questions.insert(insert_index, follow_up)

        # Move to next question
        self.current_question_index += 1
        self._display_current_question()
        self._update_progress()

    def _go_back(self):
        """Go back to the previous question"""
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self._display_current_question()
            self._update_progress()

    def _skip_question(self):
        """Skip the current question"""
        current_question = self.current_questions[self.current_question_index]

        # Record skip as None
        self.answers[current_question.id] = None

        # Move to next question
        self.current_question_index += 1
        self._display_current_question()
        self._update_progress()

    def _get_answer_from_widget(self) -> Any:
        """Get answer from the current input widget"""
        if isinstance(self.input_widget, ModernRadioGroup):
            answer = self.input_widget.get()
            if not answer:
                return None
            return answer == "Yes" if answer in ["Yes", "No"] else answer
        elif isinstance(self.input_widget, ctk.CTkEntry):
            answer = self.input_widget.get().strip()
            if not answer:
                return None

            # Try to convert to number if it looks like one
            try:
                if "." in answer or answer.isdigit():
                    return float(answer)
                else:
                    return int(answer)
            except ValueError:
                return answer
        else:
            return None

    def _update_progress(self):
        """Update the progress bar"""
        if not self.progress_bar:
            return

        progress = self.interview_service.get_progress_percentage()
        self.progress_bar.set(progress / 100.0)

        # Update progress label
        completed = len([a for a in self.answers.values() if a is not None])
        total = len(self.current_questions)
        self.progress_bar.label.configure(
            text=f"Interview Progress: {completed}/{total} questions answered"
        )

    def _complete_interview(self):
        """Complete the interview and show results"""
        try:
            # Get final recommendations
            summary = self.interview_service.get_answers_summary()

            # Show completion dialog
            completion_text = f"""
Interview Complete!

Questions Answered: {summary['total_questions_answered']}
Form Recommendations: {summary['total_recommendations']}
Estimated Time: {summary['estimated_total_time']} minutes

Recommended Forms:
"""

            for rec in summary['recommendations'][:5]:  # Show top 5
                completion_text += f"• {rec['form']} ({rec['category']})\n"

            if summary['recommendations']:
                completion_text += f"\n... and {len(summary['recommendations']) - 5} more forms" \
                    if len(summary['recommendations']) > 5 else ""

            show_info_message("Interview Complete", completion_text.strip())

            # Call completion callback
            if self.on_complete:
                self.on_complete(summary)

            # Close wizard
            self.destroy()

        except Exception as e:
            show_error_message("Completion Error", f"Failed to complete interview: {e}")
            self.destroy()