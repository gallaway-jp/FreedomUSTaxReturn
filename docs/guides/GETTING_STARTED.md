# Getting Started with Freedom US Tax Return

## Quick Start

1. **Download or Clone the Repository**
   ```bash
   cd d:\Development\Python\FreedomUSTaxReturn
   ```

2. **Run the Application**
   ```bash
   python main.py
   ```

3. **Start Filling Out Your Tax Return**
   - The application will open with the Personal Information page
   - Fill out each section in order
   - Click "Save and Continue" to move to the next section
   - You can save your progress at any time using the "Save Progress" button

## Step-by-Step Guide

### 1. Personal Information
- Enter your full name as it appears on your Social Security card
- Enter your Social Security Number (SSN)
- Provide your date of birth and occupation
- Enter your current mailing address
- Add contact information (email and phone)

**Tips:**
- Double-check your SSN for accuracy
- Use your current mailing address where you want to receive correspondence from the IRS

### 2. Filing Status
Choose the filing status that applies to you:

- **Single**: You are unmarried or legally separated
- **Married Filing Jointly (MFJ)**: You are married and filing together with your spouse
- **Married Filing Separately (MFS)**: You are married but filing separately
- **Head of Household (HOH)**: You are unmarried and pay more than half the cost of keeping up a home for a qualifying person
- **Qualifying Widow(er) (QW)**: Your spouse died in the previous two years and you have a dependent child

**Tips:**
- Your filing status affects your tax rates and standard deduction
- The application shows your standard deduction amount after you select your status
- Most married couples benefit from filing jointly

### 3. Income
Report all sources of income:

#### W-2 Wages
- Click "+ Add W-2" for each employer
- Enter employer name and EIN from Box b
- Enter wages from Box 1
- Enter federal withholding from Box 2
- Enter Social Security and Medicare wages from Boxes 3 and 5

**Where to find it:** Your employer should provide Form W-2 by January 31

#### Interest Income
- Click "+ Add Interest Income"
- Enter the payer name and amount from Form 1099-INT

**Where to find it:** Banks and financial institutions send Form 1099-INT if you earned more than $10 in interest

#### Dividend Income
- Click "+ Add Dividend Income"
- Enter the payer name and amount from Form 1099-DIV

**Where to find it:** Investment companies send Form 1099-DIV if you received dividends

**Tips:**
- Gather all your tax forms before starting
- Don't forget interest from all bank accounts
- Include dividends from stocks and mutual funds

### 4. Deductions
Choose between standard deduction or itemizing:

#### Standard Deduction (Recommended for Most People)
- Automatically calculated based on your filing status
- No additional documentation needed
- Easiest option

**2025 Standard Deduction Amounts:**
- Single: $15,750
- Married Filing Jointly: $31,500
- Head of Household: $23,625

#### Itemized Deductions
Only choose this if your total itemized deductions exceed the standard deduction.

Itemized deductions include:
- Medical and dental expenses (over 7.5% of AGI)
- State and local taxes (max $10,000)
- Mortgage interest
- Charitable contributions

**Tips:**
- Most people benefit from the standard deduction
- Click "Calculate Total" to see if itemizing saves you money
- Keep receipts for all itemized deductions

### 5. Credits & Taxes
Claim tax credits you qualify for:

#### Child Tax Credit
- Enter the number of qualifying children under age 17
- Each qualifying child can get you up to $2,000

**Who qualifies:**
- Child is under 17 at end of tax year
- Child is your dependent
- Child lived with you more than half the year

#### Earned Income Credit (EIC)
- For low to moderate income workers
- Credit amount depends on income and number of children
- Can be refundable

#### Education Credits
- American Opportunity Tax Credit: Up to $2,500 (first 4 years of college)
- Lifetime Learning Credit: Up to $2,000 (any post-secondary education)

**Tips:**
- Tax credits reduce your tax dollar-for-dollar
- Review IRS requirements for each credit carefully
- Some credits are refundable (you can get money back even if you owe no tax)

