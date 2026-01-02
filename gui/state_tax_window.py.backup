"""
State Tax Window - GUI for state tax return preparation

This module provides a comprehensive interface for:
- State tax calculations
- Multi-state tax returns
- State-specific forms
- State tax planning
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from typing import Dict, Any, Optional, List
from services.state_tax_service import StateTaxService, StateCode, StateTaxCalculation
from services.state_form_pdf_generator import StateFormPDFGenerator, StateFormData
from utils.event_bus import EventBus

logger = logging.getLogger(__name__)


class StateTaxWindow:
    """
    Window for managing state tax returns and calculations.

    Provides interface for:
    - Selecting states of residence
    - Calculating state taxes
    - Viewing state-specific forms
    - Multi-state tax planning
    """

    def __init__(self, parent: tk.Tk, tax_data: Any, event_bus: EventBus):
        self.parent = parent
        self.tax_data = tax_data
        self.event_bus = event_bus
        self.state_service = StateTaxService()
        self.pdf_generator = StateFormPDFGenerator()

        # Window setup
        self.window = tk.Toplevel(parent)
        self.window.title("State Tax Returns")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)

        # Initialize data
        self.selected_states: List[StateCode] = []
        self.state_calculations: Dict[StateCode, StateTaxCalculation] = {}

        self._setup_ui()
        self._load_current_data()

    def _setup_ui(self):
        """Setup the main UI components"""
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="State Tax Return Preparation",
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # State Selection Tab
        self._create_state_selection_tab()

        # Tax Calculation Tab
        self._create_tax_calculation_tab()

        # Forms Tab
        self._create_forms_tab()

        # Summary Tab
        self._create_summary_tab()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Calculate Taxes",
                  command=self._calculate_taxes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Generate Forms",
                  command=self._generate_forms).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Save State Data",
                  command=self._save_state_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close",
                  command=self.window.destroy).pack(side=tk.RIGHT)

    def _create_state_selection_tab(self):
        """Create the state selection tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="State Selection")

        # Instructions
        instructions = ttk.Label(tab,
            text="Select the states where you have income tax obligations.\n"
                 "This includes states where you lived or earned income during the tax year.",
            wraplength=600, justify=tk.LEFT)
        instructions.pack(pady=(10, 20))

        # State selection frame
        selection_frame = ttk.LabelFrame(tab, text="State Selection", padding="10")
        selection_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Search and filter
        filter_frame = ttk.Frame(selection_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT)
        self.state_search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.state_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self._filter_states)

        # States listbox with scrollbar
        listbox_frame = ttk.Frame(selection_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.states_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE,
                                       yscrollcommand=scrollbar.set, height=15)
        self.states_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.states_listbox.yview)

        # Populate states
        self._populate_states_list()

        # Selected states display
        selected_frame = ttk.LabelFrame(selection_frame, text="Selected States", padding="10")
        selected_frame.pack(fill=tk.X, pady=(10, 0))

        self.selected_states_text = tk.Text(selected_frame, height=3, wrap=tk.WORD)
        scrollbar_selected = ttk.Scrollbar(selected_frame)
        scrollbar_selected.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_states_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.selected_states_text.config(yscrollcommand=scrollbar_selected.set)
        scrollbar_selected.config(command=self.selected_states_text.yview)

        # Update selection button
        ttk.Button(selection_frame, text="Update Selection",
                  command=self._update_state_selection).pack(pady=(10, 0))

    def _create_tax_calculation_tab(self):
        """Create the tax calculation tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Tax Calculations")

        # Results display
        results_frame = ttk.LabelFrame(tab, text="State Tax Calculations", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview for results
        columns = ("State", "Taxable Income", "Tax Owed", "Effective Rate", "Credits")
        self.calc_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.calc_tree.heading(col, text=col)
            self.calc_tree.column(col, width=120, anchor=tk.E)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.calc_tree.yview)
        self.calc_tree.configure(yscrollcommand=scrollbar.set)

        self.calc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Summary frame
        summary_frame = ttk.LabelFrame(tab, text="Summary", padding="10")
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.summary_text = tk.Text(summary_frame, height=6, wrap=tk.WORD)
        summary_scrollbar = ttk.Scrollbar(summary_frame)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.summary_text.config(yscrollcommand=summary_scrollbar.set)
        summary_scrollbar.config(command=self.summary_text.yview)

    def _create_forms_tab(self):
        """Create the forms tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="State Forms")

        # Forms list
        forms_frame = ttk.LabelFrame(tab, text="Required State Forms", padding="10")
        forms_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.forms_tree = ttk.Treeview(forms_frame, columns=("State", "Form", "Description"),
                                     show="headings", height=15)

        for col in ("State", "Form", "Description"):
            self.forms_tree.heading(col, text=col)
            if col == "Description":
                self.forms_tree.column(col, width=300)
            else:
                self.forms_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(forms_frame, orient=tk.VERTICAL, command=self.forms_tree.yview)
        self.forms_tree.configure(yscrollcommand=scrollbar.set)

        self.forms_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Form actions
        actions_frame = ttk.Frame(tab)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(actions_frame, text="View Form Details",
                  command=self._view_form_details).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(actions_frame, text="Generate PDF",
                  command=self._generate_state_pdf).pack(side=tk.LEFT, padx=(0, 10))

    def _create_summary_tab(self):
        """Create the summary tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Summary & Filing")

        # Overall summary
        summary_frame = ttk.LabelFrame(tab, text="Tax Year Summary", padding="10")
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.overall_summary = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=20)
        self.overall_summary.pack(fill=tk.BOTH, expand=True)

        # Filing instructions
        instructions_frame = ttk.LabelFrame(tab, text="Filing Instructions", padding="10")
        instructions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        instructions_text = """
