"""
Year Comparison Page

Provides year-over-year tax return comparison and analysis
for understanding changes and trends.

Features:
- Multi-year return comparison
- Item-by-item analysis
- Variance analysis
- Trend visualization
- Change summary reports
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


class YearComparisonPage(ctk.CTkScrollableFrame):
    """Year Comparison Page - Multi-year tax return analysis."""
    
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
        
        title_label = ModernLabel(header_frame, text="📈 Year-Over-Year Comparison", font=("Segoe UI", 24, "bold"), text_color="#FFFFFF")
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = ModernLabel(header_frame, text="Compare tax returns across multiple years", font=("Segoe UI", 12), text_color="#A0A0A0")
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
    
    def _create_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar_frame = ModernFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(0, 10))
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        button_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="w")
        
        compare_btn = ModernButton(button_frame, text="📊 Generate Comparison", button_type="success", width=180, height=36,
                                  command=self._action_generate_comparison)
        compare_btn.grid(row=0, column=0, padx=(0, 10))
        
        export_btn = ModernButton(button_frame, text="📤 Export Report", button_type="secondary", width=140, height=36,
                                 command=self._action_export_report)
        export_btn.grid(row=0, column=1, padx=5)
        
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.grid(row=0, column=1, sticky="e")
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=200, height=8, progress_color="#28A745")
        self.progress_bar.grid(row=0, column=0, sticky="e")
        self.progress_bar.set(0.92)
        
        self.status_label = ModernLabel(progress_frame, text="4 years available for comparison", font=("Segoe UI", 10), text_color="#A0A0A0")
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
        
        self.tabview.add("2024 vs 2023")
        self.tabview.add("3-Year Trend")
        self.tabview.add("5-Year Summary")
        self.tabview.add("Item Analysis")
        self.tabview.add("Variance Report")
        
        self._setup_2024_vs_2023_tab()
        self._setup_3_year_trend_tab()
        self._setup_5_year_summary_tab()
        self._setup_item_analysis_tab()
        self._setup_variance_report_tab()
    
    def _setup_2024_vs_2023_tab(self):
        """Setup 2024 vs 2023 tab."""
        tab = self.tabview.tab("2024 vs 2023")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="Direct comparison of 2024 and 2023 returns", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        comparison_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        comparison_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        comparison_frame.grid_columnconfigure(0, weight=1)
        
        metrics = [("Total Income", "$185,000", "$165,000", "+$20,000 (+12.1%)"),
                  ("Deductions", "$52,000", "$48,500", "+$3,500 (+7.2%)"),
                  ("Taxable Income", "$133,000", "$116,500", "+$16,500 (+14.2%)"),
                  ("Tax Liability", "$27,850", "$24,465", "+$3,385 (+13.8%)")]
        
        for item, val2024, val2023, change in metrics:
            item_frame = ctk.CTkFrame(comparison_frame, fg_color="#2B2B2B", height=50)
            item_frame.pack(fill="x", pady=5)
            item_frame.grid_columnconfigure(1, weight=1)
            
            item_label = ModernLabel(item_frame, text=item, font=("Segoe UI", 11, "bold"))
            item_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            val_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            val_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            
            val2024_label = ModernLabel(val_frame, text=f"2024: {val2024}", font=("Segoe UI", 10), text_color="#2196F3")
            val2024_label.pack(side="left", padx=10)
            
            val2023_label = ModernLabel(val_frame, text=f"2023: {val2023}", font=("Segoe UI", 10), text_color="#A0A0A0")
            val2023_label.pack(side="left", padx=10)
            
            change_label = ModernLabel(item_frame, text=change, font=("Segoe UI", 10, "bold"), text_color="#FF9800")
            change_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0, 5))
    
    def _setup_3_year_trend_tab(self):
        """Setup 3-Year Trend tab."""
        tab = self.tabview.tab("3-Year Trend")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="Three-year trend analysis", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        trend_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        trend_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        trend_frame.grid_columnconfigure(1, weight=1)
        
        years = [("2024", "$185,000", "$27,850", "14.9%"),
                ("2023", "$165,000", "$24,465", "14.8%"),
                ("2022", "$142,000", "$20,158", "14.2%")]
        
        for year, income, tax, rate in years:
            year_frame = ctk.CTkFrame(trend_frame, fg_color="#2B2B2B", height=50)
            year_frame.pack(fill="x", pady=5)
            year_frame.grid_columnconfigure(1, weight=1)
            
            year_label = ModernLabel(year_frame, text=year, font=("Segoe UI", 11, "bold"))
            year_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            income_label = ModernLabel(year_frame, text=f"Income: {income}", font=("Segoe UI", 10), text_color="#2196F3")
            income_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            
            tax_label = ModernLabel(year_frame, text=f"Tax: {tax} ({rate})", font=("Segoe UI", 10), text_color="#FF9800")
            tax_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0, 5))
    
    def _setup_5_year_summary_tab(self):
        """Setup 5-Year Summary tab."""
        tab = self.tabview.tab("5-Year Summary")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(tab, text="Five-year summary and averages", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        summary_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        summary_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_rowconfigure(0, weight=1)
        
        summary_text = ctk.CTkTextbox(summary_frame, text_color="#FFFFFF", fg_color="#2B2B2B")
        summary_text.grid(row=0, column=0, sticky="nsew")
        
        summary_content = """5-Year Summary (2020-2024):

