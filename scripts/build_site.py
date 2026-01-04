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
        existing_tags = item.get("tags") or []
        # Normalize tags - handle mix of strings and dicts
        normalized_tags = []
        for t in existing_tags:
            if isinstance(t, dict):
                normalized_tags.append(t.get("name", str(t)))
            elif t:  # Skip None/empty
                normalized_tags.append(str(t))
        
        existing_tag_names_lower = [t.lower() for t in normalized_tags]
        # Map folder names to standardized tag names
        folder_to_tag = {
            "financial": "finance",
            "it": "IT",  # IT is an acronym, keep uppercase
            "general": None,  # Don't auto-add "general" tag - too generic
            "textile": "textiles",  # Standardize to plural
        }
        folder_name = md_file.parent.name.replace("-", " ").lower()
        category_tag = folder_to_tag.get(folder_name, folder_name)
        
        if category_tag and category_tag.lower() not in existing_tag_names_lower:
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
    # Pages in root directory: home, tags. Pages in subdirectories: glossary, term
    is_root_page = current_page in ("home", "tags")
    home_active = 'class="active"' if current_page == "home" else ''
    tagline = '<span class="header-tagline">Open-source, GitHub-hosted multilingual terminology database</span>'
    return f'''<header class="site-header">
        <div class="header-content">
            <div class="header-left">
                <a href="/beijerterm/" class="site-brand" title="Beijerterm homepage">
                    <img src="{'' if is_root_page else '../'}mb-icon.svg" alt="Beijerterm" class="site-logo">
                    <span>Beijerterm</span>
                    <span class="version-badge">v1.0.8</span>
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
                <p>Open-source, GitHub-hosted multilingual terminology database for translators.</p>
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


def collect_all_tags(glossaries: list[dict], terms: list[dict]) -> dict:
    """Collect all unique tags from glossaries and terms with their usage counts and items."""
    tag_index = {}
    
    for g in glossaries:
        for tag in g.get("tags", []):
            tag_normalized = tag.strip()
            if tag_normalized not in tag_index:
                tag_index[tag_normalized] = {"glossaries": [], "terms": [], "term_entries": 0}
            tag_index[tag_normalized]["glossaries"].append(g)
            tag_index[tag_normalized]["term_entries"] += g.get("term_count", 0)
    
    for t in terms:
        for tag in t.get("tags", []):
            tag_normalized = tag.strip()
            if tag_normalized not in tag_index:
                tag_index[tag_normalized] = {"glossaries": [], "terms": [], "term_entries": 0}
            tag_index[tag_normalized]["terms"].append(t)
    
    return tag_index


def generate_tags_reference(tag_index: dict) -> tuple[str, str]:
    """Generate TAGS.md (for repo) and tags.html (for website)."""
    
    # Sort tags alphabetically (case-insensitive)
    sorted_tags = sorted(tag_index.items(), key=lambda x: x[0].lower())
    
    # Generate TAGS.md content
    md_content = """# Tag Reference

This file is auto-generated by the build script. It lists all tags currently used in Beijerterm.

## Tag Naming Conventions

- **Lowercase** for generic subjects: `legal`, `medical`, `automotive`, `diamonds`
- **Capitalize** proper nouns only: `Microsoft`, `EU`, `BBC`, `ISO 9001`
- **Multi-word tags**: Use spaces: `machine learning`, `3D printing`

## All Tags

| Tag | Glossaries | Terms | Entries |
|-----|------------|-------|---------|
"""
    
    for tag, data in sorted_tags:
        g_count = len(data["glossaries"])
        t_count = len(data["terms"])
        e_count = data["term_entries"]
        md_content += f"| {tag} | {g_count} | {t_count} | {e_count:,} |\n"
    
    md_content += f"\n---\n\n*Total unique tags: {len(tag_index)}*\n"
    md_content += "*Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "*\n"
    
    # Generate tags.html content  
    site_header = generate_site_header("tags")
    site_footer = generate_site_footer()
    
    table_rows = ""
    for tag, data in sorted_tags:
        g_count = len(data["glossaries"])
        t_count = len(data["terms"])
        e_count = data["term_entries"]
        table_rows += f"""
        <tr>
            <td><span class="tag-badge">{tag}</span></td>
            <td>{g_count}</td>
            <td>{t_count}</td>
            <td>{e_count:,}</td>
        </tr>"""
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tag Reference - Beijerterm</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="icon" href="favicon.ico" type="image/x-icon">
</head>
<body>
    {site_header}

    <div class="page-container">
        <div class="page-header">
            <nav class="breadcrumb"><a href="index.html">&larr; Back to home</a></nav>
            <h1>🏷️ Tag Reference</h1>
            <p class="page-description">All tags used in Beijerterm. Use this reference when adding tags to new glossaries or terms.</p>
        </div>

        <main>
            <section class="tag-conventions">
                <h2>Tag Naming Conventions</h2>
                <ul>
                    <li><strong>Lowercase</strong> for generic subjects: <code>legal</code>, <code>medical</code>, <code>automotive</code>, <code>diamonds</code></li>
                    <li><strong>Capitalize</strong> proper nouns only: <code>Microsoft</code>, <code>EU</code>, <code>BBC</code>, <code>ISO 9001</code></li>
                    <li><strong>Multi-word tags</strong>: Use spaces: <code>machine learning</code>, <code>3D printing</code></li>
                </ul>
            </section>

            <section class="tag-table-section">
                <h2>All Tags ({len(tag_index)})</h2>
                <table class="tag-reference-table">
                    <thead>
                        <tr>
                            <th>Tag</th>
                            <th>Glossaries</th>
                            <th>Terms</th>
                            <th>Entries</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </section>
        </main>
    </div>

    {site_footer}
{SCROLL_TO_TOP_HTML}
</body>
</html>'''
    
    return md_content, html_content


