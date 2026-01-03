#!/usr/bin/env python3
"""
Build script for Superlookup.

Reads all Markdown glossary files, generates HTML pages, and creates
a JSON index for search functionality.
"""

import os
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
import shutil

# Configuration
GLOSSARIES_DIR = Path("glossaries")
SITE_DIR = Path("site")
OUTPUT_DIR = Path("_site")
TEMPLATES_DIR = Path("templates")


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from Markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return frontmatter, body
    return {}, content


def parse_markdown_table(body: str) -> list[dict]:
    """Extract terms from Markdown table."""
    terms = []
    lines = body.split("\n")
    
    # Find table header
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "|" in line[1:]:
            header_idx = i
            break
    
    if header_idx is None:
        return terms
    
    # Parse header
    header_line = lines[header_idx]
    headers = [h.strip() for h in header_line.split("|")[1:-1]]
    
    # Skip separator line (|---|---|)
    # Parse data rows
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


def load_categories() -> dict:
    """Load all category metadata."""
    categories = {}
    for cat_file in GLOSSARIES_DIR.rglob("_category.yaml"):
        with open(cat_file, "r", encoding="utf-8") as f:
            cat_data = yaml.safe_load(f)
            categories[cat_data["slug"]] = cat_data
    return categories


def load_glossaries() -> list[dict]:
    """Load all glossary files."""
    glossaries = []
    
    for md_file in GLOSSARIES_DIR.rglob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        frontmatter, body = parse_frontmatter(content)
        if not frontmatter:
            continue
        
        terms = parse_markdown_table(body)
        
        glossary = {
            "file": str(md_file),
            "category": md_file.parent.name,
            **frontmatter,
            "terms": terms,
            "term_count": len(terms),
        }
        glossaries.append(glossary)
    
    return glossaries


def generate_search_index(glossaries: list[dict]) -> list[dict]:
    """Generate search index entries for all terms."""
    index = []
    
    for glossary in glossaries:
        for term in glossary.get("terms", []):
            entry = {
                "glossary": glossary["title"],
                "glossary_slug": glossary["slug"],
                "category": glossary["category"],
                "source_lang": glossary.get("source_lang", ""),
                "target_lang": glossary.get("target_lang", ""),
                **term,
            }
            index.append(entry)
    
    return index


