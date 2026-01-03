#!/usr/bin/env python3
"""
Re-export script for previously failed pages

These pages failed due to the 500KB API limit - now using action=raw endpoint
"""

import os
import json
import time
from pathlib import Path
from full_export import get_page_content
from wiki_parser import WikiParser, export_parsed_page

# Pages that failed in the first export (API 500KB limit)
FAILED_PAGES = [
    "acronymbook1",
    "acronymbook2",
    "acronymbook3",
    "acronymbook4",
    "acronymbook5",
    "acronymbook6",
    "Apple glossary (45,000 Dutch-English entries) - Part 1",
    "Apple glossary (45,000 Dutch-English entries) - Part 2",
    "Common Procurement Vocabulary (CPV) (Dutch-English glossary)",
    "Comprehensive Technical Dictionary (Dutch-English) - A",
    "Comprehensive Technical Dictionary (Dutch-English) - B",
    "digitalSkillsCollection (ESCO classification)",
    "DUTCH-ENGLISH DICTIONARY V.05.2011 - Jerzy Kazojć (2011)",
    "Dutch-English glossary (31224 entries)(Part 1)",
    "Dutch-English glossary (31224 entries)(Part 2)",
    "Eskom Dictionary for power generation and distribution (English-Afrikaans)",
    "EuroVoc1",
    "Glossary of Botanical & Horticultural Terms (Herman Busser)",
    "Lycaeus Juridisch Woordenboek",
    "Microsoft Terminology Collection (33,004 Dutch-English entries)(Part 1)",
    "Microsoft Terminology Collection (33,004 Dutch-English entries)(Part 2)",
    "Microsoft Terminology Collection (33,004 Dutch-English entries)(Part 3)",
    "Technical Glossary (29329 Dutch-English entries)",
]


def main():
    output_dir = Path("../data/terminology_resources")
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing index
    index_file = output_dir / "_index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {"pages": []}
    
    parser = WikiParser()
    
    stats = {
        'processed': 0,
        'succeeded': 0,
        'failed': 0,
        'total_entries': 0,
    }
    
    print("=" * 60)
    print("RE-EXPORTING PREVIOUSLY FAILED PAGES")
    print("(These failed due to MediaWiki API 500KB limit)")
    print("=" * 60)
    
    for title in FAILED_PAGES:
        print(f"\n📄 {title}")
        
        try:
            content = get_page_content(title)
            if not content:
                print(f"  ❌ Could not fetch content")
                stats['failed'] += 1
                continue
                
            print(f"  📥 Fetched {len(content):,} bytes")
            
            # Parse
            result = parser.parse(title, content)
            exported = export_parsed_page(result)
            
            print(f"  ✅ Parsed {exported['entry_count']:,} entries ({exported['metadata'].get('format')})")
            
            # Save raw
            safe_filename = "".join(c if c.isalnum() or c in ' -_' else '_' for c in title)
            with open(raw_dir / f"{safe_filename}.wiki", 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update index (remove old entry if exists, add new)
            index['pages'] = [p for p in index['pages'] if p['title'] != title]
            index['pages'].append(exported)
            
            stats['succeeded'] += 1
            stats['total_entries'] += exported['entry_count']
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            stats['failed'] += 1
            
        stats['processed'] += 1
        time.sleep(0.3)  # Rate limiting
    
    # Save updated index
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    # Update stats file
    stats_file = output_dir / "_stats.json"
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            full_stats = json.load(f)
    else:
        full_stats = {}
    
    # Recalculate totals from index
    full_stats['total_pages'] = len(index['pages'])
    full_stats['total_entries'] = sum(p['entry_count'] for p in index['pages'])
    
    # Recalculate format distribution
    by_format = {}
    by_type = {'term': 0, 'glossary': 0}
    for p in index['pages']:
        fmt = p['metadata'].get('format', 'unknown')
        by_format[fmt] = by_format.get(fmt, 0) + 1
        if p['type'] in by_type:
            by_type[p['type']] += 1
    
    full_stats['by_format'] = by_format
    full_stats['by_type'] = by_type
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(full_stats, f, indent=2)
    
    print("\n" + "=" * 60)
    print("📊 RE-EXPORT SUMMARY")
    print("=" * 60)
    print(f"  Processed: {stats['processed']}")
    print(f"  Succeeded: {stats['succeeded']}")
    print(f"  Failed:    {stats['failed']}")
    print(f"  New entries: {stats['total_entries']:,}")
    print(f"\n  Updated totals:")
    print(f"    Total pages:   {full_stats['total_pages']}")
    print(f"    Total entries: {full_stats['total_entries']:,}")


if __name__ == "__main__":
    main()
