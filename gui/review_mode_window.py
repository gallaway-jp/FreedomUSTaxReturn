"""
Review Mode Window - GUI for reviewing tax returns in collaboration

This window provides:
- Read-only view of tax return data
- Comment integration for each field
- Approval/rejection workflow
- Change tracking and highlighting
- Review summary and status
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from services.collaboration_service import CollaborationService, CollaborationRole, AccessLevel, ReviewStatus
from models.tax_data import TaxData
from gui.widgets.comments_widget import CommentsWidget

logger = logging.getLogger(__name__)


class ReviewModeWindow(tk.Toplevel):
    """
    Window for reviewing tax returns in collaboration mode.

    Provides read-only access with commenting and approval capabilities.
    """

    def __init__(self, parent, collaboration_service: CollaborationService,
                 tax_data: TaxData, return_id: str, tax_year: int,
                 current_user_id: str, current_user_name: str,
                 access_level: AccessLevel = AccessLevel.COMMENT):
        """
        Initialize the review mode window.

        Args:
            parent: Parent window
            collaboration_service: Service for collaboration features
            tax_data: Tax data to review
            return_id: ID of the shared return
            tax_year: Tax year being reviewed
            current_user_id: ID of the current user
            current_user_name: Name of the current user
            access_level: Access level of the current user
        """
        super().__init__(parent)
        self.collaboration_service = collaboration_service
        self.tax_data = tax_data
        self.return_id = return_id
        self.tax_year = tax_year
        self.current_user_id = current_user_id
        self.current_user_name = current_user_name
        self.access_level = access_level

        self.title(f"Review Mode - Tax Return {tax_year}")
        self.geometry("1200x800")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.comments_widgets: Dict[str, CommentsWidget] = {}
        self.review_status = ReviewStatus.PENDING

        self._setup_ui()
        self._load_review_data()

    def _setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text=f"Reviewing Tax Return - {self.tax_year}",
                 font=("", 14, "bold")).pack(side=tk.LEFT)

        # Status indicator
        self.status_label = ttk.Label(header_frame, text="Status: Loading...",
                                    font=("", 10))
        self.status_label.pack(side=tk.RIGHT)

        # Toolbar
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar_frame, text="Refresh", command=self._load_review_data).pack(side=tk.LEFT, padx=(0, 5))

        if self.access_level in [AccessLevel.EDIT, AccessLevel.FULL_ACCESS]:
            ttk.Button(toolbar_frame, text="Approve", command=self._approve_review).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(toolbar_frame, text="Reject", command=self._reject_review).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(toolbar_frame, text="Export Comments",
                  command=self._export_comments).pack(side=tk.LEFT, padx=(0, 5))

        # Paned window for split view
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Tax data sections
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)

        # Notebook for tax sections
        self.sections_notebook = ttk.Notebook(left_frame)
        self.sections_notebook.pack(fill=tk.BOTH, expand=True)

        # Create section tabs
        self._create_section_tabs()

        # Right panel - Comments and review info
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        # Comments notebook
        comments_notebook = ttk.Notebook(right_frame)
        comments_notebook.pack(fill=tk.BOTH, expand=True)

        # Current field comments
        self.current_comments_frame = ttk.Frame(comments_notebook)
        comments_notebook.add(self.current_comments_frame, text="Field Comments")

        ttk.Label(self.current_comments_frame,
                 text="Select a field to view comments",
                 font=("", 10, "italic")).pack(pady=20)

        # Review summary
        summary_frame = ttk.Frame(comments_notebook)
        comments_notebook.add(summary_frame, text="Review Summary")
        self._setup_review_summary(summary_frame)

    def _create_section_tabs(self):
        """Create tabs for different tax return sections"""
        sections = {
            "Personal Info": ["personal_info"],
            "Income": ["wages", "interest", "dividends", "business_income"],
            "Deductions": ["standard_deduction", "itemized_deductions"],
            "Credits": ["child_tax_credit", "education_credits"],
            "Taxes": ["federal_tax", "state_tax"],
            "Payments": ["withholding", "estimated_payments"]
        }

        for section_name, field_groups in sections.items():
            frame = ttk.Frame(self.sections_notebook)
            self.sections_notebook.add(frame, text=section_name)
            self._populate_section_tab(frame, field_groups)

    def _populate_section_tab(self, parent, field_groups: List[str]):
        """Populate a section tab with fields and values"""
        canvas = tk.Canvas(parent, bg=parent.cget('bg'))
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add fields for this section
        for field_group in field_groups:
            self._add_field_group(scrollable_frame, field_group)

    def _add_field_group(self, parent, field_group: str):
        """Add a group of related fields"""
        # Group header
        ttk.Label(parent, text=field_group.replace('_', ' ').title(),
                 font=("", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))

        # Get fields for this group
        fields = self._get_fields_for_group(field_group)

        for field_path, field_info in fields.items():
            self._add_field_display(parent, field_path, field_info)

    def _get_fields_for_group(self, field_group: str) -> Dict[str, Dict]:
        """Get fields for a specific group"""
        # This would be expanded based on the actual tax data structure
        # For now, return some sample fields
        sample_fields = {
            f"{field_group}.amount": {"value": "0.00", "type": "currency"},
            f"{field_group}.description": {"value": "", "type": "text"},
        }

        # Try to get actual data from tax_data
        try:
            if hasattr(self.tax_data, 'get'):
                actual_value = self.tax_data.get(field_group, "", self.tax_year)
                if actual_value is not None:
                    sample_fields[field_group] = {"value": str(actual_value), "type": "text"}
        except:
            pass

        return sample_fields

    def _add_field_display(self, parent, field_path: str, field_info: Dict):
        """Add a field display with value and comment button"""
        field_frame = ttk.Frame(parent, relief="ridge", borderwidth=1)
        field_frame.pack(fill=tk.X, padx=5, pady=2)

        # Field name
        field_name = field_path.split('.')[-1].replace('_', ' ').title()
        ttk.Label(field_frame, text=f"{field_name}:",
                 font=("", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        # Field value (read-only)
        value_var = tk.StringVar(value=str(field_info.get('value', '')))
        value_entry = ttk.Entry(field_frame, textvariable=value_var, state="readonly", width=30)
        value_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Comment indicator and button
        comment_frame = ttk.Frame(field_frame)
        comment_frame.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Comment count indicator
        self.comment_indicators = getattr(self, 'comment_indicators', {})
        self.comment_indicators[field_path] = ttk.Label(comment_frame, text="(0)", foreground="gray")
        self.comment_indicators[field_path].pack(side=tk.LEFT)

        # View comments button
        ttk.Button(comment_frame, text="💬",
                  command=lambda: self._show_field_comments(field_path)).pack(side=tk.LEFT, padx=(5, 0))

        field_frame.columnconfigure(1, weight=1)

    def _show_field_comments(self, field_path: str):
        """Show comments for a specific field"""
        # Clear current comments frame
        for widget in self.current_comments_frame.winfo_children():
            widget.destroy()

        # Create comments widget
        comments_widget = CommentsWidget(
            self.current_comments_frame,
            self.collaboration_service,
            self.current_user_id,
            self.current_user_name,
            self.return_id,
            self.tax_year,
            field_path,
            self.access_level
        )
        comments_widget.pack(fill=tk.BOTH, expand=True)

        # Store reference
        self.comments_widgets[field_path] = comments_widget

        # Update comment count
        self._update_comment_counts()

    def _setup_review_summary(self, parent):
        """Set up the review summary panel"""
        # Review status
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(status_frame, text="Review Status:",
                 font=("", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        self.review_status_label = ttk.Label(status_frame, text="Loading...")
        self.review_status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        # Statistics
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(stats_frame, text="Total Comments:",
                 font=("", 9, "bold")).grid(row=0, column=0, sticky=tk.W)
        self.total_comments_label = ttk.Label(stats_frame, text="0")
        self.total_comments_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        ttk.Label(stats_frame, text="Unresolved:",
                 font=("", 9, "bold")).grid(row=1, column=0, sticky=tk.W)
        self.unresolved_comments_label = ttk.Label(stats_frame, text="0")
        self.unresolved_comments_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))

        # Review notes
        notes_frame = ttk.Frame(parent)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        ttk.Label(notes_frame, text="Review Notes:",
                  font=("", 10, "bold")).pack(anchor=tk.W)

        self.review_notes_text = scrolledtext.ScrolledText(notes_frame, height=10, wrap=tk.WORD)
        self.review_notes_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Save notes button
        ttk.Button(notes_frame, text="Save Notes",
                  command=self._save_review_notes).pack(pady=(5, 0))

    def _load_review_data(self):
        """Load review data and status"""
        try:
            # Get review status
            self.review_status = self.collaboration_service.get_review_status(
                self.return_id, self.tax_year
            )

            # Update status display
            status_text = self.review_status.value.title()
            color = {
                ReviewStatus.PENDING: "orange",
                ReviewStatus.APPROVED: "green",
                ReviewStatus.REJECTED: "red"
            }.get(self.review_status, "black")

            self.status_label.config(text=f"Status: {status_text}", foreground=color)
            self.review_status_label.config(text=status_text, foreground=color)

            # Load review notes
            notes = self.collaboration_service.get_review_notes(self.return_id, self.tax_year)
            self.review_notes_text.delete(1.0, tk.END)
            if notes:
                self.review_notes_text.insert(1.0, notes)

            # Update comment counts
            self._update_comment_counts()

        except Exception as e:
            logger.error(f"Failed to load review data: {e}")
            messagebox.showerror("Error", "Failed to load review data.")

    def _update_comment_counts(self):
        """Update comment counts across all fields"""
        total_comments = 0
        unresolved_comments = 0

        # Get all comments for this return
        try:
            all_comments = self.collaboration_service.get_all_comments_for_return(
                self.return_id, self.tax_year
            )

            total_comments = len(all_comments)
            unresolved_comments = len([c for c in all_comments if not c.resolved])

            # Update indicators for visible fields
            for field_path, indicator in getattr(self, 'comment_indicators', {}).items():
                field_comments = [c for c in all_comments if c.field_path == field_path]
                count = len(field_comments)
                unresolved = len([c for c in field_comments if not c.resolved])

                if count > 0:
                    indicator.config(text=f"({count})", foreground="blue" if unresolved > 0 else "green")
                else:
                    indicator.config(text="(0)", foreground="gray")

        except Exception as e:
            logger.error(f"Failed to update comment counts: {e}")

        # Update summary labels
        self.total_comments_label.config(text=str(total_comments))
        self.unresolved_comments_label.config(text=str(unresolved_comments))

    def _approve_review(self):
        """Approve the tax return review"""
        if messagebox.askyesno("Approve Review",
                              "Approve this tax return? This will mark the review as complete."):
            try:
                success = self.collaboration_service.update_review_status(
                    self.return_id, self.tax_year, ReviewStatus.APPROVED,
                    self.current_user_id, self.current_user_name
                )

                if success:
                    self._load_review_data()
                    messagebox.showinfo("Review Approved", "Tax return has been approved.")
                else:
                    messagebox.showerror("Error", "Failed to approve review.")

            except Exception as e:
                logger.error(f"Failed to approve review: {e}")
                messagebox.showerror("Error", f"Failed to approve review: {str(e)}")

    def _reject_review(self):
        """Reject the tax return review"""
        reason = tk.simpledialog.askstring("Reject Review",
                                          "Please provide a reason for rejection:",
                                          parent=self)
        if reason:
            try:
                success = self.collaboration_service.update_review_status(
                    self.return_id, self.tax_year, ReviewStatus.REJECTED,
                    self.current_user_id, self.current_user_name, reason
                )

                if success:
                    self._load_review_data()
                    messagebox.showinfo("Review Rejected", "Tax return has been rejected.")
                else:
                    messagebox.showerror("Error", "Failed to reject review.")

            except Exception as e:
                logger.error(f"Failed to reject review: {e}")
                messagebox.showerror("Error", f"Failed to reject review: {str(e)}")

    def _save_review_notes(self):
        """Save review notes"""
        notes = self.review_notes_text.get(1.0, tk.END).strip()

        try:
            success = self.collaboration_service.save_review_notes(
                self.return_id, self.tax_year, notes,
                self.current_user_id, self.current_user_name
            )

            if success:
                messagebox.showinfo("Notes Saved", "Review notes have been saved.")
            else:
                messagebox.showerror("Error", "Failed to save review notes.")

        except Exception as e:
            logger.error(f"Failed to save review notes: {e}")
            messagebox.showerror("Error", f"Failed to save review notes: {str(e)}")

    def _export_comments(self):
        """Export all comments to a file"""
        try:
            comments_data = self.collaboration_service.export_comments(
                self.return_id, self.tax_year
            )

            # For now, just show in a dialog
            export_window = tk.Toplevel(self)
            export_window.title("Comments Export")
            export_window.geometry("600x400")

            text_widget = scrolledtext.ScrolledText(export_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Format comments for display
            export_text = f"Comments Export - Tax Return {self.tax_year}\n"
            export_text += "=" * 50 + "\n\n"

            for comment in comments_data:
                export_text += f"Field: {comment['field_path']}\n"
                export_text += f"Author: {comment['author_name']} ({comment['created_date']})\n"
                export_text += f"Status: {'Resolved' if comment['resolved'] else 'Unresolved'}\n"
                export_text += f"Comment: {comment['content']}\n"
                export_text += "-" * 30 + "\n\n"

            text_widget.insert(1.0, export_text)
            text_widget.config(state="disabled")

        except Exception as e:
            logger.error(f"Failed to export comments: {e}")
            messagebox.showerror("Error", f"Failed to export comments: {str(e)}")