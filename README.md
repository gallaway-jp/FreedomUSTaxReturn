# Freedom US Tax Return

A completely free Python GUI application for preparing US federal income tax returns.

## Tax Year 2026

This application is designed for the **2026 tax year** (returns filed in 2027).

## Features

- **Question and Answer Style**: Easy-to-understand interface that guides you through tax preparation
- **Multiple Pages**: Organized sections for different types of information
  - Personal Information
  - Filing Status
  - Income (W-2, Interest, Dividends, etc.)
  - Deductions (Standard or Itemized)
  - Credits
  - Payments
- **Form Viewer**: View calculated forms and your tax return summary
- **Form List**: Automatically determines which forms you need based on your entries
- **Save/Load**: Save your progress and continue later
- **Based on Official IRS Documentation**: Follows IRS forms and instructions

## Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)

## Installation

No additional packages required! Just run:

```bash
python main.py
```

## Usage

1. Run `python main.py` to start the application
2. Fill out each section in order
3. Click "Save and Continue" to move between sections
4. Review your tax return in the "View Forms" section
5. Save your progress at any time

## Features by Section

### Personal Information
- Name, SSN, date of birth
- Mailing address
- Contact information

### Filing Status
- Single
- Married Filing Jointly
- Married Filing Separately
- Head of Household
- Qualifying Widow(er)

### Income
- W-2 wages and salaries
- Interest income (1099-INT)
- Dividend income (1099-DIV)
- And more...

### Deductions
- Standard deduction (recommended for most)
- Itemized deductions (medical, taxes, mortgage interest, charitable contributions)

### Credits
- Child Tax Credit
- Earned Income Credit
- Education Credits
- Retirement Savings Contributions Credit

### Payments
- Federal income tax withheld (from W-2)
- Estimated tax payments
- Prior year overpayment applied

## Testing

### Integration Tests

To run integration tests that verify GUI components can be imported without blocking the terminal:

```bash
python test_integration.py
```

Or use the batch file:
```bash
run_integration_tests.bat
```

### Unit Tests

Run unit tests with pytest:
```bash
python -m pytest tests/
```

## Project Structure

```
FreedomUSTaxReturn/
├── main.py                 # Application entry point
├── gui/
│   ├── main_window.py      # Main application window
│   ├── pages/              # Individual page components
│   │   ├── personal_info.py
│   │   ├── filing_status.py
│   │   ├── income.py
│   │   ├── deductions.py
│   │   ├── credits.py
│   │   ├── payments.py
│   │   └── form_viewer.py
│   └── widgets/            # Reusable UI components
│       ├── form_field.py
│       └── section_header.py
├── models/
│   └── tax_data.py         # Tax data model and calculations
└── IRSTaxReturnDocumentation/  # IRS forms and instructions (PDFs)
```

## Important Notes

⚠️ **Disclaimer**: This is a free, open-source tool for educational purposes. While it follows IRS guidelines, please consult with a tax professional for complex tax situations. Always review your return carefully before filing.

## Future Enhancements

- PDF form generation with actual IRS forms
- More income types (self-employment, rental, etc.)
- State tax returns
- E-filing integration
- Import from prior year returns
- More detailed calculations and validations

## License

This project is free and open source.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.
