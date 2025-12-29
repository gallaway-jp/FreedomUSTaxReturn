import csv
import requests
import os
import time
from pathlib import Path
from urllib.parse import urlparse

def sanitize_filename(filename):
    """Remove or replace characters that are invalid in Windows filenames"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def download_irs_forms():
    csv_file = r'C:\Users\Colin\Downloads\irs_forms_with_links.csv'
    output_dir = r'C:\Users\Colin\Downloads\IRSTaxReturnDocumentation'
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Read CSV file
    print(f"Reading CSV file: {csv_file}")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        forms = list(reader)
    
    total_forms = len(forms)
    print(f"Found {total_forms} forms to download\n")
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for idx, form in enumerate(forms, 1):
        product_number = form.get('Product Number', '').strip()
        pdf_link = form.get('PDF Link', '').strip()
        
        if not pdf_link:
            print(f"[{idx}/{total_forms}] Skipping {product_number} - No PDF link")
            skipped += 1
            continue
        
        # Create filename from product number
        filename = sanitize_filename(product_number) + '.pdf'
        filepath = os.path.join(output_dir, filename)
        
        # Skip if already downloaded
        if os.path.exists(filepath):
            print(f"[{idx}/{total_forms}] Skipping {product_number} - Already exists")
            skipped += 1
            continue
        
        try:
            print(f"[{idx}/{total_forms}] Downloading {product_number}...", end=' ')
            response = requests.get(pdf_link, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024  # KB
            print(f"✓ ({file_size:.1f} KB)")
            downloaded += 1
            
            # Be nice to the server - wait between downloads
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            failed += 1
            continue
    
    print(f"\n{'='*60}")
    print(f"Download Summary:")
    print(f"  Total forms: {total_forms}")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Output directory: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        download_irs_forms()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
