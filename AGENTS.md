# Beijerterm - AI Agent Documentation

> **This is the single source of truth for AI coding assistants working on this project.**
> **Last Updated:** January 17, 2026 | **Version:** v1.6.1

---

## 🎯 Project Overview

**Beijerterm** is an open-source multilingual terminology database and glossary website. It provides a searchable collection of Dutch-English translation glossaries, terminology lists, and individual term definitions for professional translators.

| Property | Value |
|----------|-------|
| **Name** | Beijerterm |
| **Type** | Static website (GitHub Pages) |
| **Language** | Python (build scripts), HTML/CSS/JS (frontend) |
| **Repository** | https://github.com/michaelbeijer/beijerterm |
| **Live Site** | https://beijerterm.com |
| **Build System** | Python + Pagefind (search indexing) |
| **Hosting** | GitHub Pages via GitHub Actions |
| **Custom Domain** | beijerterm.com |
| **Related Project** | [Supervertaler](https://supervertaler.com) - Desktop translation app |

### Key Statistics

| Metric | Count |
|--------|-------|
| **Glossaries** | ~208 |
| **Term Pages** | ~9 |
| **Resources** | ~1 |
| **Total Term Entries** | ~583,652 |
| **Categories** | 14 |
| **Tags** | ~133 |
| **Languages** | Dutch ↔ English (primarily) |

### Content Types

| Type | Location | Description |
|------|----------|-------------|
| **Glossaries** | `content/glossaries/` | Multi-term lists with Markdown tables |
| **Terms** | `content/terms/` | Individual term definition pages |
| **Resources** | `content/resources/` | Articles, guides, reference materials |
| **What's New** | `content/resources/whats-new.md` | User-facing content changelog |

### Key Capabilities

- **Full-text Search**: Pagefind-powered search across all glossaries and terms
- **Three Content Tabs**: Glossaries, Terms, and Resources
- **A-Z Navigation**: Alphabetical browsing with sticky navigation bar
- **Tag Filtering**: 102 tags for cross-category filtering
- **Markdown Descriptions**: Glossary descriptions support full markdown (bold, lists, links)
- **Responsive Design**: Mobile-friendly layout with header/footer navigation
- **Source Attribution**: Links to original sources (GitHub repository)

---

## 📁 Project Structure

```
beijerterm/
├── AGENTS.md                  # This file - AI agent documentation
├── CHANGELOG.md               # Version history
├── README.md                  # User-facing documentation
│
├── content/                   # Source content (Markdown files)
│   ├── glossaries/            # Multi-term glossary files
│   │   ├── agriculture/
│   │   ├── automotive/
│   │   ├── aviation/
│   │   ├── chemistry/
│   │   ├── construction/
│   │   ├── energy/
│   │   ├── financial/
│   │   ├── food/
│   │   ├── general/
│   │   ├── it/
│   │   ├── legal/
│   │   ├── medical/
│   │   ├── technical/
│   │   └── textile/
│   ├── terms/                 # Individual term pages
│   │   └── vergisting.md
│   └── resources/             # Articles & reference materials
│       └── nederbrackets.md
│
├── scripts/                   # Build tools
│   └── build_site.py          # Main static site generator (~2000 lines)
│
├── site/                      # Static assets (copied to _site/)
│   ├── styles.css             # Main stylesheet
│   ├── mb-icon.svg            # Site logo
│   └── favicon.ico            # Browser icon
│
├── _site/                     # Generated output (gitignored)
│   ├── index.html             # Home page
│   ├── glossaries/            # /glossaries/ index + individual pages
│   ├── terms/                 # /terms/ index + individual pages
│   ├── resources/             # /resources/ index + individual pages
│   ├── pagefind/              # Search index
│   └── *.css, *.svg, etc.     # Copied assets
│
└── .github/
    └── workflows/
        └── deploy.yaml        # GitHub Actions build & deploy
```

---

## 🔧 Key Technical Details

### Build Process

The site is built by `scripts/build_site.py`:

1. **Load Content**: Reads all `.md` files from `content/glossaries/`, `content/terms/`, and `content/resources/`
2. **Parse Frontmatter**: Extracts YAML metadata (title, slug, languages, tags, description, etc.)
3. **Categorize**: Files sorted into three content types with separate index pages
4. **Generate HTML**: Creates index pages and individual pages for each content type
5. **Copy Assets**: Copies styles.css, favicon, logo to `_site/`
6. **Search Index**: Pagefind indexes all pages for full-text search

### Content Format

Each glossary/term/resource file is Markdown with YAML frontmatter:

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
- Footer Background: `#1a1a1a` (dark charcoal - updated Jan 16, 2026)

### Site Identity

- **Icon**: 🌐 globe emoji (as of v1.5.1)
  - Replaced B logo SVG (`b-icon.svg`)
  - Displayed via `.site-icon` CSS class
- **Navigation**: Michael Beijer | What's New | GitHub icon | **|** | Admin
  - Visual separator (|) between main nav and admin area (v1.6.1)
  - Admin link positioned at far right (authentication-required)
  - All links have no underlines on hover (fixed v1.6.1)
- **Version Badge**: Shows current site version in header
- **Edit Links**: All content pages have dual edit links (v1.6.1)
  - "Edit this [item] on GitHub or Admin panel"
  - Links open directly to specific editor in admin panel

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

### January 17, 2026 - Navigation & Edit Links (v1.6.1)

**Admin panel integration and navigation improvements:**

- **Admin panel edit links**: Added to all content pages (glossaries, terms, resources)
  - Format: "Edit this [item] on **GitHub** or **Admin panel**"
  - Links open directly to the specific item in the admin panel editor
  - Admin URLs: `/glossaries/{filename}`, `/terms/{slug}`, `/resources/{slug}`
- **Navigation reorganization**: Moved Admin link to far right after GitHub icon
  - Visual separator (|) between main navigation and admin area
  - Better separation of public links vs authentication-required links
- **Hover underline fix**: Removed underlines from site icon and title on all link states
- **Auto-slug generation**: Terms and resources now auto-generate slugs from filename if missing

**Files Modified:**
- `scripts/build_site.py` - Updated `generate_glossary_page()`, `generate_term_page()`, `generate_resource_page()`, `load_all_content()`, `generate_site_header()`
- `site/styles.css` - Added `.nav-separator` styles, comprehensive link state rules
- Version badge: v1.6.0 → v1.6.1

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

## 🔄 Recent Development History

### January 16, 2026 - v1.5.0: Theme Switcher & Visual Improvements

**🎨 Client-Side Theme Switcher Implementation**

Added complete theming system with 6 color schemes:

**Features:**
- Client-side theme switcher using CSS custom properties (CSS variables)
- localStorage persistence across all pages
- Subtle 🎨 emoji button in header (no text, minimal UI)
- Dropdown menu with 6 theme options and color swatches
- Theme selection shows checkmark indicator

**Available Themes:**
1. **Royal Blue** (default) - `#4169e1` / `#2948a8`
2. **Modern Tech Blue** - `#0969da` / `#0550ae` (GitHub-style)
3. **Corporate Navy** - `#1e3a8a` / `#1e293b`
4. **Academic Slate** - `#334155` / `#1e293b` (with `#0ea5e9` accent)
5. **Refined Teal** - `#0891b2` / `#0e7490`
6. **Minimalist B&W** - `#1a1a1a` / `#0a0a0a` (black header, white body)

**Technical Implementation:**
- `:root` and `[data-theme="..."]` CSS selectors define color variables
- JavaScript in footer:
  - `loadTheme()` - Reads from localStorage, applies data-theme attribute
  - `setTheme(theme)` - Saves to localStorage, updates UI, closes dropdown
  - `updateThemeUI(theme)` - Updates dropdown checkmarks
  - `toggleThemeDropdown()` - Shows/hides dropdown
  - Click-outside listener to auto-close dropdown
- localStorage key: `beijerterm-theme`

**Comprehensive Theme Integration:**
- Fixed all hardcoded colors to use CSS variables
- Header gradient: `linear-gradient(135deg, var(--primary-color), var(--primary-dark))`
- Footer gradient: `linear-gradient(135deg, var(--primary-dark), #1a1a1a)`
- Active tab buttons: `var(--primary-color)`
- All links, badges, highlights: theme-aware
- Tag reference tables: theme-aware headers
- Special handling for Minimal theme: inverted black header with white text

**Icon Update:**
- Changed from MB (Michael Beijer) to B (Beijerterm)
- Circular icon with white background and colored border
- Border color changes with theme: `var(--primary-color)`

**Files Modified:**
- `site/styles.css` - CSS variables for 6 themes + theme switcher UI styles (~100 lines added)
- `scripts/build_site.py` - Theme switcher HTML in header + JavaScript in footer (~90 lines)
- `site/b-icon.svg` - NEW circular B icon (replacing MB icon)

**User Experience:**
- Theme persists across page navigation
- Works on all 208 glossary pages
- No backend required - pure client-side
- Instant theme switching with no page reload

**Deployment:**
- GitHub Actions automatically builds site on push
- Workflow located at `.github/workflows/deploy.yaml`
- Build script generates `_site/` folder (not tracked in git due to 196MB search index)
- GitHub Pages serves from built `_site/` artifact

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

### Update What's New page:

**Option 1: Interactive helper script (recommended)**
```bash
python scripts/add_whats_new_entry.py
```
The script will:
- Auto-create current month section if needed
- Prompt for term/glossary details
- Insert entries in correct location
- Remind you to rebuild and push

**Option 2: Manual edit**
Edit `content/resources/whats-new.md` using the template comment at the top.

**Workflow after adding entries:**
```bash
# Rebuild site
python scripts/build_site.py

# Commit and push
git add content/resources/whats-new.md
git commit -m "docs: Add [term/glossary] to What's New"
git push
```

---

## �️ Admin Panel (New in v1.6.0)

### Overview

The custom admin panel provides a user-friendly interface for editing glossaries, terms, and resources without directly manipulating Markdown files. It's designed specifically for Beijerterm's needs.

**Access:** http://localhost:5000 (development mode)

### Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Flask 3.0+ | REST API, authentication, file I/O |
| **Frontend** | Pure JavaScript | Spreadsheet editor, no frameworks |
| **Authentication** | GitHub OAuth | Production mode |
| **Dev Mode** | Env variable bypass | Local development |
| **Parser** | Custom Python | Markdown tables ↔ JSON |

### Features

**✅ Implemented:**
- Excel-like glossary spreadsheet editor
- Inline cell editing with Tab navigation
- Add/delete rows, sort A→Z / Z→A
- Search/filter across all fields
- Find duplicates highlighting
- Import/Export TSV for bulk operations
- Auto-save with change tracking
- Keyboard shortcuts (Ctrl+S, Ctrl+Enter)

**🔄 In Progress:**
- Term page WYSIWYG Markdown editor
- Resources editor for What's New
- Git commit/push from admin panel
- Preview functionality

### File Structure

```
admin/
├── app.py                     # Flask application (~450 lines)
│   ├── parse_glossary_markdown() - Parses .md with frontmatter + table
│   ├── generate_glossary_markdown() - Converts JSON back to markdown
│   ├── Routes: /, /login, /auth/*, /glossaries, /api/glossaries/*
│   └── GitHub OAuth + dev mode authentication
│
├── start_dev.py               # Development launcher
│   └── Sets ADMIN_DEV_MODE=true for OAuth bypass
│
├── requirements.txt           # Python dependencies
│   ├── Flask>=3.0.0
│   ├── PyYAML>=6.0
│   ├── requests>=2.31.0
│   └── PyGithub>=2.1.1
│
├── templates/                 # Jinja2 templates
│   ├── base.html              # Navigation layout, navbar, user menu
│   ├── login.html             # GitHub OAuth or dev mode login
│   ├── index.html             # Dashboard with stats (208 glossaries, 9 terms)
│   ├── glossaries.html        # List view with entry counts
│   └── glossary_editor.html   # Full spreadsheet interface with toolbar
│
└── static/
    ├── css/
    │   ├── admin.css          # Main admin styling (~450 lines)
    │   └── glossary_editor.css # Spreadsheet table, cells (~250 lines)
    └── js/
        ├── admin.js           # Global utilities, notifications, Ctrl+S
        └── glossary_editor.js # GlossaryEditor class (~400 lines)
```

### Development Workflow

**Starting the server:**
```bash
cd admin/
python start_dev.py
# Visit http://localhost:5000
# Click "Continue in Dev Mode" to bypass OAuth
```

**Making changes:**
1. Edit files in `admin/`
2. Flask auto-reloads on file changes
3. Refresh browser to see updates
4. Test glossary editing thoroughly

**Production deployment (future):**
- Set up GitHub OAuth app
- Configure `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
- Deploy to server or use GitHub Codespaces

### Glossary File Format

Glossaries are stored as `.md` files with YAML frontmatter + Markdown table:

```markdown
---
title: Agricultural Terms
category: agriculture
source_language: en
target_language: nl
source: "Original source citation"
entries: 245
---

| Dutch | English | Domain | Notes |
|-------|---------|--------|-------|
| akkerbouw | arable farming | Agriculture | |
| gewasbescherming | crop protection | Agriculture | Pesticides, herbicides |
```

**Parser behavior:**
- `parse_glossary_markdown()`: Splits on `---`, parses YAML, extracts table rows
- `generate_glossary_markdown()`: Converts JSON back to frontmatter + table format
- Handles empty cells, missing columns, special characters

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Tab** | Move to next cell |
| **Shift+Tab** | Move to previous cell |
| **Enter** | Move to next row (same column) |
| **Ctrl+Enter** | Add new row at end |
| **Ctrl+S** | Save changes |
| **Escape** | Clear search/cancel edit |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /` | GET | Dashboard |
| `GET /login` | GET | Login page |
| `GET /glossaries` | GET | Glossary list view |
| `GET /glossaries/<filename>` | GET | Glossary editor page |
| `GET /api/glossaries/<filename>` | GET | Get glossary data (JSON) |
| `POST /api/glossaries/<filename>` | POST | Save glossary changes |

### Known Issues

- Server crashes on syntax errors (needs better error handling)
- No validation for required fields yet
- Git commit/push not yet implemented
- No rollback/undo for saved changes

### Future Enhancements

- Visual Markdown editor for term pages (TinyMCE or SimpleMDE)
- Bulk operations: merge glossaries, split by category
- Import from other formats (CSV, XLSX, TMX)
- Conflict resolution for concurrent edits
- Activity log and change history
- Search across all content types

---

## �📚 Related Projects

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
