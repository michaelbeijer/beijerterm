#!/usr/bin/env python3
"""
Build script for Beijerterm.

Reads all Markdown glossary and term files, generates HTML pages,
and creates a JSON index for search functionality.
"""

import os
import json
import yaml
import re
import markdown
from pathlib import Path
from datetime import datetime
import shutil

# Configuration
GLOSSARIES_DIR = Path("glossaries")
TERMS_DIR = Path("terms")
SITE_DIR = Path("site")
OUTPUT_DIR = Path("_site")
GITHUB_GLOSSARIES_URL = "https://github.com/michaelbeijer/beijerterm/blob/main/glossaries"
GITHUB_TERMS_URL = "https://github.com/michaelbeijer/beijerterm/blob/main/terms"

# Scroll to top button HTML snippet
SCROLL_TO_TOP_HTML = '''
    <!-- Scroll to top button -->
    <button id="scrollTopBtn" onclick="scrollToTop()" title="Back to top">&#8593;</button>
    <style>
        #scrollTopBtn {
            display: none;
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 99;
            border: none;
            outline: none;
            background-color: #3498db;
            color: white;
            cursor: pointer;
            padding: 15px 20px;
            border-radius: 50%;
            font-size: 18px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }
        #scrollTopBtn:hover {
            background-color: #2980b9;
            transform: scale(1.1);
        }
    </style>
    <script>
        window.onscroll = function() {
            const btn = document.getElementById("scrollTopBtn");
            if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
                btn.style.display = "block";
            } else {
                btn.style.display = "none";
            }
        };
        function scrollToTop() {
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    </script>
'''

