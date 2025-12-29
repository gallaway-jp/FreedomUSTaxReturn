"""
PDF Field Inspector - Discover field names in IRS PDF forms
This helps identify the exact field names needed for form filling
"""

import sys
from pathlib import Path
from pypdf import PdfReader

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def inspect_pdf_fields(pdf_path: str, verbose: bool = False):
    """
    Inspect all fillable fields in a PDF form
    
    Args:
        pdf_path: Path to the PDF file
        verbose: If True, show detailed field information
    """
    try:
        reader = PdfReader(pdf_path)
        
        print(f"\n{'='*80}")
        print(f"PDF Form: {Path(pdf_path).name}")
        print(f"{'='*80}")
        print(f"Total Pages: {len(reader.pages)}")
        
        fields = reader.get_fields()
        
        if not fields:
            print("\n[WARNING] No fillable fields found in this PDF")
            return
        
        print(f"\nTotal Fillable Fields: {len(fields)}")
        print(f"{'='*80}\n")
        
        # Group fields by type
        field_types = {}
        for field_name, field_info in fields.items():
            field_type = field_info.get('/FT', 'Unknown')
            if field_type not in field_types:
                field_types[field_type] = []
            field_types[field_type].append((field_name, field_info))
        
        # Display field types summary
        print("Field Types Summary:")
        for field_type, field_list in field_types.items():
            type_name = {
                '/Tx': 'Text Fields',
                '/Btn': 'Buttons/Checkboxes',
                '/Ch': 'Choice Fields (Dropdown)',
                'Unknown': 'Unknown Type'
            }.get(field_type, field_type)
            print(f"  - {type_name}: {len(field_list)}")
        
        print(f"\n{'='*80}\n")
        
        # Display all fields
        for i, (field_name, field_info) in enumerate(sorted(fields.items()), 1):
            field_type = field_info.get('/FT', 'Unknown')
            field_value = field_info.get('/V', '')
            field_flags = field_info.get('/Ff', 0)
            
            # Type name
            type_name = {
                '/Tx': 'TEXT',
                '/Btn': 'CHECKBOX/BUTTON',
                '/Ch': 'CHOICE',
                'Unknown': 'UNKNOWN'
            }.get(field_type, field_type)
            
            print(f"[{i:3d}] {field_name}")
            print(f"      Type: {type_name}")
            
            if verbose:
                if field_value:
                    print(f"      Default Value: {field_value}")
                if field_flags:
                    print(f"      Flags: {field_flags}")
                    
                # Additional info for text fields
                if field_type == '/Tx':
                    max_len = field_info.get('/MaxLen', 'Not specified')
                    print(f"      Max Length: {max_len}")
                
                # Additional info for buttons
                if field_type == '/Btn':
                    on_value = field_info.get('/AS', field_info.get('/DV', ''))
                    print(f"      On Value: {on_value}")
            
            print()
        
    except FileNotFoundError:
        print(f"[ERROR] File not found: {pdf_path}")
    except Exception as e:
        print(f"[ERROR] Error inspecting PDF: {e}")


def inspect_common_forms():
    """Inspect common IRS forms"""
    base_dir = Path(__file__).parent.parent / "IRSTaxReturnDocumentation"
    
    common_forms = [
        "Form 1040.pdf",
        "Form 1040 (Schedule 1).pdf",
        "Form 1040 (Schedule A).pdf",
        "Form 1040 (Schedule C).pdf",
        "Form 1040 (Schedule SE).pdf",
        "Form W-2.pdf"
    ]
    
    print("Inspecting Common IRS Forms")
    print(f"Forms Directory: {base_dir}")
    
    for form_name in common_forms:
        form_path = base_dir / form_name
        
        if form_path.exists():
            inspect_pdf_fields(str(form_path), verbose=False)
        else:
            print(f"\n[WARNING] {form_name} not found")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Inspect specific file provided as argument
        pdf_path = sys.argv[1]
        verbose = '--verbose' in sys.argv or '-v' in sys.argv
        inspect_pdf_fields(pdf_path, verbose)
    else:
        # Inspect common forms
        inspect_common_forms()
        print("\n" + "="*80)
        print("Usage: python pdf_field_inspector.py <path_to_pdf> [--verbose]")
        print("="*80)


if __name__ == "__main__":
    main()