Filing Instructions for State Tax Returns:

1. Review all calculated taxes and forms for accuracy
2. File returns in states where you have tax obligations
3. Pay any taxes owed by the state deadlines
4. Keep copies of all filed returns and payment confirmations
5. Some states allow e-filing, others require paper filing

Important: State tax deadlines may differ from federal deadlines.
Check each state's specific requirements.
        """

        instructions_label = ttk.Label(instructions_frame, text=instructions_text,
                                    wraplength=600, justify=tk.LEFT)
        instructions_label.pack()

    def _populate_states_list(self):
        """Populate the states listbox with all supported states"""
        self.states_listbox.delete(0, tk.END)
        for state_code in self.state_service.get_supported_states():
            state_info = self.state_service.get_state_info(state_code)
            if state_info:
                display_text = f"{state_code.value} - {state_info.name}"
                if not state_info.has_income_tax:
                    display_text += " (No Income Tax)"
                self.states_listbox.insert(tk.END, display_text)

    def _filter_states(self, event=None):
        """Filter the states list based on search text"""
        search_text = self.state_search_var.get().lower()
        self.states_listbox.delete(0, tk.END)

        for state_code in self.state_service.get_supported_states():
            state_info = self.state_service.get_state_info(state_code)
            if state_info:
                display_text = f"{state_code.value} - {state_info.name}"
                if not state_info.has_income_tax:
                    display_text += " (No Income Tax)"

                if search_text in display_text.lower():
                    self.states_listbox.insert(tk.END, display_text)

    def _update_state_selection(self):
        """Update the selected states based on listbox selection"""
        selected_indices = self.states_listbox.curselection()
        self.selected_states = []

        for index in selected_indices:
            state_text = self.states_listbox.get(index)
            state_code_str = state_text.split(' - ')[0]
            try:
                state_code = StateCode(state_code_str)
                self.selected_states.append(state_code)
            except ValueError:
                continue

        # Update display
        self.selected_states_text.delete(1.0, tk.END)
        if self.selected_states:
            state_names = []
            for state_code in self.selected_states:
                state_info = self.state_service.get_state_info(state_code)
                if state_info:
                    state_names.append(f"{state_info.name} ({state_code.value})")

            self.selected_states_text.insert(tk.END, ", ".join(state_names))
        else:
            self.selected_states_text.insert(tk.END, "No states selected")

    def _calculate_taxes(self):
        """Calculate taxes for selected states"""
        if not self.selected_states:
            messagebox.showwarning("No States Selected",
                                 "Please select at least one state before calculating taxes.")
            return

        try:
            # Get federal tax data
            federal_income = self.tax_data.calculate_total_income()
            federal_deductions = self.tax_data.calculate_total_deductions()
            federal_taxable = self.tax_data.calculate_taxable_income()

            filing_status = self.tax_data.data.get('filing_status', 'single')
            dependents = len(self.tax_data.data.get('dependents', []))

            # Calculate state taxes
            self.state_calculations = self.state_service.calculate_multi_state_tax(
                self.selected_states, federal_taxable, filing_status, dependents
            )

            # Update display
            self._update_calculation_display()
            self._update_summary_display()

            messagebox.showinfo("Calculation Complete",
                              f"Calculated taxes for {len(self.state_calculations)} state(s).")

        except Exception as e:
            logger.error(f"Error calculating state taxes: {e}")
            messagebox.showerror("Calculation Error",
                               f"Failed to calculate state taxes:\n\n{str(e)}")

    def _update_calculation_display(self):
        """Update the tax calculation display"""
        # Clear existing items
        for item in self.calc_tree.get_children():
            self.calc_tree.delete(item)

        # Add new calculations
        for state_code, calculation in self.state_calculations.items():
            state_info = self.state_service.get_state_info(state_code)
            state_name = state_info.name if state_info else state_code.value

            self.calc_tree.insert("", tk.END, values=(
                state_name,
                f"${calculation.taxable_income:,.0f}",
                f"${calculation.tax_owed:,.2f}",
                f"{calculation.effective_rate:.2%}",
                f"${calculation.credits:,.2f}"
            ))

    def _update_summary_display(self):
        """Update the summary display"""
        if not self.state_calculations:
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, "No calculations available")
            return

        total_tax = sum(calc.tax_owed for calc in self.state_calculations.values())
        total_credits = sum(calc.credits for calc in self.state_calculations.values())

        summary = f"""
