"""
Phase 6 Implementation Module
Integration of all 27 converted pages into modern_main_window.py

This module provides:
1. Complete import statements for all 27 pages
2. Page registry system with lazy loading
3. Enhanced navigation system
4. Comprehensive sidebar with all page categories
5. Page switching and caching logic

To integrate:
- Add these imports to modern_main_window.py
- Add page_registry dictionary to __init__
- Add page caching system
- Update sidebar with comprehensive navigation
"""

# ============================================================================
# IMPORT STATEMENTS - Add to modern_main_window.py imports section
# ============================================================================

# Phase 1: Foundation Pages
from gui.pages.state_tax_integration_page import StateTaxIntegrationPage

# Phase 2: Financial & Tax Pages  
from gui.pages.estate_trust_page import EstateTrustPage
from gui.pages.partnership_s_corp_page import PartnershipSCorpPage
from gui.pages.state_tax_page import StateTaxPage
from gui.pages.state_tax_calculator_page import StateTaxCalculatorPage

# Phase 3: Advanced Feature Pages
from gui.pages.ai_deduction_finder_page import AiDeductionFinderPage
from gui.pages.cryptocurrency_tax_page import CryptocurrencyTaxPage
from gui.pages.audit_trail_page import AuditTrailPage
from gui.pages.tax_planning_page import TaxPlanningPage

# Phase 4: Comprehensive Feature Pages
from gui.pages.quickbooks_integration_page import QuickbooksIntegrationPage
from gui.pages.tax_dashboard_page import TaxDashboardPage
from gui.pages.receipt_scanning_page import ReceiptScanningPage
from gui.pages.client_portal_page import ClientPortalPage
from gui.pages.tax_interview_page import TaxInterviewPage
from gui.pages.cloud_backup_page import CloudBackupPage
from gui.pages.ptin_ero_management_page import PTINEROManagementPage
from gui.pages.tax_analytics_page import TaxAnalyticsPage
from gui.pages.settings_preferences_page import SettingsPreferencesPage
from gui.pages.help_documentation_page import HelpDocumentationPage

# Phase 5: Management & Analysis Pages
from gui.pages.bank_account_linking_page import BankAccountLinkingPage
from gui.pages.e_filing_page import EFilingPage
from gui.pages.foreign_income_fbar_page import ForeignIncomeFBARPage
from gui.pages.plugin_management_page import PluginManagementPage
from gui.pages.tax_projections_page import TaxProjectionsPage
from gui.pages.translation_management_page import TranslationManagementPage
from gui.pages.year_comparison_page import YearComparisonPage


# ============================================================================
# PAGE REGISTRY - Add to ModernMainWindow.__init__() after UI initialization
# ============================================================================

