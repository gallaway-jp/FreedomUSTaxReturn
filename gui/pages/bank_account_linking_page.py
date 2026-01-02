"""
Bank Account Linking Page

A modern, integrated page for managing bank account connections and data synchronization.
This page consolidates all bank account linking functionality previously in a popup window.

Features:
- Connected bank account management
- Account mapping and selection
- Sync settings and status monitoring
- Transaction categorization
- Bank credential management
- Sync history and logs
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
from datetime import datetime


class ModernButton(ctk.CTkButton):
    """Custom button with type variants (primary, secondary, success, danger)."""
    
    def __init__(self, *args, button_type: str = "primary", **kwargs):
        # Color scheme for button types
        colors = {
            "primary": ("#0066CC", "#0052A3"),
            "secondary": ("#666666", "#4D4D4D"),
            "success": ("#28A745", "#1E8449"),
            "danger": ("#DC3545", "#C82333"),
        }
        
        fg_color, hover_color = colors.get(button_type, colors["primary"])
        kwargs.update({
            "fg_color": fg_color,
            "hover_color": hover_color,
            "text_color": "white",
        })
        super().__init__(*args, **kwargs)


class ModernFrame(ctk.CTkFrame):
    """Custom frame with consistent styling."""
    pass


class ModernLabel(ctk.CTkLabel):
    """Custom label with consistent styling."""
    pass


class BankAccountLinkingPage(ctk.CTkScrollableFrame):
    """
    Bank Account Linking Page
    
    Provides comprehensive interface for managing bank account connections,
    transaction synchronization, and account mapping for tax return preparation.
    
    Attributes:
        config: Application configuration object
        tax_data: Tax data management object
        accessibility_service: Accessibility features service
    """
    
    def __init__(
        self,
        master,
        config: Optional[Any] = None,
        tax_data: Optional[Any] = None,
        accessibility_service: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        # Store service references
        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        
        # Data storage
        self.connected_banks = []
        self.sync_status = {}
        self.account_mappings = {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Build page structure
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
    
    def _create_header(self):
        """Create page header with title and description."""
        header_frame = ModernFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title with emoji
        title_label = ModernLabel(
            header_frame,
            text="🏦 Bank Account Linking",
            font=("Segoe UI", 24, "bold"),
            text_color="#FFFFFF"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Subtitle
        subtitle_label = ModernLabel(
            header_frame,
            text="Connect your bank accounts for secure transaction import and automatic categorization",
            font=("Segoe UI", 12),
            text_color="#A0A0A0"
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
    
    def _create_toolbar(self):
        """Create toolbar with action buttons and progress indicator."""
        toolbar_frame = ModernFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(0, 10))
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        # Action buttons
        button_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="w", padx=0)
        
        add_bank_btn = ModernButton(
            button_frame,
            text="+ Add Bank Connection",
            button_type="primary",
            width=180,
            height=36,
            command=self._action_add_bank
        )
        add_bank_btn.grid(row=0, column=0, padx=(0, 10))
        
        sync_btn = ModernButton(
            button_frame,
            text="🔄 Sync Now",
            button_type="success",
            width=120,
            height=36,
            command=self._action_sync_accounts
        )
        sync_btn.grid(row=0, column=1, padx=5)
        
        settings_btn = ModernButton(
            button_frame,
            text="⚙ Settings",
            button_type="secondary",
            width=100,
            height=36,
            command=self._action_open_settings
        )
        settings_btn.grid(row=0, column=2, padx=5)
        
        # Progress bar (right side)
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.grid(row=0, column=1, sticky="e", padx=0)
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=200,
            height=8,
            progress_color="#28A745"
        )
        self.progress_bar.grid(row=0, column=0, sticky="e")
        self.progress_bar.set(0.65)
        
        # Status label
        self.status_label = ModernLabel(
            progress_frame,
            text="3 of 5 accounts synced",
            font=("Segoe UI", 10),
            text_color="#A0A0A0"
        )
        self.status_label.grid(row=1, column=0, sticky="e", pady=(5, 0))
    
    def _create_main_content(self):
        """Create tabbed interface for bank account management."""
        # Main content frame
        content_frame = ModernFrame(self, fg_color="#2B2B2B")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(
            content_frame,
            text_color="#FFFFFF",
            segmented_button_fg_color="#1E1E1E",
            segmented_button_selected_color="#0066CC",
            fg_color="#2B2B2B"
        )
        self.tabview.grid(row=0, column=0, sticky="nsew")
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)
        
        # Create tabs
        self.tabview.add("Connected Accounts")
        self.tabview.add("Sync History")
        self.tabview.add("Account Mapping")
        self.tabview.add("Transaction Categorization")
        self.tabview.add("Bank Settings")
        
        # Setup individual tabs
        self._setup_connected_accounts_tab()
        self._setup_sync_history_tab()
        self._setup_account_mapping_tab()
        self._setup_transaction_categorization_tab()
        self._setup_bank_settings_tab()
    
    def _setup_connected_accounts_tab(self):
        """Setup Connected Accounts tab."""
        tab = self.tabview.tab("Connected Accounts")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Description
        desc_label = ModernLabel(
            tab,
            text="Manage your connected bank accounts and update credentials",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Accounts list frame
        list_frame = ModernFrame(tab, fg_color="#1E1E1E")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Sample accounts
        accounts = [
            ("Chase Checking", "●●●●7382", "Synced 2 hours ago"),
            ("Bank of America Savings", "●●●●2891", "Synced 30 min ago"),
            ("Wells Fargo Money Market", "●●●●5541", "Sync pending"),
        ]
        
        for i, (bank_name, account_num, status) in enumerate(accounts):
            account_frame = ctk.CTkFrame(list_frame, fg_color="#2B2B2B", height=80)
            account_frame.grid(row=i, column=0, sticky="ew", pady=5)
            account_frame.grid_columnconfigure(1, weight=1)
            
            # Bank icon and name
            icon_label = ModernLabel(account_frame, text="🏦", font=("Segoe UI", 16))
            icon_label.grid(row=0, column=0, padx=10, pady=10)
            
            # Account info
            info_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="w", pady=10)
            
            bank_label = ModernLabel(info_frame, text=bank_name, font=("Segoe UI", 12, "bold"))
            bank_label.grid(row=0, column=0, sticky="w")
            
            account_label = ModernLabel(info_frame, text=account_num, font=("Segoe UI", 10), text_color="#A0A0A0")
            account_label.grid(row=1, column=0, sticky="w")
            
            status_label = ModernLabel(info_frame, text=status, font=("Segoe UI", 9), text_color="#28A745")
            status_label.grid(row=2, column=0, sticky="w")
            
            # Actions
            action_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
            action_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
            
            ModernButton(action_frame, text="Edit", button_type="secondary", width=70, height=32,
                        command=lambda: self._action_edit_account(bank_name)).pack(side="left", padx=5)
            ModernButton(action_frame, text="Remove", button_type="danger", width=70, height=32,
                        command=lambda: self._action_remove_account(bank_name)).pack(side="left", padx=5)
    
    def _setup_sync_history_tab(self):
        """Setup Sync History tab."""
        tab = self.tabview.tab("Sync History")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Description
        desc_label = ModernLabel(
            tab,
            text="View detailed history of all synchronization activities",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Sync history textbox
        history_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        history_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        history_frame.grid_columnconfigure(0, weight=1)
        history_frame.grid_rowconfigure(0, weight=1)
        
        history_text = ctk.CTkTextbox(history_frame, text_color="#FFFFFF", fg_color="#2B2B2B")
        history_text.grid(row=0, column=0, sticky="nsew")
        
        # Sample history
        history_content = """2024-01-15 14:32:21 - Chase Checking: Synced 342 transactions
