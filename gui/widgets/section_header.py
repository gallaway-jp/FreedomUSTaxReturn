"""
Section header widget - styled section separator
"""

from tkinter import ttk

class SectionHeader(ttk.Frame):
    """Section header with horizontal line"""
    
    def __init__(self, parent, text):
        super().__init__(parent)
        
        # Header label
        label = ttk.Label(
            self,
            text=text,
            font=("Arial", 12, "bold"),
            foreground="#2c3e50"
        )
        label.pack(side="left", pady=(0, 5))
        
        # Horizontal line
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(side="left", fill="x", expand=True, padx=(10, 0))