State Tax Summary:

Total State Tax Owed: ${total_tax:,.2f}
Total State Credits: ${total_credits:,.2f}
Net State Tax: ${total_tax - total_credits:,.2f}

States with Tax Obligations: {len([c for c in self.state_calculations.values() if c.tax_owed > 0])}
States with No Income Tax: {len([c for c in self.state_calculations.values() if c.tax_owed == 0])}

Note: This summary is for estimation purposes. Consult with a tax professional
for final tax calculations and filing requirements.
        """

        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary.strip())

    def _generate_forms(self):
        """Generate state tax forms"""
        if not self.state_calculations:
            messagebox.showwarning("No Calculations",
                                 "Please calculate taxes first before generating forms.")
            return

        # Clear existing forms
        for item in self.forms_tree.get_children():
            self.forms_tree.delete(item)

        # Add forms for each state
        for state_code, calculation in self.state_calculations.items():
            if calculation.tax_owed > 0:  # Only show forms for states with tax
                forms = self.state_service.get_state_tax_forms(state_code)
                for form in forms:
                    state_info = self.state_service.get_state_info(state_code)
                    state_name = state_info.name if state_info else state_code.value

                    self.forms_tree.insert("", tk.END, values=(
                        state_name,
                        form,
                        f"State income tax return form for {state_name}"
                    ))

        messagebox.showinfo("Forms Generated",
                          "State tax forms have been prepared. Use the Forms tab to view details.")

    def _view_form_details(self):
        """View details of selected form"""
        selection = self.forms_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a form to view details.")
            return

        item = self.forms_tree.item(selection[0])
        values = item['values']

        details = f"""
Form Details:

State: {values[0]}
Form: {values[1]}
Description: {values[2]}

