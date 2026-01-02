"""
Script to fix CustomTkinter font compatibility issues
Removes unsupported 'weight' parameter from CTkFont declarations
"""

import re
import os
import sys
from pathlib import Path

def fix_font_declarations(file_path):
    """Fix CTkFont declarations by removing weight parameter"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: ctk.CTkFont(size=X, weight="bold") -> ctk.CTkFont(size=X)
    content = re.sub(
        r'ctk\.CTkFont\(size=(\d+),\s*weight="bold"\)',
        r'ctk.CTkFont(size=\1)',
        content
    )
    
    # Pattern 2: ctk.CTkFont(size=X, weight='bold') -> ctk.CTkFont(size=X)
    content = re.sub(
        r"ctk\.CTkFont\(size=(\d+),\s*weight='bold'\)",
        r'ctk.CTkFont(size=\1)',
        content
    )
    
    # Pattern 3: ctk.CTkFont(weight="bold") -> ctk.CTkFont()
    content = re.sub(
        r'ctk\.CTkFont\(weight="bold"\)',
        r'ctk.CTkFont()',
        content
    )
    
    # Pattern 4: ctk.CTkFont(weight='bold') -> ctk.CTkFont()
    content = re.sub(
        r"ctk\.CTkFont\(weight='bold'\)",
        r'ctk.CTkFont()',
        content
    )
    
    # Pattern 5: font=ctk.CTkFont(size=X, weight="bold") in labels
    content = re.sub(
        r'font=ctk\.CTkFont\(size=(\d+),\s*weight="bold"\)',
        r'font=ctk.CTkFont(size=\1)',
        content
    )
    
    # Pattern 6: font=ctk.CTkFont(weight="bold") in labels
    content = re.sub(
        r'font=ctk\.CTkFont\(weight="bold"\)',
        r'font=ctk.CTkFont()',
        content
    )
    
    # Pattern 7: ModernFrame with weight in font
    content = re.sub(
        r'font=ctk\.CTkFont\(size=(\d+),\s*weight="bold"\)',
        r'font=ctk.CTkFont(size=\1)',
        content
    )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix all Python files"""
    
    root_dir = Path('.')
    files_to_process = list(root_dir.glob('gui/**/*.py')) + list(root_dir.glob('gui/*.py'))
    
    fixed_files = []
    
    for file_path in files_to_process:
        # Skip __pycache__
        if '__pycache__' in str(file_path):
            continue
            
        try:
            if fix_font_declarations(file_path):
                fixed_files.append(str(file_path))
                print(f"✓ Fixed: {file_path}")
            else:
                print(f"  Skipped: {file_path} (no changes needed)")
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary: Fixed {len(fixed_files)} files")
    print(f"{'='*60}\n")
    
    if fixed_files:
        print("Files modified:")
        for f in sorted(fixed_files):
            print(f"  - {f}")

if __name__ == '__main__':
    main()