# Search highlight and navigation HTML snippet
SEARCH_HIGHLIGHT_HTML = '''
    <!-- Search highlight navigation -->
    <div id="searchNav" class="search-nav" style="display: none;">
        <div class="search-nav-content">
            <span class="search-nav-info">
                "<span id="searchTerm"></span>": 
                <span id="matchCount">0</span> matches
            </span>
            <div class="search-nav-buttons">
                <button onclick="prevMatch()" title="Previous match">
                    <span class="key-hint">P</span> &#9650;
                </button>
                <span id="matchPosition">0/0</span>
                <button onclick="nextMatch()" title="Next match">
                    &#9660; <span class="key-hint">N</span>
                </button>
                <button onclick="closeSearchNav()" title="Close (Esc)" class="close-btn">&times;</button>
            </div>
        </div>
    </div>
    <style>
        .search-nav {
            position: fixed;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            background: #1f2937;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 1000;
            font-size: 14px;
        }
        .search-nav-content {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .search-nav-info {
            color: #9ca3af;
        }
        #searchTerm {
            color: #fbbf24;
            font-weight: 600;
        }
        .search-nav-buttons {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .search-nav button {
            background: #374151;
            border: none;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: background 0.2s;
        }
        .search-nav button:hover {
            background: #4b5563;
        }
        .search-nav .close-btn {
            padding: 6px 10px;
            font-size: 18px;
            margin-left: 8px;
        }
        .key-hint {
            background: #1f2937;
            border: 1px solid #4b5563;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-family: monospace;
        }
        #matchPosition {
            color: #9ca3af;
            min-width: 50px;
            text-align: center;
        }
        .search-highlight {
            background-color: #fef08a !important;
            color: #1f2937 !important;
            padding: 1px 2px;
            border-radius: 2px;
        }
        .search-highlight.current {
            background-color: #f97316 !important;
            color: white !important;
            box-shadow: 0 0 0 2px #f97316;
        }
    </style>
    <script>
        let highlights = [];
        let currentIndex = -1;
        
        function initSearchHighlight() {
            const params = new URLSearchParams(window.location.search);
            const query = params.get('q');
            if (!query) return;
            
            const searchTerm = query.trim();
            if (searchTerm.length < 2) return;
            
            // Find and highlight matches in tables and content
            const container = document.querySelector('[data-pagefind-body]') || document.querySelector('main');
            if (!container) return;
            
            highlightText(container, searchTerm);
            
            if (highlights.length > 0) {
                document.getElementById('searchNav').style.display = 'block';
                document.getElementById('searchTerm').textContent = searchTerm;
                document.getElementById('matchCount').textContent = highlights.length;
                currentIndex = 0;
                goToMatch(0);
            }
        }
        
        function highlightText(element, searchTerm) {
            const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
            const textNodes = [];
            const lowerSearch = searchTerm.toLowerCase();
            
            while (walker.nextNode()) {
                if (walker.currentNode.textContent.toLowerCase().includes(lowerSearch)) {
                    textNodes.push(walker.currentNode);
                }
            }
            
            textNodes.forEach(node => {
                const text = node.textContent;
                const regex = new RegExp('(' + escapeRegex(searchTerm) + ')', 'gi');
                const parts = text.split(regex);
                
                if (parts.length > 1) {
                    const fragment = document.createDocumentFragment();
                    parts.forEach(part => {
                        if (part.toLowerCase() === searchTerm.toLowerCase()) {
                            const mark = document.createElement('mark');
                            mark.className = 'search-highlight';
                            mark.textContent = part;
                            highlights.push(mark);
                            fragment.appendChild(mark);
                        } else {
                            fragment.appendChild(document.createTextNode(part));
                        }
                    });
                    node.parentNode.replaceChild(fragment, node);
                }
            });
        }
        
        function escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
        }
        
        function goToMatch(index) {
            if (highlights.length === 0) return;
            
            highlights.forEach(h => h.classList.remove('current'));
            
            currentIndex = index;
            if (currentIndex < 0) currentIndex = highlights.length - 1;
            if (currentIndex >= highlights.length) currentIndex = 0;
            
            const current = highlights[currentIndex];
            current.classList.add('current');
            current.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            document.getElementById('matchPosition').textContent = 
                (currentIndex + 1) + '/' + highlights.length;
        }
        
        function nextMatch() { goToMatch(currentIndex + 1); }
        function prevMatch() { goToMatch(currentIndex - 1); }
        
        function closeSearchNav() {
            document.getElementById('searchNav').style.display = 'none';
            highlights.forEach(h => {
                const text = h.textContent;
                h.parentNode.replaceChild(document.createTextNode(text), h);
            });
            highlights = [];
            const url = new URL(window.location);
            url.searchParams.delete('q');
            window.history.replaceState({}, '', url);
        }
        
        document.addEventListener('keydown', function(e) {
            if (highlights.length === 0) return;
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            if (e.key === 'n' || e.key === 'N') { e.preventDefault(); nextMatch(); }
            else if (e.key === 'p' || e.key === 'P') { e.preventDefault(); prevMatch(); }
            else if (e.key === 'Escape') { closeSearchNav(); }
        });
        
        document.addEventListener('DOMContentLoaded', initSearchHighlight);
    </script>
'''


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from Markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return frontmatter or {}, body
            except:
                pass
    return {}, content


def parse_markdown_table(body: str) -> list[dict]:
    """Extract terms from Markdown table."""
    terms = []
    lines = body.split("\n")

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "|" in line[1:]:
            header_idx = i
            break

    if header_idx is None:
        return terms

    header_line = lines[header_idx]
    headers = [h.strip() for h in header_line.split("|")[1:-1]]

    for line in lines[header_idx + 2:]:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 2:
            term = {}
            for j, header in enumerate(headers):
                if j < len(cells):
                    term[header.lower()] = cells[j]
            terms.append(term)

    return terms


def markdown_to_html(md_content: str) -> str:
    """Convert Markdown to HTML."""
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    return html


def load_categories() -> dict:
    """Load all category metadata."""
    categories = {}
    for cat_file in GLOSSARIES_DIR.rglob("_category.yaml"):
        with open(cat_file, "r", encoding="utf-8") as f:
            cat_data = yaml.safe_load(f)
            if cat_data:
                categories[cat_data.get("slug", cat_file.parent.name)] = cat_data
    return categories


