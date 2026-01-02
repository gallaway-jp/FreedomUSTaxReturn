"""
AI Deduction Finder Window - GUI for AI-powered deduction analysis

Provides an intelligent interface for analyzing tax data to identify
potential missed deductions and tax-saving opportunities.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.ai_deduction_finder_service import AIDeductionFinderService, DeductionAnalysisResult, DeductionSuggestion, DeductionCategory
from services.tax_calculation_service import TaxCalculationService
from services.accessibility_service import AccessibilityService
from gui.modern_ui_components import ModernFrame, ModernLabel, ModernButton
from utils.error_tracker import get_error_tracker


class AIDeductionFinderWindow:
    """
    Window for AI-powered deduction analysis and recommendations.

    Features:
    - Intelligent deduction analysis across multiple categories
    - Confidence scoring and priority ranking
    - Detailed suggestions with potential savings
    - Category-specific insights
    - Exportable analysis reports
    """

    def __init__(self, parent: ctk.CTk, config: AppConfig, tax_data: Optional[TaxData] = None, accessibility_service: Optional[AccessibilityService] = None):
        """
        Initialize AI deduction finder window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax return data to analyze
            accessibility_service: Accessibility service instance
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        self.error_tracker = get_error_tracker()

        # Initialize services
        tax_year = tax_data.get_current_year() if tax_data else 2026
        self.tax_calculation = TaxCalculationService(tax_year)
        self.ai_service = AIDeductionFinderService(config, self.tax_calculation)

        # Current analysis results
        self.current_analysis: Optional[DeductionAnalysisResult] = None

        # UI components
        self.window: Optional[ctk.CTkToplevel] = None
        self.tabview: Optional[ctk.CTkTabview] = None
        self.progress_var: Optional[ctk.DoubleVar] = None
        self.status_label: Optional[ModernLabel] = None
        self.textbox: Optional[ctk.CTkTextbox] = None

        self._create_window()
        self._setup_ui()
        self._load_initial_data()

    def _create_window(self):
        """Create the main deduction finder window"""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("🤖 AI Deduction Finder")
        self.window.geometry("1100x750")
        self.window.resizable(True, True)

        # Configure grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        # Set window icon if available
        try:
            self.window.iconbitmap("assets/icon.ico")
        except:
            pass

        # Center window
        self.window.transient(self.parent)
        self.window.grab_set()

    def _setup_ui(self):
        """Setup the user interface"""
        # Header
        self._create_header()

        # Toolbar
        self._create_toolbar()

        # Tabview for different analysis views
        self.tabview = ctk.CTkTabview(self.window)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))

        # Create tabs
        self._setup_overview_tab()
        self._setup_suggestions_tab()
        self._setup_categories_tab()
        self._setup_analysis_details_tab()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self.window)
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))

        title_label = ModernLabel(
            header_frame,
            text="🤖 AI Deduction Finder",
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(anchor="w")

        subtitle_label = ModernLabel(
            header_frame,
            text="Intelligent analysis to identify missed deductions and tax-saving opportunities",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar_frame = ModernFrame(self.window)
        toolbar_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 10))

        # Action buttons
        buttons_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        buttons_frame.pack(side="left")

        ModernButton(
            buttons_frame,
            text="▶ Run AI Analysis",
            command=self._run_analysis,
            button_type="primary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            buttons_frame,
            text="📄 Export Report",
            command=self._export_report,
            button_type="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            buttons_frame,
            text="🔄 Refresh Data",
            command=self._refresh_data,
            button_type="secondary"
        ).pack(side="left", padx=(0, 8))

        # Progress and status
        status_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        status_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.progress_var = ctk.DoubleVar(value=0)
        progress_bar = ctk.CTkProgressBar(status_frame, variable=self.progress_var)
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.status_label = ModernLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.pack(side="left")

    def _setup_overview_tab(self):
        """Setup the overview tab with summary metrics"""
        overview_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Overview", overview_tab)

        # Summary metrics
        self._create_summary_metrics(overview_tab)

        # Top suggestions preview
        preview_label = ModernLabel(
            overview_tab,
            text="💡 Top Deduction Opportunities",
            font=ctk.CTkFont(size=13)
        )
        preview_label.pack(anchor="w", padx=15, pady=(15, 10))

        preview_frame = ModernFrame(overview_tab)
        preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.preview_textbox = ctk.CTkTextbox(preview_frame, height=200)
        self.preview_textbox.pack(fill="both", expand=True)
        self.preview_textbox.configure(state="disabled")

    def _create_summary_metrics(self, parent):
        """Create summary metrics cards"""
        metrics_frame = ctk.CTkFrame(parent, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=15, pady=(15, 0))

        self.summary_labels = {}
        metrics = [
            ("Total Potential Savings", "total_savings", "$0"),
            ("High Confidence", "high_confidence", "0"),
            ("Medium Confidence", "medium_confidence", "0"),
            ("Low Confidence", "low_confidence", "0"),
            ("Categories Analyzed", "categories_analyzed", "0"),
            ("Analysis Date", "timestamp", "Never"),
        ]

        # Create metric cards in 2 rows of 3
        for i, (label_text, key, default) in enumerate(metrics):
            row = i // 3
            col = i % 3
            
            card = ModernFrame(metrics_frame)
            card.grid(row=row, column=col, sticky="ew", padx=(0, 10), pady=(0, 10))

            title = ModernLabel(
                card,
                text=label_text,
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            )
            title.pack(anchor="w", padx=12, pady=(12, 3))

            value = ModernLabel(
                card,
                text=default,
                font=ctk.CTkFont(size=14)
            )
            value.pack(anchor="w", padx=12, pady=(0, 12))

            self.summary_labels[key] = value

        metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)

    def _setup_suggestions_tab(self):
        """Setup the suggestions tab with detailed list"""
        suggestions_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("All Suggestions", suggestions_tab)

        # Filter frame
        filter_frame = ModernFrame(suggestions_tab)
        filter_frame.pack(fill="x", padx=15, pady=(15, 10))

        ModernLabel(filter_frame, text="Filter by Category:", font=ctk.CTkFont(size=10)).pack(side="left", padx=(0, 10))

        self.category_filter = ctk.CTkComboBox(
            filter_frame,
            state="readonly",
            width=150,
            font=ctk.CTkFont(size=10)
        )
        self.category_filter.pack(side="left", padx=(0, 20))
        self.category_filter.bind("<<ComboboxSelected>>", self._filter_suggestions)

        ModernLabel(filter_frame, text="Min Confidence:", font=ctk.CTkFont(size=10)).pack(side="left", padx=(0, 10))

        self.confidence_filter = ctk.CTkComboBox(
            filter_frame,
            values=["All", "High", "Medium", "Low"],
            state="readonly",
            width=100,
            font=ctk.CTkFont(size=10)
        )
        self.confidence_filter.pack(side="left")
        self.confidence_filter.set("All")
        self.confidence_filter.bind("<<ComboboxSelected>>", self._filter_suggestions)

        # Suggestions list
        suggestions_label = ModernLabel(
            suggestions_tab,
            text="📝 Deduction Suggestions",
            font=ctk.CTkFont(size=13)
        )
        suggestions_label.pack(anchor="w", padx=15, pady=(10, 10))

        suggestions_frame = ModernFrame(suggestions_tab)
        suggestions_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.suggestions_textbox = ctk.CTkTextbox(suggestions_frame)
        self.suggestions_textbox.pack(fill="both", expand=True)
        self.suggestions_textbox.bind("<Button-1>", self._on_suggestion_select)

        # Details frame
        details_label = ModernLabel(
            suggestions_tab,
            text="📌 Suggestion Details",
            font=ctk.CTkFont(size=11)
        )
        details_label.pack(anchor="w", padx=15, pady=(10, 8))

        details_frame = ModernFrame(suggestions_tab)
        details_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.details_textbox = ctk.CTkTextbox(details_frame, height=120)
        self.details_textbox.pack(fill="both", expand=True)
        self.details_textbox.configure(state="disabled")

    def _setup_categories_tab(self):
        """Setup the categories analysis tab"""
        categories_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Categories", categories_tab)

        # Categories overview
        categories_label = ModernLabel(
            categories_tab,
            text="📊 Deduction Categories Analysis",
            font=ctk.CTkFont(size=13)
        )
        categories_label.pack(anchor="w", padx=15, pady=(15, 10))

        categories_frame = ModernFrame(categories_tab)
        categories_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.categories_textbox = ctk.CTkTextbox(categories_frame)
        self.categories_textbox.pack(fill="both", expand=True)
        self.categories_textbox.configure(state="disabled")

        # Category details
        insights_label = ModernLabel(
            categories_tab,
            text="💡 Category Insights",
            font=ctk.CTkFont(size=11)
        )
        insights_label.pack(anchor="w", padx=15, pady=(10, 8))

        insights_frame = ModernFrame(categories_tab)
        insights_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.insights_textbox = ctk.CTkTextbox(insights_frame, height=150)
        self.insights_textbox.pack(fill="both", expand=True)
        self.insights_textbox.configure(state="disabled")

    def _setup_analysis_details_tab(self):
        """Setup the analysis details tab"""
        details_tab = ctk.CTkScrollableFrame(self.tabview)
        self.tabview.add("Analysis Details", details_tab)

        title_label = ModernLabel(
            details_tab,
            text="📖 Analysis Methodology",
            font=ctk.CTkFont(size=13)
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 10))

        details_frame = ModernFrame(details_tab)
        details_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.analysis_details_textbox = ctk.CTkTextbox(details_frame)
        self.analysis_details_textbox.pack(fill="both", expand=True)

        # Add methodology info
        info_text = """
🤖 AI DEDUCTION FINDER ANALYSIS METHODOLOGY:

1. DATA ANALYSIS
   Examines income, expenses, and tax forms for deduction patterns
   Identifies spending categories and charitable contributions

2. RULE-BASED INTELLIGENCE
   Applies current tax rules and IRS regulations
   Matches common deduction scenarios against your data
   Cross-references tax filing status and income level

3. CONFIDENCE SCORING
   Rates suggestions based on:
   - Data completeness and clarity
   - Rule matching strength
   - Historical approval likelihood
   - Documentation availability

4. PRIORITY RANKING
   Orders suggestions by:
   - Potential tax savings amount
   - Confidence level
   - Complexity and documentation needs
   - Category relevance to your profile

5. CATEGORY COVERAGE
   Analyzes 9 major deduction categories:
   ✓ Medical expenses
   ✓ Charitable contributions
   ✓ Business expenses
   ✓ Education costs
   ✓ Home office deduction
   ✓ Vehicle expenses
   ✓ Retirement contributions
   ✓ State/local taxes (SALT)
   ✓ Energy efficiency credits

📊 CONFIDENCE LEVELS EXPLAINED:

HIGH (Green)
  - Strong indicators present
  - High likelihood of qualification
  - Comprehensive supporting documentation available
  - Low IRS audit risk

MEDIUM (Yellow)
  - Some indicators present
  - Moderate likelihood of qualification
  - Partial documentation may be needed
  - Standard IRS scrutiny expected

LOW (Red)
  - Limited indicators
  - Further research recommended
  - Documentation collection needed
  - Higher audit risk potential

⚠️  IMPORTANT DISCLAIMER:

This tool provides suggestions based on available data and general tax rules.
It is NOT a substitute for professional tax advice.

Always consult a qualified tax professional for:
- Final return preparation
- Complex deduction scenarios
- Multi-state tax situations
- Business or investment income
- Audit representation

© 2025 Freedom US Tax Return - AI Analysis Engine
        """

        self.analysis_details_textbox.insert("0.0", info_text.strip())
        self.analysis_details_textbox.configure(state="disabled")

    def _load_initial_data(self):
        """Load initial data and setup"""
        if self.tax_data:
            self.status_label.configure(text="Tax data loaded - Ready for analysis")
        else:
            self.status_label.configure(text="No tax data available")

        # Setup category filter
        categories = ["All"] + [cat.value for cat in DeductionCategory]
        self.category_filter.configure(values=categories)
        self.category_filter.set("All")

    def _run_analysis(self):
        """Run the AI deduction analysis"""
        if not self.tax_data:
            messagebox.showwarning("No Data", "Please load tax data first.")
            return

        # Disable button and show progress
        self.status_label.configure(text="Running AI analysis...")
        self.progress_var.set(0)

        # Run analysis in background thread
        def run_analysis_thread():
            try:
                self.progress_var.set(25)
                self.current_analysis = self.ai_service.analyze_deductions(self.tax_data)

                self.progress_var.set(100)
                self.status_label.configure(text="Analysis complete")

                # Update UI on main thread
                self.window.after(0, self._update_ui_with_results)

            except Exception as e:
                self.error_tracker.log_error(e, "AI Deduction Analysis")
                self.window.after(0, lambda: messagebox.showerror("Analysis Error", f"Failed to run analysis: {e}"))
                self.window.after(0, lambda: self.status_label.configure(text="Analysis failed"))

        thread = threading.Thread(target=run_analysis_thread, daemon=True)
        thread.start()

    def _update_ui_with_results(self):
        """Update the UI with analysis results"""
        if not self.current_analysis:
            return

        analysis = self.current_analysis

        # Update overview tab
        self.summary_labels["total_savings"].configure(text=f"${analysis.total_potential_savings:,.2f}")
        self.summary_labels["high_confidence"].configure(text=str(analysis.high_confidence_count))
        self.summary_labels["medium_confidence"].configure(text=str(analysis.medium_confidence_count))
        self.summary_labels["low_confidence"].configure(text=str(analysis.low_confidence_count))
        self.summary_labels["categories_analyzed"].configure(text=str(len(analysis.category_summaries)))
        self.summary_labels["timestamp"].configure(text=analysis.analysis_timestamp.strftime("%Y-%m-%d %H:%M"))

        # Update preview
        self._populate_preview()

        # Update suggestions
        self._populate_suggestions()

        # Update categories
        self._populate_categories()

    def _populate_preview(self):
        """Populate the preview with top suggestions"""
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("0.0", "end")

        if not self.current_analysis:
            return

        # Get top 8 suggestions by potential savings
        top_suggestions = sorted(
            self.current_analysis.suggestions,
            key=lambda s: s.potential_savings,
            reverse=True
        )[:8]

        for i, suggestion in enumerate(top_suggestions, 1):
            text = f"{i}. {suggestion.description}\n"
            text += f"   Category: {suggestion.category.value}\n"
            text += f"   Potential Savings: ${suggestion.potential_savings:,.2f}\n"
            text += f"   Confidence: {suggestion.confidence_level.value}\n"
            text += f"   Score: {suggestion.priority_score:.1f}\n\n"
            self.preview_textbox.insert("end", text)

        self.preview_textbox.configure(state="disabled")

    def _populate_suggestions(self):
        """Populate the suggestions textbox"""
        self.suggestions_textbox.configure(state="normal")
        self.suggestions_textbox.delete("0.0", "end")

        if not self.current_analysis:
            return

        # Sort by priority
        sorted_suggestions = sorted(
            self.current_analysis.suggestions,
            key=lambda s: (s.priority_score, s.potential_savings),
            reverse=True
        )

        for i, suggestion in enumerate(sorted_suggestions, 1):
            text = f"\n[{i}] {suggestion.description}\n"
            text += f"     Category: {suggestion.category.value}\n"
            text += f"     Savings: ${suggestion.potential_savings:,.2f}\n"
            text += f"     Confidence: {suggestion.confidence_level.value}\n"
            text += f"     Priority: {suggestion.priority_score:.1f}\n"
            self.suggestions_textbox.insert("end", text)

    def _populate_categories(self):
        """Populate the categories tab"""
        self.categories_textbox.configure(state="normal")
        self.categories_textbox.delete("0.0", "end")

        if not self.current_analysis:
            return

        text = "Category Summary:\n" + "=" * 60 + "\n\n"
        for summary in self.current_analysis.category_summaries:
            text += f"{summary.category.value}\n"
            text += f"  Suggestions: {summary.suggestion_count}\n"
            text += f"  Potential Savings: ${summary.total_potential_savings:,.2f}\n"
            text += f"  Avg Confidence: {summary.average_confidence:.1f}\n\n"

        self.categories_textbox.insert("0.0", text)
        self.categories_textbox.configure(state="disabled")

    def _filter_suggestions(self, event=None):
        """Filter suggestions based on category and confidence"""
        category_filter = self.category_filter.get()
        confidence_filter = self.confidence_filter.get()

        self.suggestions_textbox.configure(state="normal")
        self.suggestions_textbox.delete("0.0", "end")

        if not self.current_analysis:
            return

        # Sort by priority
        sorted_suggestions = sorted(
            self.current_analysis.suggestions,
            key=lambda s: (s.priority_score, s.potential_savings),
            reverse=True
        )

        # Apply filters
        filtered = []
        for suggestion in sorted_suggestions:
            if category_filter != "All" and suggestion.category.value != category_filter:
                continue
            if confidence_filter != "All" and suggestion.confidence_level.value != confidence_filter:
                continue
            filtered.append(suggestion)

        # Display filtered suggestions
        for i, suggestion in enumerate(filtered, 1):
            text = f"\n[{i}] {suggestion.description}\n"
            text += f"     Category: {suggestion.category.value}\n"
            text += f"     Savings: ${suggestion.potential_savings:,.2f}\n"
            text += f"     Confidence: {suggestion.confidence_level.value}\n"
            text += f"     Priority: {suggestion.priority_score:.1f}\n"
            self.suggestions_textbox.insert("end", text)

        self.suggestions_textbox.configure(state="disabled")

    def _on_suggestion_select(self, event):
        """Handle suggestion selection in textbox"""
        # For simplicity, show first suggestion details
        if not self.current_analysis or not self.current_analysis.suggestions:
            return

        suggestion = self.current_analysis.suggestions[0]

        details = f"""
SUGGESTION DETAILS

Description: {suggestion.description}

Category: {suggestion.category.value}
Potential Savings: ${suggestion.potential_savings:,.2f}
Confidence: {suggestion.confidence_level.value}
Priority Score: {suggestion.priority_score:.1f}

RATIONALE:
{suggestion.rationale}

RECOMMENDATIONS:
{suggestion.recommendations}

REQUIRED DOCUMENTATION:
{suggestion.required_documentation}
        """

        self.details_textbox.configure(state="normal")
        self.details_textbox.delete("0.0", "end")
        self.details_textbox.insert("0.0", details.strip())
        self.details_textbox.configure(state="disabled")

    def _export_report(self):
        """Export analysis report"""
        if not self.current_analysis:
            messagebox.showwarning("No Data", "Please run analysis first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Deduction Analysis Report"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w') as f:
                f.write("AI Deduction Finder Analysis Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Analysis Date: {self.current_analysis.analysis_timestamp}\n")
                f.write(f"Total Potential Savings: ${self.current_analysis.total_potential_savings:,.2f}\n")
                f.write(f"High Confidence Suggestions: {self.current_analysis.high_confidence_count}\n")
                f.write(f"Medium Confidence Suggestions: {self.current_analysis.medium_confidence_count}\n")
                f.write(f"Low Confidence Suggestions: {self.current_analysis.low_confidence_count}\n\n")

                f.write("Top Deduction Opportunities:\n")
                f.write("-" * 30 + "\n")

                # Sort by potential savings
                sorted_suggestions = sorted(
                    self.current_analysis.suggestions,
                    key=lambda s: s.potential_savings,
                    reverse=True
                )

                for i, suggestion in enumerate(sorted_suggestions[:10], 1):
                    f.write(f"{i}. {suggestion.category.value}: {suggestion.description}\n")
                    f.write(f"   Potential Savings: ${suggestion.potential_savings:,.2f}\n")
                    f.write(f"   Confidence: {suggestion.confidence_level.value}\n")
                    f.write(f"   Rationale: {suggestion.rationale}\n\n")

                f.write("\nCategory Summary:\n")
                f.write("-" * 20 + "\n")
                for summary in self.current_analysis.category_summaries:
                    f.write(f"{summary.category.value}: {summary.suggestion_count} suggestions, ")
                    f.write(f"${summary.total_potential_savings:,.2f} potential savings\n")

            messagebox.showinfo("Export Complete", f"Report exported to {file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report: {e}")

    def _refresh_data(self):
        """Refresh tax data and reset analysis"""
        self.current_analysis = None
        self.status_label.configure(text="Data refreshed - Ready for analysis")
        self.progress_var.set(0)

        # Clear all textboxes
        for textbox in [self.preview_textbox, self.suggestions_textbox, self.categories_textbox, self.details_textbox]:
            if textbox:
                textbox.configure(state="normal")
                textbox.delete("0.0", "end")
                textbox.configure(state="disabled")

        for label in self.summary_labels.values():
            label.configure(text="--")

    def show(self):
        """Show the window"""
        self.window.mainloop()