### 6. Payments
Enter all tax payments you made:

#### Federal Withholding
- Automatically calculated from your W-2 forms
- This is the amount your employer(s) withheld from your paychecks

#### Estimated Tax Payments
- If you made quarterly estimated tax payments, add them here
- Include the date and amount of each payment

#### Prior Year Overpayment
- If you had a refund last year and chose to apply it to this year, enter that amount

**Tips:**
- Your W-2 withholding is automatically totaled
- Add all estimated payments you made during the year
- Save receipts for estimated payments

### 7. Review & Forms
The Form Viewer shows:

- **Tax Return Summary**: Overview of your income, deductions, and tax
- **Refund or Amount Owed**: Your bottom line
- **Required Forms**: List of all IRS forms you need based on your entries
- **Form 1040 Preview**: Text preview of your main tax form

**What to check:**
- Verify all amounts are correct
- Check that your name and SSN are accurate
- Review the list of required forms
- Note whether you're getting a refund or owe taxes

### 8. Save Your Return
- Click "Save Return" to save your progress
- The file is saved in JSON format
- You can load it later to continue working

## Saving and Loading

### Save Progress
- Click the "Save Progress" button in the sidebar
- Choose a location and filename
- Recommended format: `tax_return_2025_LastName.json`

### Load Progress
- Click "Load Progress" in the sidebar
- Select your previously saved file
- All your data will be restored

## Common Questions

### Q: Is this application really free?
**A:** Yes! This is completely free and open-source. No hidden costs.

### Q: Can I e-file with this application?
**A:** Not yet. Currently, this application helps you prepare your return and see what forms you need. E-filing functionality is planned for future versions.

### Q: What about state taxes?
**A:** This version focuses on federal taxes. State tax support may be added in future versions.

### Q: Is my data safe?
**A:** All data is stored locally on your computer. Nothing is sent over the internet. Your tax information stays private.

### Q: Can I print my forms?
**A:** Currently, you can export to PDF (requires additional setup). Direct form printing is planned for future versions.

### Q: What if I make a mistake?
**A:** You can go back to any section and change your information. Just click the section in the sidebar.

### Q: Do I need to fill out everything at once?
**A:** No! Save your progress at any time and come back later.

## Tips for Success

1. **Gather All Documents First**
   - W-2s from all employers
   - 1099 forms (INT, DIV, MISC, NEC, etc.)
   - Previous year's tax return
   - Records of deductible expenses
   - Records of estimated tax payments

2. **Work Through Systematically**
   - Complete each section in order
   - Don't skip sections
   - Save frequently

3. **Double-Check Everything**
   - Verify SSN and other identification numbers
   - Check all dollar amounts
   - Review calculations

4. **Keep Records**
   - Save your completed return
   - Keep all supporting documents for at least 3 years
   - Make a backup copy

5. **When in Doubt, Get Help**
   - Consult IRS publications
   - Consider professional tax advice for complex situations
   - Visit IRS.gov for official guidance

## Next Steps After Completing Your Return

1. **Review Everything** - Carefully review all entries and calculations
2. **Save Your Work** - Make sure you save your completed return
3. **Print Forms** - Export to PDF or print your forms
4. **File Your Return** - Mail your return to the IRS or use approved e-filing software
5. **Keep Records** - Save copies of your return and all supporting documents

## Getting Help

- **IRS Website**: [www.irs.gov](https://www.irs.gov)
- **IRS Forms & Instructions**: Available in the IRSTaxReturnDocumentation folder
- **IRS Help**: 1-800-829-1040

## Important Disclaimer

This is a free, open-source tool for educational purposes. While it follows IRS guidelines and uses official IRS forms and instructions, please consult with a tax professional for complex tax situations. Always review your return carefully before filing with the IRS.

---

**Ready to start?** Run `python main.py` and begin your tax return!
