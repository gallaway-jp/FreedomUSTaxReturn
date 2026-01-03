#!/usr/bin/env python3
"""
Script to refactor all pages from ctk.CTkScrollableFrame inheritance to ModernFrame.
This fixes the geometry manager conflict that causes pages to render incorrectly.
"""

import os
import re

# List of pages to fix
PAGES_TO_FIX = [
    "cloud_backup_page.py",
    "client_portal_page.py",
    "bank_account_linking_page.py",
    "audit_trail_page.py",
    "ai_deduction_finder_page.py",
    "cryptocurrency_tax_page.py",
    "help_documentation_page.py",
    "e_filing_page.py",
    "estate_trust_page.py",
    "partnership_s_corp_page.py",
    "plugin_management_page.py",
    "ptin_ero_management_page.py",
    "quickbooks_integration_page.py",
    "tax_analytics_page.py",
    "tax_projections_page.py",
    "year_comparison_page.py",
    "translation_management_page.py",
    "tax_planning_page.py",
    "tax_interview_page.py",
    "state_tax_calculator_page.py",
    "tax_dashboard_page.py",
]

PAGES_DIR = "gui/pages"

def get_page_title_from_filename(filename):
    """Extract a nice title from filename."""
    # Remove .py extension and convert snake_case to Title Case
    base = filename.replace(".py", "")
    parts = base.split("_")
    # Filter out common words
    title_parts = []
    for part in parts:
        if part not in ["page"]:
            title_parts.append(part.capitalize())
    return " ".join(title_parts)

def fix_page_file(filepath):
    """Fix a single page file."""
    print(f"\nProcessing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Step 1: Check if ModernFrame/ModernScrollableFrame are imported properly
    has_modern_frame_import = "from gui.modern_ui_components import" in content and "ModernFrame" in content
    has_modern_scrollable_import = "ModernScrollableFrame" in content
    
    if not has_modern_frame_import:
        print(f"  ⚠️  Missing ModernFrame import")
        # Add import after existing imports
        if "from gui.modern_ui_components import" in content:
            # Update existing import
            content = re.sub(
                r"from gui\.modern_ui_components import ([^\n]+)",
                lambda m: f"from gui.modern_ui_components import {m.group(1)}, ModernFrame, ModernScrollableFrame"
                if "ModernFrame" not in m.group(1)
                else m.group(0),
                content,
                count=1
            )
        else:
            # Add new import
            import_line = "from gui.modern_ui_components import ModernFrame, ModernScrollableFrame\n"
            # Find the last import line and insert after it
            lines = content.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    insert_idx = i + 1
            lines.insert(insert_idx, import_line)
            content = '\n'.join(lines)
            print(f"  ✅ Added ModernFrame/ModernScrollableFrame import")
    
    # Step 2: Remove local ModernFrame/ModernLabel/ModernButton definitions if present
    # Look for class definitions
    modern_class_pattern = r'^class Modern(Frame|Label|Button)\([^)]+\):.*?\n(?:    .*\n)*'
    if re.search(modern_class_pattern, content, re.MULTILINE):
        print(f"  ℹ️  Found local Modern* class definitions - will be replaced by imports")
        content = re.sub(modern_class_pattern, '', content, flags=re.MULTILINE)
        print(f"  ✅ Removed local Modern* class definitions")
    
    # Step 3: Change class inheritance from ctk.CTkScrollableFrame to ModernFrame
    class_pattern = r'class (\w+Page)\(ctk\.CTkScrollableFrame\):'
    if re.search(class_pattern, content):
        match = re.search(class_pattern, content)
        class_name = match.group(1)
        print(f"  ℹ️  Found class: {class_name}")
        
        content = re.sub(
            class_pattern,
            r'class \1(ModernFrame):',
            content
        )
        print(f"  ✅ Changed inheritance to ModernFrame")
    else:
        print(f"  ⚠️  Could not find class definition pattern")
        return original_content
    
    # Step 4: Update __init__ method
    # Find the __init__ method and update the super().__init__() call
    init_pattern = r'(\s+)super\(\)\.__init__\(master(?:, \*\*kwargs)?\)'
    
    if re.search(init_pattern, content):
        # Get the title from filename
        title = get_page_title_from_filename(os.path.basename(filepath))
        replacement = f'\\1super().__init__(master, title="{title}", **kwargs)'
        content = re.sub(init_pattern, replacement, content)
        print(f"  ✅ Updated super().__init__() call with title='{title}'")
    
    # Step 5: Remove grid_columnconfigure/grid_rowconfigure calls from __init__
    # These are not needed for pack-based layout
    grid_config_pattern = r'\s+self\.grid_(row|column)configure\([^)]+\)\n'
    if re.search(grid_config_pattern, content):
        content = re.sub(grid_config_pattern, '', content)
        print(f"  ✅ Removed grid_configure calls")
    
    # Check if any content has changed
    if content == original_content:
        print(f"  ℹ️  No changes needed")
        return original_content
    
    return content

def main():
    """Main function."""
    print("=" * 60)
    print("PAGE GEOMETRY MANAGER REFACTORING")
    print("=" * 60)
    print(f"Found {len(PAGES_TO_FIX)} pages to refactor")
    
    for page_file in PAGES_TO_FIX:
        filepath = os.path.join(PAGES_DIR, page_file)
        if not os.path.exists(filepath):
            print(f"✗ File not found: {filepath}")
            continue
        
        try:
            # Note: This script only reads and analyzes
            # Actual file modifications would be done with replace_string_in_file tool
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📄 {page_file}")
            
            # Check current state
            if "class " in content:
                # Find class definition
                class_match = re.search(r'class (\w+Page)\(([^)]+)\):', content)
                if class_match:
                    class_name, base_class = class_match.groups()
                    print(f"  Class: {class_name}")
                    print(f"  Base: {base_class}")
                    
                    if "ctk.CTkScrollableFrame" in base_class:
                        print(f"  Status: ❌ Needs refactoring (ctk.CTkScrollableFrame)")
                    elif "ModernFrame" in base_class:
                        print(f"  Status: ✅ Already using ModernFrame")
                    else:
                        print(f"  Status: ⚠️ Unknown base class")
            
            # Count geometry manager calls
            grid_calls = len(re.findall(r'\.grid\(', content))
            pack_calls = len(re.findall(r'\.pack\(', content))
            
            if grid_calls > 0 or pack_calls > 0:
                print(f"  Geometry: {pack_calls} pack() / {grid_calls} grid() calls")
        
        except Exception as e:
            print(f"✗ Error processing {page_file}: {e}")

if __name__ == "__main__":
    main()