Note: This is a placeholder for form details.
Full form generation will be implemented in a future version.
        """

        messagebox.showinfo("Form Details", details)

    def _generate_state_pdf(self):
        """Generate PDF for selected state form"""
        selection = self.forms_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a form to generate PDF.")
            return

        item = self.forms_tree.item(selection[0])
        values = item['values']
        state_name = values[0]
        form_name = values[1]

        # Find the state code from the state name
        state_code = None
        for code in self.state_service.get_supported_states():
            state_info = self.state_service.get_state_info(code)
            if state_info and state_info.name == state_name:
                state_code = code
                break

        if not state_code or state_code not in self.state_calculations:
            messagebox.showerror("Error", f"No calculation data found for {state_name}.")
            return

        # Check if state is supported for PDF generation
        if state_code not in self.pdf_generator.get_supported_states():
            messagebox.showinfo("Not Supported",
                              f"PDF generation for {state_name} is not yet implemented.\n\n"
                              f"Currently supported states: {', '.join([s.name for s in self.pdf_generator.get_supported_states()])}")
            return

        try:
            # Prepare form data
            taxpayer_info = self._extract_taxpayer_info()
            income_data = self._extract_income_data()
            tax_calculation = self.state_calculations[state_code]

            form_data = StateFormData(
                state_code=state_code,
                tax_year=self.tax_data.data.get('tax_year', 2024),
                taxpayer_info=taxpayer_info,
                income_data=income_data,
                tax_calculation=tax_calculation,
                filing_status=self.tax_data.data.get('filing_status', 'single'),
                dependents=len(self.tax_data.data.get('dependents', []))
            )

            # Generate PDF
            pdf_path = self.pdf_generator.generate_state_form_pdf(form_data)

            messagebox.showinfo("PDF Generated",
                              f"State tax form PDF has been generated successfully!\n\n"
                              f"File saved to: {pdf_path}")

            # Optionally open the PDF
            import subprocess
            import platform
            try:
                if platform.system() == "Windows":
                    subprocess.run(["start", pdf_path], shell=True)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", pdf_path])
                else:  # Linux
                    subprocess.run(["xdg-open", pdf_path])
            except Exception as e:
                logger.warning(f"Could not open PDF automatically: {e}")

        except Exception as e:
            logger.error(f"Error generating state PDF: {e}")
            messagebox.showerror("PDF Generation Error",
                               f"Failed to generate PDF for {state_name}:\n\n{str(e)}")

    def _save_state_data(self):
        """Save state tax data to the main tax return"""
        if not self.state_calculations:
            messagebox.showwarning("No Data", "No state tax data to save.")
            return

        try:
            # Save state calculations to tax data
            if 'state_taxes' not in self.tax_data.data:
                self.tax_data.data['state_taxes'] = {}

            self.tax_data.data['state_taxes']['calculations'] = {
                state.value: {
                    'taxable_income': calc.taxable_income,
                    'tax_owed': calc.tax_owed,
                    'effective_rate': calc.effective_rate,
                    'credits': calc.credits,
                    'deductions': calc.deductions
                }
                for state, calc in self.state_calculations.items()
            }

            self.tax_data.data['state_taxes']['selected_states'] = [
                state.value for state in self.selected_states
            ]

            # Emit event to notify other components
            self.event_bus.emit('state_tax_data_updated', self.state_calculations)

            messagebox.showinfo("Data Saved", "State tax data has been saved to your tax return.")

        except Exception as e:
            logger.error(f"Error saving state tax data: {e}")
            messagebox.showerror("Save Error", f"Failed to save state tax data:\n\n{str(e)}")

    def _extract_taxpayer_info(self) -> Dict[str, Any]:
        """Extract taxpayer information from tax data"""
        data = self.tax_data.data
        return {
            'first_name': data.get('first_name', ''),
            'middle_initial': data.get('middle_initial', ''),
            'last_name': data.get('last_name', ''),
            'ssn': data.get('ssn', ''),
            'address': data.get('address', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'zip_code': data.get('zip_code', ''),
        }

    def _extract_income_data(self) -> Dict[str, Any]:
        """Extract income data from tax data"""
        data = self.tax_data.data
        return {
            'federal_agi': self.tax_data.calculate_taxable_income(),
            'federal_gross_income': self.tax_data.calculate_total_income(),
            'wages': data.get('income', {}).get('wages', 0),
            'interest': data.get('income', {}).get('interest', 0),
            'dividends': data.get('income', {}).get('dividends', 0),
            'business_income': data.get('income', {}).get('business_income', 0),
        }

    def _load_current_data(self):
        """Load existing state tax data if available"""
        state_data = self.tax_data.data.get('state_taxes', {})
        selected_states = state_data.get('selected_states', [])

        # Restore selected states
        for state_code_str in selected_states:
            try:
                state_code = StateCode(state_code_str)
                self.selected_states.append(state_code)
            except ValueError:
                continue

        # Update display
        if self.selected_states:
            state_names = []
            for state_code in self.selected_states:
                state_info = self.state_service.get_state_info(state_code)
                if state_info:
                    state_names.append(f"{state_info.name} ({state_code.value})")

            self.selected_states_text.delete(1.0, tk.END)
            self.selected_states_text.insert(tk.END, ", ".join(state_names))


def open_state_tax_window(parent: tk.Tk, tax_data: Any) -> None:
    """
    Open the state tax window.

    Args:
        parent: Parent tkinter window
        tax_data: Tax data object
    """
    try:
        from utils.event_bus import get_event_bus
        event_bus = get_event_bus()
        StateTaxWindow(parent, tax_data, event_bus)
    except Exception as e:
        logger.error(f"Failed to open state tax window: {e}")
        messagebox.showerror("State Tax Error",
                           f"Failed to open state tax tools:\n\n{str(e)}")