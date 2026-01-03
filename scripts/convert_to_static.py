#!/usr/bin/env python3
"""
Convert exported wiki data to static site format

UPDATED: Now handles Terms pages differently from Glossary pages
- Terms: Preserve rich wiki content (definitions, examples, links)
- Glossaries: Table format as before
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
    slug = text.lower()
    slug = re.sub(r'\([^)]*\)', '', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    slug = re.sub(r'-+', '-', slug)
    if len(slug) > 60:
        slug = slug[:60].rsplit('-', 1)[0]
    return slug


def detect_domain(title: str, categories: List[str]) -> str:
    """Detect domain/category from title and wiki categories"""
    title_lower = title.lower()
    cats_lower = [c.lower() for c in categories]
    
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
        'general': []
    }

    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if any(keyword in cat for cat in cats_lower):
                return domain

    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if keyword in title_lower:
                return domain
    
    return 'general'


def detect_languages(title: str, entries: List[Dict]) -> tuple:
    """Detect source and target languages from title and entries"""
    title_lower = title.lower()

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

    return 'nl', 'en'


def wiki_to_markdown(wiki_text: str) -> str:
    """Convert MediaWiki markup to Markdown"""
    md = wiki_text
    
    # Remove MediaWiki directives
    md = re.sub(r'__[A-Z]+__', '', md)
    md = re.sub(r'\{\{[^}]+\}\}', '', md)  # Remove templates like {{Back to the top}}
    md = re.sub(r'\[\[Category:[^\]]+\]\]', '', md)  # Remove categories
    
    # Convert headers: == Header == -> ## Header
    md = re.sub(r'^=====\s*(.+?)\s*=====', r'##### \1', md, flags=re.MULTILINE)
    md = re.sub(r'^====\s*(.+?)\s*====', r'#### \1', md, flags=re.MULTILINE)
    md = re.sub(r'^===\s*(.+?)\s*===', r'### \1', md, flags=re.MULTILINE)
    md = re.sub(r'^==\s*(.+?)\s*==', r'## \1', md, flags=re.MULTILINE)
    
    # Convert bold: '''text''' -> **text**
    md = re.sub(r"'''(.+?)'''", r'**\1**', md)
    
    # Convert italic: ''text'' -> *text*
    md = re.sub(r"''(.+?)''", r'*\1*', md)
    
    # Convert bullet lists: * item -> - item
    md = re.sub(r'^\*\s*', r'- ', md, flags=re.MULTILINE)
    
    # Convert numbered lists: # item -> 1. item
    md = re.sub(r'^#\s*', r'1. ', md, flags=re.MULTILINE)
    
    # Convert internal links: [[Page|Text]] -> [Text](Page) or [[Page]] -> Page
    md = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'[\2](\1)', md)
    md = re.sub(r'\[\[([^\]]+)\]\]', r'\1', md)
    
    # Convert external links: [url text] -> [text](url)
    md = re.sub(r'\[([^\s\]]+)\s+([^\]]+)\]', r'[\2](\1)', md)
    
    # Keep bare URLs as links
    md = re.sub(r'^\*\s*(https?://[^\s]+)\s*$', r'- [\1](\1)', md, flags=re.MULTILINE)
    md = re.sub(r'^-\s*(https?://[^\s]+)\s*$', r'- [\1](\1)', md, flags=re.MULTILINE)
    
    # Convert references: <ref>text</ref> -> (text)
    md = re.sub(r'<ref>([^<]+)</ref>', r' (\1)', md)
    md = re.sub(r'<[Rr]eferences\s*/>', '', md)
    
    # Convert wikitables to markdown tables
    md = convert_wikitable_to_markdown(md)
    
    # Clean up multiple blank lines
    md = re.sub(r'\n{3,}', '\n\n', md)
    
    return md.strip()


def convert_wikitable_to_markdown(wiki_text: str) -> str:
    """Convert MediaWiki tables to Markdown tables"""
    result = wiki_text
    
    # Find all tables
    table_pattern = r'\{\|\s*class="wikitable"(.*?)\|\}'
    
    def convert_single_table(match):
        table_content = match.group(1)
        lines = table_content.strip().split('\n')
        
        md_rows = []
        current_row = []
        is_header = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('|-'):
                if current_row:
                    md_rows.append(current_row)
                    current_row = []
                continue
            if line.startswith('!'):
                # Header cell
                is_header = True
                cell = line[1:].strip()
                current_row.append(cell)
            elif line.startswith('|'):
                # Data cell
                cell = line[1:].strip()
                current_row.append(cell)
        
        if current_row:
            md_rows.append(current_row)
        
        if not md_rows:
            return ''
        
        # Build markdown table
        md_lines = []
        for i, row in enumerate(md_rows):
            # Escape pipes in cell content
            escaped_row = [cell.replace('|', '\\|') for cell in row]
            md_lines.append('| ' + ' | '.join(escaped_row) + ' |')
            if i == 0:
                # Add header separator
                md_lines.append('|' + '|'.join(['---' for _ in row]) + '|')
        
        return '\n' + '\n'.join(md_lines) + '\n'
    
    result = re.sub(table_pattern, convert_single_table, result, flags=re.DOTALL)
    return result


def generate_term_markdown(page: Dict, raw_content: str, domain: str) -> str:
    """Generate markdown for a Terms page (dictionary entry style)"""
    title = page['title']
    categories = page.get('categories', [])
    
    slug = slugify(title)
    source_lang, target_lang = detect_languages(title, [])
    
    # Build YAML frontmatter
    frontmatter = {
        'title': title,
        'slug': slug,
        'description': f"Translation and definition of {title}",
        'type': 'term',
        'source_lang': source_lang,
        'target_lang': target_lang,
        'domain': domain,
        'source_url': f"https://superlookup.wiki/wiki/{title.replace(' ', '_')}",
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'tags': [cat for cat in categories if cat not in ['Terms', 'Terminology resources']],
    }
    
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
            if ':' in str(value) or '\n' in str(value):
                yaml_lines.append(f'{key}: "{value}"')
            else:
                yaml_lines.append(f'{key}: {value}')
    yaml_lines.append('---')
    yaml_lines.append('')
    
    # Title
    yaml_lines.append(f'# {title}')
    yaml_lines.append('')
    
    # Convert wiki content to markdown
    markdown_content = wiki_to_markdown(raw_content)
    yaml_lines.append(markdown_content)
    
    return '\n'.join(yaml_lines)


def generate_glossary_markdown(page: Dict, domain: str) -> str:
    """Generate markdown for a Glossary page (table format)"""
    title = page['title']
    entries = page.get('entries', [])
    categories = page.get('categories', [])
    
    slug = slugify(title)
    source_lang, target_lang = detect_languages(title, entries)
    
    frontmatter = {
        'title': title,
        'slug': slug,
        'description': f"Terminology from {title}",
        'type': 'glossary',
        'source_lang': source_lang,
        'target_lang': target_lang,
        'domain': domain,
        'term_count': len(entries),
        'source_url': f"https://superlookup.wiki/wiki/{title.replace(' ', '_')}",
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'tags': [cat for cat in categories if cat not in ['Terms', 'Terminology resources']],
    }
    
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
            if ':' in str(value) or '\n' in str(value):
                yaml_lines.append(f'{key}: "{value}"')
            else:
                yaml_lines.append(f'{key}: {value}')
    yaml_lines.append('---')
    yaml_lines.append('')
    
    yaml_lines.append(f'# {title}')
    yaml_lines.append('')
    
    if entries:
        src_name = {'nl': 'Dutch', 'en': 'English', 'de': 'German', 'fr': 'French', 'af': 'Afrikaans'}.get(source_lang, 'Source')
        tgt_name = {'nl': 'Dutch', 'en': 'English', 'de': 'German', 'fr': 'French', 'af': 'Afrikaans'}.get(target_lang, 'Target')
        
        yaml_lines.append('## Terms')
        yaml_lines.append('')
        yaml_lines.append(f'| {src_name} | {tgt_name} | Notes |')
        yaml_lines.append('|--------|---------|-------|')
        
        for entry in entries:
            dutch = entry.get('dutch', '').replace('|', '\\|').replace('\n', ' ')
            english_list = entry.get('english', [])
            english = ', '.join(english_list) if isinstance(english_list, list) else str(english_list)
            english = english.replace('|', '\\|').replace('\n', ' ')
            notes = entry.get('notes', '') or entry.get('context', '') or ''
            notes = notes.replace('|', '\\|').replace('\n', ' ')
            
            yaml_lines.append(f'| {dutch} | {english} | {notes} |')
    
    return '\n'.join(yaml_lines)


def convert_terms(input_dir: str, output_dir: str):
    """Convert Terms pages - preserve full wiki content"""
    input_path = Path(input_dir)
    output_path = Path(output_dir) / 'terms'
    output_path.mkdir(parents=True, exist_ok=True)
    
    index_file = input_path / '_index.json'
    if not index_file.exists():
        print(f"  Index not found: {index_file}")
        return {'converted': 0, 'skipped': 0}
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    pages = index.get('pages', [])
    raw_dir = input_path / 'raw'
    
    stats = {'converted': 0, 'skipped': 0, 'total_entries': 0}
    
    for i, page in enumerate(pages):
        title = page['title']
        categories = page.get('categories', [])
        
        # Load raw wiki content
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', title)
        raw_file = raw_dir / f"{safe_filename}.wiki"
        
        if not raw_file.exists():
            stats['skipped'] += 1
            continue
        
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Skip very short content
        if len(raw_content.strip()) < 50:
            stats['skipped'] += 1
            continue
        
        domain = detect_domain(title, categories)
        markdown = generate_term_markdown(page, raw_content, domain)
        
        slug = slugify(title)
        filename = f"{slug}.md"
        filepath = output_path / filename
        
        counter = 1
        while filepath.exists():
            filename = f"{slug}-{counter}.md"
            filepath = output_path / filename
            counter += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        stats['converted'] += 1
        
        if (i + 1) % 100 == 0:
            print(f"    Converted {i + 1}/{len(pages)} terms...")
    
    return stats


def convert_glossaries(input_dir: str, output_dir: str):
    """Convert Glossary pages - table format"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    index_file = input_path / '_index.json'
    if not index_file.exists():
        print(f"  Index not found: {index_file}")
        return {'converted': 0, 'skipped': 0, 'by_domain': {}, 'total_entries': 0}
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    pages = index.get('pages', [])
    stats = {'converted': 0, 'skipped': 0, 'by_domain': defaultdict(int), 'total_entries': 0}
    
    for i, page in enumerate(pages):
        title = page['title']
        entries = page.get('entries', [])
        categories = page.get('categories', [])
        
        if not entries or len(entries) < 3:
            stats['skipped'] += 1
            continue
        
        domain = detect_domain(title, categories)
        domain_dir = output_path / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        markdown = generate_glossary_markdown(page, domain)
        
        slug = slugify(title)
        filename = f"{slug}.md"
        filepath = domain_dir / filename
        
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
            print(f"    Converted {i + 1}/{len(pages)} glossaries...")
    
    # Generate category index files
    for domain, count in stats['by_domain'].items():
        domain_dir = output_path / domain
        category_file = domain_dir / '_category.yaml'
        
        domain_names = {
            'legal': ('Legal', '#9b59b6'),
            'medical': ('Medical', '#e74c3c'),
            'technical': ('Technical', '#3498db'),
            'it': ('IT & Computing', '#2ecc71'),
            'automotive': ('Automotive', '#e67e22'),
            'aviation': ('Aviation', '#1abc9c'),
            'financial': ('Financial', '#f39c12'),
            'construction': ('Construction', '#95a5a6'),
            'maritime': ('Maritime', '#3498db'),
            'military': ('Military', '#2c3e50'),
            'food': ('Food & Culinary', '#e74c3c'),
            'textile': ('Textile', '#9b59b6'),
            'energy': ('Energy', '#f1c40f'),
            'agriculture': ('Agriculture', '#27ae60'),
            'chemistry': ('Chemistry', '#8e44ad'),
            'general': ('General', '#34495e'),
        }
        
        name, color = domain_names.get(domain, (domain.title(), '#666666'))
        
        yaml_content = f"""name: {name}
slug: {domain}
description: {name} terminology and glossaries
color: "{color}"
glossary_count: {count}
"""
        with open(category_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert wiki exports to static site')
    parser.add_argument('--source', default='both', choices=['terms', 'glossaries', 'both'])
    parser.add_argument('--output', default='../glossaries')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WIKI TO STATIC SITE CONVERTER v2")
    print("=" * 60)
    
    total_stats = {'terms': 0, 'glossaries': 0, 'entries': 0}
    
    if args.source in ('terms', 'both'):
        print("\n Converting Terms (dictionary entries)...")
        stats = convert_terms('../data/terms', args.output)
        total_stats['terms'] = stats['converted']
        print(f"   Converted {stats['converted']} terms")
        print(f"   Skipped {stats['skipped']} (no raw content)")
    
    if args.source in ('glossaries', 'both'):
        print("\n Converting Glossaries (term tables)...")
        stats = convert_glossaries('../data/terminology_resources', args.output)
        total_stats['glossaries'] = stats['converted']
        total_stats['entries'] = stats['total_entries']
        print(f"   Converted {stats['converted']} glossaries")
        print(f"   Skipped {stats['skipped']} (empty/few entries)")
        print(f"\n  By domain:")
        for domain, count in sorted(stats['by_domain'].items(), key=lambda x: -x[1]):
            print(f"    {domain}: {count}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Terms: {total_stats['terms']}")
    print(f"  Glossaries: {total_stats['glossaries']}")
    print(f"  Total entries in glossaries: {total_stats['entries']:,}")
    print(f"  Output: {args.output}")


if __name__ == "__main__":
    main()