def load_all_content() -> tuple[list[dict], list[dict]]:
    """Load all glossary and term files."""
    glossaries = []
    terms = []

    # Load glossaries from glossaries/ directory
    for md_file in GLOSSARIES_DIR.rglob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, body = parse_frontmatter(content)
        if not frontmatter:
            continue

        # Build GitHub source URL
        relative_path = md_file.relative_to(GLOSSARIES_DIR)
        github_url = f"{GITHUB_GLOSSARIES_URL}/{relative_path}".replace("\\", "/")

        item = {
            "file": str(md_file),
            "category": md_file.parent.name,
            "body": body,
            **frontmatter,
        }
        # Override source_url with GitHub URL (frontmatter may have old wiki URL)
        item["source_url"] = github_url
        item["type"] = "glossary"
        item["terms"] = parse_markdown_table(body)
        item["term_count"] = len(item["terms"])
        
        # Auto-add category folder name as a tag (if not already present)
        existing_tags = item.get("tags", [])
        # Normalize tags - handle mix of strings and dicts
        normalized_tags = []
        for t in existing_tags:
            if isinstance(t, dict):
                normalized_tags.append(t.get("name", str(t)))
            else:
                normalized_tags.append(str(t))
        
        existing_tag_names_lower = [t.lower() for t in normalized_tags]
        category_tag = md_file.parent.name.replace("-", " ").title()
        if category_tag.lower() not in existing_tag_names_lower:
            item["tags"] = [category_tag] + normalized_tags
        else:
            item["tags"] = normalized_tags
        
        glossaries.append(item)

    # Load terms from terms/ directory (at root level)
    if TERMS_DIR.exists():
        for md_file in TERMS_DIR.rglob("*.md"):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, body = parse_frontmatter(content)
            if not frontmatter:
                continue

            # Build GitHub source URL for terms
            relative_path = md_file.relative_to(TERMS_DIR)
            github_url = f"{GITHUB_TERMS_URL}/{relative_path}".replace("\\", "/")

            item = {
                "file": str(md_file),
                "category": "terms",
                "body": body,
                **frontmatter,
            }
            item["source_url"] = github_url
            item["type"] = "term"
            item["html_content"] = markdown_to_html(body)
            terms.append(item)

    return glossaries, terms


def generate_site_header(current_page: str = "home") -> str:
    """Generate the site header with navigation."""
    home_active = 'class="active"' if current_page == "home" else ''
    tagline = '<span class="header-tagline">Open source multilingual terminology</span>' if current_page == "home" else ''
    return f'''<header class="site-header">
        <div class="header-content">
            <div class="header-left">
                <a href="/beijerterm/" class="site-brand" title="Beijerterm homepage">
                    <img src="{'../' if current_page != 'home' else ''}mb-icon.svg" alt="Beijerterm" class="site-logo">
                    <span>Beijerterm</span>
                    <span class="version-badge">v1.0.2</span>
                </a>
                {tagline}
            </div>
            <nav class="header-nav">
                <a href="https://michaelbeijer.co.uk" target="_blank" title="Author's website">Michael Beijer</a>
                <a href="https://github.com/michaelbeijer/beijerterm" target="_blank" title="View source code and contribute">GitHub</a>
                <a href="https://supervertaler.com" target="_blank" title="AI-powered translation workbench">Supervertaler</a>
            </nav>
        </div>
    </header>'''


def generate_site_footer() -> str:
    """Generate the site footer."""
    return '''<footer class="site-footer">
        <div class="footer-content">
            <div class="footer-section">
                <h4>Beijerterm</h4>
                <p>Open source multilingual terminology database for translators.</p>
            </div>
            <div class="footer-section">
                <h4>Links</h4>
                <ul>
                    <li><a href="https://github.com/michaelbeijer/beijerterm">GitHub Repository</a></li>
                    <li><a href="https://supervertaler.com">Supervertaler</a></li>
                    <li><a href="https://michaelbeijer.co.uk">Michael Beijer</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h4>License</h4>
                <p>All data is open source and freely available.</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2025 Michael Beijer. Built with ❤️ for the translation community.</p>
        </div>
    </footer>'''


