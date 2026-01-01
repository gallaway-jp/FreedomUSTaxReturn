"""
Tax Dashboard Window - Overview of tax situation and key metrics

Provides a comprehensive dashboard view showing:
- Tax liability summary
- Upcoming deadlines
- Action items and recommendations
- Key financial metrics
- Progress indicators
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
import threading

from config.app_config import AppConfig
from models.tax_data import TaxData
from services.tax_calculation_service import TaxCalculationService
from services.tax_year_service import TaxYearService
from services.ai_deduction_finder_service import AIDeductionFinderService
from utils.error_tracker import get_error_tracker


class TaxDashboardWindow:
    """
    Dashboard window providing overview of tax situation and key metrics.

    Features:
    - Tax liability summary with progress indicators
    - Upcoming deadlines and reminders
    - Action items and recommendations
    - Key financial metrics visualization
    - Quick access to common tasks
    """

    def __init__(self, parent: tk.Tk, config: AppConfig, tax_data: TaxData):
        """
        Initialize tax dashboard window.

        Args:
            parent: Parent window
            config: Application configuration
            tax_data: Current tax data
        """
        self.parent = parent
        self.config = config
        self.tax_data = tax_data
        self.error_tracker = get_error_tracker()

        # Initialize services
        self.tax_calculation = TaxCalculationService(config)
        self.tax_year_service = TaxYearService(config)
        self.ai_service = AIDeductionFinderService(config, self.tax_calculation)

        # Dashboard data
        self.dashboard_data: Optional[Dict[str, Any]] = None

        # UI components
        self.window: Optional[tk.Toplevel] = None
        self.progress_vars: Dict[str, tk.DoubleVar] = {}
        self.status_labels: Dict[str, ttk.Label] = {}

        self._create_window()
        self._setup_ui()
        self._load_dashboard_data()

    def _create_window(self):
        """Create the main dashboard window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Tax Dashboard - Freedom US Tax Return")
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

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Tax Dashboard",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Create scrollable frame for dashboard content
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Dashboard sections
        self._create_tax_summary_section(scrollable_frame)
        self._create_deadlines_section(scrollable_frame)
        self._create_action_items_section(scrollable_frame)
        self._create_metrics_section(scrollable_frame)
        self._create_quick_actions_section(scrollable_frame)

        # Status bar
        self.status_label = ttk.Label(main_frame, text="Loading dashboard data...")
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def _create_tax_summary_section(self, parent):
        """Create tax liability summary section"""
        # Section frame
        section_frame = ttk.LabelFrame(parent, text="Tax Summary", padding=10)
        section_frame.pack(fill=tk.X, pady=(0, 15))

        # Tax year and status
        header_frame = ttk.Frame(section_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        current_year = self.tax_data.get_current_year()
        ttk.Label(header_frame, text=f"Tax Year: {current_year}", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        # Filing status
        filing_status = self.tax_data.get('filing_status.status', 'Not Set')
        ttk.Label(header_frame, text=f"Filing Status: {filing_status}").pack(side=tk.RIGHT)

        # Tax calculation summary
        summary_frame = ttk.Frame(section_frame)
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        # Create progress bars for key tax metrics
        self._create_metric_progress(summary_frame, "Tax Liability", "tax_liability", "Calculating...")
        self._create_metric_progress(summary_frame, "Effective Rate", "effective_rate", "Calculating...")
        self._create_metric_progress(summary_frame, "Refund/Owed", "refund_owed", "Calculating...")

        # Key amounts display
        amounts_frame = ttk.Frame(section_frame)
        amounts_frame.pack(fill=tk.X)

        # Left column - Income
        income_frame = ttk.Frame(amounts_frame)
        income_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(income_frame, text="Income Summary", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        self.income_label = ttk.Label(income_frame, text="Calculating...")
        self.income_label.pack(anchor=tk.W, pady=(2, 0))

        # Middle column - Deductions
        deduction_frame = ttk.Frame(amounts_frame)
        deduction_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(deduction_frame, text="Deductions & Credits", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        self.deductions_label = ttk.Label(deduction_frame, text="Calculating...")
        self.deductions_label.pack(anchor=tk.W, pady=(2, 0))

        # Right column - Tax
        tax_frame = ttk.Frame(amounts_frame)
        tax_frame.pack(side=tk.LEFT)

        ttk.Label(tax_frame, text="Tax Calculation", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        self.tax_label = ttk.Label(tax_frame, text="Calculating...")
        self.tax_label.pack(anchor=tk.W, pady=(2, 0))

    def _create_metric_progress(self, parent, label_text, metric_key, default_text):
        """Create a progress bar with label for a metric"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 5))

        # Label
        ttk.Label(frame, text=f"{label_text}:").pack(side=tk.LEFT)

        # Progress bar
        self.progress_vars[metric_key] = tk.DoubleVar()
        progress = ttk.Progressbar(frame, variable=self.progress_vars[metric_key],
                                 maximum=100, length=200)
        progress.pack(side=tk.LEFT, padx=(10, 10))

        # Value label
        self.status_labels[metric_key] = ttk.Label(frame, text=default_text)
        self.status_labels[metric_key].pack(side=tk.LEFT)

    def _create_deadlines_section(self, parent):
        """Create upcoming deadlines section"""
        section_frame = ttk.LabelFrame(parent, text="Upcoming Deadlines", padding=10)
        section_frame.pack(fill=tk.X, pady=(0, 15))

        # Deadlines list
        self.deadlines_text = tk.Text(section_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(section_frame, command=self.deadlines_text.yview)
        self.deadlines_text.configure(yscrollcommand=scrollbar.set)

        self.deadlines_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_action_items_section(self, parent):
        """Create action items and recommendations section"""
        section_frame = ttk.LabelFrame(parent, text="Action Items & Recommendations", padding=10)
        section_frame.pack(fill=tk.X, pady=(0, 15))

        # Action items list
        self.actions_text = tk.Text(section_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(section_frame, command=self.actions_text.yview)
        self.actions_text.configure(yscrollcommand=scrollbar.set)

        self.actions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_metrics_section(self, parent):
        """Create key metrics visualization section"""
        section_frame = ttk.LabelFrame(parent, text="Key Metrics", padding=10)
        section_frame.pack(fill=tk.X, pady=(0, 15))

        # Metrics grid
        metrics_frame = ttk.Frame(section_frame)
        metrics_frame.pack(fill=tk.X)

        # Row 1
        ttk.Label(metrics_frame, text="Data Completeness:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.completeness_label = ttk.Label(metrics_frame, text="Calculating...")
        self.completeness_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        # Row 2
        ttk.Label(metrics_frame, text="Potential Deductions:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.deductions_potential_label = ttk.Label(metrics_frame, text="Calculating...")
        self.deductions_potential_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        # Row 3
        ttk.Label(metrics_frame, text="Tax Efficiency Score:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.efficiency_label = ttk.Label(metrics_frame, text="Calculating...")
        self.efficiency_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)

    def _create_quick_actions_section(self, parent):
        """Create quick actions section"""
        section_frame = ttk.LabelFrame(parent, text="Quick Actions", padding=10)
        section_frame.pack(fill=tk.X, pady=(0, 15))

        # Action buttons
        actions_frame = ttk.Frame(section_frame)
        actions_frame.pack(fill=tk.X)

        ttk.Button(actions_frame, text="Run AI Analysis",
                  command=self._run_ai_analysis).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(actions_frame, text="Generate Forms",
                  command=self._generate_forms).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(actions_frame, text="Export Report",
                  command=self._export_report).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(actions_frame, text="Refresh Dashboard",
                  command=self._refresh_dashboard).pack(side=tk.LEFT)

    def _load_dashboard_data(self):
        """Load dashboard data in background thread"""
        def load_data():
            try:
                self.status_label.config(text="Calculating tax summary...")

                # Calculate tax summary
                tax_summary = self._calculate_tax_summary()

                # Get upcoming deadlines
                deadlines = self._get_upcoming_deadlines()

                # Get action items
                action_items = self._get_action_items()

                # Calculate metrics
                metrics = self._calculate_metrics()

                # Update UI
                self.window.after(0, lambda: self._update_dashboard_display(
                    tax_summary, deadlines, action_items, metrics
                ))

            except Exception as e:
                self.error_tracker.track_error(e, {"operation": "load_dashboard_data"})
                self.window.after(0, lambda: self.status_label.config(
                    text=f"Error loading dashboard: {str(e)}", foreground="red"
                ))

        # Run in background thread
        threading.Thread(target=load_data, daemon=True).start()

    def _calculate_tax_summary(self) -> Dict[str, Any]:
        """Calculate tax summary data"""
        current_year = self.tax_data.get_current_year()

        # Calculate total income
        total_income = self.tax_calculation.calculate_total_income(self.tax_data, current_year)

        # Calculate deductions and credits
        deductions = self.tax_calculation.calculate_total_deductions(self.tax_data, current_year)
        credits = self.tax_calculation.calculate_total_credits(self.tax_data, current_year)

        # Calculate tax liability
        taxable_income = max(0, total_income - deductions)
        tax_liability = self.tax_calculation.calculate_income_tax(taxable_income,
                                                                self.tax_data.get('filing_status.status', 'single'),
                                                                current_year)

        # Calculate effective rate
        effective_rate = (tax_liability / total_income * 100) if total_income > 0 else 0

        # Calculate refund/owed
        payments = self.tax_calculation.calculate_total_payments(self.tax_data, current_year)
        refund_owed = payments - tax_liability

        return {
            'total_income': total_income,
            'deductions_credits': deductions + credits,
            'tax_liability': tax_liability,
            'effective_rate': effective_rate,
            'refund_owed': refund_owed,
            'taxable_income': taxable_income
        }

    def _get_upcoming_deadlines(self) -> List[str]:
        """Get list of upcoming tax deadlines"""
        deadlines = []
        current_year = self.tax_data.get_current_year()

        # Federal filing deadline
        filing_deadline = self.tax_year_service.get_filing_deadline(current_year)
        if filing_deadline:
            days_until = (filing_deadline - date.today()).days
            if days_until >= 0:
                deadlines.append(f"Federal tax return due: {filing_deadline.strftime('%B %d, %Y')} ({days_until} days)")

        # Estimated tax deadlines (quarterly)
        estimated_deadlines = [
            date(current_year, 4, 15),   # Q1
            date(current_year, 6, 15),   # Q2
            date(current_year, 9, 15),   # Q3
            date(current_year + 1, 1, 15) # Q4
        ]

        for deadline in estimated_deadlines:
            if deadline >= date.today():
                days_until = (deadline - date.today()).days
                deadlines.append(f"Estimated tax payment due: {deadline.strftime('%B %d, %Y')} ({days_until} days)")
                break  # Only show next one

        return deadlines[:5]  # Limit to 5 deadlines

    def _get_action_items(self) -> List[str]:
        """Get list of recommended action items"""
        actions = []

        # Check data completeness
        completeness = self._calculate_data_completeness()
        if completeness < 80:
            actions.append(f"Complete your tax data ({completeness:.1f}% complete)")

        # Check for potential deductions
        try:
            analysis = self.ai_service.analyze_deductions(self.tax_data)
            if analysis.total_potential_savings > 1000:
                actions.append(f"Review {len(analysis.suggestions)} potential deductions (save ~${analysis.total_potential_savings:,.0f})")
        except:
            actions.append("Run AI deduction analysis to find savings opportunities")

        # Check filing status
        if not self.tax_data.get('filing_status.status'):
            actions.append("Set your filing status")

        # Check for missing income
        income_sources = len(self.tax_data.get('income.w2_forms', [])) + \
                        len(self.tax_data.get('income1099_forms', []))
        if income_sources == 0:
            actions.append("Add your income sources (W-2, 1099 forms)")

        # Check e-filing readiness
        ssn = self.tax_data.get('personal_info.ssn')
        if not ssn:
            actions.append("Enter your SSN for e-filing")

        return actions[:8]  # Limit to 8 actions

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate key metrics"""
        # Data completeness
        completeness = self._calculate_data_completeness()

        # Potential deductions
        potential_savings = 0
        try:
            analysis = self.ai_service.analyze_deductions(self.tax_data)
            potential_savings = analysis.total_potential_savings
        except:
            pass

        # Tax efficiency score (simplified)
        tax_summary = self._calculate_tax_summary()
        efficiency_score = min(100, max(0, 100 - (tax_summary['effective_rate'] * 2)))

        return {
            'data_completeness': completeness,
            'potential_deductions': potential_savings,
            'tax_efficiency': efficiency_score
        }

    def _calculate_data_completeness(self) -> float:
        """Calculate data completeness percentage"""
        required_fields = [
            'personal_info.first_name',
            'personal_info.last_name',
            'personal_info.ssn',
            'personal_info.address',
            'filing_status.status',
        ]

        completed_fields = sum(1 for field in required_fields if self.tax_data.get(field))
        return (completed_fields / len(required_fields)) * 100

    def _update_dashboard_display(self, tax_summary, deadlines, action_items, metrics):
        """Update the dashboard display with calculated data"""
        # Update tax summary
        self.income_label.config(text=".2f")
        self.deductions_label.config(text=".2f")
        self.tax_label.config(text=".2f")

        # Update progress bars
        self._update_progress_bar('tax_liability', tax_summary['tax_liability'] / max(tax_summary['taxable_income'], 1) * 100,
                                 ".2f")
        self._update_progress_bar('effective_rate', tax_summary['effective_rate'], ".1f")
        self._update_progress_bar('refund_owed', abs(tax_summary['refund_owed']) / max(tax_summary['tax_liability'], 1) * 100,
                                 ".2f")

        # Update deadlines
        self.deadlines_text.config(state=tk.NORMAL)
        self.deadlines_text.delete(1.0, tk.END)
        for deadline in deadlines:
            self.deadlines_text.insert(tk.END, f"• {deadline}\n")
        self.deadlines_text.config(state=tk.DISABLED)

        # Update action items
        self.actions_text.config(state=tk.NORMAL)
        self.actions_text.delete(1.0, tk.END)
        for action in action_items:
            self.actions_text.insert(tk.END, f"• {action}\n")
        self.actions_text.config(state=tk.DISABLED)

        # Update metrics
        self.completeness_label.config(text=".1f")
        self.deductions_potential_label.config(text=".0f")
        self.efficiency_label.config(text=".1f")

        # Update status
        self.status_label.config(text="Dashboard loaded successfully", foreground="green")

    def _update_progress_bar(self, key, value, format_str):
        """Update a progress bar and its label"""
        self.progress_vars[key].set(min(100, max(0, value)))
        self.status_labels[key].config(text=format_str)

    def _run_ai_analysis(self):
        """Run AI deduction analysis"""
        try:
            from gui.ai_deduction_finder_window import AIDeductionFinderWindow
            AIDeductionFinderWindow(self.window, self.config, self.tax_data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open AI analysis: {str(e)}")

    def _generate_forms(self):
        """Generate tax forms"""
        try:
            # This would open the form viewer with generated forms
            messagebox.showinfo("Generate Forms", "Form generation would open here")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate forms: {str(e)}")

    def _export_report(self):
        """Export dashboard report"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w') as f:
                    f.write("Tax Dashboard Report\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    # Add dashboard data
                    if self.dashboard_data:
                        f.write("Tax Summary:\n")
                        f.write(f"- Total Income: ${self.dashboard_data.get('total_income', 0):,.2f}\n")
                        f.write(f"- Tax Liability: ${self.dashboard_data.get('tax_liability', 0):,.2f}\n")
                        f.write(f"- Effective Rate: {self.dashboard_data.get('effective_rate', 0):.1f}%\n")

                messagebox.showinfo("Success", f"Report exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {str(e)}")

    def _refresh_dashboard(self):
        """Refresh dashboard data"""
        self.status_label.config(text="Refreshing dashboard...")
        self._load_dashboard_data()


def open_tax_dashboard(parent: tk.Tk, config: AppConfig, tax_data: TaxData):
    """
    Open the tax dashboard window.

    Args:
        parent: Parent window
        config: Application configuration
        tax_data: Tax return data
    """
    try:
        TaxDashboardWindow(parent, config, tax_data)
    except Exception as e:
        messagebox.showerror("Dashboard Error",
            f"Failed to open tax dashboard:\n\n{str(e)}")