import PyPDF2

pdf_path = 'IRSTaxReturnDocumentation/rp-25-32.pdf'
with open(pdf_path, 'rb', encoding='utf-8') as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    
    # Search for tax bracket information - usually in first 15 pages
    for i in range(min(15, len(reader.pages))):
        text = reader.pages[i].extract_text()
        
        # Look for tax rate tables
        if 'tax rate' in text.lower() or 'taxable income' in text.lower():
            print(f"=== Page {i+1} - Tax Brackets ===")
            print(text)
            print("\n" + "="*80 + "\n")
