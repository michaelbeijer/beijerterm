#!/usr/bin/env python3
"""
Build script for Superlookup.

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
SITE_DIR = Path("site")
OUTPUT_DIR = Path("_site")
GITHUB_BASE_URL = "https://github.com/michaelbeijer/superlookup/blob/main/glossaries"

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

    for md_file in GLOSSARIES_DIR.rglob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, body = parse_frontmatter(content)
        if not frontmatter:
            continue

        # Build GitHub source URL
        relative_path = md_file.relative_to(GLOSSARIES_DIR)
        github_url = f"{GITHUB_BASE_URL}/{relative_path}".replace("\\", "/")

        item = {
            "file": str(md_file),
            "category": md_file.parent.name,
            "body": body,
            "source_url": github_url,
            **frontmatter,
        }

        # Determine type: ONLY files in the "terms" folder are terms
        if md_file.parent.name == "terms":
            item["type"] = "term"
            item["html_content"] = markdown_to_html(body)
            terms.append(item)
        else:
            item["type"] = "glossary"
            item["terms"] = parse_markdown_table(body)
            item["term_count"] = len(item["terms"])
            glossaries.append(item)

    return glossaries, terms


def load_sidebar_content() -> str:
    """Load and convert sidebar markdown to HTML."""
    sidebar_file = SITE_DIR / "sidebar.md"
    if not sidebar_file.exists():
        return ""
    with open(sidebar_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    return html


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
    
    sidebar_html = load_sidebar_content()
    total_glossaries = len(glossaries)
    total_terms_pages = len(terms)
    total_term_entries = sum(g.get('term_count', 0) for g in glossaries)

    glossary_nav, glossary_sections = generate_table_for_items(glossaries, categories, "glossary")
    terms_nav, terms_sections = generate_table_for_items(terms, categories, "term")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Superlookup - Open Source Multilingual Terminology</title>
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
    </style>
</head>
<body>
    <div class="page-layout">
        <aside class="sidebar">
            {sidebar_html}
        </aside>

        <div class="main-content">
            <header>
                <h1><img src="sv-icon.svg" alt="Sv" class="site-logo"> Superlookup</h1>
                <p>Open source multilingual terminology database</p>
            </header>

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
                </section>
            </main>

            <footer>
                <p>Data is open source and available on <a href="https://github.com/michaelbeijer/superlookup">GitHub</a></p>
                <p>Built with love by <a href="https://michaelbeijer.co.uk">Michael Beijer</a></p>
            </footer>
        </div>
    </div>

    <script src="pagefind/pagefind-ui.js"></script>
    <script>
        window.addEventListener('DOMContentLoaded', (event) => {{
            const pf = new PagefindUI({{
                element: "#search",
                showSubResults: true,
                showImages: false
            }});
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

    sidebar_html = load_sidebar_content()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{glossary['title']} - Superlookup</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="icon" href="../favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="../pagefind/pagefind-ui.css">
</head>
<body>
    <div class="page-layout">
        <aside class="sidebar">
            {sidebar_html}
        </aside>

        <div class="main-content">
            <header>
                <nav><a href="../index.html">&larr; Back to all glossaries</a></nav>
                <h1>{glossary['title']}</h1>
                <p>{glossary.get('description', '')}</p>
            </header>

            <main>
                <section class="glossary-meta">
                    <span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', '')}</span>
                    <span class="lang-badge">{glossary.get('source_lang', '')} &rarr; {glossary.get('target_lang', '')}</span>
                    <span class="term-count">{glossary.get('term_count', 0):,} terms</span>
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
    </div>

    <script src="../pagefind/pagefind-ui.js"></script>
{SCROLL_TO_TOP_HTML}
</body>
</html>'''


def generate_term_page(term: dict, categories: dict) -> str:
    """Generate an individual term page."""
    cat_info = categories.get(term.get("category", "terms"), {"name": "Terms", "color": "#34495e"})
    sidebar_html = load_sidebar_content()
    html_content = term.get("html_content", "")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{term['title']} - Superlookup</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="icon" href="../favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="../pagefind/pagefind-ui.css">
</head>
<body>
    <div class="page-layout">
        <aside class="sidebar">
            {sidebar_html}
        </aside>

        <div class="main-content">
            <header>
                <nav><a href="../index.html">&larr; Back to all content</a></nav>
                <h1>{term['title']}</h1>
                <p>{term.get('description', '')}</p>
            </header>

            <main>
                <section class="term-meta">
                    <span class="type-badge term">Term</span>
                    <span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', 'Terms')}</span>
                    <span class="lang-badge">{term.get('source_lang', 'nl')} &rarr; {term.get('target_lang', 'en')}</span>
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
    </div>

    <script src="../pagefind/pagefind-ui.js"></script>
{SCROLL_TO_TOP_HTML}
</body>
</html>'''


def build_site():
    """Main build function."""
    print("Building Superlookup site...")

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
    if (SITE_DIR / "sv-icon.svg").exists():
        shutil.copy(SITE_DIR / "sv-icon.svg", OUTPUT_DIR / "sv-icon.svg")
    if (SITE_DIR / "favicon.ico").exists():
        shutil.copy(SITE_DIR / "favicon.ico", OUTPUT_DIR / "favicon.ico")

    print(f"Site built successfully in {OUTPUT_DIR}/")
    print(f"\nSummary:")
    print(f"   - Glossaries: {len(glossaries)}")
    print(f"   - Term pages: {len(terms)}")
    print(f"   - Total term entries: {sum(g.get('term_count', 0) for g in glossaries):,}")


if __name__ == "__main__":
    build_site()
