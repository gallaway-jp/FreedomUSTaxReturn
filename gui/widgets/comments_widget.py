"""
Comments Widget - GUI component for displaying and managing comments

This widget provides:
- Display of comments for specific fields
- Adding new comments
- Resolving comments
- Threaded comment display
- Real-time comment updates
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from services.collaboration_service import CollaborationService, Comment, CollaborationRole, AccessLevel

logger = logging.getLogger(__name__)


class CommentsWidget(ttk.Frame):
    """
    Widget for displaying and managing comments on tax data fields.

    Shows comments for a specific field and allows adding new comments.
    """

    def __init__(self, parent, collaboration_service: CollaborationService,
                 current_user_id: str, current_user_name: str,
                 return_id: str, tax_year: int, field_path: str,
                 access_level: AccessLevel = AccessLevel.COMMENT):
        """
        Initialize the comments widget.

        Args:
            parent: Parent tkinter widget
            collaboration_service: Service for collaboration features
            current_user_id: ID of the current user
            current_user_name: Name of the current user
            return_id: ID of the shared return
            tax_year: Tax year for comments
            field_path: Path to the field being commented on
            access_level: Access level of the current user
        """
        super().__init__(parent)
        self.collaboration_service = collaboration_service
        self.current_user_id = current_user_id
        self.current_user_name = current_user_name
        self.return_id = return_id
        self.tax_year = tax_year
        self.field_path = field_path
        self.access_level = access_level

        self.comments: List[Comment] = []
        self._setup_ui()
        self.refresh_comments()

    def _setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header_frame, text=f"Comments for {self.field_path}",
                 font=("", 10, "bold")).pack(side=tk.LEFT)

        # Refresh button
        ttk.Button(header_frame, text="↻", width=3,
                  command=self.refresh_comments).pack(side=tk.RIGHT)

        # Comments display area
        self.comments_frame = ttk.Frame(main_frame)
        self.comments_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable canvas for comments
        self.canvas = tk.Canvas(self.comments_frame, bg=self.cget('bg'))
        scrollbar = ttk.Scrollbar(self.comments_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add comment section (only if user can comment)
        if self.access_level in [AccessLevel.COMMENT, AccessLevel.EDIT, AccessLevel.FULL_ACCESS]:
            self._setup_add_comment_ui(main_frame)

    def _setup_add_comment_ui(self, parent):
        """Set up the UI for adding new comments"""
        add_frame = ttk.Frame(parent)
        add_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(add_frame, text="Add Comment:", font=("", 9, "bold")).pack(anchor=tk.W)

        # Comment text area
        self.comment_text = scrolledtext.ScrolledText(add_frame, height=3, width=50, wrap=tk.WORD)
        self.comment_text.pack(fill=tk.X, pady=(2, 5))

        # Buttons
        button_frame = ttk.Frame(add_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Add Comment",
                  command=self._add_comment).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Clear",
                  command=lambda: self.comment_text.delete(1.0, tk.END)).pack(side=tk.LEFT)

    def refresh_comments(self):
        """Refresh the display of comments"""
        try:
            # Clear existing comments
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # Get comments for this field
            self.comments = self.collaboration_service.get_comments_for_field(
                self.return_id, self.field_path, self.tax_year
            )

            if not self.comments:
                ttk.Label(self.scrollable_frame, text="No comments yet.",
                         foreground="gray").pack(pady=20)
                return

            # Display comments
            for i, comment in enumerate(self.comments):
                self._display_comment(comment, i)

            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except Exception as e:
            logger.error(f"Failed to refresh comments: {e}")
            ttk.Label(self.scrollable_frame, text="Error loading comments.",
                     foreground="red").pack(pady=20)

    def _display_comment(self, comment: Comment, index: int):
        """Display a single comment"""
        # Comment frame
        comment_frame = ttk.Frame(self.scrollable_frame, relief="ridge", borderwidth=1)
        comment_frame.pack(fill=tk.X, padx=5, pady=2)

        # Header
        header_frame = ttk.Frame(comment_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=2)

        # Author and date
        author_label = ttk.Label(header_frame,
                                text=f"{comment.author_name} - {comment.created_date.strftime('%m/%d/%Y %H:%M')}",
                                font=("", 9, "bold"))
        author_label.pack(side=tk.LEFT)

        # Status indicators
        if comment.resolved:
            ttk.Label(header_frame, text="✓ Resolved",
                     foreground="green", font=("", 8)).pack(side=tk.RIGHT, padx=(5, 0))

        # Comment content
        content_label = ttk.Label(comment_frame, text=comment.content,
                                 wraplength=400, justify=tk.LEFT)
        content_label.pack(fill=tk.X, padx=5, pady=(0, 5), anchor=tk.W)

        # Action buttons (only for appropriate users)
        if self._can_modify_comment(comment):
            button_frame = ttk.Frame(comment_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

            if not comment.resolved:
                ttk.Button(button_frame, text="Resolve",
                          command=lambda: self._resolve_comment(comment.id)).pack(side=tk.LEFT, padx=(0, 5))

            ttk.Button(button_frame, text="Reply",
                      command=lambda: self._reply_to_comment(comment.id)).pack(side=tk.LEFT)

    def _can_modify_comment(self, comment: Comment) -> bool:
        """Check if current user can modify this comment"""
        if self.access_level in [AccessLevel.EDIT, AccessLevel.FULL_ACCESS]:
            return True
        if comment.author_id == self.current_user_id:
            return True
        return False

    def _add_comment(self):
        """Add a new comment"""
        content = self.comment_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Empty Comment", "Please enter a comment before adding.")
            return

        try:
            comment_id = self.collaboration_service.add_comment(
                return_id=self.return_id,
                tax_year=self.tax_year,
                field_path=self.field_path,
                content=content,
                author_id=self.current_user_id,
                author_name=self.current_user_name
            )

            if comment_id:
                self.comment_text.delete(1.0, tk.END)
                self.refresh_comments()
                messagebox.showinfo("Comment Added", "Your comment has been added successfully.")
            else:
                messagebox.showerror("Error", "Failed to add comment. Please check your permissions.")

        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            messagebox.showerror("Error", f"Failed to add comment: {str(e)}")

    def _resolve_comment(self, comment_id: str):
        """Resolve a comment"""
        if messagebox.askyesno("Resolve Comment", "Mark this comment as resolved?"):
            try:
                success = self.collaboration_service.resolve_comment(
                    self.return_id, comment_id, self.current_user_id, self.current_user_name
                )

                if success:
                    self.refresh_comments()
                    messagebox.showinfo("Comment Resolved", "Comment has been marked as resolved.")
                else:
                    messagebox.showerror("Error", "Failed to resolve comment.")

            except Exception as e:
                logger.error(f"Failed to resolve comment: {e}")
                messagebox.showerror("Error", f"Failed to resolve comment: {str(e)}")

    def _reply_to_comment(self, parent_comment_id: str):
        """Reply to a comment"""
        # For now, just add a regular comment (could be enhanced with threading)
        reply_content = f"Reply to comment: {parent_comment_id}\n\n"
        self.comment_text.delete(1.0, tk.END)
        self.comment_text.insert(1.0, reply_content)
        self.comment_text.focus_set()

    def get_comment_count(self) -> int:
        """Get the number of comments"""
        return len(self.comments)

    def get_unresolved_count(self) -> int:
        """Get the number of unresolved comments"""
        return len([c for c in self.comments if not c.resolved])

    def has_comments(self) -> bool:
        """Check if there are any comments"""
        return len(self.comments) > 0