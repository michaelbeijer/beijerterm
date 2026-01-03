#!/usr/bin/env python3
"""
Build script for Superlookup.

Reads all Markdown glossary and term files, generates HTML pages, 
and creates a JSON index for search functionality.

Updated to handle:
- Glossaries: Table format with extracted terms
- Terms: Rich content (definitions, examples, links)
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
    # Use Python markdown library
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

        item = {
            "file": str(md_file),
            "category": md_file.parent.name,
            "body": body,
            **frontmatter,
        }

        # Check if it's a Term (dictionary entry) or Glossary (table)
        if frontmatter.get("type") == "term" or md_file.parent.name == "terms":
            # Term page - rich content
            item["type"] = "term"
            item["html_content"] = markdown_to_html(body)
            terms.append(item)
        else:
            # Glossary page - table format
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
        content = f.read()

    html = content
    html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'((?:<li>.+</li>\n?)+)', r'<ul>\1</ul>', html)

    lines = html.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('<') and not line.startswith('#'):
            line = f'<p>{line}</p>'
        result.append(line)
    html = '\n'.join(result)

    return html


def generate_search_index(glossaries: list[dict], terms: list[dict]) -> list[dict]:
    """Generate search index for all content."""
    index = []

    # Index glossary terms
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

    # Index term pages
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


def generate_html_index(glossaries: list[dict], terms: list[dict], categories: dict) -> str:
    """Generate the main index.html page."""
    # Combine all items for alphabetical listing
    all_items = []
    for g in glossaries:
        all_items.append({**g, "item_type": "glossary"})
    for t in terms:
        all_items.append({**t, "item_type": "term", "term_count": 0})

    sorted_items = sorted(all_items, key=lambda x: x["title"].upper())

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
            alphabet_nav += f'<a href="#letter-{letter}" class="alphabet-link">{letter}</a>'
        else:
            alphabet_nav += f'<span class="alphabet-link disabled">{letter}</span>'

    glossary_sections = ""
    for letter in all_letters:
        if letter not in by_letter:
            continue

        glossary_sections += f'''
        <section class="letter-section" id="letter-{letter}">
            <h3 class="letter-heading">{letter}</h3>
            <table class="glossary-table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Category</th>
                        <th>Languages</th>
                        <th>Terms</th>
                    </tr>
                </thead>
                <tbody>'''

        for item in by_letter[letter]:
            cat_info = categories.get(item["category"], {"name": item["category"], "color": "#666"})
            item_type = item.get("item_type", "glossary")
            
            if item_type == "term":
                link = f"term/{item['slug']}.html"
                type_badge = '<span class="type-badge term">Term</span>'
            else:
                link = f"glossary/{item['slug']}.html"
                type_badge = '<span class="type-badge glossary">Glossary</span>'

            glossary_sections += f'''
                    <tr data-category="{item['category']}" data-source="{item.get('source_lang', '')}" data-target="{item.get('target_lang', '')}">
                        <td><a href="{link}">{item['title']}</a></td>
                        <td>{type_badge}</td>
                        <td><span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', item['category'])}</span></td>
                        <td>{item.get('source_lang', '')}  {item.get('target_lang', '')}</td>
                        <td>{item.get('term_count', '-'):,}</td>
                    </tr>'''

        glossary_sections += '''
                </tbody>
            </table>
        </section>'''

    sidebar_html = load_sidebar_content()
    total_glossaries = len(glossaries)
    total_terms_pages = len(terms)
    total_term_entries = sum(g.get('term_count', 0) for g in glossaries)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Superlookup - Open Source Multilingual Terminology</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="icon" href="favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="pagefind/pagefind-ui.css">
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

                <section class="glossary-list">
                    <h2>All Content</h2>

                    <nav class="alphabet-nav">
                        {alphabet_nav}
                    </nav>

                    {glossary_sections}
                </section>
            </main>

            <footer>
                <p>Data is open source and available on <a href="https://github.com/michaelbeijer/superlookup">GitHub</a></p>
                <p>Built with  by <a href="https://michaelbeijer.co.uk">Michael Beijer</a></p>
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
    </script>
</body>
</html>"""


