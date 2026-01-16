#!/usr/bin/env python3
"""
Interactive helper script to add entries to What's New page.

Usage:
    python scripts/add_whats_new_entry.py
"""

import re
from pathlib import Path
from datetime import datetime

WHATS_NEW_FILE = Path("content/resources/whats-new.md")

def get_current_month_section():
    """Get the current month/year section header."""
    now = datetime.now()
    return f"## {now.strftime('%B %Y')}"

def read_whats_new():
    """Read the current What's New file."""
    if not WHATS_NEW_FILE.exists():
        print(f"❌ Error: {WHATS_NEW_FILE} not found!")
        return None
    return WHATS_NEW_FILE.read_text(encoding='utf-8')

def write_whats_new(content):
    """Write updated content to What's New file."""
    WHATS_NEW_FILE.write_text(content, encoding='utf-8')
    print(f"✅ Updated {WHATS_NEW_FILE}")

def ensure_month_section_exists(content):
    """Ensure current month section exists, add if missing."""
    month_header = get_current_month_section()
    
    if month_header in content:
        return content
    
    # Find where to insert (after the intro section, before first existing month)
    # Look for the pattern "---\n\n## " which marks start of months section
    match = re.search(r'(---\n\n)(## )', content)
    if match:
        # Insert before first existing month
        insert_pos = match.start(2)
        new_section = f"{month_header}\n\n### New Terms Added\n\n### New Glossaries Added\n\n### Updated Glossaries\n\n---\n\n"
        content = content[:insert_pos] + new_section + content[insert_pos:]
        print(f"✨ Created new section: {month_header}")
    else:
        print("⚠️  Could not find insertion point. Please add month section manually.")
    
    return content

def add_term_entry(content, slug, lang_pair, description):
    """Add a new term entry under 'New Terms Added' in current month."""
    month_header = get_current_month_section()
    
    # Find "### New Terms Added" section under current month
    pattern = rf'({re.escape(month_header)}.*?### New Terms Added\n)(.*?)(\n###|\n---|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"⚠️  Could not find 'New Terms Added' section under {month_header}")
        return content
    
    before = match.group(1)
    existing = match.group(2)
    after = match.group(3)
    
    # Create new entry
    entry = f"- **[{slug}](/terms/{slug})** ({lang_pair}) - {description}\n"
    
    # Add entry
    updated = before + existing + entry + after
    content = content[:match.start()] + updated + content[match.end():]
    
    print(f"✅ Added term: {slug}")
    return content

def add_glossary_entry(content, name, slug, description, entry_count=None):
    """Add a new glossary entry under 'New Glossaries Added' in current month."""
    month_header = get_current_month_section()
    
    # Find "### New Glossaries Added" section under current month
    pattern = rf'({re.escape(month_header)}.*?### New Glossaries Added\n)(.*?)(\n###|\n---|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"⚠️  Could not find 'New Glossaries Added' section under {month_header}")
        return content
    
    before = match.group(1)
    existing = match.group(2)
    after = match.group(3)
    
    # Create new entry
    count_str = f" ({entry_count:,} entries)" if entry_count else ""
    entry = f"- **[{name}](/glossaries/{slug})** - {description}{count_str}\n"
    
    # Add entry
    updated = before + existing + entry + after
    content = content[:match.start()] + updated + content[match.end():]
    
    print(f"✅ Added glossary: {name}")
    return content

def add_update_entry(content, glossary_name, update_description):
    """Add an update entry under 'Updated Glossaries' in current month."""
    month_header = get_current_month_section()
    
    # Find "### Updated Glossaries" section under current month
    pattern = rf'({re.escape(month_header)}.*?### Updated Glossaries\n)(.*?)(\n###|\n---|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"⚠️  Could not find 'Updated Glossaries' section under {month_header}")
        return content
    
    before = match.group(1)
    existing = match.group(2)
    after = match.group(3)
    
    # Create new entry
    entry = f"- **{glossary_name}** - {update_description}\n"
    
    # Add entry
    updated = before + existing + entry + after
    content = content[:match.start()] + updated + content[match.end():]
    
    print(f"✅ Added update: {glossary_name}")
    return content

def main():
    print("\n📰 What's New Entry Helper\n")
    
    # Read current file
    content = read_whats_new()
    if not content:
        return
    
    # Ensure current month section exists
    content = ensure_month_section_exists(content)
    
    # Ask what type of entry to add
    print("What would you like to add?")
    print("  1) New term")
    print("  2) New glossary")
    print("  3) Glossary update")
    print("  0) Exit")
    
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        # New term
        slug = input("Term slug (e.g., 'splitpen'): ").strip()
        lang_pair = input("Language pair (e.g., 'NL→EN'): ").strip()
        description = input("Brief description: ").strip()
        
        if slug and lang_pair and description:
            content = add_term_entry(content, slug, lang_pair, description)
            write_whats_new(content)
        else:
            print("❌ All fields are required!")
    
    elif choice == "2":
        # New glossary
        name = input("Glossary name (e.g., 'Patent Mechanics'): ").strip()
        slug = input("Glossary slug (e.g., 'patent-mechanics'): ").strip()
        description = input("Brief description: ").strip()
        entry_count_str = input("Entry count (optional, press Enter to skip): ").strip()
        
        entry_count = None
        if entry_count_str:
            try:
                entry_count = int(entry_count_str)
            except ValueError:
                print("⚠️  Invalid entry count, skipping")
        
        if name and slug and description:
            content = add_glossary_entry(content, name, slug, description, entry_count)
            write_whats_new(content)
        else:
            print("❌ Name, slug, and description are required!")
    
    elif choice == "3":
        # Glossary update
        glossary_name = input("Glossary name (e.g., 'Patent Mechanics'): ").strip()
        update_desc = input("What was updated? (e.g., 'Added 15+ new mechanical terms'): ").strip()
        
        if glossary_name and update_desc:
            content = add_update_entry(content, glossary_name, update_desc)
            write_whats_new(content)
        else:
            print("❌ All fields are required!")
    
    elif choice == "0":
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice!")
    
    print("\n💡 Don't forget to rebuild the site: python scripts/build_site.py")
    print("💡 Then commit and push your changes!")

if __name__ == "__main__":
    main()
