"""
Modern Main Window - CustomTkinter-based main application window

Provides a modern, intuitive interface for tax preparation with guided
interview, simplified navigation, and contextual help.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
import tkinter as tk

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.tax_interview_service import TaxInterviewService
from services.form_recommendation_service import FormRecommendationService
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton, ModernProgressBar,
    show_info_message, show_error_message, show_confirmation
)
from gui.tax_interview_wizard import TaxInterviewWizard


class ModernMainWindow(ctk.CTk):
    """
    Modern main application window using CustomTkinter.

    Features:
    - Guided tax interview wizard
    - Simplified navigation based on recommendations
    - Progress tracking
    - Contextual help
    - Modern UI design
    """

    def __init__(self, config: AppConfig):
        """
        Initialize the modern main window.

        Args:
            config: Application configuration
        """
        super().__init__()

        self.config = config
        self.tax_data: Optional[TaxData] = None
        self.interview_completed = False
        self.form_recommendations = []

        # Initialize services
        self.interview_service = TaxInterviewService(config)
        self.recommendation_service = FormRecommendationService(config)

        # UI components
        self.sidebar_frame: Optional[ModernFrame] = None
        self.content_frame: Optional[ModernFrame] = None
        self.progress_bar: Optional[ModernProgressBar] = None
        self.status_label: Optional[ModernLabel] = None

        self._setup_window()
        self._setup_ui()
        self._show_welcome_screen()

    def _setup_window(self):
        """Setup the main window properties"""
        self.title("Freedom US Tax Return - Modern Edition")
        self.geometry("1200x800")
        self.resizable(True, True)

        # Set theme
        ctk.set_appearance_mode("system")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_ui(self):
        """Setup the main user interface"""
        # Create main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Sidebar (left)
        self.sidebar_frame = ModernFrame(
            main_container,
            width=250,
            title="Navigation"
        )
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 10))

        # Content area (right)
        self.content_frame = ModernFrame(main_container, title="")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Progress bar (bottom)
        self.progress_bar = ModernProgressBar(
            main_container,
            label_text="Tax Return Progress"
        )
        self.progress_bar.pack(side="bottom", fill="x", pady=(10, 0))

        # Status bar
        status_frame = ctk.CTkFrame(main_container, height=30)
        status_frame.pack(side="bottom", fill="x", pady=(5, 0))

        self.status_label = ModernLabel(
            status_frame,
            text="Ready to start your tax interview",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.pack(side="left", padx=10)

        # Setup sidebar navigation
        self._setup_sidebar()

    def _setup_sidebar(self):
        """Setup the sidebar navigation"""
        # Interview button
        self.interview_button = ModernButton(
            self.sidebar_frame,
            text="🚀 Start Tax Interview",
            command=self._start_interview,
            button_type="primary",
            height=40
        )
        self.interview_button.pack(fill="x", padx=10, pady=(10, 5))

        # Separator
        separator = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="gray70")
        separator.pack(fill="x", padx=10, pady=5)

        # Form sections (initially hidden)
        self.form_buttons_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.form_buttons_frame.pack(fill="x", padx=10, pady=5)

        # Initially hide form buttons
        self.form_buttons_frame.pack_forget()

        # Action buttons
        actions_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=(20, 10))

        ModernButton(
            actions_frame,
            text="💾 Save Progress",
            command=self._save_progress,
            button_type="secondary",
            height=35
        ).pack(fill="x", pady=(0, 5))

        ModernButton(
            actions_frame,
            text="📊 View Summary",
            command=self._show_summary,
            button_type="secondary",
            height=35
        ).pack(fill="x", pady=(0, 5))

        ModernButton(
            actions_frame,
            text="⚙️ Settings",
            command=self._show_settings,
            button_type="secondary",
            height=35
        ).pack(fill="x", pady=(0, 10))

    def _show_welcome_screen(self):
        """Show the welcome screen"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Welcome content
        welcome_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            welcome_frame,
            text="Welcome to Freedom US Tax Return",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(50, 10))

        # Subtitle
        subtitle_label = ModernLabel(
            welcome_frame,
            text="Modern Edition - Guided Tax Preparation",
            font=ctk.CTkFont(size=16),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 30))

        # Description
        desc_text = """
        This modern tax preparation application will guide you through
        the process of filing your US federal income tax return.

        Features:
        • Intelligent tax interview to determine what you need to report
        • Step-by-step guidance with contextual help
        • Modern, intuitive interface
        • Automatic form recommendations
        • Progress tracking and validation

        To get started, click "Start Tax Interview" in the sidebar.
        """

        desc_label = ModernLabel(
            welcome_frame,
            text=desc_text,
            font=ctk.CTkFont(size=12),
            wraplength=600,
            justify="left"
        )
        desc_label.pack(pady=(0, 40))

        # Quick start button
        quick_start_button = ModernButton(
            welcome_frame,
            text="🚀 Quick Start - Begin Interview",
            command=self._start_interview,
            button_type="primary",
            height=50,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        quick_start_button.pack(pady=(0, 20))

        # Help text
        help_label = ModernLabel(
            welcome_frame,
            text="Need help? Hover over questions for guidance, or check our documentation.",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        help_label.pack(pady=(20, 0))

    def _start_interview(self):
        """Start the tax interview wizard"""
        def on_interview_complete(summary: Dict[str, Any]):
            """Handle interview completion"""
            self.interview_completed = True
            self.form_recommendations = summary.get('recommendations', [])

            # Update UI
            self._update_sidebar_after_interview()
            self._show_recommendations_screen(summary)
            self._update_progress()

            show_info_message(
                "Interview Complete",
                f"Great! We've identified {len(self.form_recommendations)} forms you may need to complete."
            )

        # Show interview wizard
        TaxInterviewWizard(self, self.config, on_complete=on_interview_complete)

    def _update_sidebar_after_interview(self):
        """Update sidebar after interview completion"""
        # Hide interview button
        self.interview_button.pack_forget()

        # Show form buttons
        self.form_buttons_frame.pack(fill="x", padx=10, pady=5)

        # Add form section buttons based on recommendations
        for rec in self.form_recommendations[:8]:  # Show top 8
            button_text = f"{rec['form'][:20]}..." if len(rec['form']) > 20 else rec['form']

            ModernButton(
                self.form_buttons_frame,
                text=f"📄 {button_text}",
                command=lambda r=rec: self._navigate_to_form(r),
                button_type="secondary",
                height=35,
                anchor="w"
            ).pack(fill="x", pady=(0, 2))

        # Update status
        self.status_label.configure(
            text=f"Interview complete - {len(self.form_recommendations)} forms recommended"
        )

    def _show_recommendations_screen(self, summary: Dict[str, Any]):
        """Show the form recommendations screen"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Recommendations content
        rec_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        rec_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            rec_frame,
            text="Your Recommended Tax Forms",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        # Summary
        summary_text = f"""
        Based on your answers, we recommend completing {len(self.form_recommendations)} tax forms.

        Estimated time: {summary.get('estimated_total_time', 0)} minutes
        Priority forms: {len([r for r in self.form_recommendations if r.get('priority', 0) >= 8])}
        """

        summary_label = ModernLabel(
            rec_frame,
            text=summary_text.strip(),
            font=ctk.CTkFont(size=12),
            wraplength=600,
            justify="left"
        )
        summary_label.pack(pady=(0, 20))

        # Recommendations list
        list_frame = ctk.CTkScrollableFrame(rec_frame, height=300)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))

        for i, rec in enumerate(self.form_recommendations, 1):
            # Form card
            card_frame = ctk.CTkFrame(list_frame)
            card_frame.pack(fill="x", pady=(0, 10), padx=5)

            # Form title and priority
            priority_colors = {
                10: "red",    # Critical
                8: "orange",  # High
                6: "blue",    # Medium
                4: "green",   # Low
                2: "gray"     # Optional
            }

            priority_color = priority_colors.get(rec.get('priority', 2), "gray")

            title_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            title_frame.pack(fill="x", padx=10, pady=(10, 5))

            ModernLabel(
                title_frame,
                text=f"{i}. {rec['form']}",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(side="left")

            priority_label = ModernLabel(
                title_frame,
                text=f"Priority: {rec.get('priority', 2)}/10",
                font=ctk.CTkFont(size=10),
                text_color=priority_color
            )
            priority_label.pack(side="right")

            # Reason
            reason_label = ModernLabel(
                card_frame,
                text=f"Reason: {rec.get('reason', 'Recommended based on your situation')}",
                font=ctk.CTkFont(size=11),
                wraplength=500,
                justify="left"
            )
            reason_label.pack(padx=10, pady=(0, 10), anchor="w")

        # Continue button
        continue_button = ModernButton(
            rec_frame,
            text="Continue to Form Entry →",
            command=self._start_form_entry,
            button_type="primary",
            height=40
        )
        continue_button.pack(pady=(20, 0))

    def _navigate_to_form(self, recommendation: Dict[str, Any]):
        """Navigate to a specific form"""
        form_name = recommendation.get('form', '')
        show_info_message("Navigation", f"Navigation to {form_name} will be implemented in the next phase.")

    def _start_form_entry(self):
        """Start the form entry process"""
        show_info_message("Form Entry", "Form entry interface will be implemented in the next development phase.")

    def _save_progress(self):
        """Save current progress"""
        show_info_message("Save Progress", "Progress saving will be implemented in the next phase.")

    def _show_summary(self):
        """Show tax return summary"""
        if not self.interview_completed:
            show_error_message("No Data", "Please complete the tax interview first.")
            return

        show_info_message("Summary", "Tax return summary will be implemented in the next phase.")

    def _show_settings(self):
        """Show settings dialog"""
        show_info_message("Settings", "Settings dialog will be implemented in the next phase.")

    def _update_progress(self):
        """Update the progress bar"""
        if not self.progress_bar:
            return

        if not self.interview_completed:
            self.progress_bar.set(0.1)  # 10% for interview completion
            self.progress_bar.label.configure(text="Progress: Interview not completed")
        else:
            # Calculate progress based on recommendations
            completed_forms = 0  # This will be updated as forms are completed
            total_forms = len(self.form_recommendations)

            if total_forms > 0:
                progress = min(0.9, 0.1 + (completed_forms / total_forms) * 0.8)
                self.progress_bar.set(progress)
                self.progress_bar.label.configure(
                    text=f"Progress: {completed_forms}/{total_forms} forms completed"
                )
            else:
                self.progress_bar.set(0.1)
                self.progress_bar.label.configure(text="Progress: No forms recommended")

    def run(self):
        """Run the application"""
        self.mainloop()