def generate_search_index(glossaries: list[dict], terms: list[dict]) -> list[dict]:
    """Generate search index for all content."""
    index = []
    for glossary in glossaries:
        for term in glossary.get("terms", []):
            entry = {
                "type": "glossary_term",
                "glossary": glossary["title"],
                "glossary_slug": glossary["slug"],
                "category": glossary["category"],
                "source_lang": glossary.get("source_lang", ""),
                "target_lang": glossary.get("target_lang", ""),
                **term,
            }
            index.append(entry)

    for term in terms:
        entry = {
            "type": "term",
            "title": term["title"],
            "slug": term["slug"],
            "category": term.get("category", "terms"),
            "description": term.get("description", ""),
        }
        index.append(entry)
    return index


def generate_categories_content(glossaries: list[dict], terms: list[dict], categories: dict) -> str:
    """Generate the tags tab content showing all tags with their glossaries/terms as clickable links."""
    
    # Group glossaries and terms by category
    cat_items = {}
    for g in glossaries:
        cat = g.get("category", "uncategorized")
        if cat not in cat_items:
            cat_items[cat] = {"glossaries": [], "terms": [], "term_entries": 0}
        cat_items[cat]["glossaries"].append(g)
        cat_items[cat]["term_entries"] += g.get("term_count", 0)
    
    for t in terms:
        cat = t.get("category", "terms")
        if cat not in cat_items:
            cat_items[cat] = {"glossaries": [], "terms": [], "term_entries": 0}
        cat_items[cat]["terms"].append(t)
    
    # Build category cards
    cards_html = ""
    for cat_slug, items in sorted(cat_items.items(), key=lambda x: x[0]):
        cat_info = categories.get(cat_slug, {"name": cat_slug.replace("-", " ").title(), "color": "#666", "description": ""})
        cat_name = cat_info.get("name", cat_slug.replace("-", " ").title())
        cat_color = cat_info.get("color", "#666")
        
        glossary_list = items["glossaries"]
        term_list = items["terms"]
        entry_count = items["term_entries"]
        
        # Build glossary links (show all, sorted by title)
        glossary_links = ""
        if glossary_list:
            sorted_glossaries = sorted(glossary_list, key=lambda x: x["title"].upper())
            links = [f'<a href="glossary/{g["slug"]}.html" class="tag-item-link">{g["title"]}</a>' for g in sorted_glossaries]
            glossary_links = f'''
            <div class="tag-items-section">
                <div class="tag-items-header">📚 Glossaries ({len(glossary_list)})</div>
                <div class="tag-items-list">{"".join(links)}</div>
            </div>'''
        
        # Build term links (show all, sorted by title)
        term_links = ""
        if term_list:
            sorted_terms = sorted(term_list, key=lambda x: x["title"].upper())
            links = [f'<a href="term/{t["slug"]}.html" class="tag-item-link">{t["title"]}</a>' for t in sorted_terms]
            term_links = f'''
            <div class="tag-items-section">
                <div class="tag-items-header">📖 Terms ({len(term_list)})</div>
                <div class="tag-items-list">{"".join(links)}</div>
            </div>'''
        
        # Stats summary
        stats_summary = f'{len(glossary_list)} glossaries • {len(term_list)} terms • {entry_count:,} entries'
        
        cards_html += f'''
        <div class="category-card">
            <div class="category-card-header" style="background-color: {cat_color}">
                <h3>{cat_name}</h3>
                <span class="tag-stats-summary">{stats_summary}</span>
            </div>
            <div class="category-card-body">
                {glossary_links}
                {term_links}
            </div>
        </div>'''
    
    return f'''<div class="categories-grid">{cards_html}</div>'''


