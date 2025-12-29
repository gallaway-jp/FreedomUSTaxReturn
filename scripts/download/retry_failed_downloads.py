import csv
import os
import requests
import time
from pathlib import Path

def sanitize_filename(filename):
    """Remove or replace characters that are invalid in Windows filenames"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def retry_failed_downloads():
    csv_file = r'C:\Users\Colin\Downloads\irs_forms_with_links.csv'
    output_dir = r'C:\Users\Colin\Downloads\IRSTaxReturnDocumentation'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Read CSV and find missing files
    print("Checking for missing files...")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        forms = list(reader)
    
    missing_files = []
    for form in forms:
        product_number = form.get('Product Number', '').strip()
        pdf_link = form.get('PDF Link', '').strip()
        
        if not pdf_link:
            continue
            
        filename = sanitize_filename(product_number) + '.pdf'
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            missing_files.append({
                'product_number': product_number,
                'pdf_link': pdf_link,
                'filename': filename,
                'filepath': filepath
            })
    
    if not missing_files:
        print("No missing files found. All downloads were successful!")
        return
    
    print(f"Found {len(missing_files)} missing file(s):\n")
    for item in missing_files:
        print(f"  - {item['product_number']}")
    
    print(f"\nRetrying downloads...\n")
    
    success = 0
    failed = 0
    
    for item in missing_files:
        try:
            print(f"Downloading {item['product_number']}...", end=' ')
            response = requests.get(item['pdf_link'], headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(item['filepath'], 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024
            print(f"✓ ({file_size:.1f} KB)")
            success += 1
            
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Retry Summary:")
    print(f"  Successfully downloaded: {success}")
    print(f"  Failed: {failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        retry_failed_downloads()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
