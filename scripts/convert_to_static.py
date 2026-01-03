#!/usr/bin/env python3
"""
Convert exported wiki data to static site format

Converts JSON exports to markdown files with YAML frontmatter
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Lowercase
    slug = text.lower()
    # Remove parentheses and their contents for cleaner slugs
    slug = re.sub(r'\([^)]*\)', '', slug)
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    # Truncate if too long
    if len(slug) > 60:
        slug = slug[:60].rsplit('-', 1)[0]
    return slug


def detect_domain(title: str, categories: List[str]) -> str:
    """Detect domain/category from title and wiki categories"""
    title_lower = title.lower()
    cats_lower = [c.lower() for c in categories]
    
    # Domain mappings
    domain_keywords = {
        'legal': ['legal', 'law', 'juridisch', 'court', 'advocaat', 'juridical'],
        'medical': ['medical', 'medisch', 'health', 'pharmaceutical', 'geneeskund'],
        'technical': ['technical', 'technisch', 'engineering', 'mechanical'],
        'it': ['it', 'computer', 'software', 'microsoft', 'apple', 'digital', 'ict'],
        'automotive': ['automotive', 'auto', 'car', 'vehicle', 'voertuig'],
        'aviation': ['aviation', 'aerospace', 'aircraft', 'luchtvaart'],
        'financial': ['financial', 'finance', 'banking', 'economisch', 'fiscal'],
        'construction': ['construction', 'building', 'bouw', 'architecture'],
        'maritime': ['maritime', 'shipping', 'naval', 'scheepvaart'],
        'military': ['military', 'defense', 'militair', 'army'],
        'food': ['food', 'culinary', 'culinair', 'voeding', 'horeca'],
        'textile': ['textile', 'fabric', 'clothing', 'textiel'],
        'energy': ['energy', 'power', 'electricity', 'energie', 'eskom'],
        'agriculture': ['agriculture', 'farming', 'botanical', 'horticultural'],
        'chemistry': ['chemistry', 'chemical', 'chemisch'],
        'general': []  # fallback
    }
    
    # Check categories first
    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if any(keyword in cat for cat in cats_lower):
                return domain
    
    # Check title
    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if keyword in title_lower:
                return domain
    
    return 'general'


def detect_languages(title: str, entries: List[Dict]) -> tuple:
    """Detect source and target languages from title and entries"""
    title_lower = title.lower()
    
    # Common language patterns in titles
    lang_patterns = [
        (r'dutch[- ]english', 'nl', 'en'),
        (r'english[- ]dutch', 'en', 'nl'),
        (r'dutch[- ]german', 'nl', 'de'),
        (r'german[- ]dutch', 'de', 'nl'),
        (r'english[- ]german', 'en', 'de'),
        (r'german[- ]english', 'de', 'en'),
        (r'english[- ]french', 'en', 'fr'),
        (r'french[- ]english', 'fr', 'en'),
        (r'dutch[- ]french', 'nl', 'fr'),
        (r'french[- ]dutch', 'fr', 'nl'),
        (r'english[- ]afrikaans', 'en', 'af'),
        (r'afrikaans[- ]english', 'af', 'en'),
        (r'nederlands[- ]engels', 'nl', 'en'),
        (r'engels[- ]nederlands', 'en', 'nl'),
    ]
    
    for pattern, src, tgt in lang_patterns:
        if re.search(pattern, title_lower):
            return src, tgt
    
    # Default to Dutch-English (most common in this wiki)
    return 'nl', 'en'


def generate_markdown(page: Dict, domain: str) -> str:
    """Generate markdown content for a glossary page"""
    title = page['title']
    entries = page.get('entries', [])
    categories = page.get('categories', [])
    
    # Generate slug
    slug = slugify(title)
    
    # Detect languages
    source_lang, target_lang = detect_languages(title, entries)
    
    # Build YAML frontmatter
    frontmatter = {
        'title': title,
        'slug': slug,
        'description': f"Terminology from {title}",
        'source_lang': source_lang,
        'target_lang': target_lang,
        'domain': domain,
        'term_count': len(entries),
        'source_url': f"https://superlookup.wiki/wiki/{title.replace(' ', '_')}",
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'tags': [cat for cat in categories if cat not in ['Terms', 'Terminology resources']],
    }
    
    # Build YAML
    yaml_lines = ['---']
    for key, value in frontmatter.items():
        if isinstance(value, list):
            if value:
                yaml_lines.append(f'{key}:')
                for item in value:
                    yaml_lines.append(f'  - {item}')
            else:
                yaml_lines.append(f'{key}: []')
        elif isinstance(value, int):
            yaml_lines.append(f'{key}: {value}')
        else:
            # Quote strings that might cause YAML issues
            if ':' in str(value) or '\n' in str(value):
                yaml_lines.append(f'{key}: "{value}"')
            else:
                yaml_lines.append(f'{key}: {value}')
    yaml_lines.append('---')
    yaml_lines.append('')
    
    # Title and description
    yaml_lines.append(f'# {title}')
    yaml_lines.append('')
    
    # Terms table
    if entries:
        # Determine columns based on languages
        src_name = {'nl': 'Dutch', 'en': 'English', 'de': 'German', 'fr': 'French', 'af': 'Afrikaans'}.get(source_lang, 'Source')
        tgt_name = {'nl': 'Dutch', 'en': 'English', 'de': 'German', 'fr': 'French', 'af': 'Afrikaans'}.get(target_lang, 'Target')
        
        yaml_lines.append('## Terms')
        yaml_lines.append('')
        yaml_lines.append(f'| {src_name} | {tgt_name} | Notes |')
        yaml_lines.append('|-------|---------|-------|')
        
        for entry in entries:
            dutch = entry.get('dutch', '').replace('|', '\\|').replace('\n', ' ')
            english_list = entry.get('english', [])
            english = ', '.join(english_list) if isinstance(english_list, list) else str(english_list)
            english = english.replace('|', '\\|').replace('\n', ' ')
            notes = entry.get('notes', '') or entry.get('context', '') or ''
            notes = notes.replace('|', '\\|').replace('\n', ' ')
            
            yaml_lines.append(f'| {dutch} | {english} | {notes} |')
    
    return '\n'.join(yaml_lines)


def convert_all(input_dir: str, output_dir: str):
    """Convert all exported JSON data to static site format"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Load index
    index_file = input_path / '_index.json'
    if not index_file.exists():
        print(f"❌ Index file not found: {index_file}")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    pages = index.get('pages', [])
    print(f"📚 Converting {len(pages)} pages...")
    
    # Track statistics
    stats = {
        'converted': 0,
        'skipped': 0,
        'by_domain': defaultdict(int),
        'total_entries': 0,
    }
    
    # Process each page
    for i, page in enumerate(pages):
        title = page['title']
        entries = page.get('entries', [])
        categories = page.get('categories', [])
        
        # Skip pages with no entries
        if not entries:
            stats['skipped'] += 1
            continue
        
        # Skip pages with very few entries (likely parsing issues)
        if len(entries) < 3:
            stats['skipped'] += 1
            continue
        
        # Detect domain
        domain = detect_domain(title, categories)
        
        # Create domain directory
        domain_dir = output_path / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate markdown
        markdown = generate_markdown(page, domain)
        
        # Write file
        slug = slugify(title)
        filename = f"{slug}.md"
        filepath = domain_dir / filename
        
        # Handle duplicates
        counter = 1
        while filepath.exists():
            filename = f"{slug}-{counter}.md"
            filepath = domain_dir / filename
            counter += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        stats['converted'] += 1
        stats['by_domain'][domain] += 1
        stats['total_entries'] += len(entries)
        
        if (i + 1) % 50 == 0:
            print(f"  Converted {i + 1}/{len(pages)}...")
    
    # Generate category index files
    print("\n📂 Generating category indexes...")
    for domain, count in stats['by_domain'].items():
        domain_dir = output_path / domain
        category_file = domain_dir / '_category.yaml'
        
        # Pretty domain names
        domain_names = {
            'legal': ('Legal', '⚖️', '#9b59b6'),
            'medical': ('Medical', '🏥', '#e74c3c'),
            'technical': ('Technical', '🔧', '#3498db'),
            'it': ('IT & Computing', '💻', '#2ecc71'),
            'automotive': ('Automotive', '🚗', '#e67e22'),
            'aviation': ('Aviation', '✈️', '#1abc9c'),
            'financial': ('Financial', '💰', '#f39c12'),
            'construction': ('Construction', '🏗️', '#95a5a6'),
            'maritime': ('Maritime', '🚢', '#3498db'),
            'military': ('Military', '🎖️', '#2c3e50'),
            'food': ('Food & Culinary', '🍽️', '#e74c3c'),
            'textile': ('Textile', '🧵', '#9b59b6'),
            'energy': ('Energy', '⚡', '#f1c40f'),
            'agriculture': ('Agriculture', '🌱', '#27ae60'),
            'chemistry': ('Chemistry', '🧪', '#8e44ad'),
            'general': ('General', '📚', '#34495e'),
        }
        
        name, icon, color = domain_names.get(domain, (domain.title(), '📖', '#666666'))
        
        yaml_content = f"""name: {name}
slug: {domain}
description: {name} terminology and glossaries
icon: {icon}
color: "{color}"
glossary_count: {count}
"""
        with open(category_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 CONVERSION SUMMARY")
    print("=" * 60)
    print(f"  Total pages processed: {len(pages)}")
    print(f"  Converted: {stats['converted']}")
    print(f"  Skipped (empty/few entries): {stats['skipped']}")
    print(f"  Total entries: {stats['total_entries']:,}")
    print(f"\n  By domain:")
    for domain, count in sorted(stats['by_domain'].items(), key=lambda x: -x[1]):
        print(f"    {domain}: {count} glossaries")
    print(f"\n  Output: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert wiki exports to static site')
    parser.add_argument('--source', default='terms', choices=['terms', 'terminology_resources', 'both'],
                        help='Which data source to convert')
    parser.add_argument('--output', default='../glossaries',
                        help='Output directory for markdown files')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WIKI TO STATIC SITE CONVERTER")
    print("=" * 60)
    
    if args.source in ('terms', 'both'):
        print("\n📚 Converting Terms...")
        convert_all('../data/terms', args.output)
    
    if args.source in ('terminology_resources', 'both'):
        print("\n📚 Converting Terminology Resources...")
        convert_all('../data/terminology_resources', args.output)


if __name__ == "__main__":
    main()
