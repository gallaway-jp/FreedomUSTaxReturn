"""
Script to fix ModernLabel font_size and font_weight parameters
Converts font_size/font_weight to proper font parameter
"""

import re
import os
from pathlib import Path

def fix_modernlabel_fonts(file_path):
    """Fix ModernLabel calls with font_size and font_weight parameters"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern: ModernLabel(..., font_size=X, font_weight="bold")
    # This is tricky because we need to:
    # 1. Find ModernLabel calls that have font_size and font_weight
    # 2. Replace them with font=ctk.CTkFont(size=X)
    
    # For now, let's do a simpler approach: replace font_size and font_weight usage
    
    # Pattern 1: Replace font_size=X, font_weight="bold" with proper font
    # This is complex because we need context. Let's do it step by step.
    
    # Find all ModernLabel( ... font_size=... font_weight=...)  calls
    # Replace them with font=ctk.CTkFont(size=...)
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a ModernLabel call
        if 'ModernLabel(' in line and 'font_size=' in line:
            # Collect lines until we find the closing )
            full_call = line
            j = i + 1
            while ')' not in full_call.rstrip() and j < len(lines):
                full_call += '\n' + lines[j]
                j += 1
            
            # Now parse and fix the call
            # Extract font_size value
            font_size_match = re.search(r'font_size=(\d+)', full_call)
            if font_size_match:
                font_size = font_size_match.group(1)
                
                # Remove font_size and font_weight parameters
                fixed_call = re.sub(r',?\s*font_size=\d+', '', full_call)
                fixed_call = re.sub(r',?\s*font_weight="[^"]*"', '', fixed_call)
                fixed_call = re.sub(r",?\s*font_weight='[^']*'", '', fixed_call)
                
                # Add font parameter before the closing paren
                # Find the last closing paren
                last_paren_idx = fixed_call.rfind(')')
                if last_paren_idx > 0:
                    fixed_call = fixed_call[:last_paren_idx] + f',\n            font=ctk.CTkFont(size={font_size})' + fixed_call[last_paren_idx:]
                
                # Add the lines
                for line_part in fixed_call.split('\n')[:-1]:
                    new_lines.append(line_part)
                
                i = j
                continue
        
        new_lines.append(line)
        i += 1
    
    fixed_content = '\n'.join(new_lines)
    
    # Simple replacements for single-line ModernLabel calls
    # Pattern: ModernLabel(..., font_size=X, font_weight="bold" ... )
    fixed_content = re.sub(
        r'ModernLabel\(([^)]*),\s*font_size=(\d+),\s*font_weight="bold"([^)]*)\)',
        r'ModernLabel(\1,\n            font=ctk.CTkFont(size=\2)\3)',
        fixed_content
    )
    
    # Also handle cases where font_weight comes before font_size
    fixed_content = re.sub(
        r'ModernLabel\(([^)]*),\s*font_weight="bold",\s*font_size=(\d+)([^)]*)\)',
        r'ModernLabel(\1,\n            font=ctk.CTkFont(size=\2)\3)',
        fixed_content
    )
    
    # Handle font_size without font_weight
    fixed_content = re.sub(
        r'ModernLabel\(([^)]*),\s*font_size=(\d+)([^)]*)\)',
        r'ModernLabel(\1,\n            font=ctk.CTkFont(size=\2)\3)',
        fixed_content
    )
    
    if fixed_content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        return True
    return False

def main():
    """Main function"""
    
    root_dir = Path('.')
    files_to_process = list(root_dir.glob('gui/**/*.py')) + list(root_dir.glob('gui/*.py'))
    
    fixed_files = []
    
    for file_path in files_to_process:
        if '__pycache__' in str(file_path):
            continue
            
        try:
            if fix_modernlabel_fonts(file_path):
                fixed_files.append(str(file_path))
                print(f"✓ Fixed: {file_path}")
            else:
                # Check if file needs fixing
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'font_size=' in content or 'font_weight=' in content:
                        print(f"  ⚠ May need fixing: {file_path}")
                    else:
                        print(f"  Skipped: {file_path}")
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary: Fixed {len(fixed_files)} files")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
