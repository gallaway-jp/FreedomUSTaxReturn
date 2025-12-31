"""
Dependents page - manage qualifying children and other dependents
"""

import tkinter as tk
from tkinter import ttk, messagebox
from gui.widgets.section_header import SectionHeader
from gui.widgets.form_field import FormField

class DependentsPage(ttk.Frame):
    """Dependents information collection page"""

    def __init__(self, parent, tax_data, main_window, theme_manager=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        self.theme_manager = theme_manager

        # Create scrollable canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Build form
        self.build_form()

    def build_form(self):
        """Build the dependents form"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Dependents",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")

        instruction = ttk.Label(
            self.scrollable_frame,
            text="Enter information for all dependents claimed on your tax return.\n"
                 "Qualifying children and other dependents may affect your tax credits and deductions.",
            wraplength=700,
            justify="left"
        )
        instruction.pack(pady=(0, 20), anchor="w")

        # Dependents list section
        SectionHeader(self.scrollable_frame, "Dependents").pack(fill="x", pady=(20, 10))

        # List frame for dependents
        list_frame = ttk.LabelFrame(self.scrollable_frame, text="Current Dependents", padding="10")
        list_frame.pack(fill="x", pady=(0, 20))

        # Dependents listbox with scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill="both", expand=True)

        self.dependents_listbox = tk.Listbox(
            listbox_frame,
            height=6,
            selectmode=tk.SINGLE,
            font=("Arial", 10)
        )
        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.dependents_listbox.yview)
        self.dependents_listbox.configure(yscrollcommand=listbox_scrollbar.set)

        self.dependents_listbox.pack(side="left", fill="both", expand=True)
        listbox_scrollbar.pack(side="right", fill="y")

        # Buttons for managing dependents
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(button_frame, text="Add Dependent", command=self.add_dependent).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_dependent).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_dependent).pack(side="left")

        # Load existing dependents
        self.refresh_dependents_list()

    def refresh_dependents_list(self):
        """Refresh the dependents list display"""
        self.dependents_listbox.delete(0, tk.END)

        dependents = self.tax_data.get("dependents", [])
        if not dependents:
            self.dependents_listbox.insert(tk.END, "No dependents added yet")
            return

        for i, dependent in enumerate(dependents):
            name = f"{dependent.get('first_name', '')} {dependent.get('last_name', '')}".strip()
            relationship = dependent.get('relationship', 'Unknown')
            age = self._calculate_age(dependent.get('birth_date', ''))
            display_text = f"{name} - {relationship}"
            if age:
                display_text += f" (Age: {age})"
            self.dependents_listbox.insert(tk.END, display_text)

    def _calculate_age(self, birth_date_str):
        """Calculate age from birth date string"""
        if not birth_date_str:
            return None
        try:
            from datetime import datetime
            birth_date = datetime.strptime(birth_date_str, '%m/%d/%Y')
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except:
            return None

    def add_dependent(self):
        """Add a new dependent"""
        dialog = DependentDialog(self, self.tax_data, self.theme_manager)
        self.wait_window(dialog)
        self.refresh_dependents_list()

    def edit_dependent(self):
        """Edit the selected dependent"""
        selection = self.dependents_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a dependent to edit.")
            return

        index = selection[0]
        dependents = self.tax_data.get("dependents", [])
        if index >= len(dependents):
            return

        dialog = DependentDialog(self, self.tax_data, self.theme_manager, edit_index=index)
        self.wait_window(dialog)
        self.refresh_dependents_list()

    def delete_dependent(self):
        """Delete the selected dependent"""
        selection = self.dependents_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a dependent to delete.")
            return

        index = selection[0]
        dependents = self.tax_data.get("dependents", [])
        if index >= len(dependents):
            return

        dependent = dependents[index]
        name = f"{dependent.get('first_name', '')} {dependent.get('last_name', '')}".strip()

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete dependent '{name}'?"):
            # Remove from list
            dependents.pop(index)
            self.tax_data.set("dependents", dependents)
            self.refresh_dependents_list()
            messagebox.showinfo("Success", f"Dependent '{name}' has been deleted.")
    
    def refresh_data(self):
        """Refresh the dependents list for the current tax year"""
        self.refresh_dependents_list()


class DependentDialog(tk.Toplevel):
    """Dialog for entering dependent information"""

    def __init__(self, parent, tax_data, theme_manager=None, edit_index=None):
        super().__init__(parent)
        self.tax_data = tax_data
        self.theme_manager = theme_manager
        self.edit_index = edit_index

        self.title("Add Dependent" if edit_index is None else "Edit Dependent")
        self.geometry("500x600")

        self.transient(parent)
        self.grab_set()

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Dependent Information", font=("Arial", 14, "bold")).pack(pady=(0, 20))

        # Personal Information
        ttk.Label(main_frame, text="Personal Information", font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 10))

        # Name fields
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill="x", pady=(0, 10))

        self.first_name = FormField(
            name_frame,
            "First Name",
            "",
            width=15,
            required=True,
            theme_manager=self.theme_manager
        )
        self.first_name.pack(side="left", padx=(0, 10))

        self.last_name = FormField(
            name_frame,
            "Last Name",
            "",
            width=15,
            required=True,
            theme_manager=self.theme_manager
        )
        self.last_name.pack(side="left")

        # SSN
        self.ssn = FormField(
            main_frame,
            "Social Security Number",
            "",
            field_type="ssn",
            required=True,
            theme_manager=self.theme_manager
        )
        self.ssn.pack(fill="x", pady=(0, 10))

        # Birth date
        self.birth_date = FormField(
            main_frame,
            "Birth Date (MM/DD/YYYY)",
            "",
            field_type="date",
            required=True,
            theme_manager=self.theme_manager
        )
        self.birth_date.pack(fill="x", pady=(0, 10))

        # Relationship
        ttk.Label(main_frame, text="Relationship to Taxpayer", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))

        self.relationship_var = tk.StringVar()
        relationship_frame = ttk.Frame(main_frame)
        relationship_frame.pack(fill="x", pady=(0, 10))

        relationships = [
            "Son", "Daughter", "Step-son", "Step-daughter",
            "Brother", "Sister", "Step-brother", "Step-sister",
            "Father", "Mother", "Grandfather", "Grandmother",
            "Grandson", "Granddaughter", "Uncle", "Aunt",
            "Nephew", "Niece", "Other"
        ]

        for i, rel in enumerate(relationships):
            rb = ttk.Radiobutton(
                relationship_frame,
                text=rel,
                variable=self.relationship_var,
                value=rel
            )
            rb.grid(row=i//3, column=i%3, sticky="w", padx=(0, 20), pady=2)

        # Living arrangement
        ttk.Label(main_frame, text="Living Arrangement", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))

        self.months_lived = FormField(
            main_frame,
            "Months lived in your home during tax year",
            "",
            required=True,
            theme_manager=self.theme_manager
        )
        self.months_lived.pack(fill="x", pady=(0, 10))

        # Load existing data if editing
        if self.edit_index is not None:
            self.load_dependent_data()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(30, 0))

        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 10))
        ttk.Button(
            button_frame,
            text="Save Dependent",
            command=self.save_dependent
        ).pack(side="right")

    def load_dependent_data(self):
        """Load existing dependent data for editing"""
        dependents = self.tax_data.get("dependents", [])
        if self.edit_index < len(dependents):
            dependent = dependents[self.edit_index]
            self.first_name.set(dependent.get('first_name', ''))
            self.last_name.set(dependent.get('last_name', ''))
            self.ssn.set(dependent.get('ssn', ''))
            self.birth_date.set(dependent.get('birth_date', ''))
            self.relationship_var.set(dependent.get('relationship', ''))
            self.months_lived.set(str(dependent.get('months_lived_in_home', '')))

    def save_dependent(self):
        """Save the dependent information"""
        # Validate required fields
        if not self.first_name.get().strip():
            messagebox.showerror("Validation Error", "First name is required.")
            return

        if not self.last_name.get().strip():
            messagebox.showerror("Validation Error", "Last name is required.")
            return

        if not self.ssn.get().strip():
            messagebox.showerror("Validation Error", "Social Security Number is required.")
            return

        if not self.birth_date.get():
            messagebox.showerror("Validation Error", "Birth date is required.")
            return

        if not self.relationship_var.get():
            messagebox.showerror("Validation Error", "Relationship is required.")
            return

        try:
            months = int(self.months_lived.get().strip())
            if months < 0 or months > 12:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Months lived in home must be a number between 0 and 12.")
            return

        # Create dependent data
        dependent_data = {
            'first_name': self.first_name.get().strip(),
            'last_name': self.last_name.get().strip(),
            'ssn': self.ssn.get().strip(),
            'birth_date': self.birth_date.get().strftime('%m/%d/%Y') if hasattr(self.birth_date.get(), 'strftime') else str(self.birth_date.get()),
            'relationship': self.relationship_var.get(),
            'months_lived_in_home': months
        }

        # Save to tax data
        dependents = self.tax_data.get("dependents", [])

        if self.edit_index is not None:
            # Update existing
            dependents[self.edit_index] = dependent_data
            message = "Dependent updated successfully!"
        else:
            # Add new
            dependents.append(dependent_data)
            message = "Dependent added successfully!"

        self.tax_data.set("dependents", dependents)

        messagebox.showinfo("Success", message)
        self.destroy()