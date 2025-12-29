"""
Form field widget - reusable labeled entry field
"""

import tkinter as tk
from tkinter import ttk

class FormField(ttk.Frame):
    """Labeled entry field widget"""
    
    def __init__(self, parent, label_text, initial_value="", width=None):
        super().__init__(parent)
        
        self.label_text = label_text
        
        # Label
        self.label = ttk.Label(self, text=label_text)
        self.label.pack(anchor="w", pady=(0, 3))
        
        # Entry
        self.entry = ttk.Entry(self, width=width)
        self.entry.pack(fill="x")
        
        if initial_value:
            self.entry.insert(0, str(initial_value))
    
    def get(self):
        """Get the current value"""
        return self.entry.get()
    
    def set(self, value):
        """Set the value"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))
    
    def clear(self):
        """Clear the field"""
        self.entry.delete(0, tk.END)