Total Income: $752,000 (Average: $150,400)
Average Tax: $24,768 (Average Rate: 14.7%)

Year-by-Year:
2024: $185,000 (+12.1% from prior year)
2023: $165,000 (-16.2% from prior year)
2022: $142,000 (-5.3% from prior year)
2021: $150,000 (+8.7% from prior year)
2020: $138,000 (Baseline)

Growth Trend: +34.1% over 5 years
Average Annual Growth: 6.1%"""
        
        summary_text.insert("0.0", summary_content)
        summary_text.configure(state="disabled")
    
    def _setup_item_analysis_tab(self):
        """Setup Item Analysis tab."""
        tab = self.tabview.tab("Item Analysis")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(tab, text="Item-by-item variance analysis", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        items_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        items_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        items_frame.grid_columnconfigure(0, weight=1)
        items_frame.grid_rowconfigure(0, weight=1)
        
        items_scroll = ctk.CTkScrollableFrame(items_frame, fg_color="#2B2B2B")
        items_scroll.grid(row=0, column=0, sticky="nsew")
        items_scroll.grid_columnconfigure(0, weight=1)
        
        items = [("W-2 Wages", "$150,000", "$135,000", "+$15,000"),
                ("Interest Income", "$8,500", "$7,200", "+$1,300"),
                ("Dividend Income", "$12,000", "$14,500", "-$2,500"),
                ("Business Income", "$14,500", "$8,300", "+$6,200")]
        
        for item, amount2024, amount2023, variance in items:
            item_frame = ctk.CTkFrame(items_scroll, fg_color="#1E1E1E", height=50)
            item_frame.pack(fill="x", pady=5)
            item_frame.grid_columnconfigure(1, weight=1)
            
            item_label = ModernLabel(item_frame, text=item, font=("Segoe UI", 11))
            item_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            variance_label = ModernLabel(item_frame, text=variance, font=("Segoe UI", 11, "bold"), text_color="#FF9800")
            variance_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _setup_variance_report_tab(self):
        """Setup Variance Report tab."""
        tab = self.tabview.tab("Variance Report")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="Detailed variance report", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        report_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        report_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        report_frame.grid_columnconfigure(1, weight=1)
        
        variances = [("Income Increase", "+$20,000", "+12.1%"),
                    ("Deduction Increase", "+$3,500", "+7.2%"),
                    ("Tax Increase", "+$3,385", "+13.8%")]
        
        for item, amount, percent in variances:
            var_frame = ctk.CTkFrame(report_frame, fg_color="#2B2B2B", height=50)
            var_frame.pack(fill="x", pady=5)
            var_frame.grid_columnconfigure(1, weight=1)
            
            item_label = ModernLabel(var_frame, text=item, font=("Segoe UI", 11, "bold"))
            item_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            amount_label = ModernLabel(var_frame, text=amount, font=("Segoe UI", 11, "bold"), text_color="#28A745")
            amount_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            
            percent_label = ModernLabel(var_frame, text=percent, font=("Segoe UI", 10), text_color="#FF9800")
            percent_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0, 5))
    
    def _action_generate_comparison(self):
        """Action: Generate comparison report."""
        print("[Year Comparison] Generate comparison initiated")
        self.progress_bar.set(1.0)
    
    def _action_export_report(self):
        """Action: Export comparison report."""
        print("[Year Comparison] Export report initiated")
