"""
Tax Projections Page

Provides tax forecasting and year-end tax planning capabilities
with multiple scenarios and projections.

Features:
- Multi-year tax projections
- Scenario-based planning
- Tax liability forecasts
- Estimated payment planning
- Tax optimization recommendations
"""

import customtkinter as ctk
from typing import Optional, Any


class ModernButton(ctk.CTkButton):
    """Custom button with type variants."""
    def __init__(self, *args, button_type: str = "primary", **kwargs):
        colors = {
            "primary": ("#0066CC", "#0052A3"),
            "secondary": ("#666666", "#4D4D4D"),
            "success": ("#28A745", "#1E8449"),
            "danger": ("#DC3545", "#C82333"),
        }
        fg_color, hover_color = colors.get(button_type, colors["primary"])
        kwargs.update({"fg_color": fg_color, "hover_color": hover_color, "text_color": "white"})
        super().__init__(*args, **kwargs)


class ModernFrame(ctk.CTkFrame):
    """Custom frame with consistent styling."""
    pass


class ModernLabel(ctk.CTkLabel):
    """Custom label with consistent styling."""
    pass


class TaxProjectionsPage(ctk.CTkScrollableFrame):
    """Tax Projections Page - Multi-year tax forecasting and planning."""
    
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
        
        title_label = ModernLabel(
            header_frame,
            text="📊 Tax Projections & Planning",
            font=("Segoe UI", 24, "bold"),
            text_color="#FFFFFF"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = ModernLabel(
            header_frame,
            text="Project tax liability and plan year-end tax strategies",
            font=("Segoe UI", 12),
            text_color="#A0A0A0"
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
    
    def _create_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar_frame = ModernFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(0, 10))
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        button_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="w")
        
        new_scenario_btn = ModernButton(
            button_frame,
            text="+ New Scenario",
            button_type="primary",
            width=140,
            height=36,
            command=self._action_new_scenario
        )
        new_scenario_btn.grid(row=0, column=0, padx=(0, 10))
        
        calculate_btn = ModernButton(
            button_frame,
            text="📈 Calculate",
            button_type="success",
            width=120,
            height=36,
            command=self._action_calculate
        )
        calculate_btn.grid(row=0, column=1, padx=5)
        
        progress_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        progress_frame.grid(row=0, column=1, sticky="e")
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=200, height=8, progress_color="#28A745")
        self.progress_bar.grid(row=0, column=0, sticky="e")
        self.progress_bar.set(0.72)
        
        self.status_label = ModernLabel(progress_frame, text="3 projections created", font=("Segoe UI", 10), text_color="#A0A0A0")
        self.status_label.grid(row=1, column=0, sticky="e", pady=(5, 0))
    
    def _create_main_content(self):
        """Create tabbed interface."""
        content_frame = ModernFrame(self, fg_color="#2B2B2B")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
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
        
        self.tabview.add("Scenarios")
        self.tabview.add("2024 Projection")
        self.tabview.add("2025 Projection")
        self.tabview.add("Recommendations")
        self.tabview.add("Comparison")
        
        self._setup_scenarios_tab()
        self._setup_2024_projection_tab()
        self._setup_2025_projection_tab()
        self._setup_recommendations_tab()
        self._setup_comparison_tab()
    
    def _setup_scenarios_tab(self):
        """Setup Scenarios tab."""
        tab = self.tabview.tab("Scenarios")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(tab, text="Manage tax projection scenarios", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        scenarios_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        scenarios_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        scenarios_frame.grid_columnconfigure(0, weight=1)
        scenarios_frame.grid_rowconfigure(0, weight=1)
        
        scenarios_scroll = ctk.CTkScrollableFrame(scenarios_frame, fg_color="#2B2B2B")
        scenarios_scroll.grid(row=0, column=0, sticky="nsew")
        scenarios_scroll.grid_columnconfigure(0, weight=1)
        
        scenarios = [("Conservative", "Lowest income estimate", "$125,000"),
                    ("Moderate", "Expected income", "$185,000"),
                    ("Aggressive", "Highest income potential", "$245,000")]
        
        for scenario, desc, amount in scenarios:
            scenario_frame = ctk.CTkFrame(scenarios_scroll, fg_color="#1E1E1E", height=60)
            scenario_frame.pack(fill="x", pady=5)
            scenario_frame.grid_columnconfigure(1, weight=1)
            
            scenario_label = ModernLabel(scenario_frame, text=scenario, font=("Segoe UI", 11, "bold"))
            scenario_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            desc_label_item = ModernLabel(scenario_frame, text=desc, font=("Segoe UI", 10), text_color="#A0A0A0")
            desc_label_item.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
            
            amount_label = ModernLabel(scenario_frame, text=amount, font=("Segoe UI", 11, "bold"), text_color="#2196F3")
            amount_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _setup_2024_projection_tab(self):
        """Setup 2024 Projection tab."""
        tab = self.tabview.tab("2024 Projection")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="2024 Tax Year Projections", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        projection_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        projection_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        projection_frame.grid_columnconfigure(1, weight=1)
        
        metrics = [("Projected Income", "$185,000"),
                  ("Estimated Tax Liability", "$42,500"),
                  ("Estimated Payments Made", "$38,000"),
                  ("Estimated Balance Due", "$4,500"),
                  ("Next Estimated Payment", "01/15/2025")]
        
        for label_text, value in metrics:
            label = ModernLabel(projection_frame, text=label_text + ":", font=("Segoe UI", 11))
            label.grid(sticky="w", padx=15, pady=8)
            
            value_label = ModernLabel(projection_frame, text=value, font=("Segoe UI", 12, "bold"), text_color="#2196F3")
            value_label.grid(sticky="e", padx=15, pady=8)
    
    def _setup_2025_projection_tab(self):
        """Setup 2025 Projection tab."""
        tab = self.tabview.tab("2025 Projection")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="2025 Tax Year Projections (Early Estimate)", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        projection_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        projection_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        projection_frame.grid_columnconfigure(1, weight=1)
        
        metrics = [("Projected Income", "$195,000 (based on YTD)"),
                  ("Estimated Tax Liability", "$45,200"),
                  ("Recommended Est. Payments", "$11,300/quarter"),
                  ("First Payment Due", "04/15/2025")]
        
        for label_text, value in metrics:
            label = ModernLabel(projection_frame, text=label_text + ":", font=("Segoe UI", 11))
            label.grid(sticky="w", padx=15, pady=8)
            
            value_label = ModernLabel(projection_frame, text=value, font=("Segoe UI", 12, "bold"), text_color="#4CAF50")
            value_label.grid(sticky="e", padx=15, pady=8)
    
    def _setup_recommendations_tab(self):
        """Setup Recommendations tab."""
        tab = self.tabview.tab("Recommendations")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        desc_label = ModernLabel(tab, text="Tax optimization recommendations", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        recs_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        recs_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        recs_frame.grid_columnconfigure(0, weight=1)
        recs_frame.grid_rowconfigure(0, weight=1)
        
        recs_scroll = ctk.CTkScrollableFrame(recs_frame, fg_color="#2B2B2B")
        recs_scroll.grid(row=0, column=0, sticky="nsew")
        recs_scroll.grid_columnconfigure(0, weight=1)
        
        recs = [("Increase 401(k) contributions", "Potential savings: $2,400"),
               ("Accelerate charitable donations", "Potential savings: $1,800"),
               ("Review home office deduction", "Potential savings: $1,200")]
        
        for rec, savings in recs:
            rec_frame = ctk.CTkFrame(recs_scroll, fg_color="#1E1E1E", height=50)
            rec_frame.pack(fill="x", pady=5)
            rec_frame.grid_columnconfigure(1, weight=1)
            
            rec_label = ModernLabel(rec_frame, text=rec, font=("Segoe UI", 11))
            rec_label.grid(row=0, column=0, sticky="w", padx=10, pady=8)
            
            savings_label = ModernLabel(rec_frame, text=savings, font=("Segoe UI", 11, "bold"), text_color="#28A745")
            savings_label.grid(row=0, column=1, sticky="e", padx=10, pady=8)
    
    def _setup_comparison_tab(self):
        """Setup Comparison tab."""
        tab = self.tabview.tab("Comparison")
        tab.grid_columnconfigure(0, weight=1)
        
        desc_label = ModernLabel(tab, text="Compare scenarios and projections", font=("Segoe UI", 11), text_color="#A0A0A0")
        desc_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))
        
        comparison_frame = ctk.CTkFrame(tab, fg_color="#1E1E1E")
        comparison_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        comparison_frame.grid_columnconfigure(0, weight=1)
        
        # Comparison table
        comp_label = ModernLabel(comparison_frame, text="Scenario Comparison Summary", font=("Segoe UI", 11, "bold"))
        comp_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        comp_text = ctk.CTkTextbox(comparison_frame, text_color="#FFFFFF", fg_color="#2B2B2B", height=150)
        comp_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        comp_content = """Scenario Comparison (2024):
        
Conservative: $125,000 income → $24,500 tax liability
Moderate: $185,000 income → $42,500 tax liability
Aggressive: $245,000 income → $58,000 tax liability

Recommendation: Plan for Moderate scenario
Estimated Q1 2025 Payment: $11,300"""
        
        comp_text.insert("0.0", comp_content)
        comp_text.configure(state="disabled")
    
    def _action_new_scenario(self):
        """Action: Create new scenario."""
        print("[Tax Projections] New scenario creation initiated")
    
    def _action_calculate(self):
        """Action: Calculate projections."""
        print("[Tax Projections] Calculation initiated")
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Calculation complete")