def generate_html_index(glossaries: list[dict], categories: dict) -> str:
    """Generate the main index.html page."""
    # Sort glossaries alphabetically by title
    sorted_glossaries = sorted(glossaries, key=lambda x: x["title"].upper())
    
    # Group glossaries by first letter
    by_letter = {}
    for g in sorted_glossaries:
        first_letter = g["title"][0].upper()
        if not first_letter.isalpha():
            first_letter = "#"  # Numbers and symbols
        if first_letter not in by_letter:
            by_letter[first_letter] = []
        by_letter[first_letter].append(g)
    
    # Generate A-Z navigation
    all_letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    alphabet_nav = ""
    for letter in all_letters:
        if letter in by_letter:
            alphabet_nav += f'<a href="#letter-{letter}" class="alphabet-link">{letter}</a>'
        else:
            alphabet_nav += f'<span class="alphabet-link disabled">{letter}</span>'
    
    # Generate glossary sections by letter
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
                        <th>Glossary</th>
                        <th>Category</th>
                        <th>Languages</th>
                        <th>Terms</th>
                    </tr>
                </thead>
                <tbody>'''
        
        for g in by_letter[letter]:
            cat_info = categories.get(g["category"], {"name": g["category"], "icon": "📁", "color": "#666"})
            glossary_sections += f'''
                    <tr data-category="{g['category']}" data-source="{g.get('source_lang', '')}" data-target="{g.get('target_lang', '')}">
                        <td><a href="glossary/{g['slug']}.html">{g['title']}</a></td>
                        <td><span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('icon', '📁')} {cat_info.get('name', g['category'])}</span></td>
                        <td>{g.get('source_lang', '')} → {g.get('target_lang', '')}</td>
                        <td>{g.get('term_count', 0):,}</td>
                    </tr>'''
        
        glossary_sections += '''
                </tbody>
            </table>
        </section>'''
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Superlookup - Open Source Multilingual Terminology</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="pagefind/pagefind-ui.css">
</head>
<body>
    <header>
        <h1>📚 Superlookup</h1>
        <p>Open source multilingual terminology database</p>
    </header>
    
    <main>
        <section class="search-section">
            <div id="search"></div>
        </section>
        
        <section class="stats">
            <div class="stat">
                <span class="stat-value">{len(glossaries)}</span>
                <span class="stat-label">Glossaries</span>
            </div>
            <div class="stat">
                <span class="stat-value">{sum(g.get('term_count', 0) for g in glossaries):,}</span>
                <span class="stat-label">Terms</span>
            </div>
            <div class="stat">
                <span class="stat-value">{len(categories)}</span>
                <span class="stat-label">Categories</span>
            </div>
        </section>
        
        <section class="glossary-list">
            <h2>All Glossaries</h2>
            
            <nav class="alphabet-nav">
                {alphabet_nav}
            </nav>
            
            {glossary_sections}
        </section>
    </main>
    
    <footer>
        <p>Data is open source and available on <a href="https://github.com/michaelbeijer/superlookup">GitHub</a></p>
        <p>Built with ❤️ by <a href="https://michaelbeijer.co.uk">Michael Beijer</a></p>
    </footer>
    
    <script src="pagefind/pagefind-ui.js"></script>
    <script>
        window.addEventListener('DOMContentLoaded', (event) => {{
            const pf = new PagefindUI({{
                element: "#search",
                showSubResults: true,
                showImages: false
            }});
            
            // Track search query and store before navigation
            const searchContainer = document.querySelector('#search');
            let currentQuery = '';
            
            // Track the search query as user types
            searchContainer.addEventListener('input', (e) => {{
                if (e.target.classList.contains('pagefind-ui__search-input')) {{
                    currentQuery = e.target.value;
                }}
            }});
            
            // Store query in sessionStorage when clicking any link in search results
            searchContainer.addEventListener('click', (e) => {{
                const link = e.target.closest('a');
                if (link && link.href && currentQuery) {{
                    sessionStorage.setItem('Superlookup_highlight', currentQuery);
                }}
            }});
            
            // Also use MutationObserver to capture query from input after results load
            const observer = new MutationObserver(() => {{
                const searchInput = document.querySelector('.pagefind-ui__search-input');
                if (searchInput && searchInput.value) {{
                    currentQuery = searchInput.value;
                }}
            }});
            
            observer.observe(searchContainer, {{
                childList: true,
                subtree: true
            }});
        }});
    </script>
</body>
</html>"""


def generate_glossary_page(glossary: dict, categories: dict) -> str:
    """Generate an individual glossary page."""
    cat_info = categories.get(glossary["category"], {"name": glossary["category"], "icon": "📁"})
    
    # Determine table headers from first term
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
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{glossary['title']} - Superlookup</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="stylesheet" href="../pagefind/pagefind-ui.css">
</head>
<body>
    <header>
        <nav><a href="../index.html">← Back to all glossaries</a></nav>
        <h1>{glossary['title']}</h1>
        <p>{glossary.get('description', '')}</p>
    </header>
    
    <main>
        <section class="search-section">
            <div id="search"></div>
        </section>
        
        <section class="glossary-meta">
            <span class="category-badge" style="background-color: {cat_info.get('color', '#666')}">{cat_info.get('icon', '📁')} {cat_info.get('name', '')}</span>
            <span class="lang-badge">{glossary.get('source_lang', '')} → {glossary.get('target_lang', '')}</span>
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
                <dt>Author</dt>
                <dd>{glossary.get('author', 'Unknown')}</dd>
                <dt>License</dt>
                <dd>{glossary.get('license', 'Unknown')}</dd>
                <dt>Last Updated</dt>
                <dd>{glossary.get('last_updated', 'Unknown')}</dd>
            </dl>
        </section>
    </main>
    
    <footer>
        <p><a href="https://github.com/michaelbeijer/superlookup/blob/main/{glossary['file']}">Edit this glossary on GitHub</a></p>
    </footer>
    
    <script src="../pagefind/pagefind-ui.js"></script>
    <script>
        window.addEventListener('DOMContentLoaded', (event) => {{
            // Initialize Pagefind search
            new PagefindUI({{
                element: "#search",
                showSubResults: true,
                showImages: false,
            }});
            
            // Highlight search terms from URL parameter OR sessionStorage
            highlightSearchTerms();
        }});
        
        function highlightSearchTerms() {{
            // Get search query from URL first, then fall back to sessionStorage
            const params = new URLSearchParams(window.location.search);
            let query = params.get('q') || params.get('search') || params.get('highlight');
            
            // Fall back to sessionStorage (set by index page when clicking search results)
            if (!query) {{
                query = sessionStorage.getItem('Superlookup_highlight');
                // Clear it so it doesn't persist forever
                if (query) {{
                    sessionStorage.removeItem('Superlookup_highlight');
                }}
            }}
            
            if (!query) return;
            
            // Split query into words
            const terms = query.toLowerCase().split(/\\s+/).filter(t => t.length > 1);
            if (terms.length === 0) return;
            
            // Show highlight banner
            const banner = document.createElement('div');
            banner.className = 'highlight-banner';
            banner.innerHTML = `<span>🔍 Highlighting: <strong>${{escapeHtml(query)}}</strong></span><button onclick="clearHighlights()">✕ Clear</button>`;
            document.querySelector('main').prepend(banner);
            
            // Highlight in table cells
            const cells = document.querySelectorAll('.terms-table td');
            cells.forEach(cell => {{
                let html = cell.innerHTML;
                terms.forEach(term => {{
                    const regex = new RegExp(`(>${{term}}|${{term}})(?![^<]*>)`, 'gi');
                    html = html.replace(regex, (match) => {{
                        if (match.startsWith('>')) return match; // Skip if inside tag
                        return `<mark class="search-highlight">${{match}}</mark>`;
                    }});
                }});
                cell.innerHTML = html;
            }});
            
            // Scroll to first highlight
            const firstHighlight = document.querySelector('.search-highlight');
            if (firstHighlight) {{
                firstHighlight.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
        }}
        
        function clearHighlights() {{
            // Remove highlight marks
            document.querySelectorAll('.search-highlight').forEach(mark => {{
                const text = document.createTextNode(mark.textContent);
                mark.parentNode.replaceChild(text, mark);
            }});
            // Remove banner
            document.querySelector('.highlight-banner')?.remove();
            // Remove query param from URL
            const url = new URL(window.location);
            url.searchParams.delete('q');
            url.searchParams.delete('search');
            url.searchParams.delete('highlight');
            window.history.replaceState({{}}, '', url);
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
    </script>
</body>
</html>"""


def build_site():
    """Main build function."""
    print("🏗️  Building Superlookup site...")
    
    # Clean output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "glossary").mkdir()
    
    # Load data
    print("📖 Loading glossaries...")
    categories = load_categories()
    glossaries = load_glossaries()
    print(f"   Found {len(glossaries)} glossaries in {len(categories)} categories")
    
    # Generate search index
    print("🔍 Generating search index...")
    search_index = generate_search_index(glossaries)
    with open(OUTPUT_DIR / "search-index.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    print(f"   Indexed {len(search_index)} terms")
    
    # Generate index page
    print("📄 Generating HTML pages...")
    index_html = generate_html_index(glossaries, categories)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # Generate individual glossary pages
    for glossary in glossaries:
        page_html = generate_glossary_page(glossary, categories)
        output_path = OUTPUT_DIR / "glossary" / f"{glossary['slug']}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_html)
    
    # Copy static assets
    print("📁 Copying static assets...")
    if (SITE_DIR / "styles.css").exists():
        shutil.copy(SITE_DIR / "styles.css", OUTPUT_DIR / "styles.css")
    
    print(f"✅ Site built successfully in {OUTPUT_DIR}/")
    print(f"\n📝 Next steps:")
    print(f"   1. Run: npx pagefind --site {OUTPUT_DIR}")
    print(f"   2. Run: npx serve {OUTPUT_DIR}")
    print(f"   3. Open: http://localhost:3000")


if __name__ == "__main__":
    build_site()
