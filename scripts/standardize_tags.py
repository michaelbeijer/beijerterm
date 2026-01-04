#!/usr/bin/env python3
"""
Standardize tags across all Beijerterm glossaries and terms.

Tag conventions:
- lowercase for generic subjects: legal, medical, automotive
- Capitalize proper nouns only: Microsoft, EU, BBC, ISO 9001
- Plural for countable nouns: diamonds, dictionaries (not diamond, dictionary)
- Multi-word tags use spaces: machine learning, 3D printing
"""

import os
import re
from pathlib import Path

# Define tag mappings: old -> new (or None to remove)
TAG_MAPPINGS = {
    # Case standardization (lowercase for generic)
    'airports': 'aviation',
    'cardiology': 'medical',
    'court': 'legal',
    'heart': 'medical',
    'medical': 'medical',
    'Medical': 'medical',
    'procedure': 'legal',
    'statistics': 'statistics',
    'Statistics': 'statistics',
    'transportation': 'transport',
    'travel': 'transport',
    'vehicles': 'automotive',
    'off-road': 'automotive',
    
    # Merge redundant acronym + full name (keep shorter)
    'Centrum voor Innovatie van Opleidingen (CINOP)': 'CINOP',
    'European Union Aviation Safety Agency (EASA)': 'EASA',
    'Eindhoven University of Technology (TU/e)': 'TU/e',
    'European Single Access Point (ESAP)': 'ESAP',
    'International Monetary Fund (IMF)': 'IMF',
    'Thesaurus Zorg en Welzijn (TZW)': 'TZW',
    'Lycaeus Juridisch Woordenboek': 'legal',
    'Onroerend Goed Lexicon': 'OGL',
    
    # Source attributions -> remove or convert to topic
    'Acronymbook': None,
    'Acronymbook.com': None,
    'Autowoordenboek': None,
    'gerritspeek.nl': None,
    'piektraining.com': None,
    'woordjesleren.nl': None,
    'Jerzy Kazojć': None,
    'Michael Beijer': None,
    'Origin unknown': None,
    'TT-Software': None,
    'Van Houtum': None,
    'Patitia.net': None,
    'Pinkhof': None,
    'Librarylingo': 'libraries',
    'TermFolders 2.0': None,
    'TermCoord': None,
    
    # Meta/quality tags -> remove
    'Original has been edited': None,
    'Pages with broken file links': None,
    'Glossaries:C': None,
    'Admin': None,
    'Misc.': None,
    'Links': None,
    
    # Standardize case for generic topics (lowercase)
    'Law': 'legal',
    'Crime': 'legal',
    'Abbreviations': 'abbreviations',
    'Agriculture': 'agriculture',
    'Agricultural machinery': 'agriculture',
    'Automotive': 'automotive',
    'Aviation': 'aviation',
    'Ballooning': 'aviation',
    'Banking': 'finance',
    'Finance': 'finance',
    'Tax': 'finance',
    'Bicycles': 'cycling',
    'Blockchain': 'blockchain',
    'Distributed ledgers': 'blockchain',
    'Edge Computing': 'IT',
    'Computer vision': 'IT',
    'Botany': 'botany',
    'Plants': 'botany',
    'Brewing': 'brewing',
    'Business': 'business',
    'Cameras': 'photography',
    'Ihagee': 'photography',
    'Cement': 'construction',
    'Construction': 'construction',
    'Chemistry': 'chemistry',
    'Cleanrooms': 'cleanrooms',
    'Combustion engines': 'engines',
    'CIMAC': 'engines',
    'Crossword puzzles': 'puzzles',
    'Puzzelwoordenboek': 'puzzles',
    'Dictionaries': 'dictionaries',
    'Dunglish': 'Dunglish',
    '(Neder)brackets': 'Dunglish',
    'E-numbers': 'food additives',
    'Economics': 'economics',
    'Education': 'education',
    'Electricity': 'electrical',
    'Energy': 'energy',
    'Firefighting': 'firefighting',
    'Geotechnical engineering': 'geotechnical',
    'Grammar': 'grammar',
    'Insects': 'entomology',
    'Latin': 'Latin',
    'Libraries': 'libraries',
    'Mathematics': 'mathematics',
    'Ordinal numerals': 'numerals',
    'Rangtelwoorden': 'numerals',
    'Palletising': 'palletising',
    'Patents': 'patents',
    'Pumps': 'pumps',
    'Sewing': 'sewing',
    'Technical': 'technical',
    'Tenders': 'tenders',
    'Terminology': 'terminology',
    'Textile': 'textiles',
    'Tractors': 'tractors',
    'Translation': 'translation',
    'Voting': 'voting',
    'Water': 'water management',
    'Alternative medicine': 'alternative medicine',
    'Diamonds': 'diamonds',
    '4x4': 'automotive',
    
    # Keep proper nouns capitalized
    'Afrikaans': 'Afrikaans',
    'Apple': 'Apple',
    'Belgium': 'Belgium',
    'COVID-19': 'COVID-19',
    'CPV': 'CPV',
    'CROHO': 'CROHO',
    'Consilium': 'Consilium',
    'Council of the European Union': 'EU Council',
    'DSL': 'DSL',
    'EASA': 'EASA',
    'EIOPA': 'EIOPA',
    'EMCDDA': 'EMCDDA',
    'ESCO classification': 'ESCO',
    'Eskom': 'Eskom',
    'EU': 'EU',
    'EuroVoc': 'EuroVoc',
    'Eurocode vertaallijst': 'Eurocode',
    'Eurydice': 'Eurydice',
    'Excel': 'Microsoft Excel',
    'Flemish': 'Flemish',
    'FPS Finance': 'FPS Finance',
    'French': 'French',
    'IT': 'IT',
    'KMEHR': 'KMEHR',
    'KvK': 'KvK',
    'LOINC': 'LOINC',
    'Microsoft': 'Microsoft',
    'MISSOC': 'MISSOC',
    'Madaster': 'Madaster',
    'NCC': 'NCC',
    'NICE': 'NICE',
    'Netherlands': 'Netherlands',
    'NVWA': 'NVWA',
    'OGL': 'OGL',
    'OHIM': 'OHIM',
    'R-Phrases': 'R-phrases',
    'Risk phrases': 'R-phrases',
    'Rijnland': 'Rijnland',
    'TU/e': 'TU/e',
    'Tilburg University': 'Tilburg University',
    'Universiteit Antwerpen': 'University of Antwerp',
    'Utrecht University': 'Utrecht University',
    'Avans University of Applied Sciences': 'Avans',
}


