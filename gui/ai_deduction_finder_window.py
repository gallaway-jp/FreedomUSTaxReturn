"""
AI Deduction Finder Window - GUI for AI-powered deduction analysis

Provides an intelligent interface for analyzing tax data to identify
potential missed deductions and tax-saving opportunities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.ai_deduction_finder_service import AIDeductionFinderService, DeductionAnalysisResult, DeductionSuggestion
from services.tax_calculation_service import TaxCalculationService
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

    def __init__(self, parent: tk.Tk, config: AppConfig, tax_data: Optional[TaxData] = None):
        """
        Initialize AI deduction finder window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Tax return data to analyze
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.error_tracker = get_error_tracker()

        # Initialize services
        self.tax_calculation = TaxCalculationService(config)
        self.ai_service = AIDeductionFinderService(config, self.tax_calculation)

        # Current analysis results
        self.current_analysis: Optional[DeductionAnalysisResult] = None

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        self.progress_var: Optional[tk.DoubleVar] = None
        self.status_label: Optional[ttk.Label] = None
        self.tree: Optional[ttk.Treeview] = None

        self._create_window()
        self._setup_ui()
        self._load_initial_data()

    def _create_window(self):
        """Create the main deduction finder window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("AI Deduction Finder")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)

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
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Analysis buttons
        ttk.Button(toolbar, text="Run AI Analysis", command=self._run_analysis).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Export Report", command=self._export_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Refresh Data", command=self._refresh_data).pack(side=tk.LEFT, padx=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(toolbar, variable=self.progress_var, maximum=100)
        progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Status label
        self.status_label = ttk.Label(toolbar, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Notebook for different analysis views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self._create_overview_tab()
        self._create_suggestions_tab()
        self._create_categories_tab()
        self._create_details_tab()

    def _create_overview_tab(self):
        """Create the overview tab with summary metrics"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Overview")

        # Summary metrics frame
        summary_frame = ttk.LabelFrame(tab, text="Analysis Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        # Create summary labels
        self.summary_labels = {}
        metrics = [
            ("Total Potential Savings", "total_savings"),
            ("High Confidence Suggestions", "high_confidence"),
            ("Medium Confidence Suggestions", "medium_confidence"),
            ("Low Confidence Suggestions", "low_confidence"),
            ("Categories Analyzed", "categories_analyzed"),
            ("Analysis Timestamp", "timestamp")
        ]

        for i, (label_text, key) in enumerate(metrics):
            row = i // 3
            col = i % 3

            frame = ttk.Frame(summary_frame)
            frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")

            ttk.Label(frame, text=f"{label_text}:").pack(anchor="w")
            value_label = ttk.Label(frame, text="--", font=("Arial", 10, "bold"))
            value_label.pack(anchor="w")
            self.summary_labels[key] = value_label

        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)
        summary_frame.columnconfigure(2, weight=1)

        # Top suggestions preview
        preview_frame = ttk.LabelFrame(tab, text="Top Deduction Opportunities", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for top suggestions
        columns = ("Category", "Description", "Potential Savings", "Confidence")
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=8)

        for col in columns:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=scrollbar.set)

        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_suggestions_tab(self):
        """Create the suggestions tab with detailed list"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="All Suggestions")

        # Filter frame
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter by Category:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_filter = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.category_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.category_filter.bind("<<ComboboxSelected>>", self._filter_suggestions)

        ttk.Label(filter_frame, text="Min Confidence:").pack(side=tk.LEFT, padx=(0, 5))
        self.confidence_filter = ttk.Combobox(filter_frame, values=["All", "High", "Medium", "Low"], state="readonly", width=10)
        self.confidence_filter.pack(side=tk.LEFT, padx=(0, 5))
        self.confidence_filter.current(0)
        self.confidence_filter.bind("<<ComboboxSelected>>", self._filter_suggestions)

        # Suggestions list
        list_frame = ttk.LabelFrame(tab, text="Deduction Suggestions", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for suggestions
        columns = ("Priority", "Category", "Description", "Potential Savings", "Confidence", "Rationale")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        column_widths = {
            "Priority": 80,
            "Category": 120,
            "Description": 200,
            "Potential Savings": 120,
            "Confidence": 100,
            "Rationale": 250
        }

        for col, width in column_widths.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_suggestion_select)

        # Details frame
        details_frame = ttk.LabelFrame(tab, text="Suggestion Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(10, 0))

        self.details_text = tk.Text(details_frame, wrap=tk.WORD, height=6)
        scrollbar = ttk.Scrollbar(details_frame, command=self.details_text.yview)
        self.details_text.config(yscrollcommand=scrollbar.set)

        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_categories_tab(self):
        """Create the categories analysis tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Categories")

        # Categories overview
        categories_frame = ttk.LabelFrame(tab, text="Deduction Categories Analysis", padding=10)
        categories_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for categories
        columns = ("Category", "Suggestions Found", "Total Potential Savings", "Avg Confidence")
        self.categories_tree = ttk.Treeview(categories_frame, columns=columns, show="headings", height=12)

        for col in columns:
            self.categories_tree.heading(col, text=col)
            self.categories_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(categories_frame, orient=tk.VERTICAL, command=self.categories_tree.yview)
        self.categories_tree.configure(yscrollcommand=scrollbar.set)

        self.categories_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Category details
        details_frame = ttk.LabelFrame(tab, text="Category Insights", padding=10)
        details_frame.pack(fill=tk.X, pady=(10, 0))

        self.category_details_text = tk.Text(details_frame, wrap=tk.WORD, height=8)
        scrollbar = ttk.Scrollbar(details_frame, command=self.category_details_text.yview)
        self.category_details_text.config(yscrollcommand=scrollbar.set)

        self.category_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_details_tab(self):
        """Create the detailed analysis tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Analysis Details")

        # Analysis details
        details_frame = ttk.LabelFrame(tab, text="Analysis Methodology & Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)

        self.analysis_details_text = tk.Text(details_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(details_frame, command=self.analysis_details_text.yview)
        self.analysis_details_text.config(yscrollcommand=scrollbar.set)

        self.analysis_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Analysis info
        info_text = """
