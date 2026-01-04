# Beijerterm - AI Agent Documentation

> **This is the single source of truth for AI coding assistants working on this project.**
> **Last Updated:** January 4, 2026 | **Version:** v1.0.6

---

## 🎯 Project Overview

**Beijerterm** is an open-source multilingual terminology database and glossary website. It provides a searchable collection of Dutch-English translation glossaries, terminology lists, and individual term definitions for professional translators.

| Property | Value |
|----------|-------|
| **Name** | Beijerterm |
| **Type** | Static website (GitHub Pages) |
| **Language** | Python (build scripts), HTML/CSS/JS (frontend) |
| **Repository** | https://github.com/michaelbeijer/beijerterm |
| **Live Site** | https://michaelbeijer.github.io/beijerterm/ |
| **Build System** | Python + Pagefind (search indexing) |
| **Hosting** | GitHub Pages via GitHub Actions |
| **Related Project** | [Supervertaler](https://supervertaler.com) - Desktop translation app |

### Key Statistics

| Metric | Count |
|--------|-------|
| **Glossaries** | ~207 |
| **Term Pages** | ~141 |
| **Total Term Entries** | ~584,000 |
| **Categories** | 14 |
| **Languages** | Dutch ↔ English (primarily) |

### Key Capabilities

- **Full-text Search**: Pagefind-powered search across all glossaries and terms
- **Tabbed Interface**: Separate tabs for Glossaries (multi-term lists) vs Terms (individual entries)
- **A-Z Navigation**: Alphabetical browsing with sticky navigation bar
- **Category Filtering**: 14 domain categories (IT, Medical, Legal, Technical, etc.)
- **Responsive Design**: Mobile-friendly layout with header/footer navigation
- **Source Attribution**: Links to original sources (GitHub repository)

---

## 📁 Project Structure

```
superlookup-glossaries/
├── AGENTS.md                  # This file - AI agent documentation
├── CHANGELOG.md               # Version history
├── README.md                  # User-facing documentation
│
├── glossaries/                # Source content (Markdown files)
│   ├── _category.yaml         # Root category config (optional)
│   ├── agriculture/           # Category folders
│   │   ├── _category.yaml     # Category metadata
│   │   └── *.md               # Glossary files
│   ├── automotive/
│   ├── aviation/
│   ├── chemistry/
│   ├── construction/
│   ├── energy/
│   ├── financial/
│   ├── food/
│   ├── general/               # Largest category
│   ├── it/
│   ├── legal/
│   ├── medical/
│   ├── technical/
│   ├── textile/
│   └── terms/                 # Individual term pages (<10 entries)
│
├── scripts/                   # Build and export tools
│   ├── build_site.py          # Main static site generator (~700 lines)
│   ├── convert_to_static.py   # Wiki → Markdown converter
│   ├── full_export.py         # MediaWiki API export
│   ├── wiki_parser.py         # Wiki markup parser
│   └── reexport_failed.py     # Re-export failed pages
│
├── site/                      # Static assets (copied to _site/)
│   ├── styles.css             # Main stylesheet
│   ├── sv-icon.svg            # Site logo
│   ├── favicon.ico            # Browser icon
│   └── sidebar.md             # (deprecated - no longer used)
│
├── _site/                     # Generated output (gitignored)
│   ├── index.html             # Home page
│   ├── glossary/              # Generated glossary pages
│   ├── term/                  # Generated term pages
│   ├── pagefind/              # Search index
│   └── *.css, *.svg, etc.     # Copied assets
│
├── .github/
│   └── workflows/
│       └── deploy.yaml        # GitHub Actions build & deploy
│
└── data/                      # Raw export data (gitignored partially)
    ├── glossaries/            # Exported glossary JSON
    └── terms/                 # Exported term JSON
```

---

## 🔧 Key Technical Details

### Build Process

The site is built by `scripts/build_site.py`:

1. **Load Content**: Reads all `.md` files from `glossaries/` and `terms/` folders
2. **Parse Frontmatter**: Extracts YAML metadata (title, slug, languages, etc.)
3. **Categorize**: Files in `terms/` folder → Terms tab; files in `glossaries/` → Glossaries tab
4. **Generate HTML**: Creates index.html, glossary/*.html, term/*.html
5. **Copy Assets**: Copies styles.css, favicon, logo to `_site/`
6. **Search Index**: Pagefind indexes all pages for full-text search

### Content Format

Each glossary/term file is Markdown with YAML frontmatter:

```markdown
---
title: Tractor Glossary (English-Dutch)
slug: tractor-glossary
description: Terminology from Tractor Glossary
type: glossary
source_lang: en
target_lang: nl
domain: agriculture
term_count: 288
source_url: \"https://github.com/michaelbeijer/beijerterm/blob/main/glossaries/...\"
last_updated: 2026-01-03
tags:
  - Agriculture
  - Tractors
---

# Tractor Glossary (English-Dutch)

## Terms

| English | Dutch | Notes |
|---------|-------|-------|
| tractor | trekker | |
| wheel | wiel | |
...
```

### Category Configuration

Each category folder has a `_category.yaml`:

```yaml
slug: agriculture
name: Agriculture
description: Agricultural and farming terminology
color: "#22c55e"
```

### GitHub Actions Workflow

`.github/workflows/deploy.yaml`:

1. Checkout repository
2. Setup Python 3.11
3. Install dependencies (pyyaml, markdown)
4. Run `python scripts/build_site.py`
5. Setup Node.js and run `npx pagefind --site _site`
6. Deploy `_site/` to GitHub Pages

---

## 📜 Key Scripts

### `scripts/build_site.py` (~700 lines)

Main static site generator. Key functions:

| Function | Purpose |
|----------|---------|
| `parse_frontmatter()` | Extract YAML metadata from Markdown |
| `extract_table_terms()` | Parse Markdown tables into term lists |
| `load_categories()` | Load all `_category.yaml` files |
| `load_all_content()` | Load all glossary and term files |
| `generate_site_header()` | Generate sticky header with nav |
| `generate_site_footer()` | Generate footer with links |
| `generate_html_index()` | Generate home page with tabs |
| `generate_glossary_page()` | Generate individual glossary page |
| `generate_term_page()` | Generate individual term page |
| `build_site()` | Main entry point |

### `scripts/convert_to_static.py`

Converts exported wiki data to Markdown files:
- Reads JSON exports from `data/`
- Generates Markdown with proper frontmatter
- Organizes into category folders

### `scripts/wiki_parser.py`

Parses MediaWiki markup:
- Handles wiki tables (`{| ... |}`)
- Converts wiki links to Markdown
- Extracts metadata from templates

---

## 🎨 Styling & Layout

### Current Layout (Header/Footer)

- **Header**: Sticky, blue gradient, contains logo + tagline + nav links
- **Main Content**: Full-width, max 1200px centered
- **Footer**: Dark slate, 3-column grid with links and copyright

### CSS Structure (`site/styles.css`)

| Section | Purpose |
|---------|---------|
| CSS Variables | Colors, fonts |
| Header styles | `.site-header`, `.header-nav`, `.site-brand` |
| Footer styles | `.site-footer`, `.footer-content` |
| Tables | `.glossary-table`, `.terms-table` |
| Badges | `.category-badge`, `.lang-badge` |
| Alphabet nav | `.alphabet-nav`, `.alphabet-link` |
| Tabs | `.tabs`, `.tab-button`, `.tab-content` |
| Responsive | Media queries for mobile |

### Color Scheme

- Primary: `#2563eb` (blue)
- Primary Dark: `#1d4ed8`
- Text: `#1f2937`
- Text Light: `#6b7280`
- Background: `#ffffff`
- Background Secondary: `#f3f4f6`
- Footer Background: `#1f2937`

---

## ⚠️ Common Pitfalls

1. **Run from root directory**: `build_site.py` uses relative paths - must run from repo root:
   ```bash
   python scripts/build_site.py  # Correct
   cd scripts && python build_site.py  # WRONG - won't find glossaries/
   ```

2. **Frontmatter source_url**: The build script overrides `source_url` from frontmatter with GitHub URLs. The override happens AFTER `**frontmatter` unpacking.

3. **Terms vs Glossaries**: Files in root `terms/` folder → Terms tab. Files in `glossaries/` folder → Glossaries tab. This is folder-based detection.

4. **Pagefind indexing**: Only indexes pages with `data-pagefind-body` attribute. Make sure content sections have this attribute.

5. **File naming**: Avoid `-1.md` suffixes - these were duplicates that have been cleaned up.

---

## 🔄 Recent Development History

### January 4, 2026 - Tag Reference System (v1.0.6)

**Auto-generated tag documentation and multi-tag discovery:**

- **TAGS.md**: Human-readable tag reference file at repository root (viewable on GitHub)
- **tags.json**: Machine-readable JSON registry of all tags with counts
- **tags.html**: Dedicated webpage listing all 168 tags with naming conventions
- **"View Tag Reference" button**: Added to Tags tab header, links to tags.html
- **Multi-tag discovery**: Tags tab now indexes actual YAML `tags` field instead of folder categories
  - Glossaries/terms with multiple tags appear under ALL their tags
  - Same glossary can appear under "Medical", "Abbreviations", and "EU" simultaneously
- **Tag naming conventions**: Documented lowercase for generic subjects, capitalize proper nouns only
- **Build summary**: Now shows unique tag count

**Files Modified:**
- `scripts/build_site.py` - Added `collect_all_tags()`, `generate_tags_reference()`, `generate_tags_json()`, rewrote `generate_categories_content()`, updated `build_site()`
- `site/styles.css` - Added styles for `.tags-tab-header`, `.tag-reference-link`, `.tag-conventions`, `.tag-table-section`, `.tag-reference-table`

**Files Generated:**
- `TAGS.md` - At repo root
- `_site/tags.json` - In build output
- `_site/tags.html` - In build output

### January 4, 2026 - Expanded About Sections (v1.0.5)

- Glossary and term pages now show more metadata from YAML frontmatter:
  - Title, Description, Languages, Domain, Terms count, Source URL, Last Updated
- Source links now open in new tab (`target="_blank"`)

### January 4, 2026 - URL Search Parameter (v1.0.4)

- Added support for `?q=searchterm` URL parameter for programmatic search
- Enables integration with external tools like Supervertaler's Superlookup
- JavaScript detects URL param, populates search input, triggers search automatically
- Auto-scrolls to search results when query parameter is provided

### January 4, 2026 - Actionable Tag Cards (v1.0.3)

- Tags tab now shows clickable links to glossaries and terms instead of just statistics
- Each tag card displays lists of glossary and term links for that category
- Summary line shows total entry count per tag
- Tag card layout redesigned with dedicated sections for "📚 Glossaries" and "📄 Terms"
- Grid layout widened from 280px to 320px minimum card width for better readability

### January 4, 2026 - Folder Restructure (v1.0.2)

- Moved `terms/` folder from `glossaries/terms/` to root level `terms/`
- Updated build script to scan both directories separately
- Cleaner separation: `glossaries/` for glossaries, `terms/` for single-term pages

### January 3, 2026 - Header/Footer Redesign

- Removed sidebar layout completely
- Added sticky site header with logo, tagline, nav links
- Added footer with 3-column layout
- Removed duplicate "Superlookup" title (was in header AND hero section)
- Removed "Home" nav link (logo click goes home)

### January 3, 2026 - Duplicate Cleanup

- Removed 188 duplicate glossary files (files ending in `-1.md`)
- Kept versions with `type: glossary` in frontmatter
- Renamed remaining files to remove `-1` suffix
- Reduced glossary count from 377 to 207

### January 3, 2026 - Source URL Fix

- Fixed source URLs pointing to old superlookup.wiki instead of GitHub
- Bug was: `**frontmatter` unpacking overwrote generated GitHub URL
- Fix: Set `source_url` AFTER unpacking frontmatter

### January 3, 2026 - File Organization

- Physically moved 159 files with <10 terms to separate `terms/` folder
- These appear in Terms tab instead of Glossaries tab
- Folder-based detection: `terms/` folder = Terms, `glossaries/` = Glossaries

### January 3, 2026 - Tabbed Interface

- Added Glossaries tab (207 items) and Terms tab (141 items)
- Each tab has its own A-Z navigation
- Tab descriptions explain the difference

---

## 🧪 Testing Locally

### Build the site:
```bash
cd C:\Dev\superlookup-glossaries
python scripts/build_site.py
```

### Build search index:
```bash
npx pagefind --site _site
```

### Preview locally:
```bash
cd _site
python -m http.server 8080
# Open http://localhost:8080
```

---

## 📚 Related Projects

| Project | Description | Link |
|---------|-------------|------|
| **Supervertaler** | Desktop translation app (PyQt6) | https://supervertaler.com |
| **Superlookup (in-app)** | Unified lookup panel in Supervertaler | Part of Supervertaler |
| **Supermemory** | Vector-indexed semantic TM search | Part of Supervertaler |

---

## 🔗 Useful Links

- **Live Site**: https://michaelbeijer.github.io/beijerterm/
- **GitHub Repository**: https://github.com/michaelbeijer/beijerterm
- **GitHub Actions**: https://github.com/michaelbeijer/beijerterm/actions
- **Supervertaler**: https://supervertaler.com
- **Author**: https://michaelbeijer.co.uk

---

*This file is the single source of truth for AI coding assistants working on this project.*
*Last updated: January 4, 2026*
