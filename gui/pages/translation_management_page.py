"""
Translation Management Page

Provides multi-language support and translation management
for global tax return preparation.

Features:
- Language selection and switching
- Translation management
- Localization settings
- Export translations
- RTL language support
"""

import customtkinter as ctk
from typing import Optional, Any


class ModernButton(ctk.CTkButton):
    """Custom button with type variants."""
    def __init__(self, *args, button_type: str = "primary", **kwargs):
        colors = {"primary": ("#0066CC", "#0052A3"), "secondary": ("#666666", "#4D4D4D"),
                 "success": ("#28A745", "#1E8449"), "danger": ("#DC3545", "#C82333")}
        fg_color, hover_color = colors.get(button_type, colors["primary"])
        kwargs.update({"fg_color": fg_color, "hover_color": hover_color, "text_color": "white"})
        super().__init__(*args, **kwargs)


class ModernFrame(ctk.CTkFrame):
    """Custom frame with consistent styling."""
    pass


class ModernLabel(ctk.CTkLabel):
    """Custom label with consistent styling."""
    pass


class TranslationManagementPage(ctk.CTkScrollableFrame):
    """Translation Management Page - Multi-language support."""
    
    def __init__(
        self,
        master,
        config: Optional[Any] = None,
        tax_data: Optional[Any] = None,
        accessibility_service: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.config = config
        self.tax_data = tax_data
        self.accessibility_service = accessibility_service
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_header()
        self._create_toolbar()
        self._create_main_content()
    
    def _create_header(self):
        """Create page header."""
        header_frame = ModernFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ModernLabel(header_frame, text="🌐 Translation Management", font=("Segoe UI", 24, "bold"), text_color="#FFFFFF")
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = ModernLabel(header_frame, text="Manage multi-language support and localization", font=("Segoe UI", 12), text_color="#A0A0A0")
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
    
    def _create_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar_frame = ModernFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(0, 10))
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        button_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="w")
        
        add_lang_btn = ModernButton(button_frame, text="+ Add Language", button_type="primary", width=140, height=36,
                                   command=self._action_add_language)
        add_lang_btn.grid(row=0, column=0, padx=(0, 10))
        
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.grid(row=0, column=1, sticky="e")
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=200, height=8, progress_color="#28A745")
        self.progress_bar.grid(row=0, column=0, sticky="e")
        self.progress_bar.set(0.88)
        
        self.status_label = ModernLabel(progress_frame, text="12 languages enabled", font=("Segoe UI", 10), text_color="#A0A0A0")
        self.status_label.grid(row=1, column=0, sticky="e", pady=(5, 0))
    
    def _create_main_content(self):
        """Create tabbed interface."""
        content_frame = ModernFrame(self, fg_color="#2B2B2B")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(content_frame, text_color="#FFFFFF", segmented_button_fg_color="#1E1E1E",
                                      segmented_button_selected_color="#0066CC", fg_color="#2B2B2B")
        self.tabview.grid(row=0, column=0, sticky="nsew")
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)
        
        self.tabview.add("Languages")
        self.tabview.add("Active Language")
        self.tabview.add("Translation Files")
        self.tabview.add("Export/Import")
        self.tabview.add("Settings")
        
        self._setup_languages_tab()
        self._setup_active_language_tab()
        self._setup_translation_files_tab()
        self._setup_export_import_tab()
        self._setup_settings_tab()
    
    def _setup_languages_tab(self):
        """Setup Languages tab."""
        tab = self.tabview.tab("Languages")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(tab, text="Manage available languages", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        lang_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        lang_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        lang_frame.grid_columnconfigure(0, weight=1)
        lang_frame.grid_rowconfigure(0, weight=1)
        
        lang_scroll = ctk.CTkScrollableFrame(lang_frame, fg_color="#2B2B2B")
        lang_scroll.grid(row=0, column=0, sticky="nsew")
        lang_scroll.grid_columnconfigure(0, weight=1)
        
        languages = [("English", "✓ Default", "100%"),
                    ("Spanish", "✓ Active", "98%"),
                    ("French", "✓ Active", "95%"),
                    ("German", "✓ Installed", "92%"),
                    ("Chinese (Simplified)", "⚠ Beta", "78%")]
        
        for lang, status, coverage in languages:
            lang_item = ctk.CTkFrame(lang_scroll, fg_color="#1E1E1E", height=50)
            lang_item.pack(fill="x", pady=5)
            lang_item.grid_columnconfigure(1, weight=1)
            
            lang_label = ModernLabel(lang_item, text=lang, font=("Segoe UI", 11, "bold"))
            lang_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            status_label = ModernLabel(lang_item, text=status, font=("Segoe UI", 10), text_color="#A0A0A0")
            status_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            
            coverage_label = ModernLabel(lang_item, text=coverage, font=("Segoe UI", 10, "bold"), text_color="#28A745")
            coverage_label.grid(row=0, column=2, sticky="e", padx=10, pady=5)
    
    def _setup_active_language_tab(self):
        """Setup Active Language tab."""
        tab = self.tabview.tab("Active Language")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="Select and switch interface language", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        active_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        active_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        active_frame.grid_columnconfigure(1, weight=1)
        
        lang_label = ModernLabel(active_frame, text="Current Language:", font=("Segoe UI", 11))
        lang_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        lang_combo = ctk.CTkComboBox(active_frame, values=["English", "Spanish", "French", "German"],
                                    fg_color="#2B2B2B", button_color="#0066CC", text_color="#FFFFFF", state="readonly")
        lang_combo.grid(row=0, column=1, sticky="ew", padx=15, pady=10)
        lang_combo.set("English")
    
    def _setup_translation_files_tab(self):
        """Setup Translation Files tab."""
        tab = self.tabview.tab("Translation Files")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(tab, text="Manage translation files", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        files_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        files_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        files_frame.grid_columnconfigure(0, weight=1)
        files_frame.grid_rowconfigure(0, weight=1)
        
        files_text = ctk.CTkTextbox(files_frame, text_color="#FFFFFF", fg_color="#2B2B2B")
        files_text.grid(row=0, column=0, sticky="nsew")
        
        files_content = """Translation Files:
en_US.json (English - US) - 4.2 MB
es_ES.json (Spanish) - 4.1 MB
fr_FR.json (French) - 4.0 MB
de_DE.json (German) - 3.9 MB
zh_CN.json (Chinese - Simplified) - 3.5 MB
ja_JP.json (Japanese) - 3.8 MB
pt_BR.json (Portuguese - Brazil) - 3.7 MB
ru_RU.json (Russian) - 3.6 MB"""
        
        files_text.insert("0.0", files_content)
        files_text.configure(state="disabled")
    
    def _setup_export_import_tab(self):
        """Setup Export/Import tab."""
        tab = self.tabview.tab("Export/Import")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="Export or import translation files", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        ei_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        ei_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        ei_frame.grid_columnconfigure(0, weight=1)
        
        ModernButton(ei_frame, text="📥 Import Translations", button_type="primary", width=160, height=36,
                    command=self._action_import_translations).pack(pady=10)
        
        ModernButton(ei_frame, text="📤 Export Translations", button_type="success", width=160, height=36,
                    command=self._action_export_translations).pack(pady=10)
    
    def _setup_settings_tab(self):
        """Setup Settings tab."""
        tab = self.tabview.tab("Settings")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="Configure translation preferences", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        settings_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        settings_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        auto_detect_label = ModernLabel(settings_frame, text="Auto-Detect Language:", font=("Segoe UI", 11))
        auto_detect_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        auto_detect_switch = ctk.CTkSwitch(settings_frame, text="", fg_color="#0066CC")
        auto_detect_switch.grid(row=0, column=1, sticky="e", padx=15, pady=10)
        auto_detect_switch.select()
    
    def _action_add_language(self):
        """Action: Add new language."""
        print("[Translation Management] Add language initiated")
    
    def _action_import_translations(self):
        """Action: Import translations."""
        print("[Translation Management] Import translations initiated")
    
    def _action_export_translations(self):
        """Action: Export translations."""
        print("[Translation Management] Export translations initiated")