def generate_tags_json(tag_index: dict) -> str:
    """Generate tags.json for machine-readable tag registry."""
    tags_data = {}
    for tag, data in tag_index.items():
        tags_data[tag] = {
            "glossary_count": len(data["glossaries"]),
            "term_count": len(data["terms"]),
            "entry_count": data["term_entries"],
            "glossaries": [g["slug"] for g in data["glossaries"]],
            "terms": [t["slug"] for t in data["terms"]]
        }
    return json.dumps(tags_data, indent=2, ensure_ascii=False, sort_keys=True)


def generate_categories_content(glossaries: list[dict], terms: list[dict], categories: dict) -> str:
    """Generate the tags tab content showing all YAML tags with multi-tag discovery."""
    
    # Collect all tags from YAML frontmatter (not folder categories)
    tag_index = collect_all_tags(glossaries, terms)
    
    # Define colors for tags (cycle through a palette)
    tag_colors = [
        "#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12", 
        "#1abc9c", "#e67e22", "#34495e", "#16a085", "#c0392b",
        "#2980b9", "#27ae60", "#8e44ad", "#d35400", "#7f8c8d"
    ]
    
    # Build tag cards
    cards_html = ""
    for i, (tag_name, items) in enumerate(sorted(tag_index.items(), key=lambda x: x[0].lower())):
        tag_color = tag_colors[i % len(tag_colors)]
        
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
            <div class="category-card-header" style="background-color: {tag_color}">
                <h3>{tag_name}</h3>
                <span class="tag-stats-summary">{stats_summary}</span>
            </div>
            <div class="category-card-body">
                {glossary_links}
                {term_links}
            </div>
        </div>'''
    
    # Add link to full tag reference
    header_html = f'''
    <div class="tags-tab-header">
        <p>Browse content by tag. Each glossary/term can have multiple tags and will appear under all of them.</p>
        <a href="tags.html" class="tag-reference-link">🏷️ View Tag Reference ({len(tag_index)} tags)</a>
    </div>
    '''
    
    return f'''{header_html}<div class="categories-grid">{cards_html}</div>'''


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
                            <th>Tags</th>
                            <th>Languages</th>
                            <th>Terms</th>
                        </tr>
                    </thead>
                    <tbody>'''
            
            for item in by_letter[letter]:
                link = f"glossary/{item['slug']}.html"
                # Generate tag badges for all tags
                tags = item.get('tags', [])
                tags_data_attr = ','.join(t.lower() for t in tags) if tags else ''
                if tags:
                    tag_badges = ' '.join(f'<span class="tag-badge clickable-tag" data-tag="{t.lower()}">{t}</span>' for t in tags[:3])  # Show first 3
                    if len(tags) > 3:
                        tag_badges += f' <span class="tag-more">+{len(tags) - 3}</span>'
                else:
                    tag_badges = '<span class="tag-badge">—</span>'
                sections += f'''
                        <tr data-tags="{tags_data_attr}">
                            <td><a href="{link}">{item['title']}</a></td>
                            <td class="tags-cell">{tag_badges}</td>
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
                            <th>Tags</th>
                            <th>Languages</th>
                        </tr>
                    </thead>
                    <tbody>'''
            
            for item in by_letter[letter]:
                link = f"term/{item['slug']}.html"
                # Generate tag badges for all tags
                tags = item.get('tags', [])
                tags_data_attr = ','.join(t.lower() for t in tags) if tags else ''
                if tags:
                    tag_badges = ' '.join(f'<span class="tag-badge clickable-tag" data-tag="{t.lower()}">{t}</span>' for t in tags[:3])
                    if len(tags) > 3:
                        tag_badges += f' <span class="tag-more">+{len(tags) - 3}</span>'
                else:
                    tag_badges = '<span class="tag-badge">—</span>'
                sections += f'''
                        <tr data-tags="{tags_data_attr}">
                            <td><a href="{link}">{item['title']}</a></td>
                            <td class="tags-cell">{tag_badges}</td>
                            <td>{item.get('source_lang', 'nl')} &rarr; {item.get('target_lang', 'en')}</td>
                        </tr>'''

            sections += '''
                    </tbody>
                </table>
            </section>'''

    return alphabet_nav, sections


