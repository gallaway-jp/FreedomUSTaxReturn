"""
Sharing Dialog - GUI for managing tax return sharing

This dialog provides:
- Inviting users to share tax returns
- Setting access levels (view, comment, edit, full access)
- Managing existing shares
- Revoking access
- QR code generation for easy sharing
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
import qrcode
import io
from PIL import Image, ImageTk
from typing import Dict, Any, List, Optional, Callable
from services.collaboration_service import CollaborationService, CollaborationRole, AccessLevel, SharedReturn
from models.user import User

logger = logging.getLogger(__name__)


class SharingDialog(tk.Toplevel):
    """
    Dialog for managing tax return sharing with other users.
    """

    def __init__(self, parent, collaboration_service: CollaborationService,
                 current_user: User, return_id: str, tax_year: int):
        """
        Initialize the sharing dialog.

        Args:
            parent: Parent window
            collaboration_service: Service for collaboration features
            current_user: Current user object
            return_id: ID of the return to share
            tax_year: Tax year of the return
        """
        super().__init__(parent)
        self.collaboration_service = collaboration_service
        self.current_user = current_user
        self.return_id = return_id
        self.tax_year = tax_year

        self.title(f"Share Tax Return - {tax_year}")
        self.geometry("700x600")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.shared_users: List[SharedReturn] = []
        self._setup_ui()
        self.refresh_shared_users()

    def _setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        ttk.Label(main_frame, text="Share Your Tax Return",
                 font=("", 14, "bold")).pack(pady=(0, 10))

        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Invite tab
        invite_frame = ttk.Frame(notebook)
        notebook.add(invite_frame, text="Invite Users")
        self._setup_invite_tab(invite_frame)

        # Manage tab
        manage_frame = ttk.Frame(notebook)
        notebook.add(manage_frame, text="Manage Access")
        self._setup_manage_tab(manage_frame)

        # QR Code tab
        qr_frame = ttk.Frame(notebook)
        notebook.add(qr_frame, text="Share Link")
        self._setup_qr_tab(qr_frame)

        # Close button
        ttk.Button(main_frame, text="Close", command=self.destroy).pack(pady=(10, 0))

    def _setup_invite_tab(self, parent):
        """Set up the invite users tab"""
        # Instructions
        ttk.Label(parent, text="Invite users to collaborate on this tax return:",
                 font=("", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))

        # Email input
        email_frame = ttk.Frame(parent)
        email_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(email_frame, text="Email address:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(email_frame, textvariable=self.email_var, width=40)
        email_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        email_entry.focus()

        # Access level selection
        access_frame = ttk.Frame(parent)
        access_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(access_frame, text="Access level:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.access_level_var = tk.StringVar(value=AccessLevel.COMMENT.value)
        access_combo = ttk.Combobox(access_frame, textvariable=self.access_level_var,
                                   values=[level.value for level in AccessLevel],
                                   state="readonly", width=20)
        access_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        # Role selection
        role_frame = ttk.Frame(parent)
        role_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(role_frame, text="Role:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.role_var = tk.StringVar(value=CollaborationRole.SPOUSE.value)
        role_combo = ttk.Combobox(role_frame, textvariable=self.role_var,
                                 values=[role.value for role in CollaborationRole],
                                 state="readonly", width=20)
        role_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        # Message
        message_frame = ttk.Frame(parent)
        message_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(message_frame, text="Personal message (optional):").grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 5))
        self.message_text = scrolledtext.ScrolledText(message_frame, height=3, width=50, wrap=tk.WORD)
        self.message_text.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Invite button
        ttk.Button(parent, text="Send Invitation", command=self._send_invitation).pack(pady=(0, 10))

        # Configure grid weights
        email_frame.columnconfigure(1, weight=1)
        access_frame.columnconfigure(1, weight=1)
        role_frame.columnconfigure(1, weight=1)
        message_frame.columnconfigure(1, weight=1)
        message_frame.rowconfigure(0, weight=1)

    def _setup_manage_tab(self, parent):
        """Set up the manage access tab"""
        # Instructions
        ttk.Label(parent, text="Manage who has access to this tax return:",
                 font=("", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))

        # Treeview for shared users
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("Email", "Role", "Access Level", "Status", "Last Access")
        self.shared_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.shared_tree.heading(col, text=col)
            self.shared_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.shared_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.shared_tree.xview)
        self.shared_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.shared_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Change Access Level",
                  command=self._change_access_level).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Revoke Access",
                  command=self._revoke_access).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Refresh",
                  command=self.refresh_shared_users).pack(side=tk.RIGHT)

    def _setup_qr_tab(self, parent):
        """Set up the QR code sharing tab"""
        # Instructions
        ttk.Label(parent, text="Share this QR code or link for easy access:",
                 font=("", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))

        # Generate sharing link
        try:
            share_link = self.collaboration_service.generate_share_link(
                self.return_id, self.current_user.id, self.tax_year
            )

            # QR Code
            qr_frame = ttk.Frame(parent)
            qr_frame.pack(pady=10)

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(share_link)
            qr.make(fit=True)

            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_photo = ImageTk.PhotoImage(qr_image)

            qr_label = ttk.Label(qr_frame, image=qr_photo)
            qr_label.image = qr_photo  # Keep reference
            qr_label.pack()

            # Link display
            link_frame = ttk.Frame(parent)
            link_frame.pack(fill=tk.X, pady=(10, 5))

            ttk.Label(link_frame, text="Share Link:").pack(anchor=tk.W)
            link_entry = ttk.Entry(link_frame, width=60)
            link_entry.insert(0, share_link)
            link_entry.config(state="readonly")
            link_entry.pack(fill=tk.X, pady=(2, 0))

            ttk.Button(link_frame, text="Copy Link",
                      command=lambda: self._copy_to_clipboard(share_link)).pack(pady=(5, 0))

        except Exception as e:
            logger.error(f"Failed to generate share link: {e}")
            ttk.Label(parent, text="Error generating share link.",
                     foreground="red").pack(pady=20)

    def _send_invitation(self):
        """Send an invitation to share the tax return"""
        email = self.email_var.get().strip()
        if not email:
            messagebox.showwarning("Missing Email", "Please enter an email address.")
            return

        access_level = AccessLevel(self.access_level_var.get())
        role = CollaborationRole(self.role_var.get())
        message = self.message_text.get(1.0, tk.END).strip()

        try:
            success = self.collaboration_service.invite_user(
                return_id=self.return_id,
                tax_year=self.tax_year,
                inviter_id=self.current_user.id,
                inviter_name=self.current_user.name,
                invitee_email=email,
                role=role,
                access_level=access_level,
                message=message
            )

            if success:
                messagebox.showinfo("Invitation Sent",
                                  f"Invitation sent to {email} successfully.")
                self.email_var.set("")
                self.message_text.delete(1.0, tk.END)
                self.refresh_shared_users()
            else:
                messagebox.showerror("Error", "Failed to send invitation. Please try again.")

        except Exception as e:
            logger.error(f"Failed to send invitation: {e}")
            messagebox.showerror("Error", f"Failed to send invitation: {str(e)}")

    def refresh_shared_users(self):
        """Refresh the list of shared users"""
        try:
            # Clear existing items
            for item in self.shared_tree.get_children():
                self.shared_tree.delete(item)

            # Get shared users
            self.shared_users = self.collaboration_service.get_shared_users(self.return_id)

            for shared in self.shared_users:
                self.shared_tree.insert("", tk.END, values=(
                    shared.invitee_email,
                    shared.role.value,
                    shared.access_level.value,
                    "Active" if shared.accepted else "Pending",
                    shared.last_access.strftime("%m/%d/%Y") if shared.last_access else "Never"
                ))

        except Exception as e:
            logger.error(f"Failed to refresh shared users: {e}")
            messagebox.showerror("Error", "Failed to load shared users.")

    def _change_access_level(self):
        """Change access level for selected user"""
        selection = self.shared_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to change access level.")
            return

        item = selection[0]
        values = self.shared_tree.item(item, "values")
        email = values[0]

        # Find the shared return
        shared_return = next((s for s in self.shared_users if s.invitee_email == email), None)
        if not shared_return:
            return

        # Access level selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Change Access Level")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Change access level for {email}:",
                 font=("", 10, "bold")).pack(pady=10)

        access_var = tk.StringVar(value=shared_return.access_level.value)
        access_combo = ttk.Combobox(dialog, textvariable=access_var,
                                   values=[level.value for level in AccessLevel],
                                   state="readonly")
        access_combo.pack(pady=5)

        def apply_change():
            try:
                new_level = AccessLevel(access_var.get())
                success = self.collaboration_service.update_access_level(
                    self.return_id, shared_return.invitee_email, new_level
                )

                if success:
                    dialog.destroy()
                    self.refresh_shared_users()
                    messagebox.showinfo("Success", "Access level updated successfully.")
                else:
                    messagebox.showerror("Error", "Failed to update access level.")

            except Exception as e:
                logger.error(f"Failed to update access level: {e}")
                messagebox.showerror("Error", f"Failed to update access level: {str(e)}")

        ttk.Button(dialog, text="Apply", command=apply_change).pack(pady=10)

    def _revoke_access(self):
        """Revoke access for selected user"""
        selection = self.shared_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to revoke access.")
            return

        item = selection[0]
        values = self.shared_tree.item(item, "values")
        email = values[0]

        if messagebox.askyesno("Revoke Access",
                              f"Revoke access for {email}? They will no longer be able to view or edit this tax return."):
            try:
                success = self.collaboration_service.revoke_access(self.return_id, email)

                if success:
                    self.refresh_shared_users()
                    messagebox.showinfo("Access Revoked", f"Access revoked for {email}.")
                else:
                    messagebox.showerror("Error", "Failed to revoke access.")

            except Exception as e:
                logger.error(f"Failed to revoke access: {e}")
                messagebox.showerror("Error", f"Failed to revoke access: {str(e)}")

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Link copied to clipboard.")