def _initialize_page_registry(self):
    """Initialize the page registry with all 27 converted pages."""
    self.pages_registry = {
        # Phase 1: Foundation (1 page)
        'state_tax_integration': {
            'name': 'State Tax Integration',
            'icon': '🏛️',
            'category': 'Foundation',
            'page_class': StateTaxIntegrationPage,
            'instance': None
        },
        
        # Phase 2: Financial & Tax (4 pages)
        'estate_trust': {
            'name': 'Estate & Trust Planning',
            'icon': '👨‍👩‍👧‍👦',
            'category': 'Financial Planning',
            'page_class': EstateTrustPage,
            'instance': None
        },
        'partnership_s_corp': {
            'name': 'Partnership & S-Corp',
            'icon': '🏢',
            'category': 'Business',
            'page_class': PartnershipSCorpPage,
            'instance': None
        },
        'state_tax': {
            'name': 'State Tax Returns',
            'icon': '📋',
            'category': 'Tax Forms',
            'page_class': StateTaxPage,
            'instance': None
        },
        'state_tax_calculator': {
            'name': 'State Tax Calculator',
            'icon': '🧮',
            'category': 'Calculators',
            'page_class': StateTaxCalculatorPage,
            'instance': None
        },
        
        # Phase 3: Advanced Features (4 pages)
        'ai_deduction_finder': {
            'name': 'AI Deduction Finder',
            'icon': '🤖',
            'category': 'Advanced Features',
            'page_class': AiDeductionFinderPage,
            'instance': None
        },
        'cryptocurrency_tax': {
            'name': 'Cryptocurrency Tax',
            'icon': '₿',
            'category': 'Advanced Features',
            'page_class': CryptocurrencyTaxPage,
            'instance': None
        },
        'audit_trail': {
            'name': 'Audit Trail',
            'icon': '📝',
            'category': 'Security',
            'page_class': AuditTrailPage,
            'instance': None
        },
        'tax_planning': {
            'name': 'Tax Planning',
            'icon': '💡',
            'category': 'Planning',
            'page_class': TaxPlanningPage,
            'instance': None
        },
        
        # Phase 4: Comprehensive Features (12 pages)
        'quickbooks_integration': {
            'name': 'QuickBooks Integration',
            'icon': '📊',
            'category': 'Business Integration',
            'page_class': QuickbooksIntegrationPage,
            'instance': None
        },
        'tax_dashboard': {
            'name': 'Tax Dashboard',
            'icon': '📈',
            'category': 'Analytics',
            'page_class': TaxDashboardPage,
            'instance': None
        },
        'receipt_scanning': {
            'name': 'Receipt Scanning',
            'icon': '📸',
            'category': 'Tools',
            'page_class': ReceiptScanningPage,
            'instance': None
        },
        'client_portal': {
            'name': 'Client Portal',
            'icon': '👤',
            'category': 'Collaboration',
            'page_class': ClientPortalPage,
            'instance': None
        },
        'tax_interview': {
            'name': 'Tax Interview',
            'icon': '💬',
            'category': 'Interview',
            'page_class': TaxInterviewPage,
            'instance': None
        },
        'cloud_backup': {
            'name': 'Cloud Backup',
            '☁️',
            'category': 'Storage',
            'page_class': CloudBackupPage,
            'instance': None
        },
        'ptin_ero_management': {
            'name': 'PTIN & ERO Management',
            'icon': '🔐',
            'category': 'Compliance',
            'page_class': PTINEROManagementPage,
            'instance': None
        },
        'tax_analytics': {
            'name': 'Tax Analytics',
            'icon': '📊',
            'category': 'Analytics',
            'page_class': TaxAnalyticsPage,
            'instance': None
        },
        'settings_preferences': {
            'name': 'Settings & Preferences',
            'icon': '⚙️',
            'category': 'Configuration',
            'page_class': SettingsPreferencesPage,
            'instance': None
        },
        'help_documentation': {
            'name': 'Help & Documentation',
            'icon': '❓',
            'category': 'Help',
            'page_class': HelpDocumentationPage,
            'instance': None
        },
        
        # Phase 5: Management & Analysis (6 pages)
        'bank_account_linking': {
            'name': 'Bank Account Linking',
            'icon': '🏦',
            'category': 'Integration',
            'page_class': BankAccountLinkingPage,
            'instance': None
        },
        'e_filing': {
            'name': 'E-Filing',
            'icon': '📮',
            'category': 'Filing',
            'page_class': EFilingPage,
            'instance': None
        },
        'foreign_income_fbar': {
            'name': 'Foreign Income & FBAR',
            'icon': '🌍',
            'category': 'International',
            'page_class': ForeignIncomeFBARPage,
            'instance': None
        },
        'plugin_management': {
            'name': 'Plugin Management',
            'icon': '🔌',
            'category': 'Extensions',
            'page_class': PluginManagementPage,
            'instance': None
        },
        'tax_projections': {
            'name': 'Tax Projections',
            'icon': '🔮',
            'category': 'Planning',
            'page_class': TaxProjectionsPage,
            'instance': None
        },
        'translation_management': {
            'name': 'Translation Management',
            'icon': '🌐',
            'category': 'Localization',
            'page_class': TranslationManagementPage,
            'instance': None
        },
        'year_comparison': {
            'name': 'Year Comparison',
            'icon': '📊',
            'category': 'Analysis',
            'page_class': YearComparisonPage,
            'instance': None
        },
    }
    
    # Initialize page tracking
    self._current_page_key = None
    self._current_page = None