def extract_tags_from_yaml_line(line):
    """Extract tag string from a YAML list item, handling malformed entries."""
    line = line.strip()
    if line.startswith('- '):
        line = line[2:]
    # Handle malformed entries like "Languages: en" -> skip
    if ':' in line and not line.startswith('"') and not line.startswith("'"):
        return None
    # Remove quotes
    line = line.strip('"').strip("'")
    return line if line else None


def process_file(filepath):
    """Process a single markdown file, standardizing its tags."""
    content = filepath.read_text(encoding='utf-8')
    
    # Match YAML frontmatter
    match = re.match(r'^(---\s*\n)(.+?)(\n---)', content, re.DOTALL)
    if not match:
        return None, "No YAML frontmatter"
    
    prefix, yaml_content, suffix = match.groups()
    rest_of_file = content[match.end():]
    
    # Find tags section in YAML
    tags_match = re.search(r'^tags:\s*\n((?:  - .+\n?)+)', yaml_content, re.MULTILINE)
    if not tags_match:
        # Try inline format: tags: [tag1, tag2]
        inline_match = re.search(r'^tags:\s*\[([^\]]+)\]', yaml_content, re.MULTILINE)
        if not inline_match:
            return None, "No tags found"
        
        # Parse inline tags
        old_tags = [t.strip().strip('"').strip("'") for t in inline_match.group(1).split(',')]
        old_tags = [t for t in old_tags if t]
        
        # Map tags
        new_tags = []
        for tag in old_tags:
            if tag in TAG_MAPPINGS:
                mapped = TAG_MAPPINGS[tag]
                if mapped is not None and mapped not in new_tags:
                    new_tags.append(mapped)
            elif tag not in new_tags:
                new_tags.append(tag)
        
        if set(old_tags) == set(new_tags):
            return None, "No changes needed"
        
        # Replace inline tags
        new_tags_str = ', '.join(f'"{t}"' for t in new_tags)
        new_yaml = yaml_content[:inline_match.start()] + f'tags: [{new_tags_str}]' + yaml_content[inline_match.end():]
        new_content = prefix + new_yaml + suffix + rest_of_file
        return (old_tags, new_tags, new_content), None
    
    # Parse list-style tags
    tags_text = tags_match.group(1)
    old_tags = []
    for line in tags_text.strip().split('\n'):
        tag = extract_tags_from_yaml_line(line)
        if tag:
            old_tags.append(tag)
    
    # Map tags
    new_tags = []
    for tag in old_tags:
        if tag in TAG_MAPPINGS:
            mapped = TAG_MAPPINGS[tag]
            if mapped is not None and mapped not in new_tags:
                new_tags.append(mapped)
        elif tag not in new_tags:
            new_tags.append(tag)
    
    if set(old_tags) == set(new_tags):
        return None, "No changes needed"
    
    # Build new tags YAML
    new_tags_yaml = 'tags:\n' + '\n'.join(f'  - "{t}"' for t in new_tags) + '\n'
    
    # Replace tags section
    new_yaml = yaml_content[:tags_match.start()] + new_tags_yaml + yaml_content[tags_match.end():]
    new_content = prefix + new_yaml + suffix + rest_of_file
    
    return (old_tags, new_tags, new_content), None


def main():
    base_dir = Path(__file__).parent.parent
    os.chdir(base_dir)
    
    changes = []
    errors = []
    
    for folder in ['glossaries', 'terms']:
        folder_path = Path(folder)
        if not folder_path.exists():
            continue
        for filepath in folder_path.rglob('*.md'):
            if filepath.name.startswith('_'):
                continue
            
            result, error = process_file(filepath)
            if error:
                if error != "No changes needed" and error != "No tags found":
                    errors.append((filepath, error))
            elif result:
                old_tags, new_tags, new_content = result
                changes.append((filepath, old_tags, new_tags, new_content))
    
    print(f"Files to update: {len(changes)}")
    print(f"Errors: {len(errors)}")
    print()
    
    if errors:
        print("Errors:")
        for path, err in errors[:10]:
            print(f"  {path}: {err}")
        print()
    
    # Preview changes
    print("Preview of changes:")
    for filepath, old_tags, new_tags, _ in changes[:15]:
        print(f"\n{filepath}:")
        print(f"  OLD: {old_tags}")
        print(f"  NEW: {new_tags}")
    
    if len(changes) > 15:
        print(f"\n... and {len(changes) - 15} more files")
    
    # Ask for confirmation
    print(f"\n{'='*50}")
    response = input(f"Apply changes to {len(changes)} files? (y/n): ")
    
    if response.lower() == 'y':
        for filepath, old_tags, new_tags, new_content in changes:
            filepath.write_text(new_content, encoding='utf-8')
            print(f"Updated: {filepath}")
        print(f"\nDone! Updated {len(changes)} files.")
    else:
        print("Aborted.")


if __name__ == '__main__':
    main()
