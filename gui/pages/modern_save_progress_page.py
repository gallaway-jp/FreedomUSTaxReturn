"""
Modern Save Progress Page - Save and load tax return progress

Provides an interface to save current progress and manage saved returns.
"""

import customtkinter as ctk
from typing import Optional, Callable
import tkinter as tk
from datetime import datetime
import os

from models.tax_data import TaxData
from gui.modern_ui_components import (
    ModernFrame, ModernLabel, ModernButton,
    show_info_message, show_error_message
)


class ModernSaveProgressPage(ctk.CTkScrollableFrame):
    """
    Modern save progress page for managing tax return progress.

    Features:
    - Save current progress with timestamp
    - View saved progress files
    - Load previous progress
    - Delete saved progress files
    """

    def __init__(
        self,
        parent,
        tax_data: Optional[TaxData] = None,
        on_progress_saved: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the save progress page.

        Args:
            parent: Parent widget
            tax_data: Current tax data to save
            on_progress_saved: Callback when progress is saved
        """
        super().__init__(parent, **kwargs)

        self.tax_data = tax_data
        self.on_progress_saved = on_progress_saved

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create UI
        self._create_header()
        self._create_save_section()
        self._create_saved_files_section()

    def _create_header(self):
        """Create the header section"""
        header_frame = ModernFrame(self)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ModernLabel(
            header_frame,
            text="💾 Save Progress",
            font=ctk.CTkFont(size=18)
        )
        title_label.pack(anchor="w")

        subtitle_label = ModernLabel(
            header_frame,
            text="Save your current tax return progress and manage saved files",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _create_save_section(self):
        """Create the save current progress section"""
        save_frame = ModernFrame(self)
        save_frame.pack(fill="x", padx=20, pady=10)

        save_title = ModernLabel(
            save_frame,
            text="📝 Current Progress",
            font=ctk.CTkFont(size=12)
        )
        save_title.pack(anchor="w", pady=(0, 10))

        # Status info
        if self.tax_data:
            try:
                first_name = self.tax_data.get('personal_info.first_name', 'Unknown')
                last_name = self.tax_data.get('personal_info.last_name', 'Unknown')
                tax_year = self.tax_data.get_current_year() if hasattr(self.tax_data, 'get_current_year') else 2026

                status_text = f"Tax Year: {tax_year} | Taxpayer: {first_name} {last_name}"
            except:
                status_text = "Tax return data is loaded"
        else:
            status_text = "No tax return data loaded - Please start the tax interview first"

        status_label = ModernLabel(
            save_frame,
            text=status_text,
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        status_label.pack(anchor="w", pady=(0, 15))

        # Save button
        info_frame = ctk.CTkFrame(save_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))

        info_text = (
            "Your progress will be saved to an encrypted file with a timestamp. "
            "You can load this file later to continue where you left off."
        )
        info_label = ModernLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        info_label.pack(anchor="w")

        button_frame = ctk.CTkFrame(save_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        ModernButton(
            button_frame,
            text="💾 Save Progress Now",
            command=self._save_current_progress,
            height=40,
            width=200
        ).pack(side="left")

    def _save_current_progress(self):
        """Save the current tax data"""
        if not self.tax_data:
            show_error_message("No Data", "Please start the tax interview first before saving progress.")
            return

        try:
            # Generate progress filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tax_year = self.tax_data.get_current_year() if hasattr(self.tax_data, 'get_current_year') else 2026
            filename = f"progress_{tax_year}_{timestamp}.enc"

            # Save the tax data
            saved_path = self.tax_data.save_to_file(filename)

            show_info_message(
                "Progress Saved",
                f"Your tax return progress has been saved successfully!\n\n"
                f"File: {os.path.basename(saved_path)}\n"
                f"Location: {os.path.dirname(saved_path)}\n\n"
                f"You can load this file later to continue where you left off."
            )

            # Trigger callback if provided
            if self.on_progress_saved:
                self.on_progress_saved()

            # Refresh saved files list
            self._load_saved_files()

        except Exception as e:
            show_error_message(
                "Save Failed",
                f"Failed to save progress: {str(e)}\n\n"
                f"Please check that you have write permissions and sufficient disk space."
            )

    def _create_saved_files_section(self):
        """Create the saved files section"""
        files_frame = ModernFrame(self)
        files_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        files_title = ModernLabel(
            files_frame,
            text="📋 Previously Saved Returns",
            font=ctk.CTkFont(size=12)
        )
        files_title.pack(anchor="w", pady=(0, 10))

        # Create a frame for the saved files list
        self.saved_files_content = ctk.CTkFrame(files_frame, fg_color="transparent")
        self.saved_files_content.pack(fill="both", expand=True)

        # Load and display saved files
        self._load_saved_files()

    def _load_saved_files(self):
        """Load and display saved progress files"""
        # Clear existing content
        for widget in self.saved_files_content.winfo_children():
            widget.destroy()

        try:
            # Get saved files from tax data if method exists
            if self.tax_data and hasattr(self.tax_data, 'get_saved_files'):
                saved_files = self.tax_data.get_saved_files()
            else:
                # Default: look in home directory or config path
                import pathlib
                home = pathlib.Path.home()
                saved_files = list(home.glob("progress_*.enc"))

            if not saved_files:
                no_files_label = ModernLabel(
                    self.saved_files_content,
                    text="No previously saved returns found",
                    font=ctk.CTkFont(size=11),
                    text_color="gray60"
                )
                no_files_label.pack(anchor="w", pady=20)
                return

            # Display each saved file
            for i, file_path in enumerate(sorted(saved_files, reverse=True)[:10]):  # Show last 10
                file_name = os.path.basename(str(file_path))
                file_time = os.path.getmtime(str(file_path))
                file_date = datetime.fromtimestamp(file_time).strftime("%Y-%m-%d %H:%M:%S")

                # Create a frame for this file
                file_item_frame = ctk.CTkFrame(self.saved_files_content, fg_color="gray17")
                file_item_frame.pack(fill="x", pady=5, padx=0)

                # File info
                info_frame = ctk.CTkFrame(file_item_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=10, pady=8, side="left", expand=True)

                file_label = ModernLabel(
                    info_frame,
                    text=file_name,
                    font=ctk.CTkFont(size=11)
                )
                file_label.pack(anchor="w")

                date_label = ModernLabel(
                    info_frame,
                    text=f"Saved: {file_date}",
                    font=ctk.CTkFont(size=10),
                    text_color="gray60"
                )
                date_label.pack(anchor="w")

                # Action buttons
                button_frame = ctk.CTkFrame(file_item_frame, fg_color="transparent")
                button_frame.pack(fill="y", padx=10, pady=8, side="right")

                ModernButton(
                    button_frame,
                    text="Load",
                    command=lambda f=file_path: self._load_file(f),
                    height=32,
                    width=80
                ).pack(side="left", padx=(0, 5))

                ModernButton(
                    button_frame,
                    text="Delete",
                    command=lambda f=file_path: self._delete_file(f),
                    height=32,
                    width=80,
                    button_type="secondary"
                ).pack(side="left")

        except Exception as e:
            error_label = ModernLabel(
                self.saved_files_content,
                text=f"Error loading saved files: {str(e)}",
                font=ctk.CTkFont(size=11),
                text_color="red"
            )
            error_label.pack(anchor="w", pady=20)

    def _load_file(self, file_path):
        """Load a saved progress file"""
        try:
            if self.tax_data and hasattr(self.tax_data, 'load_from_file'):
                self.tax_data.load_from_file(str(file_path))
                show_info_message("Progress Loaded", f"Tax return loaded from:\n{os.path.basename(str(file_path))}")
            else:
                show_info_message("Load Progress", f"Would load: {os.path.basename(str(file_path))}")
        except Exception as e:
            show_error_message("Load Failed", f"Failed to load progress: {str(e)}")

    def _delete_file(self, file_path):
        """Delete a saved progress file"""
        try:
            os.remove(str(file_path))
            self._load_saved_files()
            show_info_message("File Deleted", f"Deleted: {os.path.basename(str(file_path))}")
        except Exception as e:
            show_error_message("Delete Failed", f"Failed to delete file: {str(e)}")
