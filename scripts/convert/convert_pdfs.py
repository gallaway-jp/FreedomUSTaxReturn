import PyPDF2
import os
from pathlib import Path

# Get all PDF files in the IRSTaxReturnDocumentation folder
pdf_dir = Path("IRSTaxReturnDocumentation")
pdf_files = list(pdf_dir.glob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files")

# Convert each PDF to text (skip if already exists)
converted = 0
skipped = 0

for i, pdf_file in enumerate(pdf_files, 1):
    try:
        # Create text file name
        txt_file = pdf_file.with_suffix('.txt')
        
        # Skip if already converted
        if txt_file.exists():
            skipped += 1
            if skipped % 100 == 0:
                print(f"[{i}/{len(pdf_files)}] Skipped {skipped} already converted files...")
            continue
        
        # Open and read PDF
        with open(pdf_file, 'rb') as pf:
            reader = PyPDF2.PdfReader(pf)
            
            # Extract all text
            all_text = []
            for page_num in range(len(reader.pages)):
                try:
                    text = reader.pages[page_num].extract_text()
                    all_text.append(f"=== Page {page_num + 1} ===\n{text}\n")
                except Exception as e:
                    all_text.append(f"=== Page {page_num + 1} ===\nError extracting text: {e}\n")
            
            # Write to text file
            with open(txt_file, 'w', encoding='utf-8') as tf:
                tf.write('\n'.join(all_text))
            
            converted += 1
            print(f"[{i}/{len(pdf_files)}] Converted: {pdf_file.name}")
            
    except Exception as e:
        print(f"[{i}/{len(pdf_files)}] Error converting {pdf_file.name}: {e}")

print(f"\nConversion complete! Converted: {converted}, Skipped: {skipped}, Total: {len(pdf_files)}")
