"""
Main application window with navigation
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from config.app_config import AppConfig
from gui.pages.personal_info import PersonalInfoPage
from gui.pages.filing_status import FilingStatusPage
from gui.pages.income import IncomePage
from gui.pages.deductions import DeductionsPage
from gui.pages.credits import CreditsPage
from gui.pages.payments import PaymentsPage
from gui.pages.form_viewer import FormViewerPage
from models.tax_data import TaxData

class MainWindow:
    """Main application window"""
    
    def __init__(self, root, config: AppConfig = None):
        self.root = root
        self.config = config or AppConfig.from_env()
        
        self.root.title(self.config.window_title)
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        
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
        
        # Navigation buttons
        nav_sections = [
            ("Personal Information", "personal_info"),
            ("Filing Status", "filing_status"),
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
            "income": IncomePage,
            "deductions": DeductionsPage,
            "credits": CreditsPage,
            "payments": PaymentsPage,
            "form_viewer": FormViewerPage,
        }
        
        page_class = page_classes.get(page_id)
        if page_class:
            self.current_page = page_class(self.content_frame, self.tax_data, self)
            self.current_page.pack(fill="both", expand=True)
            
            # Update navigation button states
            for btn_id, btn in self.nav_buttons.items():
                if btn_id == page_id:
                    btn.state(["pressed"])
                else:
                    btn.state(["!pressed"])
    
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
            IncomePage: "income",
            DeductionsPage: "deductions",
            CreditsPage: "credits",
            PaymentsPage: "payments",
            FormViewerPage: "form_viewer",
        }
        return page_mapping.get(type(self.current_page), "personal_info")
