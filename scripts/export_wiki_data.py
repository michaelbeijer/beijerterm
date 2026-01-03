#!/usr/bin/env python3
"""
MediaWiki Data Exporter for superlookup.wiki

Exports terminology data using the MediaWiki API.
Two main categories:
- Category:Terms (1,385+ individual term pages)
- Category:Terminology_resources (200+ glossary pages)

Usage:
    python scripts/export_wiki_data.py --category Terms --output data/terms/
    python scripts/export_wiki_data.py --category "Terminology resources" --output data/glossaries/
"""

import requests
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, urlencode
from datetime import datetime

BASE_URL = "https://superlookup.wiki"
API_URL = f"{BASE_URL}/w/api.php"

def get_category_members(category: str, limit: int = 500) -> list:
    """Get all pages in a category using MediaWiki API."""
    members = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": limit,
        "format": "json"
    }
    
    while True:
        response = requests.get(API_URL, params=params)
        data = response.json()
        
        if "query" in data and "categorymembers" in data["query"]:
            members.extend(data["query"]["categorymembers"])
        
        # Check for continuation
        if "continue" in data:
            params["cmcontinue"] = data["continue"]["cmcontinue"]
        else:
            break
        
        time.sleep(0.5)  # Be nice to the server
    
    return members

def get_page_content(title: str) -> dict:
    """Get the wikitext content of a page."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json"
    }
    
    response = requests.get(API_URL, params=params)
    data = response.json()
    
    pages = data.get("query", {}).get("pages", {})
    for page_id, page_data in pages.items():
        if page_id != "-1":  # Page exists
            revisions = page_data.get("revisions", [])
            if revisions:
                return {
                    "title": page_data.get("title", ""),
                    "content": revisions[0].get("slots", {}).get("main", {}).get("*", ""),
                    "pageid": page_id
                }
    return None

def parse_term_page(content: str) -> dict:
    """Parse a term page to extract structured data."""
    result = {
        "dutch": [],
        "english": [],
        "notes": "",
        "examples": [],
        "external_links": [],
        "categories": []
    }
    
    # Simple parsing - this would need refinement based on actual wiki templates
    # Extract Dutch terms
    dutch_match = re.search(r"==\s*Dutch\s*==\s*(.*?)(?===|$)", content, re.DOTALL | re.IGNORECASE)
    if dutch_match:
        terms = re.findall(r"\*\s*(.+)", dutch_match.group(1))
        result["dutch"] = [t.strip() for t in terms]
    
    # Extract English terms
    english_match = re.search(r"==\s*English\s*==\s*(.*?)(?===|$)", content, re.DOTALL | re.IGNORECASE)
    if english_match:
        terms = re.findall(r"\*\s*(.+)", english_match.group(1))
        result["english"] = [t.strip() for t in terms]
    
    # Extract categories
    categories = re.findall(r"\[\[Category:([^\]]+)\]\]", content)
    result["categories"] = categories
    
    return result

def export_category(category: str, output_dir: Path, test_mode: bool = False):
    """Export all pages in a category."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Fetching category members for: {category}")
    members = get_category_members(category)
    print(f"Found {len(members)} pages")
    
    if test_mode:
        members = members[:5]
        print(f"Test mode: limiting to {len(members)} pages")
    
    exported = []
    for i, member in enumerate(members):
        title = member["title"]
        print(f"  [{i+1}/{len(members)}] Exporting: {title}")
        
        page = get_page_content(title)
        if page:
            # Save raw wikitext
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            with open(output_dir / f"{safe_title}.wiki", "w", encoding="utf-8") as f:
                f.write(page["content"])
            
            # Parse and save as JSON
            parsed = parse_term_page(page["content"])
            parsed["title"] = title
            parsed["source_url"] = f"{BASE_URL}/{quote(title.replace(' ', '_'))}"
            
            exported.append(parsed)
        
        time.sleep(0.3)  # Rate limiting
    
    # Save index
    with open(output_dir / "_index.json", "w", encoding="utf-8") as f:
        json.dump({
            "category": category,
            "exported_at": datetime.now().isoformat(),
            "count": len(exported),
            "pages": exported
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nExported {len(exported)} pages to {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export superlookup.wiki data")
    parser.add_argument("--category", default="Terms", help="Category to export")
    parser.add_argument("--output", default="data/export", help="Output directory")
    parser.add_argument("--test", action="store_true", help="Test mode - export only 5 pages")
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    export_category(args.category, output_path, test_mode=args.test)