2024-01-15 14:31:15 - BofA Savings: Synced 156 transactions
2024-01-15 14:30:08 - Wells Fargo: Sync started
2024-01-15 13:45:00 - All accounts: Manual sync completed
2024-01-15 12:30:00 - Chase Checking: Sync failed - Credential update needed
2024-01-15 11:15:23 - BofA Savings: Synced 289 transactions

View full sync logs and troubleshooting information"""
        
        history_text.insert("0.0", history_content)
        history_text.configure(state="disabled")
    
    def _setup_account_mapping_tab(self):
        """Setup Account Mapping tab."""
        tab = self.tabview.tab("Account Mapping")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        
        # Description
        desc_label = ModernLabel(
            tab,
            text="Map imported bank accounts to tax form fields and categories",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Mapping controls
        controls_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        controls_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Select account
        account_label = ModernLabel(controls_frame, text="Account:", font=("Segoe UI", 11))
        account_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        account_combo = ctk.CTkComboBox(
            controls_frame,
            values=["Chase Checking", "BofA Savings", "Wells Fargo MM"],
            fg_color="#2B2B2B",
            button_color="#0066CC",
            text_color="#FFFFFF",
            state="readonly"
        )
        account_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        account_combo.set("Chase Checking")
        
        # Mapping list
        mapping_frame = ModernFrame(tab, fg_color="transparent")
        mapping_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=10)
        mapping_frame.grid_columnconfigure(0, weight=1)
        
        mapping_scroll = ctk.CTkScrollableFrame(mapping_frame, fg_color="#1E1E1E")
        mapping_scroll.grid(row=0, column=0, sticky="nsew")
        mapping_scroll.grid_columnconfigure(0, weight=1)
        
        mappings = [
            ("Checking Account", "Form 1040 - Income Verification"),
            ("Debit Card Purchases", "Schedule C - Business Expenses"),
            ("ATM Withdrawals", "Schedule A - Itemized Deductions"),
        ]
        
        for bank_field, tax_field in mappings:
            map_frame = ctk.CTkFrame(mapping_scroll, fg_color="#2B2B2B", height=60)
            map_frame.pack(fill="x", pady=5)
            map_frame.grid_columnconfigure(1, weight=1)
            
            label = ModernLabel(map_frame, text=f"{bank_field} → {tax_field}", font=("Segoe UI", 10))
            label.pack(side="left", padx=10, pady=10)
    
    def _setup_transaction_categorization_tab(self):
        """Setup Transaction Categorization tab."""
        tab = self.tabview.tab("Transaction Categorization")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Description
        desc_label = ModernLabel(
            tab,
            text="Set up automatic categorization rules for imported transactions",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Rules frame
        rules_frame = ModernFrame(tab, fg_color="#1E1E1E")
        rules_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        rules_frame.grid_columnconfigure(0, weight=1)
        rules_frame.grid_rowconfigure(0, weight=1)
        
        rules_scroll = ctk.CTkScrollableFrame(rules_frame, fg_color="#2B2B2B")
        rules_scroll.grid(row=0, column=0, sticky="nsew")
        rules_scroll.grid_columnconfigure(0, weight=1)
        
        # Sample rules
        rules = [
            ("Amazon", "Business Supplies", "Contains 'AMZN'"),
            ("Starbucks", "Meals & Entertainment", "Matches 'Starbucks Coffee'"),
            ("Office Depot", "Office Supplies", "Starts with 'OFFICE DEPOT'"),
            ("Southwest Airlines", "Travel", "Contains 'SOUTHWEST'"),
        ]
        
        for merchant, category, condition in rules:
            rule_frame = ctk.CTkFrame(rules_scroll, fg_color="#1E1E1E", height=50)
            rule_frame.pack(fill="x", pady=5)
            rule_frame.grid_columnconfigure(1, weight=1)
            
            merchant_label = ModernLabel(rule_frame, text=f"📋 {merchant}", font=("Segoe UI", 11, "bold"))
            merchant_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            category_label = ModernLabel(rule_frame, text=f"→ {category} ({condition})", font=("Segoe UI", 10), text_color="#A0A0A0")
            category_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
            
            ModernButton(rule_frame, text="Edit", button_type="secondary", width=60, height=28,
                        command=lambda: self._action_edit_rule(merchant)).grid(row=0, column=2, padx=5, pady=5)
    
    def _setup_bank_settings_tab(self):
        """Setup Bank Settings tab."""
        tab = self.tabview.tab("Bank Settings")
        tab.grid_columnconfigure(0, weight=1)
        
        # Description
        desc_label = ModernLabel(
            tab,
            text="Configure general bank account linking settings",
            font=("Segoe UI", 11),
            text_color="#A0A0A0"
        )
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        # Settings frame
        settings_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        settings_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Auto-sync option
        auto_sync_label = ModernLabel(settings_frame, text="Auto-sync Enabled:", font=("Segoe UI", 11))
        auto_sync_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        auto_sync_switch = ctk.CTkSwitch(settings_frame, text="", fg_color="#0066CC")
        auto_sync_switch.grid(row=0, column=1, sticky="e", padx=15, pady=10)
        auto_sync_switch.select()
        
        # Sync frequency
        freq_label = ModernLabel(settings_frame, text="Sync Frequency:", font=("Segoe UI", 11))
        freq_label.grid(row=1, column=0, sticky="w", padx=15, pady=10)
        
        freq_combo = ctk.CTkComboBox(
            settings_frame,
            values=["Every 15 minutes", "Every 30 minutes", "Every hour", "Every 4 hours"],
            fg_color="#2B2B2B",
            button_color="#0066CC",
            text_color="#FFFFFF",
            state="readonly"
        )
        freq_combo.grid(row=1, column=1, sticky="ew", padx=15, pady=10)
        freq_combo.set("Every 30 minutes")
        
        # Transaction limit
        limit_label = ModernLabel(settings_frame, text="Days to Sync (back):", font=("Segoe UI", 11))
        limit_label.grid(row=2, column=0, sticky="w", padx=15, pady=10)
        
        limit_entry = ctk.CTkEntry(settings_frame, fg_color="#2B2B2B", text_color="#FFFFFF")
        limit_entry.grid(row=2, column=1, sticky="ew", padx=15, pady=10)
        limit_entry.insert(0, "90")
        
        # Save settings button
        save_btn = ModernButton(
            settings_frame,
            text="💾 Save Settings",
            button_type="success",
            width=150,
            height=36,
            command=self._action_save_settings
        )
        save_btn.grid(row=3, column=1, sticky="e", padx=15, pady=15)
    
    # Action Methods
    def _action_add_bank(self):
        """Action: Add new bank connection."""
        print("[Bank Account Linking] Add bank connection initiated")
    
    def _action_sync_accounts(self):
        """Action: Synchronize all connected accounts."""
        print("[Bank Account Linking] Manual sync initiated")
        self.progress_bar.set(0.85)
        self.status_label.configure(text="Syncing... Please wait")
    
    def _action_open_settings(self):
        """Action: Open sync settings dialog."""
        print("[Bank Account Linking] Sync settings dialog requested")
    
    def _action_edit_account(self, account_name: str):
        """Action: Edit account credentials."""
        print(f"[Bank Account Linking] Edit account: {account_name}")
    
    def _action_remove_account(self, account_name: str):
        """Action: Remove connected account."""
        print(f"[Bank Account Linking] Remove account: {account_name}")
    
    def _action_edit_rule(self, merchant_name: str):
        """Action: Edit categorization rule."""
        print(f"[Bank Account Linking] Edit rule: {merchant_name}")
    
    def _action_save_settings(self):
        """Action: Save bank settings."""
        print("[Bank Account Linking] Settings saved")
        self.status_label.configure(text="Settings updated successfully")
