import sys
import os

try:
    import PyPDF2
    
    pdf_path = 'IRSTaxReturnDocumentation/rp-25-32.pdf'
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        print(f"Total pages: {len(reader.pages)}\n")
        
        # Extract first 10 pages
        for i in range(min(10, len(reader.pages))):
            print(f"=== Page {i+1} ===")
            text = reader.pages[i].extract_text()
            print(text)
            print("\n")
            
except ImportError:
    # Try without PyPDF2, using alternative method
    print("PyPDF2 not available. Trying alternative methods...")
    
    # Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open('IRSTaxReturnDocumentation/rp-25-32.pdf') as pdf:
            for i, page in enumerate(pdf.pages[:10]):
                print(f"=== Page {i+1} ===")
                print(page.extract_text())
                print("\n")
    except ImportError:
        print("Please install PyPDF2 or pdfplumber: pip install PyPDF2")
        print("\nAlternatively, please provide the key figures from the PDF:")
        print("- Standard deductions for 2025")
        print("- Tax bracket thresholds for 2025")
        print("- Social Security wage base for 2025")
