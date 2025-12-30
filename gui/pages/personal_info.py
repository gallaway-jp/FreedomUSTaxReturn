"""
Personal Information page
"""

import tkinter as tk
from tkinter import ttk
from gui.widgets.form_field import FormField
from gui.widgets.section_header import SectionHeader

class PersonalInfoPage(ttk.Frame):
    """Personal information collection page"""
    
    def __init__(self, parent, tax_data, main_window):
        super().__init__(parent)
        self.tax_data = tax_data
        self.main_window = main_window
        
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
        """Build the personal information form"""
        # Page title
        title = ttk.Label(
            self.scrollable_frame,
            text="Personal Information",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10), anchor="w")
        
        instruction = ttk.Label(
            self.scrollable_frame,
            text="Please provide your personal information as it appears on your Social Security card.",
            wraplength=700,
            foreground="gray"
        )
        instruction.pack(pady=(0, 20), anchor="w")
        
        # Taxpayer Information
        SectionHeader(self.scrollable_frame, "Taxpayer Information").pack(fill="x", pady=(10, 10))
        
        taxpayer_frame = ttk.Frame(self.scrollable_frame)
        taxpayer_frame.pack(fill="x", pady=5)
        
        # Name fields in a row
        name_frame = ttk.Frame(taxpayer_frame)
        name_frame.pack(fill="x", pady=5)
        
        self.first_name = FormField(
            name_frame,
            "First Name",
            self.tax_data.get("personal_info.first_name"),
            width=25,
            required=True
        )
        self.first_name.pack(side="left", padx=(0, 10))
        
        self.middle_initial = FormField(
            name_frame,
            "MI",
            self.tax_data.get("personal_info.middle_initial"),
            width=5
        )
        self.middle_initial.pack(side="left", padx=(0, 10))
        
        self.last_name = FormField(
            name_frame,
            "Last Name",
            self.tax_data.get("personal_info.last_name"),
            width=25,
            required=True
        )
        self.last_name.pack(side="left")
        
        # SSN and DOB
        ssn_dob_frame = ttk.Frame(taxpayer_frame)
        ssn_dob_frame.pack(fill="x", pady=5)
        
        self.ssn = FormField(
            ssn_dob_frame,
            "Social Security Number",
            self.tax_data.get("personal_info.ssn"),
            field_type="ssn",
            required=True,
            tooltip="Enter your 9-digit Social Security Number in XXX-XX-XXXX format. This is required for your tax return."
        )
        self.ssn.pack(side="left", padx=(0, 10))
        
        self.dob = FormField(
            ssn_dob_frame,
            "Date of Birth (MM/DD/YYYY)",
            self.tax_data.get("personal_info.date_of_birth"),
            field_type="date",
            required=True,
            tooltip="Enter your date of birth in MM/DD/YYYY format. This helps determine your filing requirements."
        )
        self.dob.pack(side="left", padx=(0, 10))
        
        self.occupation = FormField(
            ssn_dob_frame,
            "Occupation",
            self.tax_data.get("personal_info.occupation"),
            width=25
        )
        self.occupation.pack(side="left")
        
        # Address
        SectionHeader(self.scrollable_frame, "Mailing Address").pack(fill="x", pady=(20, 10))
        
        address_frame = ttk.Frame(self.scrollable_frame)
        address_frame.pack(fill="x", pady=5)
        
        self.address = FormField(
            address_frame,
            "Street Address",
            self.tax_data.get("personal_info.address"),
            width=60,
            required=True
        )
        self.address.pack(fill="x", pady=5)
        
        city_state_zip = ttk.Frame(address_frame)
        city_state_zip.pack(fill="x", pady=5)
        
        self.city = FormField(
            city_state_zip,
            "City",
            self.tax_data.get("personal_info.city"),
            width=30,
            required=True
        )
        self.city.pack(side="left", padx=(0, 10))
        
        self.state = FormField(
            city_state_zip,
            "State",
            self.tax_data.get("personal_info.state"),
            width=10,
            required=True
        )
        self.state.pack(side="left", padx=(0, 10))
        
        self.zip_code = FormField(
            city_state_zip,
            "ZIP Code",
            self.tax_data.get("personal_info.zip_code"),
            width=15,
            field_type="zip",
            required=True
        )
        self.zip_code.pack(side="left")
        
        # Contact Information
        SectionHeader(self.scrollable_frame, "Contact Information").pack(fill="x", pady=(20, 10))
        
        contact_frame = ttk.Frame(self.scrollable_frame)
        contact_frame.pack(fill="x", pady=5)
        
        contact_row = ttk.Frame(contact_frame)
        contact_row.pack(fill="x", pady=5)
        
        self.email = FormField(
            contact_row,
            "Email Address",
            self.tax_data.get("personal_info.email"),
            width=35,
            field_type="email",
            tooltip="Enter your email address. This will be used for IRS communications if you e-file."
        )
        self.email.pack(side="left", padx=(0, 10))
        
        self.phone = FormField(
            contact_row,
            "Phone Number",
            self.tax_data.get("personal_info.phone"),
            width=20,
            field_type="phone",
            tooltip="Enter your phone number including area code. This may be used for IRS verification."
        )
        self.phone.pack(side="left")
        
        # Save button
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=30)
        
        save_btn = ttk.Button(
            button_frame,
            text="Save and Continue",
            command=self.save_and_continue
        )
        save_btn.pack(side="right")
    
    def save_and_continue(self):
        """Save data and move to next page"""
        # Validate all required fields
        fields_to_validate = [
            self.first_name, self.last_name, self.ssn, self.dob,
            self.address, self.city, self.state, self.zip_code
        ]
        
        all_valid = True
        for field in fields_to_validate:
            if not field.is_field_valid():
                all_valid = False
                field.focus()  # Focus on first invalid field
                break
        
        if not all_valid:
            from tkinter import messagebox
            messagebox.showerror("Validation Error", "Please correct the highlighted fields before continuing.")
            return
        
        # Save all fields
        self.tax_data.set("personal_info.first_name", self.first_name.get())
        self.tax_data.set("personal_info.middle_initial", self.middle_initial.get())
        self.tax_data.set("personal_info.last_name", self.last_name.get())
        self.tax_data.set("personal_info.ssn", self.ssn.get())
        self.tax_data.set("personal_info.date_of_birth", self.dob.get())
        self.tax_data.set("personal_info.occupation", self.occupation.get())
        self.tax_data.set("personal_info.address", self.address.get())
        self.tax_data.set("personal_info.city", self.city.get())
        self.tax_data.set("personal_info.state", self.state.get())
        self.tax_data.set("personal_info.zip_code", self.zip_code.get())
        self.tax_data.set("personal_info.email", self.email.get())
        self.tax_data.set("personal_info.phone", self.phone.get())
        
        # Navigate to next page
        self.main_window.show_page("filing_status")