def generate_html_index(glossaries: list[dict], terms: list[dict], categories: dict, tag_index: dict) -> str:
    """Generate the main index.html page with tabs."""
    
    site_header = generate_site_header("home")
    site_footer = generate_site_footer()
    total_glossaries = len(glossaries)
    total_terms_pages = len(terms)
    total_term_entries = sum(g.get('term_count', 0) for g in glossaries)
    total_tags = len(tag_index)

    glossary_nav, glossary_sections = generate_table_for_items(glossaries, categories, "glossary")
    terms_nav, terms_sections = generate_table_for_items(terms, categories, "term")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beijerterm - Open-Source Multilingual Terminology Database</title>
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
        /* Clickable tags in table */
        .clickable-tag {{
            cursor: pointer;
            transition: all 0.2s;
        }}
        .clickable-tag:hover {{
            background: #3b82f6;
            color: white;
        }}
        .tag-more {{
            color: #64748b;
            font-size: 0.75rem;
            font-style: italic;
        }}
        .tags-cell {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            align-items: center;
        }}
        /* Tag filter bar */
        .tag-filter-bar {{
            background: #f1f5f9;
            padding: 10px 16px;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: none;
            align-items: center;
            gap: 12px;
        }}
        .tag-filter-bar.active {{
            display: flex;
        }}
        .tag-filter-label {{
            font-size: 0.9rem;
            color: #475569;
        }}
        .tag-filter-value {{
            background: #3b82f6;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .tag-filter-count {{
            color: #64748b;
            font-size: 0.85rem;
        }}
        .tag-filter-clear {{
            background: #e2e8f0;
            border: none;
            padding: 4px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            color: #475569;
            margin-left: auto;
        }}
        .tag-filter-clear:hover {{
            background: #cbd5e1;
        }}
        @media (prefers-color-scheme: dark) {{
            .clickable-tag:hover {{
                background: #3b82f6;
            }}
            .tag-more {{
                color: #94a3b8;
            }}
            .tag-filter-bar {{
                background: #1f2937;
            }}
            .tag-filter-label {{
                color: #9ca3af;
            }}
            .tag-filter-count {{
                color: #9ca3af;
            }}
            .tag-filter-clear {{
                background: #374151;
                color: #e5e7eb;
            }}
            .tag-filter-clear:hover {{
                background: #4b5563;
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
                        <a href="tags.html" class="stat-link">
                            <span class="stat-value">{total_tags}</span>
                            <span class="stat-label">🏷️ Tags</span>
                        </a>
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
                    </div>

                    <div id="tab-glossaries" class="tab-content active">
                        <p class="tab-description">Terminology lists and glossaries with multiple term entries each. Click any tag to filter.</p>
                        <div id="tag-filter-bar" class="tag-filter-bar">
                            <span class="tag-filter-label">Filtering by:</span>
                            <span id="tag-filter-value" class="tag-filter-value"></span>
                            <span id="tag-filter-count" class="tag-filter-count"></span>
                            <button class="tag-filter-clear" onclick="clearTagFilter()">Clear filter</button>
                        </div>
                        <nav class="alphabet-nav">
                            {glossary_nav}
                        </nav>
                        {glossary_sections}
                    </div>

                    <div id="tab-terms" class="tab-content">
                        <p class="tab-description">Individual term pages with definitions, examples, and reference links. Click any tag to filter.</p>
                        <div id="term-tag-filter-bar" class="tag-filter-bar">
                            <span class="tag-filter-label">Filtering by:</span>
                            <span id="term-tag-filter-value" class="tag-filter-value"></span>
                            <span id="term-tag-filter-count" class="tag-filter-count"></span>
                            <button class="tag-filter-clear" onclick="clearTermTagFilter()">Clear filter</button>
                        </div>
                        <nav class="alphabet-nav">
                            {terms_nav}
                        </nav>
                        {terms_sections}
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

            // Support URL search parameter: ?q=searchterm
            const urlParams = new URLSearchParams(window.location.search);
            const searchQuery = urlParams.get('q');
            if (searchQuery) {{
                // Wait for Pagefind UI to initialize, then trigger search
                setTimeout(() => {{
                    const searchInput = document.querySelector('.pagefind-ui__search-input');
                    if (searchInput) {{
                        searchInput.value = searchQuery;
                        searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        // Scroll to search results
                        document.getElementById('search').scrollIntoView({{ behavior: 'smooth' }});
                    }}
                }}, 100);
            }}

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

        // Tag filtering functionality
        let activeTagFilter = null;
        let activeTermTagFilter = null;
        
        document.addEventListener('click', function(e) {{
            if (e.target.classList.contains('clickable-tag')) {{
                const tag = e.target.dataset.tag;
                // Determine which tab we're in
                const glossaryTab = e.target.closest('#tab-glossaries');
                const termsTab = e.target.closest('#tab-terms');
                
                if (glossaryTab) {{
                    filterByTag(tag);
                }} else if (termsTab) {{
                    filterTermsByTag(tag);
                }}
            }}
        }});
        
        function filterByTag(tag) {{
            activeTagFilter = tag;
            const filterBar = document.getElementById('tag-filter-bar');
            const filterValue = document.getElementById('tag-filter-value');
            const filterCount = document.getElementById('tag-filter-count');
            
            // Show filter bar
            filterBar.classList.add('active');
            filterValue.textContent = tag;
            
            // Filter rows
            const rows = document.querySelectorAll('#tab-glossaries tr[data-tags]');
            let visibleCount = 0;
            
            rows.forEach(row => {{
                const tags = row.dataset.tags.split(',');
                if (tags.includes(tag)) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});
            
            // Hide empty letter sections
            document.querySelectorAll('#tab-glossaries .letter-section').forEach(section => {{
                const visibleRows = section.querySelectorAll('tr[data-tags]:not([style*=\"display: none\"])');
                section.style.display = visibleRows.length > 0 ? '' : 'none';
            }});
            
            // Update alphabet nav
            updateAlphabetNav('glossary');
            
            filterCount.textContent = `(${{visibleCount}} glossar${{visibleCount === 1 ? 'y' : 'ies'}})`;
        }}
        
        function clearTagFilter() {{
            activeTagFilter = null;
            const filterBar = document.getElementById('tag-filter-bar');
            filterBar.classList.remove('active');
            
            // Show all rows
            document.querySelectorAll('#tab-glossaries tr[data-tags]').forEach(row => {{
                row.style.display = '';
            }});
            
            // Show all letter sections
            document.querySelectorAll('#tab-glossaries .letter-section').forEach(section => {{
                section.style.display = '';
            }});
            
            // Update alphabet nav
            updateAlphabetNav('glossary');
        }}
        
        // Terms tab filtering
        function filterTermsByTag(tag) {{
            activeTermTagFilter = tag;
            const filterBar = document.getElementById('term-tag-filter-bar');
            const filterValue = document.getElementById('term-tag-filter-value');
            const filterCount = document.getElementById('term-tag-filter-count');
            
            // Show filter bar
            filterBar.classList.add('active');
            filterValue.textContent = tag;
            
            // Filter rows
            const rows = document.querySelectorAll('#tab-terms tr[data-tags]');
            let visibleCount = 0;
            
            rows.forEach(row => {{
                const tags = row.dataset.tags.split(',');
                if (tags.includes(tag)) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});
            
            // Hide empty letter sections
            document.querySelectorAll('#tab-terms .letter-section').forEach(section => {{
                const visibleRows = section.querySelectorAll('tr[data-tags]:not([style*=\"display: none\"])');
                section.style.display = visibleRows.length > 0 ? '' : 'none';
            }});
            
            // Update alphabet nav
            updateAlphabetNav('term');
            
            filterCount.textContent = `(${{visibleCount}} term${{visibleCount === 1 ? '' : 's'}})`;
        }}
        
        function clearTermTagFilter() {{
            activeTermTagFilter = null;
            const filterBar = document.getElementById('term-tag-filter-bar');
            filterBar.classList.remove('active');
            
            // Show all rows
            document.querySelectorAll('#tab-terms tr[data-tags]').forEach(row => {{
                row.style.display = '';
            }});
            
            // Show all letter sections
            document.querySelectorAll('#tab-terms .letter-section').forEach(section => {{
                section.style.display = '';
            }});
            
            // Update alphabet nav
            updateAlphabetNav('term');
        }}
        
        function updateAlphabetNav(itemType) {{
            const tabId = itemType === 'glossary' ? '#tab-glossaries' : '#tab-terms';
            document.querySelectorAll(tabId + ' .alphabet-nav a').forEach(link => {{
                const letter = link.getAttribute('href').replace('#letter-' + itemType + '-', '');
                const section = document.getElementById('letter-' + itemType + '-' + letter);
                if (section && section.style.display === 'none') {{
                    link.classList.add('disabled');
                    link.style.opacity = '0.3';
                    link.style.pointerEvents = 'none';
                }} else {{
                    link.classList.remove('disabled');
                    link.style.opacity = '';
                    link.style.pointerEvents = '';
                }}
            }});
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
                    <dt>Title</dt>
                    <dd>{glossary.get('title', 'Unknown')}</dd>
                    <dt>Description</dt>
                    <dd>{glossary.get('description', 'No description available')}</dd>
                    <dt>Languages</dt>
                    <dd>{glossary.get('source_lang', '?')} → {glossary.get('target_lang', '?')}</dd>
                    <dt>Tags</dt>
                    <dd>{', '.join(tags) if tags else '—'}</dd>
                    <dt>Terms</dt>
                    <dd>{glossary.get('term_count', 0):,}</dd>
                    <dt>Source</dt>
                    <dd><a href="{glossary.get('source_url', '#')}" target="_blank">{glossary.get('source_url', 'Unknown')}</a></dd>
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
                    <dt>Title</dt>
                    <dd>{term.get('title', 'Unknown')}</dd>
                    <dt>Description</dt>
                    <dd>{term.get('description', 'No description available')}</dd>
                    <dt>Languages</dt>
                    <dd>{term.get('source_lang', 'nl')} → {term.get('target_lang', 'en')}</dd>
                    <dt>Tags</dt>
                    <dd>{', '.join(tags) if tags else '—'}</dd>
                    <dt>Source</dt>
                    <dd><a href="{term.get('source_url', '#')}" target="_blank">{term.get('source_url', 'Unknown')}</a></dd>
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

    print("Generating tag registry...")
    tag_index = collect_all_tags(glossaries, terms)
    tags_md, tags_html = generate_tags_reference(tag_index)
    tags_json = generate_tags_json(tag_index)
    
    # Write TAGS.md to repo root (for humans browsing GitHub)
    with open(Path("TAGS.md"), "w", encoding="utf-8") as f:
        f.write(tags_md)
    
    # Write tags.json to _site (machine-readable)
    with open(OUTPUT_DIR / "tags.json", "w", encoding="utf-8") as f:
        f.write(tags_json)
    
    # Write tags.html to _site (web page)
    with open(OUTPUT_DIR / "tags.html", "w", encoding="utf-8") as f:
        f.write(tags_html)
    
    print(f"   Found {len(tag_index)} unique tags")

    print("Generating search index...")
    search_index = generate_search_index(glossaries, terms)
    with open(OUTPUT_DIR / "search-index.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    print(f"   Indexed {len(search_index)} entries")

    print("Generating HTML pages...")
    index_html = generate_html_index(glossaries, terms, categories, tag_index)
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
    print(f"   - Unique tags: {len(tag_index)}")
    print(f"   - Generated: TAGS.md, tags.json, tags.html")


if __name__ == "__main__":
    build_site()