def generate_table_for_items(items: list[dict], categories: dict, item_type: str) -> tuple[str, str]:
    """Generate HTML table sections for a list of items."""
    sorted_items = sorted(items, key=lambda x: x["title"].upper())
    
    by_letter = {}
    for item in sorted_items:
        first_letter = item["title"][0].upper()
        if not first_letter.isalpha():
            first_letter = "#"
        if first_letter not in by_letter:
            by_letter[first_letter] = []
        by_letter[first_letter].append(item)

    all_letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    alphabet_nav = ""
    for letter in all_letters:
        if letter in by_letter:
            alphabet_nav += f'<a href="#letter-{item_type}-{letter}" class="alphabet-link">{letter}</a>'
        else:
            alphabet_nav += f'<span class="alphabet-link disabled">{letter}</span>'

    sections = ""
    for letter in all_letters:
        if letter not in by_letter:
            continue

        if item_type == "glossary":
            sections += f'''
            <section class="letter-section" id="letter-{item_type}-{letter}">
                <h3 class="letter-heading">{letter}</h3>
                <table class="glossary-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Category</th>
                            <th>Languages</th>
                            <th>Terms</th>
                        </tr>
                    </thead>
                    <tbody>'''
            
            for item in by_letter[letter]:
                cat_info = categories.get(item["category"], {"name": item["category"], "color": "#666"})
                link = f"glossary/{item['slug']}.html"
                sections += f'''
                        <tr>
                            <td><a href="{link}">{item['title']}</a></td>
                            <td><span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', item['category'])}</span></td>
                            <td>{item.get('source_lang', '')} &rarr; {item.get('target_lang', '')}</td>
                            <td>{item.get('term_count', 0):,}</td>
                        </tr>'''

            sections += '''
                    </tbody>
                </table>
            </section>'''
        
        else:
            sections += f'''
            <section class="letter-section" id="letter-{item_type}-{letter}">
                <h3 class="letter-heading">{letter}</h3>
                <table class="glossary-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Description</th>
                            <th>Languages</th>
                        </tr>
                    </thead>
                    <tbody>'''
            
            for item in by_letter[letter]:
                link = f"term/{item['slug']}.html"
                desc = item.get('description', '')[:100]
                if len(item.get('description', '')) > 100:
                    desc += '...'
                sections += f'''
                        <tr>
                            <td><a href="{link}">{item['title']}</a></td>
                            <td>{desc}</td>
                            <td>{item.get('source_lang', 'nl')} &rarr; {item.get('target_lang', 'en')}</td>
                        </tr>'''

            sections += '''
                    </tbody>
                </table>
            </section>'''

    return alphabet_nav, sections


