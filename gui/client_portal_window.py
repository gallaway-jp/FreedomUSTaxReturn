"""
Client Portal Window - Secure client access to tax information

Provides a secure portal for clients to view their tax returns, documents,
and communicate with their tax preparer.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List
import webbrowser
from datetime import datetime
from pathlib import Path

from config.dependencies import get_container
from models.tax_data import TaxData
from services.encryption_service import EncryptionService
from utils.error_tracker import get_error_tracker


class ClientPortalWindow:
    """
    Main client portal window for secure client access.
    """

    def __init__(self, parent: tk.Tk, client_id: str, client_name: str):
        """
        Initialize client portal window.

        Args:
            parent: Parent window
            client_id: Unique client identifier
            client_name: Client's full name
        """
        self.parent = parent
        self.client_id = client_id
        self.client_name = client_name

        self.container = get_container()
        self.encryption: EncryptionService = self.container.get_encryption_service()
        self.error_tracker = get_error_tracker()

        # Create main window
        self.root = tk.Toplevel(parent)
        self.root.title(f"Client Portal - {client_name}")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        self.root.transient(parent)

        # Initialize data
        self.tax_returns: List[Dict] = []
        self.messages: List[Dict] = []
        self.documents: List[Dict] = []

        self._create_widgets()
        self._load_client_data()

        # Center window
        self.root.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

    def _create_widgets(self) -> None:
        """Create the main window widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text=f"Welcome to Your Tax Portal, {self.client_name}",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)

        logout_btn = ttk.Button(header_frame, text="Logout", command=self._logout)
        logout_btn.pack(side=tk.RIGHT)

        # Create notebook for different sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tax Returns tab
        returns_frame = ttk.Frame(self.notebook)
        self.notebook.add(returns_frame, text="My Tax Returns")
        self._create_returns_tab(returns_frame)

        # Documents tab
        docs_frame = ttk.Frame(self.notebook)
        self.notebook.add(docs_frame, text="Documents")
        self._create_documents_tab(docs_frame)

        # Messages tab
        messages_frame = ttk.Frame(self.notebook)
        self.notebook.add(messages_frame, text="Messages")
        self._create_messages_tab(messages_frame)

        # Profile tab
        profile_frame = ttk.Frame(self.notebook)
        self.notebook.add(profile_frame, text="My Profile")
        self._create_profile_tab(profile_frame)

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)

        ttk.Label(status_frame, text=f"Client ID: {self.client_id}").pack(side=tk.RIGHT)

    def _create_returns_tab(self, parent: ttk.Frame) -> None:
        """Create tax returns tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="View Return", command=self._view_selected_return).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Download PDF", command=self._download_return_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Refresh", command=self._load_client_data).pack(side=tk.RIGHT)

        # Returns list
        list_frame = ttk.LabelFrame(parent, text="Tax Returns", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for returns
        columns = ("Tax Year", "Status", "Filed Date", "Last Modified", "Notes")
        self.returns_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.returns_tree.heading(col, text=col)
            self.returns_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.returns_tree.yview)
        self.returns_tree.configure(yscrollcommand=v_scrollbar.set)

        self.returns_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click
        self.returns_tree.bind("<Double-1>", lambda e: self._view_selected_return())

    def _create_documents_tab(self, parent: ttk.Frame) -> None:
        """Create documents tab"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="View Document", command=self._view_selected_document).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Download", command=self._download_selected_document).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Refresh", command=self._load_client_data).pack(side=tk.RIGHT)

        # Documents list
        list_frame = ttk.LabelFrame(parent, text="Available Documents", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for documents
        columns = ("Document Name", "Type", "Date", "Size", "Description")
        self.docs_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.docs_tree.heading(col, text=col)
            self.docs_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.docs_tree.yview)
        self.docs_tree.configure(yscrollcommand=v_scrollbar.set)

        self.docs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click
        self.docs_tree.bind("<Double-1>", lambda e: self._view_selected_document())

    def _create_messages_tab(self, parent: ttk.Frame) -> None:
        """Create messages tab"""
        # Split pane
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Messages list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        list_frame = ttk.LabelFrame(left_frame, text="Messages", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for messages
        columns = ("From", "Subject", "Date", "Status")
        self.messages_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.messages_tree.heading(col, text=col)
            self.messages_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.messages_tree.yview)
        self.messages_tree.configure(yscrollcommand=v_scrollbar.set)

        self.messages_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Message content
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        content_frame = ttk.LabelFrame(right_frame, text="Message Content", padding="5")
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.message_text = tk.Text(content_frame, wrap=tk.WORD, state=tk.DISABLED)
        msg_scrollbar = ttk.Scrollbar(content_frame, command=self.message_text.yview)
        self.message_text.configure(yscrollcommand=msg_scrollbar.set)

        self.message_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        msg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Message actions
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(action_frame, text="New Message", command=self._compose_message).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Reply", command=self._reply_to_message).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Mark as Read", command=self._mark_message_read).pack(side=tk.LEFT)

        # Bind selection
        self.messages_tree.bind("<<TreeviewSelect>>", self._on_message_select)

    def _create_profile_tab(self, parent: ttk.Frame) -> None:
        """Create profile tab"""
        profile_frame = ttk.LabelFrame(parent, text="Client Information", padding="20")
        profile_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Profile fields (read-only for client)
        ttk.Label(profile_frame, text="Full Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.profile_name_var = tk.StringVar()
        ttk.Entry(profile_frame, textvariable=self.profile_name_var, state="readonly").grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(profile_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.profile_email_var = tk.StringVar()
        ttk.Entry(profile_frame, textvariable=self.profile_email_var, state="readonly").grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(profile_frame, text="Client ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(profile_frame, text=self.client_id).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Security settings
        security_frame = ttk.LabelFrame(parent, text="Security Settings", padding="10")
        security_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Button(security_frame, text="Change Password", command=self._change_password).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(security_frame, text="Setup 2FA", command=self._setup_2fa).pack(side=tk.LEFT)

    def _load_client_data(self) -> None:
        """Load client's tax data, documents, and messages"""
        try:
            self.status_var.set("Loading data...")

            # Load tax returns
            self._load_tax_returns()

            # Load documents
            self._load_documents()

            # Load messages
            self._load_messages()

            # Load profile
            self._load_profile()

            self.status_var.set("Data loaded successfully")

        except Exception as e:
            self.error_tracker.track_error(error=e, context={"client_id": self.client_id})
            self.status_var.set(f"Error loading data: {str(e)}")
            messagebox.showerror("Error", f"Failed to load client data: {str(e)}")

    def _load_tax_returns(self) -> None:
        """Load client's tax returns"""
        # Clear existing items
        for item in self.returns_tree.get_children():
            self.returns_tree.delete(item)

        # For now, simulate some sample returns
        # In a real implementation, this would load from the client's data directory
        sample_returns = [
            {"year": "2024", "status": "Filed", "filed_date": "2025-03-15", "modified": "2025-03-10", "notes": "Final return"},
            {"year": "2023", "status": "Filed", "filed_date": "2024-03-20", "modified": "2024-03-15", "notes": "Amended return"},
            {"year": "2022", "status": "Filed", "filed_date": "2023-04-01", "modified": "2023-03-25", "notes": "Original filing"}
        ]

        for ret in sample_returns:
            self.returns_tree.insert("", tk.END, values=(
                ret["year"],
                ret["status"],
                ret["filed_date"],
                ret["modified"],
                ret["notes"]
            ))

    def _load_documents(self) -> None:
        """Load client's documents"""
        # Clear existing items
        for item in self.docs_tree.get_children():
            self.docs_tree.delete(item)

        # Sample documents
        sample_docs = [
            {"name": "Tax Return 2024.pdf", "type": "PDF", "date": "2025-03-15", "size": "245 KB", "description": "Filed tax return"},
            {"name": "W-2 2024.pdf", "type": "PDF", "date": "2025-01-15", "size": "89 KB", "description": "Wage and tax statement"},
            {"name": "1099-INT 2024.pdf", "type": "PDF", "date": "2025-01-20", "size": "67 KB", "description": "Interest income statement"}
        ]

        for doc in sample_docs:
            self.docs_tree.insert("", tk.END, values=(
                doc["name"],
                doc["type"],
                doc["date"],
                doc["size"],
                doc["description"]
            ))

    def _load_messages(self) -> None:
        """Load client's messages"""
        # Clear existing items
        for item in self.messages_tree.get_children():
            self.messages_tree.delete(item)

        # Sample messages
        sample_messages = [
            {"from": "Tax Preparer", "subject": "Your 2024 tax return is ready", "date": "2025-03-16", "status": "Unread", "content": "Dear Client,\n\nYour 2024 tax return has been prepared and is ready for your review. Please log in to your client portal to view and approve the return.\n\nBest regards,\nYour Tax Preparer"},
            {"from": "Tax Preparer", "subject": "Welcome to your client portal", "date": "2025-01-01", "status": "Read", "content": "Welcome to your secure client portal! Here you can view your tax returns, download documents, and communicate with your tax preparer."},
            {"from": "Client", "subject": "Question about deduction", "date": "2025-02-15", "status": "Read", "content": "I have a question about the home office deduction on my return."}
        ]

        for msg in sample_messages:
            self.messages_tree.insert("", tk.END, values=(
                msg["from"],
                msg["subject"],
                msg["date"],
                msg["status"]
            ), tags=(msg["content"],))

    def _load_profile(self) -> None:
        """Load client profile information"""
        # Sample profile data
        self.profile_name_var.set(self.client_name)
        self.profile_email_var.set("client@example.com")  # Would load from actual client data

    def _view_selected_return(self) -> None:
        """View the selected tax return"""
        selection = self.returns_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tax return to view.")
            return

        item = self.returns_tree.item(selection[0])
        year = item['values'][0]

        # In a real implementation, this would open the tax return viewer
        messagebox.showinfo("View Return", f"Opening tax return for {year}...")

    def _download_return_pdf(self) -> None:
        """Download PDF of selected tax return"""
        selection = self.returns_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tax return to download.")
            return

        item = self.returns_tree.item(selection[0])
        year = item['values'][0]

        # In a real implementation, this would generate/download the PDF
        messagebox.showinfo("Download", f"Downloading PDF for tax year {year}...")

    def _view_selected_document(self) -> None:
        """View the selected document"""
        selection = self.docs_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a document to view.")
            return

        item = self.docs_tree.item(selection[0])
        doc_name = item['values'][0]

        # In a real implementation, this would open the document
        messagebox.showinfo("View Document", f"Opening document: {doc_name}")

    def _download_selected_document(self) -> None:
        """Download the selected document"""
        selection = self.docs_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a document to download.")
            return

        item = self.docs_tree.item(selection[0])
        doc_name = item['values'][0]

        # In a real implementation, this would download the document
        messagebox.showinfo("Download", f"Downloading: {doc_name}")

    def _on_message_select(self, event) -> None:
        """Handle message selection"""
        selection = self.messages_tree.selection()
        if not selection:
            return

        item = self.messages_tree.item(selection[0])
        content = item['tags'][0] if item['tags'] else ""

        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.insert(tk.END, content)
        self.message_text.config(state=tk.DISABLED)

    def _compose_message(self) -> None:
        """Compose a new message"""
        # In a real implementation, this would open a message composition dialog
        messagebox.showinfo("Compose Message", "Message composition feature coming soon!")

    def _reply_to_message(self) -> None:
        """Reply to selected message"""
        selection = self.messages_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a message to reply to.")
            return

        # In a real implementation, this would open a reply dialog
        messagebox.showinfo("Reply", "Reply feature coming soon!")

    def _mark_message_read(self) -> None:
        """Mark selected message as read"""
        selection = self.messages_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a message to mark as read.")
            return

        # Update the status in the tree
        item = self.messages_tree.item(selection[0])
        values = list(item['values'])
        values[3] = "Read"  # Status column
        self.messages_tree.item(selection[0], values=values)

        messagebox.showinfo("Success", "Message marked as read.")

    def _change_password(self) -> None:
        """Change client password"""
        # In a real implementation, this would open a password change dialog
        messagebox.showinfo("Change Password", "Password change feature coming soon!")

    def _setup_2fa(self) -> None:
        """Setup two-factor authentication"""
        # In a real implementation, this would open 2FA setup
        messagebox.showinfo("Setup 2FA", "2FA setup feature coming soon!")

    def _logout(self) -> None:
        """Logout and close the portal"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()