def generate_glossary_page(glossary: dict, categories: dict) -> str:
    """Generate an individual glossary page (table format)."""
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

    return f"""<!DOCTYPE html>
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
                <nav><a href="../index.html"> Back to all glossaries</a></nav>
                <h1>{glossary['title']}</h1>
                <p>{glossary.get('description', '')}</p>
            </header>

            <main>
                <section class="glossary-meta">
                    <span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', '')}</span>
                    <span class="lang-badge">{glossary.get('source_lang', '')}  {glossary.get('target_lang', '')}</span>
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
</body>
</html>"""


def generate_term_page(term: dict, categories: dict) -> str:
    """Generate an individual term page (rich content)."""
    cat_info = categories.get(term.get("category", "terms"), {"name": "Terms", "color": "#34495e"})
    sidebar_html = load_sidebar_content()
    
    # The body is already converted to HTML
    html_content = term.get("html_content", "")

    return f"""<!DOCTYPE html>
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
                <nav><a href="../index.html"> Back to all content</a></nav>
                <h1>{term['title']}</h1>
                <p>{term.get('description', '')}</p>
            </header>

            <main>
                <section class="term-meta">
                    <span class="type-badge term">Term</span>
                    <span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('name', 'Terms')}</span>
                    <span class="lang-badge">{term.get('source_lang', 'nl')}  {term.get('target_lang', 'en')}</span>
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
</body>
</html>"""


def build_site():
    """Main build function."""
    print(" Building Superlookup site...")

    # Clean output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "glossary").mkdir()
    (OUTPUT_DIR / "term").mkdir()

    # Load data
    print(" Loading content...")
    categories = load_categories()
    glossaries, terms = load_all_content()
    print(f"   Found {len(glossaries)} glossaries and {len(terms)} terms in {len(categories)} categories")

    # Generate search index
    print(" Generating search index...")
    search_index = generate_search_index(glossaries, terms)
    with open(OUTPUT_DIR / "search-index.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    print(f"   Indexed {len(search_index)} entries")

    # Generate index page
    print(" Generating HTML pages...")
    index_html = generate_html_index(glossaries, terms, categories)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    # Generate individual glossary pages
    for glossary in glossaries:
        page_html = generate_glossary_page(glossary, categories)
        output_path = OUTPUT_DIR / "glossary" / f"{glossary['slug']}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_html)

    # Generate individual term pages
    for term in terms:
        page_html = generate_term_page(term, categories)
        output_path = OUTPUT_DIR / "term" / f"{term['slug']}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_html)

    # Copy static assets
    print(" Copying static assets...")
    if (SITE_DIR / "styles.css").exists():
        shutil.copy(SITE_DIR / "styles.css", OUTPUT_DIR / "styles.css")
    if (SITE_DIR / "sv-icon.svg").exists():
        shutil.copy(SITE_DIR / "sv-icon.svg", OUTPUT_DIR / "sv-icon.svg")
    if (SITE_DIR / "favicon.ico").exists():
        shutil.copy(SITE_DIR / "favicon.ico", OUTPUT_DIR / "favicon.ico")

    print(f" Site built successfully in {OUTPUT_DIR}/")
    print(f"\n Summary:")
    print(f"   - Glossaries: {len(glossaries)}")
    print(f"   - Term pages: {len(terms)}")
    print(f"   - Total term entries: {sum(g.get('term_count', 0) for g in glossaries):,}")
    print(f"\n Next steps:")
    print(f"   1. Run: npx pagefind --site {OUTPUT_DIR}")
    print(f"   2. Run: npx serve {OUTPUT_DIR}")
    print(f"   3. Open: http://localhost:3000")


if __name__ == "__main__":
    build_site()
