#!/usr/bin/env python3
"""
Full Export Script for Superlookup Wiki

Uses the sophisticated WikiParser to export all content from superlookup.wiki
"""

import os
import json
import time
import argparse
import requests
from pathlib import Path
from wiki_parser import WikiParser, export_parsed_page, PageType


def get_category_members(category: str, limit: int = None) -> list:
    """Get all pages in a category using MediaWiki API with pagination"""
    url = 'https://superlookup.wiki/w/api.php'
    pages = []
    continue_token = None
    
    while True:
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': 500,
            'format': 'json'
        }
        
        if continue_token:
            params['cmcontinue'] = continue_token
            
        resp = requests.get(url, params=params)
        data = resp.json()
        
        new_pages = data['query']['categorymembers']
        pages.extend(new_pages)
        
        print(f"  Fetched {len(pages)} page titles so far...")
        
        if limit and len(pages) >= limit:
            pages = pages[:limit]
            break
            
        if 'continue' in data:
            continue_token = data['continue']['cmcontinue']
        else:
            break
            
        time.sleep(0.1)  # Be nice to the server
        
    return pages


def get_page_content(title: str) -> str:
    """Get page content via MediaWiki API
    
    Uses action=raw endpoint which handles arbitrarily large pages
    (the standard API truncates at 500KB)
    """
    import urllib.parse
    
    # Use action=raw endpoint - handles large pages without truncation
    encoded_title = urllib.parse.quote(title.replace(' ', '_'))
    url = f'https://superlookup.wiki/w/index.php?title={encoded_title}&action=raw'
    
    resp = requests.get(url)
    
    if resp.status_code == 200 and resp.text:
        return resp.text
    
    # Fallback to API for edge cases
    api_url = 'https://superlookup.wiki/w/api.php'
    params = {
        'action': 'query',
        'prop': 'revisions',
        'titles': title,
        'rvprop': 'content',
        'rvslots': 'main',
        'format': 'json'
    }
    
    resp = requests.get(api_url, params=params)
    data = resp.json()
    
    for page_id, page_data in data['query']['pages'].items():
        if 'revisions' in page_data and page_data['revisions']:
            return page_data['revisions'][0]['slots']['main']['*']
    return None


def export_category(category: str, output_dir: str, limit: int = None, 
                    save_raw: bool = True, rate_limit: float = 0.2):
    """Export all pages in a category"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all page titles
    print(f"\n📚 Fetching pages from Category:{category}")
    pages = get_category_members(category, limit)
    print(f"   Found {len(pages)} pages")
    
    # Initialize parser
    parser = WikiParser()
    
    # Track statistics
    stats = {
        'total': len(pages),
        'parsed': 0,
        'failed': 0,
        'total_entries': 0,
        'by_format': {},
        'by_type': {'term': 0, 'glossary': 0}
    }
    
    # Results index
    index = {
        'category': category,
        'export_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_pages': len(pages),
        'pages': []
    }
    
    # Process each page
    for i, page in enumerate(pages):
        title = page['title']
        print(f"\r  Processing {i+1}/{len(pages)}: {title[:50]}...", end='', flush=True)
        
        try:
            content = get_page_content(title)
            if content:
                # Parse the page
                result = parser.parse(title, content)
                exported = export_parsed_page(result)
                
                # Save raw wikitext if requested
                if save_raw:
                    raw_dir = output_path / 'raw'
                    raw_dir.mkdir(exist_ok=True)
                    safe_filename = "".join(c if c.isalnum() or c in ' -_' else '_' for c in title)
                    with open(raw_dir / f"{safe_filename}.wiki", 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # Add to index
                index['pages'].append(exported)
                
                # Update stats
                stats['parsed'] += 1
                stats['total_entries'] += exported['entry_count']
                
                fmt = exported['metadata'].get('format', 'unknown')
                stats['by_format'][fmt] = stats['by_format'].get(fmt, 0) + 1
                
                page_type = exported['type']
                if page_type in stats['by_type']:
                    stats['by_type'][page_type] += 1
                    
        except Exception as e:
            stats['failed'] += 1
            print(f"\n  ❌ Error parsing {title}: {e}")
            
        time.sleep(rate_limit)  # Rate limiting
        
    print()  # Newline after progress
    
    # Save index
    index_file = output_path / '_index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    # Save stats
    stats_file = output_path / '_stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print(f"\n📊 Export Summary for Category:{category}")
    print(f"   Total pages: {stats['total']}")
    print(f"   Parsed: {stats['parsed']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"\n   By format:")
    for fmt, count in sorted(stats['by_format'].items(), key=lambda x: -x[1]):
        print(f"      {fmt}: {count}")
    print(f"\n   By type:")
    for t, count in stats['by_type'].items():
        print(f"      {t}: {count}")
    print(f"\n   Output: {output_path}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Export Superlookup wiki content')
    parser.add_argument('--category', '-c', default='Terms',
                        help='Category to export (default: Terms)')
    parser.add_argument('--output', '-o', default='data/export',
                        help='Output directory (default: data/export)')
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='Limit number of pages (for testing)')
    parser.add_argument('--no-raw', action='store_true',
                        help='Do not save raw wikitext files')
    parser.add_argument('--rate', '-r', type=float, default=0.2,
                        help='Rate limit in seconds between requests (default: 0.2)')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Export both Terms and Terminology resources')
    
    args = parser.parse_args()
    
    if args.all:
        # Export both categories
        print("=" * 60)
        print("FULL SUPERLOOKUP EXPORT")
        print("=" * 60)
        
        total_stats = {'pages': 0, 'entries': 0}
        
        for cat in ['Terms', 'Terminology resources']:
            output = f"data/{cat.lower().replace(' ', '_')}"
            stats = export_category(
                category=cat,
                output_dir=output,
                limit=args.limit,
                save_raw=not args.no_raw,
                rate_limit=args.rate
            )
            total_stats['pages'] += stats['parsed']
            total_stats['entries'] += stats['total_entries']
            
        print("\n" + "=" * 60)
        print(f"TOTAL: {total_stats['pages']} pages, {total_stats['entries']} entries")
        print("=" * 60)
    else:
        export_category(
            category=args.category,
            output_dir=args.output,
            limit=args.limit,
            save_raw=not args.no_raw,
            rate_limit=args.rate
        )


if __name__ == '__main__':
    main()