AI Deduction Finder Analysis Methodology:

1. Data Analysis: Examines income, expenses, and tax forms for deduction patterns
2. Rule-Based Intelligence: Applies tax rules and common deduction scenarios
3. Confidence Scoring: Rates suggestions based on data completeness and rule matching
4. Priority Ranking: Orders suggestions by potential savings and confidence level
5. Category Coverage: Analyzes 9 major deduction categories:
   - Medical expenses
   - Charitable contributions
   - Business expenses
   - Education costs
   - Home office
   - Vehicle expenses
   - Retirement contributions
   - State/local taxes
   - Energy credits

Confidence Levels:
- High: Strong indicators present, high likelihood of qualification
- Medium: Some indicators present, moderate likelihood
- Low: Limited indicators, further research recommended

Note: This tool provides suggestions based on available data and tax rules.
Consult a tax professional for personalized advice.
        """

        self.analysis_details_text.insert(tk.END, info_text)
        self.analysis_details_text.config(state=tk.DISABLED)

    def _load_initial_data(self):
        """Load initial data and setup"""
        if self.tax_data:
            self.status_label.config(text="Tax data loaded - Ready for analysis")
        else:
            self.status_label.config(text="No tax data available")

        # Setup category filter
        categories = ["All"] + [cat.value for cat in self.ai_service.DeductionCategory]
        self.category_filter["values"] = categories
        self.category_filter.current(0)

    def _run_analysis(self):
        """Run the AI deduction analysis"""
        if not self.tax_data:
            messagebox.showwarning("No Data", "Please load tax data first.")
            return

        # Disable button and show progress
        self.status_label.config(text="Running AI analysis...")
        self.progress_var.set(0)

        # Run analysis in background thread
        def run_analysis_thread():
            try:
                self.progress_var.set(25)
                self.current_analysis = self.ai_service.analyze_deductions(self.tax_data)

                self.progress_var.set(100)
                self.status_label.config(text="Analysis complete")

                # Update UI on main thread
                self.window.after(0, self._update_ui_with_results)

            except Exception as e:
                self.error_tracker.log_error(e, "AI Deduction Analysis")
                self.window.after(0, lambda: messagebox.showerror("Analysis Error", f"Failed to run analysis: {e}"))
                self.window.after(0, lambda: self.status_label.config(text="Analysis failed"))

        thread = threading.Thread(target=run_analysis_thread, daemon=True)
        thread.start()

    def _update_ui_with_results(self):
        """Update the UI with analysis results"""
        if not self.current_analysis:
            return

        analysis = self.current_analysis

        # Update overview tab
        self.summary_labels["total_savings"].config(text=f"${analysis.total_potential_savings:,.2f}")
        self.summary_labels["high_confidence"].config(text=str(analysis.high_confidence_count))
        self.summary_labels["medium_confidence"].config(text=str(analysis.medium_confidence_count))
        self.summary_labels["low_confidence"].config(text=str(analysis.low_confidence_count))
        self.summary_labels["categories_analyzed"].config(text=str(len(analysis.category_summaries)))
        self.summary_labels["timestamp"].config(text=analysis.analysis_timestamp.strftime("%Y-%m-%d %H:%M"))

        # Update preview tree
        self._populate_preview_tree()

        # Update suggestions tree
        self._populate_suggestions_tree()

        # Update categories tree
        self._populate_categories_tree()

    def _populate_preview_tree(self):
        """Populate the preview tree with top suggestions"""
        # Clear existing items
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        if not self.current_analysis:
            return

        # Get top 8 suggestions by potential savings
        top_suggestions = sorted(
            self.current_analysis.suggestions,
            key=lambda s: s.potential_savings,
            reverse=True
        )[:8]

        for suggestion in top_suggestions:
            self.preview_tree.insert("", tk.END, values=(
                suggestion.category.value,
                suggestion.description[:50] + "..." if len(suggestion.description) > 50 else suggestion.description,
                f"${suggestion.potential_savings:,.2f}",
                suggestion.confidence_level.value
            ))

    def _populate_suggestions_tree(self):
        """Populate the suggestions tree"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.current_analysis:
            return

        # Sort by priority (high savings first)
        sorted_suggestions = sorted(
            self.current_analysis.suggestions,
            key=lambda s: (s.priority_score, s.potential_savings),
            reverse=True
        )

        for suggestion in sorted_suggestions:
            self.tree.insert("", tk.END, values=(
                f"{suggestion.priority_score:.1f}",
                suggestion.category.value,
                suggestion.description,
                f"${suggestion.potential_savings:,.2f}",
                suggestion.confidence_level.value,
                suggestion.rationale[:100] + "..." if len(suggestion.rationale) > 100 else suggestion.rationale
            ), tags=(suggestion.id,))

    def _populate_categories_tree(self):
        """Populate the categories tree"""
        # Clear existing items
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)

        if not self.current_analysis:
            return

        for category_summary in self.current_analysis.category_summaries:
            self.categories_tree.insert("", tk.END, values=(
                category_summary.category.value,
                category_summary.suggestion_count,
                f"${category_summary.total_potential_savings:,.2f}",
                f"{category_summary.average_confidence:.1f}"
            ))

    def _filter_suggestions(self, event=None):
        """Filter suggestions based on category and confidence"""
        if not self.tree:
            return

        category_filter = self.category_filter.get()
        confidence_filter = self.confidence_filter.get()

        # Show all items first
        for item in self.tree.get_children():
            self.tree.item(item, tags=())

        # Apply filters
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if not values:
                continue

            category = values[1]  # Category column
            confidence = values[4]  # Confidence column

            show_item = True

            if category_filter != "All" and category != category_filter:
                show_item = False

            if confidence_filter != "All" and confidence != confidence_filter:
                show_item = False

            if not show_item:
                self.tree.detach(item)
            else:
                self.tree.reattach(item, "", tk.END)

    def _on_suggestion_select(self, event):
        """Handle suggestion selection"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        if not values or len(values) < 6:
            return

        # Find the full suggestion details
        suggestion_id = self.tree.item(item, "tags")[0] if self.tree.item(item, "tags") else None

        if suggestion_id and self.current_analysis:
            suggestion = next((s for s in self.current_analysis.suggestions if s.id == suggestion_id), None)
            if suggestion:
                details = f"""
Suggestion: {suggestion.description}

Category: {suggestion.category.value}
Potential Savings: ${suggestion.potential_savings:,.2f}
Confidence: {suggestion.confidence_level.value}
Priority Score: {suggestion.priority_score:.1f}

Rationale:
{suggestion.rationale}

Recommendations:
{suggestion.recommendations}

Required Documentation:
{suggestion.required_documentation}
                """
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(tk.END, details.strip())

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
        self.status_label.config(text="Data refreshed - Ready for analysis")

        # Clear all trees and labels
        for tree in [self.preview_tree, self.tree, self.categories_tree]:
            if tree:
                for item in tree.get_children():
                    tree.delete(item)

        for label in self.summary_labels.values():
            label.config(text="--")

        self.details_text.delete(1.0, tk.END)
        self.category_details_text.delete(1.0, tk.END)

    def show(self):
        """Show the window"""
        self.window.mainloop()