def generate_html_index(glossaries: list[dict], terms: list[dict], categories: dict) -> str:
    """Generate the main index.html page with tabs."""
    
    site_header = generate_site_header("home")
    site_footer = generate_site_footer()
    total_glossaries = len(glossaries)
    total_terms_pages = len(terms)
    total_term_entries = sum(g.get('term_count', 0) for g in glossaries)

    glossary_nav, glossary_sections = generate_table_for_items(glossaries, categories, "glossary")
    terms_nav, terms_sections = generate_table_for_items(terms, categories, "term")
    categories_content = generate_categories_content(glossaries, terms, categories)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beijerterm - Open Source Multilingual Terminology</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="icon" href="favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="pagefind/pagefind-ui.css">
    <style>
        .tabs {{
            display: flex;
            gap: 0;
            border-bottom: 2px solid #ddd;
            margin-bottom: 1.5rem;
        }}
        .tab-button {{
            padding: 12px 24px;
            border: none;
            background: #f5f5f5;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            color: #666;
            border-radius: 8px 8px 0 0;
            margin-right: 4px;
            transition: all 0.2s;
        }}
        .tab-button:hover {{
            background: #e8e8e8;
        }}
        .tab-button.active {{
            background: #3498db;
            color: white;
        }}
        .tab-button .count {{
            background: rgba(0,0,0,0.1);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.85rem;
            margin-left: 8px;
        }}
        .tab-button.active .count {{
            background: rgba(255,255,255,0.2);
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .tab-description {{
            color: #666;
            margin-bottom: 1rem;
            font-style: italic;
        }}
        /* Tag cards */
        .categories-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        .category-card {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .category-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }}
        .category-card-header {{
            padding: 1rem 1.25rem;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .category-card-header h3 {{
            margin: 0;
            font-size: 1.1rem;
        }}
        .tag-stats-summary {{
            font-size: 0.75rem;
            opacity: 0.85;
        }}
        .category-card-body {{
            padding: 0.75rem 1.25rem 1rem;
        }}
        .tag-items-section {{
            margin-bottom: 0.75rem;
        }}
        .tag-items-section:last-child {{
            margin-bottom: 0;
        }}
        .tag-items-header {{
            font-size: 0.8rem;
            font-weight: 600;
            color: #666;
            margin-bottom: 0.5rem;
            padding-bottom: 0.25rem;
            border-bottom: 1px solid #eee;
        }}
        .tag-items-list {{
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }}
        .tag-item-link {{
            color: #2563eb;
            text-decoration: none;
            font-size: 0.9rem;
            padding: 0.25rem 0;
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .tag-item-link:hover {{
            color: #1d4ed8;
            text-decoration: underline;
        }}
        @media (prefers-color-scheme: dark) {{
            .category-card {{
                background: #1f2937;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            .category-card:hover {{
                box-shadow: 0 4px 16px rgba(0,0,0,0.4);
            }}
            .tag-items-header {{
                color: #9ca3af;
                border-bottom-color: #374151;
            }}
            .tag-item-link {{
                color: #60a5fa;
            }}
            .tag-item-link:hover {{
                color: #93c5fd;
            }}
        }}
    </style>
</head>
<body>
    {site_header}

    <div class="page-container">
        <main>
                <section class="search-section">
                    <div id="search"></div>
                </section>

                <section class="stats">
                    <div class="stat">
                        <span class="stat-value">{total_glossaries}</span>
                        <span class="stat-label">Glossaries</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">{total_terms_pages:,}</span>
                        <span class="stat-label">Term Pages</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">{total_term_entries:,}</span>
                        <span class="stat-label">Term Entries</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">{len(categories)}</span>
                        <span class="stat-label">Categories</span>
                    </div>
                </section>

                <section class="content-browser">
                    <div class="tabs">
                        <button class="tab-button active" onclick="showTab('glossaries', this)">
                            &#128218; Glossaries<span class="count">{total_glossaries}</span>
                        </button>
                        <button class="tab-button" onclick="showTab('terms', this)">
                            &#128214; Terms<span class="count">{total_terms_pages:,}</span>
                        </button>
                        <button class="tab-button" onclick="showTab('tags', this)">
                            &#127991; Tags<span class="count">{len(categories)}</span>
                        </button>
                    </div>

                    <div id="tab-glossaries" class="tab-content active">
                        <p class="tab-description">Terminology lists and glossaries with multiple term entries each.</p>
                        <nav class="alphabet-nav">
                            {glossary_nav}
                        </nav>
                        {glossary_sections}
                    </div>

                    <div id="tab-terms" class="tab-content">
                        <p class="tab-description">Individual term pages with definitions, examples, and reference links.</p>
                        <nav class="alphabet-nav">
                            {terms_nav}
                        </nav>
                        {terms_sections}
                    </div>

                    <div id="tab-tags" class="tab-content">
                        <p class="tab-description">Browse content by tag. Each glossary is automatically tagged with its category.</p>
                        {categories_content}
                    </div>
                </section>
        </main>
    </div>

    {site_footer}

    <script src="pagefind/pagefind-ui.js"></script>
    <script>
        window.addEventListener('DOMContentLoaded', (event) => {{
            const pf = new PagefindUI({{
                element: "#search",
                showSubResults: true,
                showImages: false
            }});

            // Intercept ALL link clicks to pass search query (Pagefind uses shadow DOM)
            document.addEventListener('click', function(e) {{
                const link = e.target.closest('a');
                if (link && link.href && link.href.includes('/glossary/') || link && link.href && link.href.includes('/term/')) {{
                    const searchInput = document.querySelector('.pagefind-ui__search-input');
                    if (searchInput && searchInput.value.trim()) {{
                        e.preventDefault();
                        const query = encodeURIComponent(searchInput.value.trim());
                        const separator = link.href.includes('?') ? '&' : '?';
                        window.location.href = link.href + separator + 'q=' + query;
                    }}
                }}
            }}, true);  // Use capture phase to intercept before shadow DOM
            
            // Also watch for Pagefind result links being added
            const searchEl = document.getElementById('search');
            const observer = new MutationObserver(function(mutations) {{
                searchEl.querySelectorAll('a[href]').forEach(link => {{
                    if (!link.dataset.intercepted) {{
                        link.dataset.intercepted = 'true';
                        link.addEventListener('click', function(e) {{
                            const searchInput = document.querySelector('.pagefind-ui__search-input');
                            if (searchInput && searchInput.value.trim()) {{
                                e.preventDefault();
                                const query = encodeURIComponent(searchInput.value.trim());
                                const separator = this.href.includes('?') ? '&' : '?';
                                window.location.href = this.href + separator + 'q=' + query;
                            }}
                        }});
                    }}
                }});
            }});
            observer.observe(searchEl, {{ childList: true, subtree: true }});
        }});

        function showTab(tabName, btn) {{
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab-button').forEach(b => {{
                b.classList.remove('active');
            }});
            document.getElementById('tab-' + tabName).classList.add('active');
            btn.classList.add('active');
        }}
    </script>
{SCROLL_TO_TOP_HTML}
</body>
</html>'''


def generate_glossary_page(glossary: dict, categories: dict) -> str:
    """Generate an individual glossary page."""
    cat_info = categories.get(glossary["category"], {"name": glossary["category"], "color": "#666"})

    terms = glossary.get("terms", [])
    if terms:
        headers = list(terms[0].keys())
    else:
        headers = ["source", "target", "notes"]

    header_row = "".join(f"<th>{h.title()}</th>" for h in headers)

    term_rows = ""
    for term in terms:
        cells = "".join(f"<td>{term.get(h, '')}</td>" for h in headers)
        term_rows += f"<tr>{cells}</tr>\n"

    # Generate tags HTML if tags exist
    tags = glossary.get("tags", [])
    tags_html = ""
    if tags:
        tag_badges = " ".join(f'<span class="tag-badge">{tag}</span>' for tag in tags)
        tags_html = f'<div class="tags-row">{tag_badges}</div>'

    site_header = generate_site_header("glossary")
    site_footer = generate_site_footer()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{glossary['title']} - Beijerterm</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="icon" href="../favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="../pagefind/pagefind-ui.css">
</head>
<body>
    {site_header}

    <div class="page-container">
        <div class="page-header">
            <nav class="breadcrumb"><a href="../index.html">&larr; Back to all glossaries</a></nav>
            <h1>{glossary['title']}</h1>
            <p class="page-description">{glossary.get('description', '')}</p>
        </div>

        <main>
            <section class="glossary-meta">
                <span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', '')}</span>
                <span class="lang-badge">{glossary.get('source_lang', '')} &rarr; {glossary.get('target_lang', '')}</span>
                <span class="term-count">{glossary.get('term_count', 0):,} terms</span>
                {tags_html}
            </section>

            <section class="glossary-content" data-pagefind-body>
                <table class="terms-table">
                    <thead>
                        <tr>{header_row}</tr>
                    </thead>
                    <tbody>
                        {term_rows}
                    </tbody>
                </table>
            </section>

            <section class="glossary-info">
                <h3>About this glossary</h3>
                <dl>
                    <dt>Source</dt>
                    <dd><a href="{glossary.get('source_url', '#')}">{glossary.get('source_url', 'Unknown')}</a></dd>
                    <dt>Last Updated</dt>
                    <dd>{glossary.get('last_updated', 'Unknown')}</dd>
                </dl>
            </section>
        </main>
    </div>

    {site_footer}

    <script src="../pagefind/pagefind-ui.js"></script>
{SEARCH_HIGHLIGHT_HTML}
{SCROLL_TO_TOP_HTML}
</body>
</html>'''


def generate_term_page(term: dict, categories: dict) -> str:
    """Generate an individual term page."""
    cat_info = categories.get(term.get("category", "terms"), {"name": "Terms", "color": "#34495e"})
    html_content = term.get("html_content", "")
    
    # Generate tags HTML if tags exist
    tags = term.get("tags", [])
    tags_html = ""
    if tags:
        tag_badges = " ".join(f'<span class="tag-badge">{tag}</span>' for tag in tags)
        tags_html = f'<div class="tags-row">{tag_badges}</div>'
    
    site_header = generate_site_header("term")
    site_footer = generate_site_footer()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{term['title']} - Beijerterm</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="icon" href="../favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="../pagefind/pagefind-ui.css">
</head>
<body>
    {site_header}

    <div class="page-container">
        <div class="page-header">
            <nav class="breadcrumb"><a href="../index.html">&larr; Back to all content</a></nav>
            <h1>{term['title']}</h1>
            <p class="page-description">{term.get('description', '')}</p>
        </div>

        <main>
            <section class="term-meta">
                <span class="type-badge term">Term</span>
                <span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', 'Terms')}</span>
                <span class="lang-badge">{term.get('source_lang', 'nl')} &rarr; {term.get('target_lang', 'en')}</span>
                {tags_html}
            </section>

            <section class="term-content" data-pagefind-body>
                {html_content}
            </section>

            <section class="term-info">
                <h3>About this term</h3>
                <dl>
                    <dt>Source</dt>
                    <dd><a href="{term.get('source_url', '#')}">{term.get('source_url', 'Unknown')}</a></dd>
                    <dt>Last Updated</dt>
                    <dd>{term.get('last_updated', 'Unknown')}</dd>
                </dl>
            </section>
        </main>
    </div>

    {site_footer}

    <script src="../pagefind/pagefind-ui.js"></script>
{SEARCH_HIGHLIGHT_HTML}
{SCROLL_TO_TOP_HTML}
</body>
</html>'''


def build_site():
    """Main build function."""
    print("Building Beijerterm site...")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "glossary").mkdir()
    (OUTPUT_DIR / "term").mkdir()

    print("Loading content...")
    categories = load_categories()
    glossaries, terms = load_all_content()
    print(f"   Found {len(glossaries)} glossaries and {len(terms)} terms in {len(categories)} categories")

    print("Generating search index...")
    search_index = generate_search_index(glossaries, terms)
    with open(OUTPUT_DIR / "search-index.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    print(f"   Indexed {len(search_index)} entries")

    print("Generating HTML pages...")
    index_html = generate_html_index(glossaries, terms, categories)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    for glossary in glossaries:
        page_html = generate_glossary_page(glossary, categories)
        output_path = OUTPUT_DIR / "glossary" / f"{glossary['slug']}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_html)

    for term in terms:
        page_html = generate_term_page(term, categories)
        output_path = OUTPUT_DIR / "term" / f"{term['slug']}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_html)

    print("Copying static assets...")
    if (SITE_DIR / "styles.css").exists():
        shutil.copy(SITE_DIR / "styles.css", OUTPUT_DIR / "styles.css")
    if (SITE_DIR / "mb-icon.svg").exists():
        shutil.copy(SITE_DIR / "mb-icon.svg", OUTPUT_DIR / "mb-icon.svg")
    if (SITE_DIR / "MB.ico").exists():
        shutil.copy(SITE_DIR / "MB.ico", OUTPUT_DIR / "favicon.ico")

    print(f"Site built successfully in {OUTPUT_DIR}/")
    print(f"\nSummary:")
    print(f"   - Glossaries: {len(glossaries)}")
    print(f"   - Term pages: {len(terms)}")
    print(f"   - Total term entries: {sum(g.get('term_count', 0) for g in glossaries):,}")


if __name__ == "__main__":
    build_site()
