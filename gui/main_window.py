"""
Main application window with navigation
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Dict
from config.app_config import AppConfig
from gui.pages.personal_info import PersonalInfoPage
from gui.pages.filing_status import FilingStatusPage
from gui.pages.income import IncomePage
from gui.pages.deductions import DeductionsPage
from gui.pages.credits import CreditsPage
from gui.pages.payments import PaymentsPage
from gui.pages.dependents import DependentsPage
from gui.pages.form_viewer import FormViewerPage
from gui.widgets.validation_summary import ValidationSummary
from gui.theme_manager import ThemeManager
from models.tax_data import TaxData

class MainWindow:
    """Main application window"""
    
    def __init__(self, root, config: AppConfig = None):
        self.root = root
        self.config = config or AppConfig.from_env()
        
        self.root.title(self.config.window_title)
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(self.root)
        self.theme_manager.set_theme(self.config.theme)
        
        # Initialize tax data model with config
        self.tax_data = TaxData(self.config)
        
        # Configure grid
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create main containers
        self.create_sidebar()
        self.create_main_content()
        
        # Initialize pages
        self.pages = {}
        self.current_page = None
        
        # Show initial page
        self.show_page("personal_info")
        
        # Update progress
        self.update_progress()
        
        # Update validation summary
        self.update_validation_summary()
        
        # Bind keyboard shortcuts
        self._bind_keyboard_shortcuts()
    
    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for common actions"""
        # Navigation shortcuts (Alt + number)
        self.root.bind('<Alt-Key-1>', lambda e: self.show_page("personal_info"))
        self.root.bind('<Alt-Key-2>', lambda e: self.show_page("filing_status"))
        self.root.bind('<Alt-Key-3>', lambda e: self.show_page("dependents"))
        self.root.bind('<Alt-Key-4>', lambda e: self.show_page("income"))
        self.root.bind('<Alt-Key-5>', lambda e: self.show_page("deductions"))
        self.root.bind('<Alt-Key-6>', lambda e: self.show_page("credits"))
        self.root.bind('<Alt-Key-7>', lambda e: self.show_page("payments"))
        self.root.bind('<Alt-Key-8>', lambda e: self.show_page("form_viewer"))
        
        # Common actions
        self.root.bind('<Control-s>', lambda e: self.save_progress())
        self.root.bind('<Control-o>', lambda e: self.load_progress())
        self.root.bind('<Control-n>', lambda e: self._new_return())
        
        # Focus shortcuts
        self.root.bind('<Control-f>', lambda e: self._focus_search())
    
    def _new_return(self):
        """Start a new tax return"""
        if messagebox.askyesno("New Return", "Start a new tax return? Any unsaved changes will be lost."):
            self.tax_data = TaxData(self.config)
            self.show_page("personal_info")
            self.update_progress()
    
    def _focus_search(self):
        """Focus on search field (placeholder for future search functionality)"""
        pass  # Could implement search functionality later
    
    def update_progress(self):
        """Update the completion progress indicator"""
        # Define page weights (approximate completion percentage per page)
        page_weights = {
            "personal_info": 10,
            "filing_status": 20,
            "dependents": 30,
            "income": 50,
            "deductions": 70,
            "credits": 85,
            "payments": 95,
            "form_viewer": 100,
        }
        
        # Get current page weight
        current_page_id = self.get_current_page_id()
        base_progress = page_weights.get(current_page_id, 0)
        
        # Add bonus for completed sections
        bonus_progress = 0
        
        # Check if personal info is complete
        if self._is_personal_info_complete():
            bonus_progress += 5
        
        # Check if income has data
        if self._has_income_data():
            bonus_progress += 10
            
        # Check if deductions/credits have data
        if self._has_deductions_data():
            bonus_progress += 5
            
        if self._has_credits_data():
            bonus_progress += 5
        
        total_progress = min(base_progress + bonus_progress, 100)
        self.progress_var.set(total_progress)
        self.progress_text.config(text=f"{int(total_progress)}% Complete")
    
    def update_validation_summary(self):
        """Update the validation summary with errors from all pages"""
        errors = {}
        
        # Check each page for validation errors
        pages_to_check = [
            ("personal_info", "Personal Information"),
            ("filing_status", "Filing Status"), 
            ("dependents", "Dependents"),
            ("income", "Income"),
            ("deductions", "Deductions"),
            ("credits", "Credits & Taxes"),
            ("payments", "Payments")
        ]
        
        for page_id, page_name in pages_to_check:
            page_errors = self._validate_page(page_id)
            if page_errors:
                errors[page_id] = page_errors
        
        # Update the validation summary widget
        self.validation_summary.update_errors(errors)
    
    def _validate_page(self, page_id: str) -> List[str]:
        """Validate a specific page and return list of errors"""
        errors = []
        
        # Get the data section for this page
        section_mapping = {
            "personal_info": "personal_info",
            "filing_status": "filing_status",
            "dependents": "dependents",
            "income": "income",
            "deductions": "deductions", 
            "credits": "credits",
            "payments": "payments"
        }
        
        section = section_mapping.get(page_id)
        if not section:
            return errors
            
        data = self.tax_data.get_section(section)
        
        # Validate based on page type
        if page_id == "personal_info":
            errors.extend(self._validate_personal_info(data))
        elif page_id == "filing_status":
            errors.extend(self._validate_filing_status(data))
        elif page_id == "dependents":
            errors.extend(self._validate_dependents(data))
        elif page_id == "income":
            errors.extend(self._validate_income(data))
        # Add more page validations as needed
        
        return errors
    
    def _validate_personal_info(self, data: Dict) -> List[str]:
        """Validate personal information"""
        errors = []
        
        required_fields = [
            ("first_name", "First name"),
            ("last_name", "Last name"),
            ("ssn", "Social Security Number"),
            ("date_of_birth", "Date of birth"),
            ("address", "Street address"),
            ("city", "City"),
            ("state", "State"),
            ("zip_code", "ZIP code")
        ]
        
        for field, label in required_fields:
            if not data.get(field):
                errors.append(f"{label} is required")
        
        # Validate SSN format
        ssn = data.get("ssn", "")
        if ssn and not self._is_valid_ssn(ssn):
            errors.append("Social Security Number must be in XXX-XX-XXXX format")
        
        # Validate ZIP code
        zip_code = data.get("zip_code", "")
        if zip_code and not self._is_valid_zip(zip_code):
            errors.append("ZIP code must be 5 or 9 digits")
        
        return errors
    
    def _validate_filing_status(self, data: Dict) -> List[str]:
        """Validate filing status"""
        errors = []
        
        if not data.get("status"):
            errors.append("Filing status must be selected")
        
        return errors
    
    def _validate_income(self, data: Dict) -> List[str]:
        """Validate income data"""
        errors = []
        
        # Check if at least one income source is provided
        has_income = (
            data.get("w2_forms") or
            data.get("interest_income") or
            data.get("dividend_income") or
            data.get("business_income") or
            data.get("self_employment") or
            data.get("retirement_distributions") or
            data.get("social_security") or
            data.get("capital_gains") or
            data.get("rental_income") or
            data.get("unemployment") or
            data.get("other_income")
        )
        
        if not has_income:
            errors.append("At least one source of income must be reported")
        
        return errors
    
    def _validate_dependents(self, data: List) -> List[str]:
        """Validate dependents data"""
        errors = []
        
        dependents = data if isinstance(data, list) else data.get("dependents", [])
        if not isinstance(dependents, list):
            errors.append("Dependents data must be a list")
            return errors
        
        for i, dependent in enumerate(dependents):
            if not isinstance(dependent, dict):
                errors.append(f"Dependent {i+1}: Invalid data format")
                continue
                
            # Check required fields
            required_fields = [
                ("first_name", "First name"),
                ("last_name", "Last name"),
                ("ssn", "Social Security Number"),
                ("birth_date", "Birth date"),
                ("relationship", "Relationship"),
            ]
            
            for field, label in required_fields:
                if not dependent.get(field):
                    errors.append(f"Dependent {i+1}: {label} is required")
            
            # Validate SSN format
            ssn = dependent.get("ssn", "")
            if ssn and not self._is_valid_ssn(ssn):
                errors.append(f"Dependent {i+1}: Social Security Number must be in XXX-XX-XXXX format")
            
            # Validate months lived in home
            months = dependent.get("months_lived_in_home")
            if months is not None:
                try:
                    months_int = int(months)
                    if months_int < 0 or months_int > 12:
                        errors.append(f"Dependent {i+1}: Months lived in home must be between 0 and 12")
                except (ValueError, TypeError):
                    errors.append(f"Dependent {i+1}: Months lived in home must be a valid number")
        
        return errors
    
    def _is_valid_ssn(self, ssn: str) -> bool:
        """Check if SSN is in valid format"""
        import re
        return bool(re.match(r'^\d{3}-\d{2}-\d{4}$', ssn))
    
    def _is_valid_zip(self, zip_code: str) -> bool:
        """Check if ZIP code is valid"""
        import re
        return bool(re.match(r'^\d{5}(-\d{4})?$', zip_code))
    
    def _is_personal_info_complete(self):
        """Check if personal information is reasonably complete"""
        personal_info = self.tax_data.get_section("personal_info")
        required_fields = ["first_name", "last_name", "ssn", "date_of_birth", "address", "city", "state", "zip_code"]
        return all(personal_info.get(field) for field in required_fields)
    
    def _has_income_data(self):
        """Check if income data has been entered"""
        income = self.tax_data.get_section("income")
        return any([
            income.get("w2_forms"),
            income.get("interest_income"),
            income.get("dividend_income"),
            income.get("self_employment"),
            income.get("retirement_distributions"),
            income.get("social_security"),
            income.get("capital_gains"),
            income.get("rental_income"),
        ])
    
    def _has_deductions_data(self):
        """Check if deductions data has been entered"""
        deductions = self.tax_data.get_section("deductions")
        return any(value for value in deductions.values() if isinstance(value, (int, float)) and value > 0)
    
    def _has_credits_data(self):
        """Check if credits data has been entered"""
        credits = self.tax_data.get_section("credits")
        return any(value for value in credits.values() if isinstance(value, (int, float)) and value > 0)
    
    def create_sidebar(self):
        """Create navigation sidebar"""
        sidebar = ttk.Frame(self.root, padding="10", relief="raised")
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Title
        title_label = ttk.Label(
            sidebar,
            text="Freedom US\nTax Return",
            font=("Arial", 16, "bold"),
            justify="center"
        )
        title_label.pack(pady=(0, 10))
        
        # Tax Year Info
        tax_year_label = ttk.Label(
            sidebar,
            text="Tax Year 2025",
            font=("Arial", 10, "bold"),
            justify="center",
            foreground="blue"
        )
        tax_year_label.pack(pady=(0, 20))
        
        # Progress indicator
        progress_frame = ttk.Frame(sidebar)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        progress_label = ttk.Label(
            progress_frame,
            text="Completion Progress",
            font=("Arial", 9, "bold")
        )
        progress_label.pack(anchor="w")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill="x", pady=(2, 0))
        
        self.progress_text = ttk.Label(
            progress_frame,
            text="0% Complete",
            font=("Arial", 8)
        )
        self.progress_text.pack(anchor="w")
        
        # Validation summary
        self.validation_summary = ValidationSummary(sidebar, self)
        self.validation_summary.pack(fill="x", pady=(10, 0))
        
        # Navigation buttons
        nav_sections = [
            ("Personal Information", "personal_info"),
            ("Filing Status", "filing_status"),
            ("Dependents", "dependents"),
            ("Income", "income"),
            ("Deductions", "deductions"),
            ("Credits & Taxes", "credits"),
            ("Payments", "payments"),
            ("View Forms", "form_viewer"),
        ]
        
        self.nav_buttons = {}
        for label, page_id in nav_sections:
            btn = ttk.Button(
                sidebar,
                text=label,
                command=lambda p=page_id: self.show_page(p),
                width=20
            )
            btn.pack(pady=5, fill="x")
            self.nav_buttons[page_id] = btn
        
        # Separator
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=20)
        
        # Action buttons
        save_btn = ttk.Button(
            sidebar,
            text="Save Progress",
            command=self.save_progress
        )
        save_btn.pack(pady=5, fill="x")
        
        load_btn = ttk.Button(
            sidebar,
            text="Load Progress",
            command=self.load_progress
        )
        load_btn.pack(pady=5, fill="x")
        
        # Theme toggle button
        theme_text = "☀️ Light Mode" if self.config.theme == "dark" else "🌙 Dark Mode"
        theme_btn = ttk.Button(
            sidebar,
            text=theme_text,
            command=self.toggle_theme
        )
        theme_btn.pack(pady=5, fill="x")
        
        # Status label
        self.status_label = ttk.Label(
            sidebar,
            text="Ready",
            font=("Arial", 9),
            foreground="gray"
        )
        self.status_label.pack(side="bottom", pady=10)
    
    def create_main_content(self):
        """Create main content area"""
        self.content_frame = ttk.Frame(self.root, padding="20")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
    
    def show_page(self, page_id):
        """Switch to specified page"""
        # Destroy current page if exists
        if self.current_page:
            self.current_page.destroy()
        
        # Create new page
        page_classes = {
            "personal_info": PersonalInfoPage,
            "filing_status": FilingStatusPage,
            "dependents": DependentsPage,
            "income": IncomePage,
            "deductions": DeductionsPage,
            "credits": CreditsPage,
            "payments": PaymentsPage,
            "form_viewer": FormViewerPage,
        }
        
        page_class = page_classes.get(page_id)
        if page_class:
            self.current_page = page_class(self.content_frame, self.tax_data, self, self.theme_manager)
            self.current_page.pack(fill="both", expand=True)
            
            # Update navigation button states
            for btn_id, btn in self.nav_buttons.items():
                if btn_id == page_id:
                    btn.state(["pressed"])
                else:
                    btn.state(["!pressed"])
            
            # Update progress
            self.update_progress()
    
    def save_progress(self):
        """Save current progress to encrypted file"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            filename = self.tax_data.save_to_file()
            messagebox.showinfo(
                "Success", 
                f"Progress saved successfully to:\n{filename}\n\n"
                "Your data is encrypted and protected."
            )
            self.status_label.config(text=f"Saved: {Path(filename).name}")
        except ValueError as e:
            # Validation or path errors
            logger.warning(f"Save failed - validation error: {e}")
            messagebox.showerror(
                "Invalid Data", 
                "Cannot save due to invalid data. Please check your entries and try again."
            )
        except PermissionError as e:
            logger.error(f"Save failed - permission denied: {e}")
            messagebox.showerror(
                "Permission Denied",
                "Cannot save file. Please check folder permissions and try again."
            )
        except Exception as e:
            logger.error(f"Save failed: {e}", exc_info=True)
            messagebox.showerror(
                "Save Failed", 
                "Failed to save tax return. Please ensure you have write permissions and try again."
            )
    
    def load_progress(self):
        """Load progress from encrypted file"""
        from tkinter import filedialog
        from pathlib import Path
        import logging
        logger = logging.getLogger(__name__)
        
        filename = filedialog.askopenfilename(
            title="Select saved tax return",
            filetypes=[
                ("Encrypted Tax Returns", "*.enc"),
                ("Legacy JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        if filename:
            try:
                self.tax_data.load_from_file(filename)
                messagebox.showinfo(
                    "Success", 
                    f"Tax return loaded successfully from:\n{Path(filename).name}"
                )
                self.status_label.config(text=f"Loaded: {Path(filename).name}")
                # Refresh current page
                if self.current_page:
                    page_id = self.get_current_page_id()
                    self.show_page(page_id)
                logger.info(f"Tax return loaded: {filename}")
            except ValueError as e:
                logger.error(f"Load failed - integrity error: {e}")
                messagebox.showerror(
                    "Data Integrity Error",
                    "File integrity verification failed. The file may be corrupted or tampered with."
                )
            except FileNotFoundError:
                logger.error(f"Load failed - file not found: {filename}")
                messagebox.showerror(
                    "File Not Found",
                    "The selected file could not be found."
                )
            except Exception as e:
                logger.error(f"Load failed: {e}", exc_info=True)
                messagebox.showerror(
                    "Load Failed", 
                    "Failed to load tax return. The file may be corrupted or encrypted with a different key."
                )
    
    def get_current_page_id(self):
        """Get the ID of the current page"""
        page_mapping = {
            PersonalInfoPage: "personal_info",
            FilingStatusPage: "filing_status",
            DependentsPage: "dependents",
            IncomePage: "income",
            DeductionsPage: "deductions",
            CreditsPage: "credits",
            PaymentsPage: "payments",
            FormViewerPage: "form_viewer",
        }
        return page_mapping.get(type(self.current_page), "personal_info")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = self.theme_manager.toggle_theme()
        self.config.theme = new_theme
        
        # Update theme toggle button text
        theme_btn = None
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):  # sidebar
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and "🌙" in str(child.cget("text")) or "☀️" in str(child.cget("text")):
                        theme_btn = child
                        break
                if theme_btn:
                    break
        
        if theme_btn:
            if new_theme == "dark":
                theme_btn.config(text="☀️ Light Mode")
            else:
                theme_btn.config(text="🌙 Dark Mode")