# ============================================================================
# PAGE CACHING & SWITCHING - Add methods to ModernMainWindow class
# ============================================================================

def _get_or_create_page(self, page_key: str):
    """
    Get or create a page instance using lazy loading.
    
    Args:
        page_key: Key of page in registry
        
    Returns:
        Page instance (CTkScrollableFrame)
    """
    if page_key not in self.pages_registry:
        raise ValueError(f"Unknown page: {page_key}")
    
    page_info = self.pages_registry[page_key]
    
    # Return cached instance if available
    if page_info['instance'] is not None:
        return page_info['instance']
    
    # Create new instance
    try:
        page_instance = page_info['page_class'](
            self.content_frame,
            config=self.config,
            tax_data=self.tax_data,
            accessibility_service=self.accessibility_service
        )
        
        # Cache the instance
        self.pages_registry[page_key]['instance'] = page_instance
        
        return page_instance
    except Exception as e:
        print(f"Error creating page {page_key}: {e}")
        raise


def _switch_to_page(self, page_key: str):
    """
    Switch the main content area to a different page.
    
    Args:
        page_key: Key of page to switch to
    """
    if page_key not in self.pages_registry:
        print(f"Unknown page: {page_key}")
        return
    
    # Hide current page
    if self._current_page is not None:
        self._current_page.pack_forget()
    
    # Get/create new page
    new_page = self._get_or_create_page(page_key)
    new_page.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Update tracking
    self._current_page = new_page
    self._current_page_key = page_key
    
    # Update status
    page_info = self.pages_registry[page_key]
    self._update_status_label(f"Now viewing: {page_info['name']}")


def _update_status_label(self, message: str):
    """Update the status bar label."""
    if self.status_label:
        self.status_label.configure(text=message)


# ============================================================================
# SIDEBAR ENHANCEMENT - Organize all 27 pages by category
# ============================================================================

