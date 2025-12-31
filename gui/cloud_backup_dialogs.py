"""
Cloud Backup Dialogs - GUI for cloud backup management

Provides dialogs for configuring cloud backup settings and managing backups.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional
import threading
from pathlib import Path

from services.cloud_backup_service import CloudBackupService, BackupMetadata
from config.app_config import AppConfig


class CloudConfigDialog:
    """
    Dialog for configuring cloud backup settings.
    """

    def __init__(self, parent: tk.Toplevel, backup_service: CloudBackupService):
        """
        Initialize cloud configuration dialog.

        Args:
            parent: Parent window
            backup_service: Cloud backup service instance
        """
        self.parent = parent
        self.backup_service = backup_service
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Cloud Backup Configuration")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Cloud Backup Settings",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Provider selection
        provider_frame = ttk.LabelFrame(main_frame, text="Cloud Provider", padding=10)
        provider_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(provider_frame, text="Provider:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.provider_var = tk.StringVar(value=self.backup_service.cloud_config.provider)
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.provider_var,
                                     values=["local", "dropbox", "google_drive", "onedrive"],
                                     state="readonly", width=20)
        provider_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)

        # Local provider note
        self.local_note = ttk.Label(provider_frame,
                                   text="Local storage (for testing) - files stored in ~/FreedomUSTaxReturn_Cloud",
                                   wraplength=350, foreground="blue")
        self.local_note.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Authentication frame (initially hidden for local provider)
        self.auth_frame = ttk.LabelFrame(main_frame, text="Authentication", padding=10)

        ttk.Label(self.auth_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_key_var = tk.StringVar(value=self.backup_service.cloud_config.api_key or "")
        ttk.Entry(self.auth_frame, textvariable=self.api_key_var, width=40).grid(row=0, column=1, pady=2)

        ttk.Label(self.auth_frame, text="API Secret:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.api_secret_var = tk.StringVar(value=self.backup_service.cloud_config.api_secret or "")
        ttk.Entry(self.auth_frame, textvariable=self.api_secret_var, width=40, show="*").grid(row=1, column=1, pady=2)

        # Backup folder
        folder_frame = ttk.LabelFrame(main_frame, text="Backup Settings", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(folder_frame, text="Backup Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.folder_var = tk.StringVar(value=self.backup_service.cloud_config.backup_folder)
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=40).grid(row=0, column=1, pady=2)

        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 20))

        self.status_var = tk.StringVar(value="Ready to configure")
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Test Connection", command=self._test_connection).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT)

        # Initialize provider display
        self._on_provider_changed()

    def _on_provider_changed(self, event=None):
        """Handle provider selection change"""
        provider = self.provider_var.get()

        if provider == "local":
            # Hide auth frame for local provider
            self.auth_frame.pack_forget()
            self.local_note.pack(fill=tk.X, pady=(10, 0))
        else:
            # Show auth frame for cloud providers
            self.auth_frame.pack(fill=tk.X, pady=(0, 20))
            self.local_note.pack_forget()

    def _test_connection(self):
        """Test cloud provider connection"""
        try:
            self.status_var.set("Testing connection...")

            # Configure provider with current settings
            config_kwargs = {
                'backup_folder': self.folder_var.get()
            }

            if self.provider_var.get() != "local":
                config_kwargs.update({
                    'api_key': self.api_key_var.get(),
                    'api_secret': self.api_secret_var.get()
                })

            success = self.backup_service.configure_cloud_provider(
                self.provider_var.get(),
                **config_kwargs
            )

            if success:
                self.status_var.set("✓ Connection successful")
            else:
                self.status_var.set("✗ Connection failed")

        except Exception as e:
            self.status_var.set(f"✗ Error: {str(e)}")

    def _save(self):
        """Save cloud configuration"""
        try:
            config_kwargs = {
                'backup_folder': self.folder_var.get()
            }

            if self.provider_var.get() != "local":
                config_kwargs.update({
                    'api_key': self.api_key_var.get(),
                    'api_secret': self.api_secret_var.get()
                })

            success = self.backup_service.configure_cloud_provider(
                self.provider_var.get(),
                **config_kwargs
            )

            if success:
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("Configuration Failed", "Failed to configure cloud provider")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def _cancel(self):
        """Cancel configuration"""
        self.result = False
        self.dialog.destroy()

    def show(self) -> bool:
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result or False


class CreateBackupDialog:
    """
    Dialog for creating a new backup.
    """

    def __init__(self, parent: tk.Toplevel, backup_service: CloudBackupService, config: AppConfig):
        """
        Initialize backup creation dialog.

        Args:
            parent: Parent window
            backup_service: Cloud backup service instance
            config: Application configuration
        """
        self.parent = parent
        self.backup_service = backup_service
        self.config = config
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Backup")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Create Cloud Backup",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ttk.Label(main_frame,
                              text="Create an encrypted backup of your tax data in the cloud.\n"
                                   "This will securely store your returns and data for safekeeping.",
                              wraplength=450, justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))

        # Files to backup
        files_frame = ttk.LabelFrame(main_frame, text="Files to Include", padding=10)
        files_frame.pack(fill=tk.X, pady=(0, 20))

        # Default files
        self.selected_files = [
            self.config.safe_dir / "tax_data.json",
            self.config.safe_dir / "audit_log.json",
            self.config.safe_dir / "encryption.key"
        ]

        self.file_vars = []
        for i, file_path in enumerate(self.selected_files):
            var = tk.BooleanVar(value=True)
            self.file_vars.append(var)

            ttk.Checkbutton(files_frame, text=str(file_path.name),
                           variable=var).pack(anchor=tk.W, pady=1)

        # Description
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(desc_frame, text="Description:").pack(anchor=tk.W)
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var, width=50).pack(fill=tk.X, pady=(5, 0))

        # Status
        self.status_var = tk.StringVar(value="Ready to create backup")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Create Backup", command=self._create_backup).pack(side=tk.RIGHT)

    def _create_backup(self):
        """Create the backup"""
        try:
            self.status_var.set("Creating backup...")

            # Get selected files
            files_to_backup = []
            for i, var in enumerate(self.file_vars):
                if var.get():
                    files_to_backup.append(self.selected_files[i])

            if not files_to_backup:
                messagebox.showwarning("No Files Selected", "Please select at least one file to backup")
                return

            # Create backup in background thread
            def create_backup_thread():
                try:
                    backup_id = self.backup_service.create_backup(
                        files_to_backup,
                        self.desc_var.get()
                    )

                    if backup_id:
                        self.result = backup_id
                        self.status_var.set(f"✓ Backup created successfully: {backup_id}")
                    else:
                        self.status_var.set("✗ Failed to create backup")

                except Exception as e:
                    self.status_var.set(f"✗ Error: {str(e)}")

            threading.Thread(target=create_backup_thread, daemon=True).start()

        except Exception as e:
            self.status_var.set(f"✗ Error: {str(e)}")

    def _cancel(self):
        """Cancel backup creation"""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[str]:
        """Show dialog and return backup ID if successful"""
        self.dialog.wait_window()
        return self.result


class RestoreBackupDialog:
    """
    Dialog for restoring from a backup.
    """

    def __init__(self, parent: tk.Toplevel, backup_service: CloudBackupService):
        """
        Initialize backup restore dialog.

        Args:
            parent: Parent window
            backup_service: Cloud backup service instance
        """
        self.parent = parent
        self.backup_service = backup_service
        self.result = False

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Restore from Backup")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self._create_widgets()
        self._load_backups()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Restore from Cloud Backup",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Backup list
        list_frame = ttk.LabelFrame(main_frame, text="Available Backups", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Create treeview for backups
        columns = ("ID", "Date", "Files", "Size", "Description")
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)

        for col in columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=100)

        self.backup_tree.column("Description", width=200)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar.set)

        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Restore location
        location_frame = ttk.LabelFrame(main_frame, text="Restore Location", padding=10)
        location_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(location_frame, text="Restore to:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.location_var = tk.StringVar()
        location_entry = ttk.Entry(location_frame, textvariable=self.location_var, width=40)
        location_entry.grid(row=0, column=1, pady=2)

        ttk.Button(location_frame, text="Browse...", command=self._browse_location).grid(row=0, column=2, padx=(5, 0))

        # Status
        self.status_var = tk.StringVar(value="Select a backup to restore")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Restore", command=self._restore_backup).pack(side=tk.RIGHT)

    def _load_backups(self):
        """Load available backups into the treeview"""
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)

        # Load backups
        backups = self.backup_service.list_backups()

        for backup in sorted(backups, key=lambda x: x.timestamp, reverse=True):
            size_mb = f"{backup.total_size / (1024*1024):.1f} MB"
            date_str = backup.timestamp.strftime("%Y-%m-%d %H:%M")

            self.backup_tree.insert("", tk.END, values=(
                backup.backup_id,
                date_str,
                backup.file_count,
                size_mb,
                backup.description
            ))

    def _browse_location(self):
        """Browse for restore location"""
        directory = filedialog.askdirectory(
            title="Select Restore Location",
            initialdir=str(Path.home())
        )
        if directory:
            self.location_var.set(directory)

    def _restore_backup(self):
        """Restore the selected backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to restore")
            return

        item = self.backup_tree.item(selection[0])
        backup_id = item['values'][0]

        restore_path_str = self.location_var.get()
        if not restore_path_str:
            messagebox.showwarning("No Location", "Please select a restore location")
            return

        restore_path = Path(restore_path_str)
        if not restore_path.exists():
            try:
                restore_path.mkdir(parents=True)
            except Exception as e:
                messagebox.showerror("Invalid Location", f"Cannot create directory: {e}")
                return

        # Confirm restore
        if not messagebox.askyesno("Confirm Restore",
                                  f"Are you sure you want to restore backup '{backup_id}'?\n\n"
                                  f"This will overwrite any existing files in:\n{restore_path}"):
            return

        try:
            self.status_var.set("Restoring backup...")

            # Restore in background thread
            def restore_thread():
                try:
                    success = self.backup_service.restore_backup(backup_id, restore_path)

                    if success:
                        self.result = True
                        self.status_var.set("✓ Backup restored successfully")
                        messagebox.showinfo("Success", f"Backup '{backup_id}' restored successfully to {restore_path}")
                    else:
                        self.status_var.set("✗ Failed to restore backup")

                except Exception as e:
                    self.status_var.set(f"✗ Error: {str(e)}")

            threading.Thread(target=restore_thread, daemon=True).start()

        except Exception as e:
            self.status_var.set(f"✗ Error: {str(e)}")

    def _cancel(self):
        """Cancel restore operation"""
        self.result = False
        self.dialog.destroy()

    def show(self) -> bool:
        """Show dialog and return success status"""
        self.dialog.wait_window()
        return self.result


