"""
Freedom US Tax Return - Free Tax Return Assistance Application
Main application entry point

Tax Year: 2025 (Returns filed in 2026)
"""

import tkinter as tk
from tkinter import ttk
from gui.main_window import MainWindow

def main():
    """Initialize and run the application"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
