"""
State Tax Integration GUI Window

Provides a comprehensive interface for preparing state tax returns,
managing multi-state filings, and handling state-specific tax calculations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import webbrowser

from services.state_tax_integration_service import (
    StateTaxIntegrationService,
    StateCode,
    FilingStatus,
    StateTaxType,
    StateTaxInfo,
    StateIncome,
    StateDeductions,
    StateTaxCalculation,
    StateTaxReturn
)
from gui.theme_manager import ThemeManager


class StateTaxIntegrationWindow:
    """Main window for state tax integration functionality"""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.service = StateTaxIntegrationService(
            self.parent.config if hasattr(self.parent, 'config') else None,
            None  # Will be initialized properly in main app
        )

        # Window setup
        self.window = tk.Toplevel(parent)
        self.window.title("State Tax Integration")
        self.window.geometry("1400x900")
        self.window.configure(bg=theme_manager.get_bg_color())

        # Initialize variables
        self.selected_state: Optional[StateCode] = None
        self.selected_return: Optional[str] = None
        self.current_tax_year = datetime.now().year
        self.multi_state_mode = False

        # Create main layout
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        # Load initial data
        self._refresh_state_list()
        self._refresh_return_list()

        # Apply theme
        self.theme_manager.apply_theme_to_window(self.window)

    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New State Return", command=self._new_state_return)
        file_menu.add_command(label="Open Return", command=self._open_return)
        file_menu.add_command(label="Save Return", command=self._save_return)
        file_menu.add_separator()
        file_menu.add_command(label="Export for E-Filing", command=self._export_for_filing)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.window.destroy)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh All", command=self._refresh_all)
        view_menu.add_command(label="State Tax Information", command=self._show_state_info)
        view_menu.add_checkbutton(label="Multi-State Mode", command=self._toggle_multi_state_mode,
                                variable=tk.BooleanVar(value=self.multi_state_mode))

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Calculate Tax", command=self._calculate_tax)
        tools_menu.add_command(label="Validate Return", command=self._validate_return)
        tools_menu.add_command(label="Compare States", command=self._compare_states)
        tools_menu.add_separator()
        tools_menu.add_command(label="Tax Calculator", command=self._show_tax_calculator)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="State Tax Deadlines", command=self._show_deadlines)
        help_menu.add_command(label="State Tax Resources", command=self._show_resources)
        help_menu.add_command(label="About State Taxes", command=self._show_about)

    def _create_main_layout(self):
        """Create the main layout with paned windows"""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - State selection and returns
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # Right panel - Return details and calculations
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        self._create_left_panel(left_frame)
        self._create_right_panel(right_frame)

    def _create_left_panel(self, parent: ttk.Frame):
        """Create the left panel with state and return lists"""
        # State selection section
        state_frame = ttk.LabelFrame(parent, text="State Selection")
        state_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # State filter controls
        filter_frame = ttk.Frame(state_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=2)
        self.state_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.state_filter_var, width=15)
        filter_combo['values'] = ["All", "Progressive", "Flat", "No Income Tax"]
        filter_combo.pack(side=tk.LEFT, padx=2)
        filter_combo.bind('<<ComboboxSelected>>', self._apply_state_filter)

        # State listbox
        state_list_frame = ttk.Frame(state_frame)
        state_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        state_scrollbar = ttk.Scrollbar(state_list_frame)
        state_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.state_listbox = tk.Listbox(
            state_list_frame,
            yscrollcommand=state_scrollbar.set,
            selectmode=tk.MULTIPLE if self.multi_state_mode else tk.SINGLE,
            bg=self.theme_manager.get_bg_color(),
            fg=self.theme_manager.get_fg_color(),
            height=12
        )
        self.state_listbox.pack(fill=tk.BOTH, expand=True)
        self.state_listbox.bind('<<ListboxSelect>>', self._on_state_select)

        state_scrollbar.config(command=self.state_listbox.yview)

        # State buttons
        state_btn_frame = ttk.Frame(state_frame)
        state_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(state_btn_frame, text="Select State(s)", command=self._select_states).pack(side=tk.LEFT, padx=2)
        ttk.Button(state_btn_frame, text="State Info", command=self._show_selected_state_info).pack(side=tk.LEFT, padx=2)

        # Returns section
        returns_frame = ttk.LabelFrame(parent, text="Tax Returns")
        returns_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Returns treeview
        returns_tree_frame = ttk.Frame(returns_frame)
        returns_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("State", "Year", "Status", "Tax Owed", "Refund")
        self.returns_tree = ttk.Treeview(returns_tree_frame, columns=columns, show="headings", height=8)

        # Configure columns
        self.returns_tree.heading("State", text="State")
        self.returns_tree.heading("Year", text="Year")
        self.returns_tree.heading("Status", text="Status")
        self.returns_tree.heading("Tax Owed", text="Tax Owed")
        self.returns_tree.heading("Refund", text="Refund")

        self.returns_tree.column("State", width=60)
        self.returns_tree.column("Year", width=60)
        self.returns_tree.column("Status", width=80)
        self.returns_tree.column("Tax Owed", width=100, anchor=tk.E)
        self.returns_tree.column("Refund", width=100, anchor=tk.E)

        # Add scrollbar
        returns_scrollbar = ttk.Scrollbar(returns_tree_frame, orient=tk.VERTICAL, command=self.returns_tree.yview)
        self.returns_tree.configure(yscrollcommand=returns_scrollbar.set)

        self.returns_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        returns_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.returns_tree.bind('<<TreeviewSelect>>', self._on_return_select)

        # Return buttons
        return_btn_frame = ttk.Frame(returns_frame)
        return_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(return_btn_frame, text="New Return", command=self._new_state_return).pack(side=tk.LEFT, padx=2)
        ttk.Button(return_btn_frame, text="Edit Return", command=self._edit_return).pack(side=tk.LEFT, padx=2)
        ttk.Button(return_btn_frame, text="Delete Return", command=self._delete_return).pack(side=tk.LEFT, padx=2)

    def _create_right_panel(self, parent: ttk.Frame):
        """Create the right panel with return details and calculations"""
        # Tax calculation section
        calc_frame = ttk.LabelFrame(parent, text="Tax Calculation")
        calc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tax year and filing status
        header_frame = ttk.Frame(calc_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header_frame, text="Tax Year:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.tax_year_var = tk.StringVar(value=str(self.current_tax_year))
        tax_year_combo = ttk.Combobox(header_frame, textvariable=self.tax_year_var, width=8)
        tax_year_combo['values'] = [str(year) for year in range(self.current_tax_year-3, self.current_tax_year+2)]
        tax_year_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(header_frame, text="Filing Status:").grid(row=0, column=2, sticky=tk.W, padx=10, pady=2)
        self.filing_status_var = tk.StringVar(value="single")
        filing_combo = ttk.Combobox(header_frame, textvariable=self.filing_status_var, width=15)
        filing_combo['values'] = ["single", "married_filing_jointly", "married_filing_separately", "head_of_household"]
        filing_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)

        # Income section
        income_frame = ttk.LabelFrame(calc_frame, text="Income")
        income_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Income inputs
        income_inputs = [
            ("Wages/Salary:", "wages"),
            ("Interest Income:", "interest"),
            ("Dividend Income:", "dividends"),
            ("Capital Gains:", "capital_gains"),
            ("Business Income:", "business_income"),
            ("Rental Income:", "rental_income"),
            ("Other Income:", "other_income")
        ]

        self.income_vars = {}
        for i, (label, var_name) in enumerate(income_inputs):
            ttk.Label(income_frame, text=label).grid(row=i//2, column=(i%2)*2, sticky=tk.W, pady=2)
            var = tk.StringVar(value="0")
            self.income_vars[var_name] = var
            ttk.Entry(income_frame, textvariable=var, width=15).grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=2)

        # Deductions section
        deduc_frame = ttk.LabelFrame(calc_frame, text="Deductions & Exemptions")
        deduc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Deduction inputs
        deduc_inputs = [
            ("Standard Deduction:", "standard_deduction"),
            ("Itemized Deductions:", "itemized_deductions"),
            ("Personal Exemption:", "personal_exemption"),
            ("Dependent Exemptions:", "dependent_exemptions")
        ]

        self.deduc_vars = {}
        for i, (label, var_name) in enumerate(deduc_inputs):
            ttk.Label(deduc_frame, text=label).grid(row=i//2, column=(i%2)*2, sticky=tk.W, pady=2)
            var = tk.StringVar(value="0")
            self.deduc_vars[var_name] = var
            ttk.Entry(deduc_frame, textvariable=var, width=15).grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=2)

        # Calculate button
        calc_btn_frame = ttk.Frame(calc_frame)
        calc_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(calc_btn_frame, text="Calculate Tax", command=self._calculate_tax).pack(side=tk.LEFT, padx=5)
        ttk.Button(calc_btn_frame, text="Clear All", command=self._clear_inputs).pack(side=tk.LEFT, padx=5)

        # Results section
        results_frame = ttk.LabelFrame(parent, text="Tax Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Results text area
        results_text_frame = ttk.Frame(results_frame)
        results_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        results_scrollbar = ttk.Scrollbar(results_text_frame)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(
            results_text_frame,
            height=12,
            wrap=tk.WORD,
            yscrollcommand=results_scrollbar.set,
            bg=self.theme_manager.get_bg_color(),
            fg=self.theme_manager.get_fg_color(),
            state=tk.DISABLED
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        results_scrollbar.config(command=self.results_text.yview)

    def _create_status_bar(self):
        """Create the status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a state to begin")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _new_state_return(self):
        """Create a new state tax return"""
        if not self.selected_state:
            messagebox.showwarning("Warning", "Please select a state first")
            return

        dialog = StateReturnDialog(self.window, self.theme_manager, self.service, self.selected_state)
        if dialog.result:
            taxpayer_info, income, deductions = dialog.result
            try:
                return_id = self.service.create_state_tax_return(
                    self.selected_state, self.current_tax_year, taxpayer_info,
                    FilingStatus(self.filing_status_var.get()), income, deductions
                )
                self._refresh_return_list()
                self.status_var.set(f"Created new return for {self.selected_state.value}")
                messagebox.showinfo("Success", f"State tax return created successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create return: {str(e)}")

    def _open_return(self):
        """Open an existing return"""
        # This would typically open a file dialog to load a saved return
        messagebox.showinfo("Info", "Open return functionality - coming soon")

    def _save_return(self):
        """Save the current return"""
        if not self.selected_return:
            messagebox.showwarning("Warning", "No return selected")
            return

        # This would save the return to a file
        messagebox.showinfo("Info", "Save return functionality - coming soon")

    def _edit_return(self):
        """Edit the selected return"""
        if not self.selected_return:
            messagebox.showwarning("Warning", "Please select a return to edit")
            return

        # Open edit dialog
        messagebox.showinfo("Info", "Edit return functionality - coming soon")

    def _delete_return(self):
        """Delete the selected return"""
        if not self.selected_return:
            messagebox.showwarning("Warning", "Please select a return to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this return?"):
            try:
                success = self.service.delete_state_tax_return(self.selected_return)
                if success:
                    self._refresh_return_list()
                    self.selected_return = None
                    self.status_var.set("Return deleted")
                else:
                    messagebox.showerror("Error", "Failed to delete return")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete return: {str(e)}")

    def _calculate_tax(self):
        """Calculate tax for current inputs"""
        try:
            # Get input values
            tax_year = int(self.tax_year_var.get())
            filing_status = FilingStatus(self.filing_status_var.get())

            # Build income object
            income = StateIncome(
                wages=float(self.income_vars['wages'].get() or 0),
                interest=float(self.income_vars['interest'].get() or 0),
                dividends=float(self.income_vars['dividends'].get() or 0),
                capital_gains=float(self.income_vars['capital_gains'].get() or 0),
                business_income=float(self.income_vars['business_income'].get() or 0),
                rental_income=float(self.income_vars['rental_income'].get() or 0),
                other_income=float(self.income_vars['other_income'].get() or 0)
            )

            # Build deductions object
            deductions = StateDeductions(
                standard_deduction=float(self.deduc_vars['standard_deduction'].get() or 0),
                itemized_deductions=float(self.deduc_vars['itemized_deductions'].get() or 0),
                personal_exemption=float(self.deduc_vars['personal_exemption'].get() or 0),
                dependent_exemptions=float(self.deduc_vars['dependent_exemptions'].get() or 0)
            )

            # Calculate tax
            if self.multi_state_mode and hasattr(self, 'selected_states') and self.selected_states:
                # Multi-state calculation
                results = self.service.calculate_multi_state_tax(
                    self.selected_states, tax_year, filing_status, income, deductions
                )
                self._display_multi_state_results(results, income, deductions)
            else:
                # Single state calculation
                if not self.selected_state:
                    messagebox.showwarning("Warning", "Please select a state first")
                    return

                calculation = self.service.calculate_state_tax(
                    self.selected_state, tax_year, filing_status, income, deductions
                )
                self._display_single_state_results(calculation, income, deductions)

            self.status_var.set(f"Tax calculated for {self.selected_state.value if self.selected_state else 'selected states'}")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input value: {str(e)}")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate tax: {str(e)}")

    def _display_single_state_results(self, calculation: StateTaxCalculation,
                                    income: StateIncome, deductions: StateDeductions):
        """Display results for single state calculation"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, f"STATE TAX CALCULATION - {calculation.state_code.value}\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")

        self.results_text.insert(tk.END, f"Tax Year: {calculation.tax_year}\n")
        self.results_text.insert(tk.END, f"Filing Status: {calculation.filing_status.value.replace('_', ' ').title()}\n\n")

        self.results_text.insert(tk.END, f"Gross Income: ${income.total_income:,.2f}\n")
        self.results_text.insert(tk.END, f"Total Deductions: ${deductions.total_deductions:,.2f}\n")
        self.results_text.insert(tk.END, f"Taxable Income: ${calculation.taxable_income:,.2f}\n\n")

        self.results_text.insert(tk.END, f"Tax Amount: ${calculation.tax_amount:,.2f}\n")
        self.results_text.insert(tk.END, f"Effective Rate: {calculation.effective_rate:.2%}\n")
        self.results_text.insert(tk.END, f"Marginal Rate: {calculation.marginal_rate:.2%}\n")
        if calculation.credits > 0:
            self.results_text.insert(tk.END, f"Tax Credits: ${calculation.credits:,.2f}\n")
        self.results_text.insert(tk.END, f"Net Tax Owed: ${calculation.net_tax_owed:,.2f}\n\n")

        if calculation.breakdown:
            self.results_text.insert(tk.END, "TAX BREAKDOWN:\n")
            for bracket_desc, tax_amount in calculation.breakdown.items():
                self.results_text.insert(tk.END, f"  {bracket_desc}: ${tax_amount:,.2f}\n")

        self.results_text.config(state=tk.DISABLED)

    def _display_multi_state_results(self, results: Dict[str, StateTaxCalculation],
                                   income: StateIncome, deductions: StateDeductions):
        """Display results for multi-state calculation"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "MULTI-STATE TAX CALCULATION\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")

        total_tax = 0
        for state_code, calculation in results.items():
            self.results_text.insert(tk.END, f"{state_code}: ${calculation.net_tax_owed:,.2f}")
            self.results_text.insert(tk.END, f" (Effective: {calculation.effective_rate:.2%})\n")
            total_tax += calculation.net_tax_owed

        self.results_text.insert(tk.END, "\n" + "-" * 30 + "\n")
        self.results_text.insert(tk.END, f"TOTAL TAX OWED: ${total_tax:,.2f}\n\n")

        # Show details for each state
        for state_code, calculation in results.items():
            self.results_text.insert(tk.END, f"DETAILS FOR {state_code}:\n")
            self.results_text.insert(tk.END, f"  Taxable Income: ${calculation.taxable_income:,.2f}\n")
            self.results_text.insert(tk.END, f"  Tax Amount: ${calculation.tax_amount:,.2f}\n")
            if calculation.credits > 0:
                self.results_text.insert(tk.END, f"  Credits: ${calculation.credits:,.2f}\n")
            self.results_text.insert(tk.END, f"  Net Owed: ${calculation.net_tax_owed:,.2f}\n\n")

        self.results_text.config(state=tk.DISABLED)

    def _validate_return(self):
        """Validate the current return"""
        if not self.selected_return:
            messagebox.showwarning("Warning", "Please select a return to validate")
            return

        try:
            errors = self.service.validate_state_tax_return(self.selected_return)

            if not errors:
                messagebox.showinfo("Validation", "Return is valid!")
                self.status_var.set("Return validation passed")
            else:
                error_text = "Validation Errors:\n\n" + "\n".join(f"• {error}" for error in errors)
                messagebox.showwarning("Validation Failed", error_text)
                self.status_var.set(f"Return has {len(errors)} validation error(s)")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to validate return: {str(e)}")

    def _export_for_filing(self):
        """Export return for e-filing"""
        if not self.selected_return:
            messagebox.showwarning("Warning", "Please select a return to export")
            return

        try:
            form_data = self.service.generate_state_tax_form(self.selected_return)

            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export State Tax Return"
            )

            if filename:
                with open(filename, 'w') as f:
                    json.dump(form_data, f, indent=2, default=str)

                self.status_var.set(f"Return exported to {filename}")
                messagebox.showinfo("Success", f"Return exported successfully to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export return: {str(e)}")

    def _compare_states(self):
        """Compare tax burdens across states"""
        if not hasattr(self, 'selected_states') or len(self.selected_states) < 2:
            messagebox.showwarning("Warning", "Please select at least 2 states to compare")
            return

        # This would show a comparison dialog
        messagebox.showinfo("Info", "State comparison functionality - coming soon")

    def _show_tax_calculator(self):
        """Show the tax calculator dialog"""
        dialog = TaxCalculatorDialog(self.window, self.theme_manager, self.service)
        dialog.show()

    def _show_deadlines(self):
        """Show state tax deadlines"""
        deadlines = self.service.get_state_tax_deadlines(self.current_tax_year)

        deadline_text = "STATE TAX DEADLINES\n" + "=" * 30 + "\n\n"
        for state, deadline in sorted(deadlines.items()):
            deadline_text += f"{state}: {deadline}\n"

        # Show in a dialog
        deadline_window = tk.Toplevel(self.window)
        deadline_window.title("State Tax Deadlines")
        deadline_window.geometry("400x600")

        text_widget = tk.Text(deadline_window, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(deadline_window, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.insert(tk.END, deadline_text)
        text_widget.config(state=tk.DISABLED)

    def _show_resources(self):
        """Show state tax resources"""
        resources_text = """
STATE TAX RESOURCES

Federal Resources:
• IRS Website: https://www.irs.gov/
• State Tax Forms: Available on state revenue department websites

State-Specific Resources:
• California: https://www.cdtfa.ca.gov/
• New York: https://www.tax.ny.gov/
• Texas: https://comptroller.texas.gov/
• Florida: https://floridarevenue.com/

Professional Resources:
• Tax software comparison sites
• State CPA society websites
• Tax preparation software documentation

For the most current information, always consult the official state tax authority website.
        """

        messagebox.showinfo("State Tax Resources", resources_text)

    def _show_about(self):
        """Show about dialog"""
        about_text = """
State Tax Integration Module

Version: 1.0.0
Purpose: Multi-state tax return preparation and e-filing

Features:
• Support for all 50 states plus territories
• Progressive, flat, and no-income-tax state handling
• Multi-state tax calculations
• State-specific form generation
• E-filing preparation
• Tax burden comparison across states

Supported States: All 50 states + DC, PR, VI, GU, MP, AS
Tax Types: Progressive brackets, flat rates, no income tax
        """
        messagebox.showinfo("About State Tax Integration", about_text)

    def _refresh_all(self):
        """Refresh all data"""
        self._refresh_state_list()
        self._refresh_return_list()

    def _refresh_state_list(self):
        """Refresh the state list"""
        self.state_listbox.delete(0, tk.END)

        states = self.service.get_all_states()
        for state in sorted(states, key=lambda s: s.state_name):
            display_text = f"{state.state_name} ({state.state_code.value})"
            if state.tax_type == StateTaxType.NO_INCOME_TAX:
                display_text += " - No Income Tax"
            elif state.tax_type == StateTaxType.FLAT:
                display_text += f" - Flat {state.flat_rate:.1%}"
            else:
                display_text += " - Progressive"

            self.state_listbox.insert(tk.END, display_text)

            # Store state code for later retrieval
            if not hasattr(self.state_listbox, 'state_codes'):
                self.state_listbox.state_codes = []
            self.state_listbox.state_codes.append(state.state_code)

    def _refresh_return_list(self):
        """Refresh the returns list"""
        # Clear existing items
        for item in self.returns_tree.get_children():
            self.returns_tree.delete(item)

        # Add returns (this would be filtered by taxpayer in a real app)
        for return_id, tax_return in self.service.tax_returns.items():
            self.returns_tree.insert("", tk.END, values=(
                tax_return.state_code.value,
                tax_return.tax_year,
                tax_return.status.title(),
                f"${tax_return.calculation.net_tax_owed:,.2f}",
                f"${tax_return.refund_amount:,.2f}"
            ), tags=(return_id,))

    def _apply_state_filter(self, event=None):
        """Apply state filter"""
        filter_value = self.state_filter_var.get()
        self._refresh_state_list()

        # Filter the displayed items
        if filter_value != "All":
            # This is a simplified filter - in practice you'd filter the actual list
            pass

    def _on_state_select(self, event):
        """Handle state selection"""
        selection = self.state_listbox.curselection()
        if selection:
            if self.multi_state_mode:
                # Multi-select mode
                selected_indices = list(selection)
                self.selected_states = []
                for idx in selected_indices:
                    if hasattr(self.state_listbox, 'state_codes') and idx < len(self.state_listbox.state_codes):
                        self.selected_states.append(self.state_listbox.state_codes[idx])

                if self.selected_states:
                    state_names = [s.value for s in self.selected_states]
                    self.status_var.set(f"Selected states: {', '.join(state_names)}")
            else:
                # Single select mode
                index = selection[0]
                if hasattr(self.state_listbox, 'state_codes') and index < len(self.state_listbox.state_codes):
                    self.selected_state = self.state_listbox.state_codes[index]
                    self.status_var.set(f"Selected state: {self.selected_state.value}")

    def _on_return_select(self, event):
        """Handle return selection"""
        selection = self.returns_tree.selection()
        if selection:
            item = selection[0]
            return_id = self.returns_tree.item(item, 'tags')[0]
            self.selected_return = return_id

            tax_return = self.service.get_state_tax_return(return_id)
            if tax_return:
                self.status_var.set(f"Selected return: {tax_return.state_code.value} {tax_return.tax_year}")

    def _select_states(self):
        """Handle state selection button"""
        self._on_state_select(None)

    def _show_selected_state_info(self):
        """Show information for selected state"""
        if not self.selected_state:
            messagebox.showwarning("Warning", "Please select a state first")
            return

        state_info = self.service.get_state_tax_info(self.selected_state)
        if state_info:
            info_text = f"""
{state_info.state_name} Tax Information

Tax Type: {state_info.tax_type.value.replace('_', ' ').title()}
Tax Deadline: {state_info.tax_deadline}
E-filing Supported: {'Yes' if state_info.e_filing_supported else 'No'}
Local Tax Supported: {'Yes' if state_info.local_tax_supported else 'No'}

Standard Deductions:
"""

            for status, amount in state_info.standard_deduction.items():
                info_text += f"  {status.value.replace('_', ' ').title()}: ${amount:,.0f}\n"

            if state_info.flat_rate:
                info_text += f"\nFlat Tax Rate: {state_info.flat_rate:.2%}"

            messagebox.showinfo(f"{state_info.state_name} Tax Info", info_text)

    def _show_state_info(self):
        """Show general state tax information"""
        states = self.service.get_all_states()

        progressive_count = len([s for s in states if s.tax_type == StateTaxType.PROGRESSIVE])
        flat_count = len([s for s in states if s.tax_type == StateTaxType.FLAT])
        no_tax_count = len([s for s in states if s.tax_type == StateTaxType.NO_INCOME_TAX])

        info_text = f"""
STATE TAX OVERVIEW

Total States/Territories: {len(states)}

Tax Systems:
• Progressive Tax States: {progressive_count}
• Flat Tax States: {flat_count}
• No Income Tax: {no_tax_count}

Progressive States: CA, NY, NJ, PA, IL, MA, MD, CT, MN, OR, ME, VT, RI, HI, DE, IA, KY, LA, MS, NE, NM, ND, OK, SC, SD, UT, WV, WY

Flat Tax States: CO, IL, IN, KS, MI, NC, NH, TN, UT, WA

No Income Tax: AK, FL, NV, NH, SD, TN, TX, WA, WY
"""

        messagebox.showinfo("State Tax Information", info_text)

    def _toggle_multi_state_mode(self):
        """Toggle multi-state mode"""
        self.multi_state_mode = not self.multi_state_mode
        selectmode = tk.MULTIPLE if self.multi_state_mode else tk.SINGLE
        self.state_listbox.config(selectmode=selectmode)

        if self.multi_state_mode:
            self.status_var.set("Multi-state mode enabled - select multiple states")
        else:
            self.status_var.set("Single state mode - select one state")

    def _clear_inputs(self):
        """Clear all input fields"""
        # Clear income fields
        for var in self.income_vars.values():
            var.set("0")

        # Clear deduction fields
        for var in self.deduc_vars.values():
            var.set("0")

        # Clear results
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)

        self.status_var.set("Inputs cleared")


class StateReturnDialog:
    """Dialog for creating a new state tax return"""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager,
                 service: StateTaxIntegrationService, state_code: StateCode):
        self.parent = parent
        self.theme_manager = theme_manager
        self.service = service
        self.state_code = state_code
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"New {state_code.value} Tax Return")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self.theme_manager.apply_theme_to_window(self.dialog)

        # Center the dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self.dialog.wait_window()

    def _create_widgets(self):
        """Create dialog widgets"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Taxpayer information
        ttk.Label(frame, text="Taxpayer Information", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="First Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.first_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.first_name_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(frame, text="Last Name:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.last_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.last_name_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(frame, text="SSN:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.ssn_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ssn_var).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)

        # Use current input values for income/deductions
        ttk.Label(frame, text="Use Current Input Values?", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, pady=10)
        self.use_current_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Use income and deduction values from main window", variable=self.use_current_var).grid(row=5, column=0, columnspan=2, pady=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Create Return", command=self._on_create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

        # Configure grid
        frame.columnconfigure(1, weight=1)

    def _on_create(self):
        """Handle create button"""
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        ssn = self.ssn_var.get().strip()

        if not all([first_name, last_name, ssn]):
            messagebox.showerror("Error", "Please fill in all taxpayer information")
            return

        taxpayer_info = {
            "first_name": first_name,
            "last_name": last_name,
            "ssn": ssn,
            "taxpayer_id": f"{ssn}_{self.state_code.value}"
        }

        # For now, create empty income/deductions (would use current values in real implementation)
        income = StateIncome()
        deductions = StateDeductions()

        self.result = (taxpayer_info, income, deductions)
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.dialog.destroy()


class TaxCalculatorDialog:
    """Dialog for advanced tax calculations"""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager, service: StateTaxIntegrationService):
        self.parent = parent
        self.theme_manager = theme_manager
        self.service = service

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Tax Calculator")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self.theme_manager.apply_theme_to_window(self.dialog)

    def _create_widgets(self):
        """Create calculator widgets"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Advanced Tax Calculator", font=("Arial", 14, "bold")).pack(pady=10)

        # Calculator content would go here
        ttk.Label(frame, text="Tax calculator functionality - coming soon").pack(pady=20)

        ttk.Button(frame, text="Close", command=self.dialog.destroy).pack(pady=10)

    def show(self):
        """Show the calculator dialog"""
        self.dialog.wait_window()