def _setup_comprehensive_sidebar(self):
    """
    Setup the sidebar with all 27 pages organized by category.
    
    This replaces the current _setup_sidebar() method with a comprehensive
    version that includes all pages in organized sections.
    """
    # Create scrollable container
    sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
    sidebar_scroll.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Quick Actions Section
    self._create_sidebar_section(sidebar_scroll, "🚀 QUICK START", [
        ('Start Interview', '🚀', lambda: self._start_interview()),
        ('View Dashboard', '📊', lambda: self._switch_to_page('tax_dashboard')),
    ])
    
    # Tax Forms Section
    self._create_sidebar_section(sidebar_scroll, "📋 TAX FORMS", [
        ('Income', '💰', lambda: self._navigate_to_form({"form": "Income"})),
        ('Deductions', '📝', lambda: self._navigate_to_form({"form": "Deductions"})),
        ('Credits', '✅', lambda: self._navigate_to_form({"form": "Credits"})),
    ])
    
    # Financial Planning Section
    self._create_sidebar_section(sidebar_scroll, "💼 FINANCIAL PLANNING", [
        ('Estate & Trust', '👨‍👩‍👧‍👦', lambda: self._switch_to_page('estate_trust')),
        ('Partnership & S-Corp', '🏢', lambda: self._switch_to_page('partnership_s_corp')),
        ('Tax Planning', '💡', lambda: self._switch_to_page('tax_planning')),
        ('Tax Projections', '🔮', lambda: self._switch_to_page('tax_projections')),
    ])
    
    # Business Integration Section
    self._create_sidebar_section(sidebar_scroll, "📊 BUSINESS INTEGRATION", [
        ('QuickBooks', '📊', lambda: self._switch_to_page('quickbooks_integration')),
        ('Receipt Scanning', '📸', lambda: self._switch_to_page('receipt_scanning')),
        ('Bank Account Linking', '🏦', lambda: self._switch_to_page('bank_account_linking')),
    ])
    
    # Advanced Features Section
    self._create_sidebar_section(sidebar_scroll, "🤖 ADVANCED FEATURES", [
        ('AI Deduction Finder', '🤖', lambda: self._switch_to_page('ai_deduction_finder')),
        ('Cryptocurrency Tax', '₿', lambda: self._switch_to_page('cryptocurrency_tax')),
    ])
    
    # International Section
    self._create_sidebar_section(sidebar_scroll, "🌍 INTERNATIONAL", [
        ('Foreign Income & FBAR', '🌍', lambda: self._switch_to_page('foreign_income_fbar')),
        ('Translation Management', '🌐', lambda: self._switch_to_page('translation_management')),
    ])
    
    # Analysis & Reporting Section
    self._create_sidebar_section(sidebar_scroll, "📈 ANALYSIS & REPORTING", [
        ('Tax Analytics', '📊', lambda: self._switch_to_page('tax_analytics')),
        ('Year Comparison', '📊', lambda: self._switch_to_page('year_comparison')),
        ('Audit Trail', '📝', lambda: self._switch_to_page('audit_trail')),
    ])
    
    # Management Section
    self._create_sidebar_section(sidebar_scroll, "⚙️ MANAGEMENT", [
        ('Cloud Backup', '☁️', lambda: self._switch_to_page('cloud_backup')),
        ('Plugin Management', '🔌', lambda: self._switch_to_page('plugin_management')),
        ('Settings & Preferences', '⚙️', lambda: self._switch_to_page('settings_preferences')),
        ('Help & Documentation', '❓', lambda: self._switch_to_page('help_documentation')),
    ])
    
    # Filing Section
    self._create_sidebar_section(sidebar_scroll, "📮 FILING", [
        ('E-Filing', '📮', lambda: self._switch_to_page('e_filing')),
        ('PTIN & ERO Management', '🔐', lambda: self._switch_to_page('ptin_ero_management')),
    ])
    
    # Compliance Section
    self._create_sidebar_section(sidebar_scroll, "🔒 SECURITY & COMPLIANCE", [
        ('PTIN & ERO', '🔐', lambda: self._switch_to_page('ptin_ero_management')),
        ('Settings', '⚙️', lambda: self._switch_to_page('settings_preferences')),
    ])
    
    # Session Section
    self._create_sidebar_section(sidebar_scroll, "🔐 SESSION", [
        ('Logout', '🚪', lambda: self._logout()),
    ])


def _create_sidebar_section(self, parent, title: str, items: list):
    """
    Create a sidebar section with title and items.
    
    Args:
        parent: Parent widget
        title: Section title
        items: List of (label, icon, command) tuples
    """
    # Section header
    header = ModernLabel(
        parent,
        text=title,
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color="gray60"
    )
    header.pack(fill="x", padx=10, pady=(10, 5), anchor="w")
    
    # Items
    for label, icon, command in items:
        button = ModernButton(
            parent,
            text=f"{icon} {label}",
            command=command,
            button_type="secondary",
            height=32,
            accessibility_service=self.accessibility_service
        )
        button.pack(fill="x", padx=5, pady=2)
    
    # Separator
    self._create_separator(parent)


# ============================================================================
# SUMMARY
# ============================================================================
"""
Phase 6 Implementation Steps:

1. Add all import statements to modern_main_window.py (lines 45-78)

2. In ModernMainWindow.__init__(), after _setup_ui() call, add:
   self._initialize_page_registry()

3. Add these methods to ModernMainWindow class:
   - _get_or_create_page()
   - _switch_to_page()
   - _update_status_label()
   - _setup_comprehensive_sidebar()
   - _create_sidebar_section()

4. Replace the _setup_sidebar() method with _setup_comprehensive_sidebar()

5. Update _setup_ui() to use _setup_comprehensive_sidebar() instead of _setup_sidebar()

6. Test all 27 pages to ensure:
   - Pages load without errors
   - Data flows correctly
   - Services integrate properly
   - Navigation works smoothly
   - No popup dialogs appear

7. Compile and verify:
   - No syntax errors
   - All imports work
   - Application starts correctly
   - All pages accessible from sidebar

Total Time Estimate: 2-3 hours
Phases Complete: 1-5 (100% window conversion)
Phase 6 Progress: Integration in progress
"""
