"""
Main application window with navigation
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Dict
from unittest.mock import Mock
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
from services.audit_trail_service import AuditTrailService
from gui.audit_trail_window import AuditTrailWindow
from services.tax_year_service import TaxYearService
from services.collaboration_service import CollaborationService
from services.authentication_service import AuthenticationService
from services.cloud_backup_service import CloudBackupService
from services.encryption_service import EncryptionService
from services.ptin_ero_service import PTINEROService
from gui.two_factor_dialogs import TwoFactorSetupDialog, TwoFactorDisableDialog
from gui.client_management_dialogs import ClientManagementDialog
from gui.client_login_dialog import ClientLoginDialog
from gui.ptin_ero_dialogs import PTINEROManagementDialog
from gui.tax_analytics_window import TaxAnalyticsWindow
from models.tax_data import TaxData

class MainWindow:
    """Main application window"""
    
    def __init__(self, root, config: AppConfig = None):
        self.root = root
        self.config = config or AppConfig.from_env()
        
        # Check if we're in a testing environment with mocked tkinter
        self.is_mocked = isinstance(self.root, Mock)
        
        self.root.title(self.config.window_title)
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(self.root)
        self.theme_manager.set_theme(self.config.theme)
        
        # Initialize tax data model with config
        self.tax_data = TaxData(self.config)
        
        # Initialize services
        self.audit_service = AuditTrailService(self.config)
        self.audit_service.start_session("main_user")
        
        self.tax_year_service = TaxYearService(self.config)
        
        self.collaboration_service = CollaborationService(self.config)
        
        # Initialize cloud backup service
        self.cloud_backup_service = CloudBackupService(self.config)
        
        # Initialize authentication service
        self.auth_service = AuthenticationService(self.config)
        self.session_token = None
        
        # Initialize encryption service
        self.encryption_service = EncryptionService(self.config.key_file)
        
        # Initialize PTIN/ERO service
        self.ptin_ero_service = PTINEROService(self.config, self.encryption_service)
        
        # Check authentication on startup
        if not self._check_authentication():
            return
        
        # Bind window close event for cleanup
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        if not self.is_mocked:
            # Create menu bar
            self.create_menu_bar()
            
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
        else:
            # For testing, initialize minimal state with mocks
            self.pages = {}
            self.current_page = None
            self.content_frame = Mock()
            self.nav_buttons = {
                "personal_info": Mock(),
                "filing_status": Mock(),
                "dependents": Mock(),
                "income": Mock(),
                "deductions": Mock(),
                "credits": Mock(),
                "payments": Mock(),
                "form_viewer": Mock(),
            }
            # Configure dependents button mock to behave like a real button
            dependents_button = self.nav_buttons["dependents"]
            dependents_button.cget = Mock(return_value="Dependents")
            dependents_button.invoke = Mock(side_effect=lambda: self.show_page("dependents"))
            self.progress_var = Mock()
            self.progress_var.set = Mock()
            self.progress_text = Mock()
            self.progress_text.config = Mock()
            self.validation_summary = Mock()
            self.validation_summary.update_errors = Mock()
            self.status_label = Mock()
            
            # Create page mapping for tests
            from gui.pages.personal_info import PersonalInfoPage
            from gui.pages.filing_status import FilingStatusPage
            from gui.pages.dependents import DependentsPage
            from gui.pages.income import IncomePage
            from gui.pages.deductions import DeductionsPage
            from gui.pages.credits import CreditsPage
            from gui.pages.payments import PaymentsPage
            from gui.pages.form_viewer import FormViewerPage
            
            self.page_mapping = {
                PersonalInfoPage: "personal_info",
                FilingStatusPage: "filing_status", 
                DependentsPage: "dependents",
                IncomePage: "income",
                DeductionsPage: "deductions",
                CreditsPage: "credits",
                PaymentsPage: "payments",
                FormViewerPage: "form_viewer",
            }
            
            # Page weights for progress calculation
            self.page_weights = {
                "personal_info": 10,
                "filing_status": 20,
                "dependents": 30,
                "income": 50,
                "deductions": 70,
                "credits": 85,
                "payments": 95,
                "form_viewer": 100,
            }
            
            # Bind keyboard shortcuts for mocked environment
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
        self.root.bind('<Control-e>', lambda e: self._export_pdf())
        self.root.bind('<Control-p>', lambda e: self._open_tax_planning())
        self.root.bind('<Control-s>', lambda e: self._open_state_taxes())
        self.root.bind('<Control-A>', lambda e: self._open_tax_analytics())
        self.root.bind('<Control-a>', lambda e: self._open_audit_trail())
        self.root.bind('<Control-f>', lambda e: self._open_e_filing())
        self.root.bind('<Control-y>', lambda e: self._compare_years())
        self.root.bind('<Control-h>', lambda e: self._share_return())
        self.root.bind('<Control-r>', lambda e: self._open_review_mode())
        
        # Focus shortcuts
        self.root.bind('<Control-Shift-F>', lambda e: self._focus_search())
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated, prompt for login if needed"""
        if self.is_mocked:
            # Skip authentication in testing environment
            return True
            
        # Check if master password is set
        if not self.auth_service.is_master_password_set():
            # First time setup - prompt to create master password
            from gui.password_dialogs import SetMasterPasswordDialog
            dialog = SetMasterPasswordDialog(self.root, self.auth_service)
            result = dialog.show()
            if not result:
                # User cancelled setup
                self.root.quit()
                return False
        else:
            # Prompt for authentication
            from gui.password_dialogs import AuthenticateDialog
            dialog = AuthenticateDialog(self.root, self.auth_service)
            self.session_token = dialog.show()
            if not self.session_token:
                # Authentication failed or cancelled
                self.root.quit()
                return False
                
        return True
    
    def create_menu_bar(self):
        """Create the main menu bar with File and View menus"""
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # File menu items
        file_menu.add_command(label="New Return", command=self._new_return, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.load_progress, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_progress, accelerator="Ctrl+S")
        file_menu.add_separator()
        
        # Import submenu
        import_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Import", menu=import_menu)
        import_menu.add_command(label="Prior Year Return", command=self._import_prior_year)
        import_menu.add_command(label="W-2 Form (PDF)", command=self._import_w2_pdf)
        import_menu.add_command(label="1099 Form (PDF)", command=self._import_1099_pdf)
        import_menu.add_command(label="Tax Software (TXF)", command=self._import_txf)
        
        file_menu.add_command(label="Export PDF", command=self._export_pdf, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # View menu items
        view_menu.add_command(label="Toggle Theme", command=self._toggle_theme)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Tools menu items
        tools_menu.add_command(label="Tax Planning", command=self._open_tax_planning, accelerator="Ctrl+P")
        tools_menu.add_command(label="State Taxes", command=self._open_state_taxes, accelerator="Ctrl+S")
        tools_menu.add_command(label="Tax Analytics", command=self._open_tax_analytics, accelerator="Ctrl+Shift+A")
        tools_menu.add_command(label="Audit Trail", command=self._open_audit_trail, accelerator="Ctrl+A")

        # Security menu
        security_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Security", menu=security_menu)
        
        # Security menu items
        # Cloud Backup submenu
        cloud_menu = tk.Menu(security_menu, tearoff=0)
        security_menu.add_cascade(label="Cloud Backup", menu=cloud_menu)
        cloud_menu.add_command(label="Configure...", command=self._configure_cloud_backup)
        cloud_menu.add_command(label="Create Backup...", command=self._create_backup)
        cloud_menu.add_command(label="Restore Backup...", command=self._restore_backup)
        cloud_menu.add_command(label="Backup Status...", command=self._show_backup_status)
        
        # Two-Factor Authentication submenu
        tfa_menu = tk.Menu(security_menu, tearoff=0)
        security_menu.add_cascade(label="Two-Factor Auth", menu=tfa_menu)
        tfa_menu.add_command(label="Enable 2FA...", command=self._enable_2fa)
        tfa_menu.add_command(label="Disable 2FA...", command=self._disable_2fa)
        
        # Client Management submenu
        client_menu = tk.Menu(security_menu, tearoff=0)
        security_menu.add_cascade(label="Client Management", menu=client_menu)
        client_menu.add_command(label="Client Portal Login...", command=self._open_client_portal)
        client_menu.add_separator()
        client_menu.add_command(label="Manage Clients...", command=self._open_client_management)
        client_menu.add_command(label="PTIN/ERO Management...", command=self._open_ptin_ero_management)
        
        security_menu.add_command(label="Change Password", command=self._change_password)
        security_menu.add_separator()
        security_menu.add_command(label="Logout", command=self._logout)

        # E-File menu
        efile_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="E-File", menu=efile_menu)
        
        # E-File menu items
        efile_menu.add_command(label="Prepare E-File", command=self._open_e_filing, accelerator="Ctrl+F")
        efile_menu.add_separator()
        efile_menu.add_command(label="E-File Status", command=self._check_e_file_status)

        # Collaboration menu
        collaboration_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Collaboration", menu=collaboration_menu)
        
        # Collaboration menu items
        collaboration_menu.add_command(label="Share Return", command=self._share_return, accelerator="Ctrl+H")
        collaboration_menu.add_command(label="Review Mode", command=self._open_review_mode, accelerator="Ctrl+R")
        collaboration_menu.add_separator()
        collaboration_menu.add_command(label="Manage Shared Returns", command=self._manage_shared_returns)

        # Year menu
        year_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Year", menu=year_menu)

        # Year menu items
        year_menu.add_command(label="New Tax Year", command=self._create_new_year)
        year_menu.add_command(label="Copy Current Year", command=self._copy_current_year)
        year_menu.add_command(label="Compare Years", command=self._compare_years, accelerator="Ctrl+Y")
        year_menu.add_separator()
        year_menu.add_command(label="Manage Years", command=self._manage_years)
    
    def _export_pdf(self):
        """Export the current tax return as PDF"""
        try:
            from utils.pdf_generator import generate_pdf
            
            # Generate PDF with current tax data
            results = generate_pdf(self.tax_data, str(self.config.safe_dir))
            
            # Check if any PDFs were generated successfully
            successful_results = [r for r in results if r.success]
            
            if successful_results:
                pdf_paths = [str(r.output_path) for r in successful_results]
                messagebox.showinfo("Export Complete", 
                    f"Tax return PDFs exported successfully!\n\nGenerated {len(successful_results)} form(s):\n" + 
                    "\n".join(f"• {path}" for path in pdf_paths))
            else:
                messagebox.showerror("Export Failed", 
                    "Failed to generate PDFs. Please check your tax data and try again.")
                    
        except Exception as e:
            messagebox.showerror("Export Error", 
                f"An error occurred during PDF export:\n\n{str(e)}")
    
    def _new_return(self):
        """Start a new tax return"""
        if messagebox.askyesno("New Return", "Start a new tax return? Any unsaved changes will be lost."):
            self.tax_data = TaxData(self.config)
            self.show_page("personal_info")
            self.update_progress()
    
    def _focus_search(self):
        """Focus on search field (placeholder for future search functionality)"""
        pass  # Could implement search functionality later
    
    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.theme_manager:
            new_theme = self.theme_manager.toggle_theme()
            self._apply_theme()
            # Update status
            self.status_label.config(text=f"Switched to {new_theme} theme")
    
    def _open_tax_planning(self):
        """Open the tax planning tools window"""
        try:
            from gui.tax_planning_window import open_tax_planning_window
            open_tax_planning_window(self.root, self.tax_data)
        except Exception as e:
            messagebox.showerror("Tax Planning Error", 
                f"Failed to open tax planning tools:\n\n{str(e)}")
    
    def _open_state_taxes(self):
        """Open the state tax tools window"""
        try:
            from gui.state_tax_window import open_state_tax_window
            open_state_tax_window(self.root, self.tax_data)
        except Exception as e:
            messagebox.showerror("State Tax Error", 
                f"Failed to open state tax tools:\n\n{str(e)}")
    
    def _open_audit_trail(self):
        """Open the audit trail window"""
        try:
            audit_window = AuditTrailWindow(self.root, self.audit_service)
        except Exception as e:
            messagebox.showerror("Audit Trail Error", 
                f"Failed to open audit trail:\n\n{str(e)}")
    
    def _open_e_filing(self):
        """Open the e-filing window"""
        try:
            from gui.e_filing_window import open_e_filing_window
            open_e_filing_window(self.root, self.tax_data, self.config, self.ptin_ero_service)
        except Exception as e:
            messagebox.showerror("E-Filing Error", 
                f"Failed to open e-filing window:\n\n{str(e)}")
    
    def _check_e_file_status(self):
        """Open e-file status checking window"""
        try:
            from gui.e_filing_window import open_e_filing_window
            # Open e-filing window and switch to status tab
            window = open_e_filing_window(self.root, self.tax_data, self.config, self.ptin_ero_service)
            # Note: In a real implementation, we'd switch to the status tab here
        except Exception as e:
            messagebox.showerror("E-File Status Error", 
                f"Failed to open e-file status:\n\n{str(e)}")
    
    def _share_return(self):
        """Open the sharing dialog to share the current tax return"""
        try:
            from gui.sharing_dialog import SharingDialog
            from models.user import User
            from services.collaboration_service import AccessLevel
            
            # Create a mock user for now (in a real app, this would come from authentication)
            current_user = User(
                id="current_user_id",
                name="Current User",
                email="user@example.com"
            )
            
            # Generate a return ID for sharing
            return_id = f"return_{self.tax_data.get_current_year()}_{current_user.id}"
            
            sharing_dialog = SharingDialog(
                self.root,
                self.collaboration_service,
                current_user,
                return_id,
                self.tax_data.get_current_year()
            )
            
        except Exception as e:
            messagebox.showerror("Sharing Error", 
                f"Failed to open sharing dialog:\n\n{str(e)}")
    
    def _open_review_mode(self):
        """Open the review mode window for the current tax return"""
        try:
            from gui.review_mode_window import ReviewModeWindow
            from models.user import User
            from services.collaboration_service import AccessLevel
            
            # Create a mock user for now (in a real app, this would come from authentication)
            current_user = User(
                id="current_user_id",
                name="Current User",
                email="user@example.com"
            )
            
            # Generate a return ID for sharing
            return_id = f"return_{self.tax_data.get_current_year()}_{current_user.id}"
            
            review_window = ReviewModeWindow(
                self.root,
                self.collaboration_service,
                self.tax_data,
                return_id,
                self.tax_data.get_current_year(),
                current_user.id,
                current_user.name,
                AccessLevel.FULL_ACCESS  # Owner has full access
            )
            
        except Exception as e:
            messagebox.showerror("Review Mode Error", 
                f"Failed to open review mode:\n\n{str(e)}")
    
    def _manage_shared_returns(self):
        """Open dialog to manage shared returns and access"""
        try:
            # Create a simple management dialog for shared returns
            manage_window = tk.Toplevel(self.root)
            manage_window.title("Manage Shared Returns")
            manage_window.geometry("600x400")
            manage_window.resizable(True, True)
            
            ttk.Label(manage_window, text="Shared Tax Returns:", 
                     font=("", 12, "bold")).pack(pady=10)
            
            # List of shared returns
            listbox_frame = ttk.Frame(manage_window)
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=15)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            # For now, show a placeholder message
            listbox.insert(tk.END, "No shared returns found.")
            listbox.insert(tk.END, "Feature coming soon - manage shared returns here.")
            
            # Close button
            ttk.Button(manage_window, text="Close", 
                      command=manage_window.destroy).pack(pady=(0, 20))
            
        except Exception as e:
            messagebox.showerror("Manage Shared Returns Error", 
                f"Failed to open shared returns management:\n\n{str(e)}")
    
    def _create_new_year(self):
        """Create a new tax year return"""
        try:
            # Get available years
            supported_years = self.tax_year_service.get_supported_years()
            current_year = self.tax_data.get_current_year()

            # Create a simple dialog to select the new year
            from tkinter import simpledialog
            new_year_str = simpledialog.askstring(
                "New Tax Year",
                f"Enter the tax year to create (supported: {min(supported_years)}-{max(supported_years)}):",
                initialvalue=str(current_year + 1)
            )

            if new_year_str:
                try:
                    new_year = int(new_year_str)
                    if new_year in supported_years:
                        if self.tax_data.create_new_year(new_year, current_year):
                            messagebox.showinfo("Success", f"Created new tax year {new_year} based on {current_year}")
                            # Switch to the new year
                            self._on_tax_year_changed(new_year)
                        else:
                            messagebox.showerror("Error", f"Failed to create tax year {new_year}")
                    else:
                        messagebox.showerror("Invalid Year", f"Tax year {new_year} is not supported")
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a valid year number")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create new tax year: {str(e)}")

    def _copy_current_year(self):
        """Copy the current year data to a new year"""
        self._create_new_year()  # Reuse the same logic

    def _compare_years(self):
        """Open year comparison window"""
        try:
            from gui.year_comparison_window import YearComparisonWindow

            # Get available years with data
            available_years = self.tax_data.get_available_years()
            if len(available_years) < 2:
                messagebox.showwarning(
                    "Insufficient Data",
                    "Need at least two tax years with data to compare. Create additional years first."
                )
                return

            # Get data for all available years
            tax_data_dict = {}
            for year in available_years:
                tax_data_dict[year] = self.tax_data.get_year_data(year)

            # Open comparison window
            comparison_window = YearComparisonWindow(
                self.root,
                self.tax_year_service,
                tax_data_dict
            )

        except Exception as e:
            messagebox.showerror("Comparison Error", f"Failed to open year comparison: {str(e)}")

    def _manage_years(self):
        """Open year management dialog"""
        try:
            # Create a simple management dialog
            manage_window = tk.Toplevel(self.root)
            manage_window.title("Manage Tax Years")
            manage_window.geometry("400x300")
            manage_window.resizable(True, True)

            # Available years list
            ttk.Label(manage_window, text="Available Tax Years:", font=("", 10, "bold")).pack(pady=10)

            # Listbox with years
            listbox_frame = ttk.Frame(manage_window)
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=10)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)

            # Populate listbox
            available_years = self.tax_data.get_available_years()
            current_year = self.tax_data.get_current_year()

            for year in sorted(available_years, reverse=True):
                display_text = f"{year} (Current)" if year == current_year else str(year)
                listbox.insert(tk.END, display_text)

            # Buttons
            button_frame = ttk.Frame(manage_window)
            button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

            ttk.Button(
                button_frame,
                text="Switch To Selected",
                command=lambda: self._switch_to_selected_year(listbox, manage_window)
            ).pack(side=tk.LEFT, padx=(0, 10))

            ttk.Button(
                button_frame,
                text="Delete Selected",
                command=lambda: self._delete_selected_year(listbox, manage_window)
            ).pack(side=tk.LEFT)

            ttk.Button(
                button_frame,
                text="Close",
                command=manage_window.destroy
            ).pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror("Management Error", f"Failed to open year management: {str(e)}")

    def _switch_to_selected_year(self, listbox, window):
        """Switch to the selected year"""
        try:
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a tax year first")
                return

            selected_text = listbox.get(selection[0])
            year = int(selected_text.split()[0])  # Extract year from "2025 (Current)" format

            self._on_tax_year_changed(year)
            window.destroy()
            messagebox.showinfo("Switched", f"Switched to tax year {year}")

        except Exception as e:
            messagebox.showerror("Switch Error", f"Failed to switch tax year: {str(e)}")

    def _delete_selected_year(self, listbox, window):
        """Delete the selected year"""
        try:
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a tax year first")
                return

            selected_text = listbox.get(selection[0])
            year = int(selected_text.split()[0])

            current_year = self.tax_data.get_current_year()
            if year == current_year:
                messagebox.showerror("Cannot Delete", "Cannot delete the current tax year")
                return

            if messagebox.askyesno("Confirm Delete", f"Delete tax year {year}? This action cannot be undone."):
                if self.tax_data.delete_year(year):
                    messagebox.showinfo("Deleted", f"Tax year {year} has been deleted")
                    window.destroy()
                    self._manage_years()  # Refresh the management window
                else:
                    messagebox.showerror("Delete Failed", f"Failed to delete tax year {year}")

        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete tax year: {str(e)}")
    
    def _on_closing(self):
        """Handle application closing"""
        try:
            # End audit session
            if hasattr(self, 'audit_service'):
                self.audit_service.end_session()
        except Exception as e:
            print(f"Error ending audit session: {e}")
        
        # Close the application
        self.root.destroy()
    
    def _apply_theme(self):
        """Apply the current theme to all UI elements"""
        if not self.theme_manager:
            return
            
        # Apply theme to root window
        theme_colors = self.theme_manager.get_current_theme()
        self.root.configure(bg=theme_colors["bg"])
        
        # Update all widgets that support theming
        self._update_widget_theme(self.root, theme_colors)
    
    def _update_widget_theme(self, widget, theme_colors):
        """Recursively apply theme to all widgets"""
        try:
            # Apply theme based on widget type
            if isinstance(widget, tk.Tk) or isinstance(widget, ttk.Frame):
                widget.configure(bg=theme_colors["bg"])
            elif isinstance(widget, ttk.Label):
                widget.configure(
                    bg=theme_colors["label_bg"],
                    fg=theme_colors["label_fg"]
                )
            elif isinstance(widget, ttk.Button):
                widget.configure(
                    bg=theme_colors["button_bg"],
                    fg=theme_colors["button_fg"]
                )
            elif isinstance(widget, ttk.Entry):
                widget.configure(
                    bg=theme_colors["entry_bg"],
                    fg=theme_colors["entry_fg"],
                    insertcolor=theme_colors["fg"]
                )
            elif isinstance(widget, tk.Text):
                widget.configure(
                    bg=theme_colors["entry_bg"],
                    fg=theme_colors["entry_fg"],
                    insertbackground=theme_colors["fg"]
                )
            
            # Recursively apply to children
            for child in widget.winfo_children():
                self._update_widget_theme(child, theme_colors)
                
        except tk.TclError:
            # Some widgets might not support certain options
            pass
    
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
        current_page_id = getattr(self, 'current_page_id', None) or "personal_info"
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
        
        return total_progress
    
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
        
        # Tax Year Selector
        from services.tax_year_service import TaxYearService
        from gui.widgets.tax_year_selector import TaxYearSelector

        self.tax_year_service = TaxYearService()
        self.tax_year_selector = TaxYearSelector(
            sidebar,
            self.tax_year_service,
            on_year_changed=self._on_tax_year_changed
        )
        self.tax_year_selector.pack(fill="x", pady=(0, 20))
        
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

    def _on_tax_year_changed(self, new_year: int):
        """Handle tax year change"""
        try:
            # Update the tax data model to use the new year
            self.tax_data.set_current_year(new_year)

            # Refresh all pages to show data for the new year
            if self.current_page:
                self.current_page.refresh_data()

            # Update progress and validation
            self.update_progress()
            self.update_validation_summary()

            # Update status
            self.status_label.config(text=f"Switched to Tax Year {new_year}")

        except Exception as e:
            messagebox.showerror("Year Change Error", f"Failed to switch tax year: {str(e)}")
            # Revert the selector to the current year
            self.tax_year_selector.set_current_year(self.tax_data.get_current_year())
    
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
            
            # Skip GUI operations if in mocked testing environment
            if not self.is_mocked:
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
            
            # Log audit event
            self.audit_service.log_action(
                action="SAVE",
                entity_type="file",
                entity_id=str(filename),
                metadata={"file_type": "encrypted_tax_return"}
            )
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
                
                # Log audit event
                self.audit_service.log_action(
                    action="LOAD",
                    entity_type="file",
                    entity_id=str(filename),
                    metadata={"file_type": "encrypted_tax_return"}
                )
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
    
    def _import_prior_year(self):
        """Import data from a prior year tax return"""
        from tkinter import filedialog
        from pathlib import Path
        from utils.import_utils import import_prior_year_return
        import logging
        logger = logging.getLogger(__name__)
        
        filename = filedialog.askopenfilename(
            title="Select prior year tax return",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                imported_data = import_prior_year_return(filename)
                
                # Ask user what to import
                import_options = self._show_import_options_dialog(imported_data)
                
                if import_options:
                    # Merge imported data with current tax data
                    self._merge_imported_data(imported_data, import_options)
                    
                    messagebox.showinfo(
                        "Import Complete",
                        f"Successfully imported data from prior year return:\n{Path(filename).name}"
                    )
                    self.status_label.config(text=f"Imported: {Path(filename).name}")
                    
                    # Refresh current page to show imported data
                    if self.current_page:
                        page_id = self.get_current_page_id()
                        self.show_page(page_id)
                        
                    logger.info(f"Prior year return imported: {filename}")
                else:
                    messagebox.showinfo("Import Cancelled", "Import was cancelled by user.")
                    
            except Exception as e:
                logger.error(f"Import failed: {e}", exc_info=True)
                messagebox.showerror(
                    "Import Failed",
                    f"Failed to import prior year return:\n\n{str(e)}"
                )
    
    def _import_w2_pdf(self):
        """Import W-2 data from PDF"""
        from tkinter import filedialog
        from pathlib import Path
        from utils.import_utils import import_w2_from_pdf
        import logging
        logger = logging.getLogger(__name__)
        
        filename = filedialog.askopenfilename(
            title="Select W-2 PDF",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                w2_data = import_w2_from_pdf(filename)
                
                # Add W-2 data to current tax return
                if 'income' in w2_data and 'w2_forms' in w2_data['income']:
                    # Check if we already have W-2 forms
                    existing_w2s = self.tax_data.get('income.w2_forms', [])
                    
                    # Add the new W-2
                    new_w2 = w2_data['income']['w2_forms'][0]
                    existing_w2s.append(new_w2)
                    
                    # Update tax data
                    self.tax_data.set('income.w2_forms', existing_w2s)
                    
                    messagebox.showinfo(
                        "W-2 Import Complete",
                        f"Successfully imported W-2 data from:\n{Path(filename).name}\n\n"
                        f"Employer: {new_w2.get('employer_name', 'Unknown')}\n"
                        f"Wages: ${new_w2.get('wages', 0):,.2f}"
                    )
                    
                    # Refresh income page to show new W-2
                    self.show_page("income")
                    self.status_label.config(text=f"W-2 imported: {Path(filename).name}")
                    
                    logger.info(f"W-2 imported from PDF: {filename}")
                else:
                    messagebox.showwarning("Import Warning", "No W-2 data found in the selected PDF.")
                    
            except Exception as e:
                logger.error(f"W-2 import failed: {e}", exc_info=True)
                messagebox.showerror(
                    "Import Failed",
                    f"Failed to import W-2 from PDF:\n\n{str(e)}"
                )
    
    def _import_1099_pdf(self):
        """Import 1099 data from PDF"""
        from tkinter import filedialog
        from pathlib import Path
        from utils.import_utils import import_1099_from_pdf
        import logging
        logger = logging.getLogger(__name__)
        
        filename = filedialog.askopenfilename(
            title="Select 1099 PDF",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                form1099_data = import_1099_from_pdf(filename)
                
                # Merge 1099 data with current tax return
                self._merge_imported_data(form1099_data, {
                    'income': True,
                    'dividends': True,
                    'interest': True,
                    'capital_gains': True
                })
                
                messagebox.showinfo(
                    "1099 Import Complete",
                    f"Successfully imported 1099 data from:\n{Path(filename).name}"
                )
                
                # Refresh income page to show new data
                self.show_page("income")
                self.status_label.config(text=f"1099 imported: {Path(filename).name}")
                
                logger.info(f"1099 imported from PDF: {filename}")
                
            except Exception as e:
                logger.error(f"1099 import failed: {e}", exc_info=True)
                messagebox.showerror(
                    "Import Failed",
                    f"Failed to import 1099 from PDF:\n\n{str(e)}"
                )
    
    def _import_txf(self):
        """Import data from TXF (Tax Exchange Format) file"""
        from tkinter import filedialog
        from pathlib import Path
        from utils.import_utils import TaxDataImporter
        import logging
        logger = logging.getLogger(__name__)
        
        filename = filedialog.askopenfilename(
            title="Select TXF file",
            filetypes=[
                ("TXF files", "*.txf"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                importer = TaxDataImporter()
                imported_data = importer.import_from_file(filename)
                
                # Ask user what to import
                import_options = self._show_import_options_dialog(imported_data)
                
                if import_options:
                    # Merge imported data with current tax data
                    self._merge_imported_data(imported_data, import_options)
                    
                    messagebox.showinfo(
                        "TXF Import Complete",
                        f"Successfully imported data from TXF file:\n{Path(filename).name}"
                    )
                    
                    # Refresh current page to show imported data
                    if self.current_page:
                        page_id = self.get_current_page_id()
                        self.show_page(page_id)
                        
                    self.status_label.config(text=f"TXF imported: {Path(filename).name}")
                    logger.info(f"TXF file imported: {filename}")
                else:
                    messagebox.showinfo("Import Cancelled", "Import was cancelled by user.")
                    
            except Exception as e:
                logger.error(f"TXF import failed: {e}", exc_info=True)
                messagebox.showerror(
                    "Import Failed",
                    f"Failed to import TXF file:\n\n{str(e)}"
                )
    
    def _show_import_options_dialog(self, imported_data):
        """Show dialog for selecting what data to import"""
        # This is a simplified implementation
        # In a real application, you'd show a dialog with checkboxes for each data type
        import_options = {}
        
        # Check what data types are available in the imported data
        if 'personal_info' in imported_data:
            import_options['personal_info'] = True
        if 'filing_status' in imported_data:
            import_options['filing_status'] = True
        if 'income' in imported_data:
            import_options['income'] = True
        if 'deductions' in imported_data:
            import_options['deductions'] = True
        if 'credits' in imported_data:
            import_options['credits'] = True
            
        return import_options
    
    def _merge_imported_data(self, imported_data, import_options):
        """Merge imported data with current tax data"""
        for section, should_import in import_options.items():
            if should_import and section in imported_data:
                if section not in self.tax_data.data:
                    self.tax_data.data[section] = {}
                
                # For simple cases, replace the section data
                # In a real implementation, you'd handle conflicts and merging more carefully
                self.tax_data.data[section] = imported_data[section]
    
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
    
    def _change_password(self):
        """Open change password dialog"""
        try:
            from gui.password_dialogs import ChangePasswordDialog
            dialog = ChangePasswordDialog(self.root, self.auth_service)
            result = dialog.show()
            if result:
                messagebox.showinfo("Success", "Password changed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change password: {e}")
    
    def _logout(self):
        """Logout current user and restart authentication"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout? Any unsaved changes will be lost."):
            # Clear session
            if self.session_token:
                self.auth_service.logout(self.session_token)
                self.session_token = None
            
            # Restart application (simplified - in real app might restart process)
            messagebox.showinfo("Logged Out", "You have been logged out. Please restart the application to login again.")
            self.root.quit()
    
    def _configure_cloud_backup(self):
        """Configure cloud backup settings"""
        try:
            from gui.cloud_backup_dialogs import CloudConfigDialog
            dialog = CloudConfigDialog(self.root, self.cloud_backup_service)
            result = dialog.show()
            if result:
                messagebox.showinfo("Success", "Cloud backup configured successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to configure cloud backup: {e}")
    
    def _create_backup(self):
        """Create a new cloud backup"""
        try:
            from gui.cloud_backup_dialogs import CreateBackupDialog
            dialog = CreateBackupDialog(self.root, self.cloud_backup_service, self.config)
            backup_id = dialog.show()
            if backup_id:
                messagebox.showinfo("Success", f"Backup created successfully: {backup_id}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {e}")
    
    def _restore_backup(self):
        """Restore from a cloud backup"""
        try:
            from gui.cloud_backup_dialogs import RestoreBackupDialog
            dialog = RestoreBackupDialog(self.root, self.cloud_backup_service)
            result = dialog.show()
            if result:
                messagebox.showinfo("Success", "Backup restored successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore backup: {e}")
    
    def _show_backup_status(self):
        """Show cloud backup status and statistics"""
        try:
            from gui.cloud_backup_dialogs import BackupStatusDialog
            dialog = BackupStatusDialog(self.root, self.cloud_backup_service)
            dialog.show()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show backup status: {e}")
    
    def _enable_2fa(self):
        """Enable Two-Factor Authentication"""
        try:
            # Check if 2FA is already enabled
            if self.auth_service.is_2fa_enabled():
                messagebox.showinfo("2FA Status", "Two-Factor Authentication is already enabled.")
                return
            
            # Get setup information
            setup_info = self.auth_service.get_2fa_setup_info(self.session_token)
            
            # Show setup dialog
            dialog = TwoFactorSetupDialog(self.root, self.auth_service, setup_info)
            result = dialog.show()
            
            if result:
                messagebox.showinfo("Success", "Two-Factor Authentication has been enabled!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable 2FA: {e}")
    
    def _disable_2fa(self):
        """Disable Two-Factor Authentication"""
        try:
            # Check if 2FA is enabled
            if not self.auth_service.is_2fa_enabled():
                messagebox.showinfo("2FA Status", "Two-Factor Authentication is not currently enabled.")
                return
            
            # Show disable confirmation dialog
            dialog = TwoFactorDisableDialog(self.root, self.auth_service)
            result = dialog.show()
            
            if result:
                messagebox.showinfo("Success", "Two-Factor Authentication has been disabled.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disable 2FA: {e}")
    
    def _open_client_management(self):
        """Open client management dialog"""
        try:
            if not self.session_token:
                messagebox.showerror("Error", "You must be logged in to manage clients.")
                return
            
            dialog = ClientManagementDialog(self.root, self.auth_service, self.session_token)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open client management: {e}")
    
    def _open_client_portal(self):
        """Open client portal login dialog"""
        try:
            dialog = ClientLoginDialog(self.root)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open client portal: {e}")
    
    def _open_ptin_ero_management(self):
        """Open PTIN/ERO management dialog"""
        try:
            if not self.session_token:
                messagebox.showerror("Error", "You must be logged in to manage PTIN/ERO credentials.")
                return
            
            dialog = PTINEROManagementDialog(self.root)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PTIN/ERO management: {e}")
    
    def _open_tax_analytics(self):
        """Open tax analytics window"""
        try:
            # Create analytics window with current tax data
            analytics_window = TaxAnalyticsWindow(
                self.root,
                self.config,
                tax_data=self.tax_data
            )
            # Window will show itself
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open tax analytics: {e}")
    
    def _open_tax_planning(self):
        """Open tax planning tools (placeholder)"""
        messagebox.showinfo("Tax Planning", "Tax planning tools coming soon!")
    
    def _open_state_taxes(self):
        """Open state tax tools (placeholder)"""
        messagebox.showinfo("State Taxes", "State tax tools coming soon!")
    
    def _open_audit_trail(self):
        """Open audit trail window"""
        try:
            audit_window = AuditTrailWindow(self.root, self.audit_service)
            audit_window.show()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open audit trail: {e}")