class BackupStatusDialog:
    """
    Dialog showing backup status and statistics.
    """

    def __init__(self, parent: tk.Toplevel, backup_service: CloudBackupService):
        """
        Initialize backup status dialog.

        Args:
            parent: Parent window
            backup_service: Cloud backup service instance
        """
        self.parent = parent
        self.backup_service = backup_service

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Backup Status")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self._create_widgets()
        self._load_status()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Cloud Backup Status",
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))

        # Status info
        self.status_text = tk.Text(main_frame, height=15, width=60, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)

        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Make text read-only
        self.status_text.config(state=tk.DISABLED)

        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Close", command=self._close).pack(side=tk.RIGHT)

    def _load_status(self):
        """Load and display backup status"""
        try:
            status = self.backup_service.get_backup_status()

            status_info = f"""Cloud Backup Status
{'='*30}

Cloud Provider: {status['cloud_provider']}
Authentication: {'✓ Connected' if status['cloud_authenticated'] else '✗ Not Connected'}

Backup Statistics:
• Total Backups: {status['total_backups']}
• Total Size: {status['total_size_mb']} MB

Date Range:
• Latest Backup: {status['latest_backup'] or 'None'}
• Oldest Backup: {status['oldest_backup'] or 'None'}

Available Backups:
"""

            if status['total_backups'] > 0:
                backups = self.backup_service.list_backups()
                for backup in sorted(backups, key=lambda x: x.timestamp, reverse=True):
                    status_info += f"\n• {backup.backup_id}\n"
                    status_info += f"  Date: {backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    status_info += f"  Files: {backup.file_count}, Size: {backup.total_size / (1024*1024):.1f} MB\n"
                    if backup.description:
                        status_info += f"  Description: {backup.description}\n"
            else:
                status_info += "\nNo backups found. Create your first backup to get started."

            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, status_info)
            self.status_text.config(state=tk.DISABLED)

        except Exception as e:
            error_msg = f"Error loading backup status: {str(e)}"
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, error_msg)
            self.status_text.config(state=tk.DISABLED)

    def _close(self):
        """Close the dialog"""
        self.dialog.destroy()

    def show(self):
        """Show the dialog"""
        self.dialog.wait_window()</content>
<parameter name="filePath">d:\Development\Python\FreedomUSTaxReturn\gui\cloud_backup_dialogs.py