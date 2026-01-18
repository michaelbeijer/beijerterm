# Changelog

All notable changes to the Beijerterm project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.6.1] - 2026-01-17

### Added
- **Admin panel edit links** on all content pages
  - Glossary pages: "Edit this glossary on GitHub or Admin panel"
  - Term pages: "Edit this term on GitHub or Admin panel"
  - Resource pages: "Edit this resource on GitHub or Admin panel"
  - Links open directly to the specific item in the admin panel editor

### Changed
- **Navigation layout improvements**
  - Moved Admin link to far right (after GitHub icon)
  - Added visual separator (|) between main navigation and admin area
  - Simplified Admin link text (removed icon, now just "Admin")
  - Better visual hierarchy separating public links from authentication-required links

### Fixed
- **Removed underlines** from site icon and "Beijerterm" title on hover
- **Auto-generated slugs** for terms and resources missing slug in frontmatter
- Added CSS rules to prevent text-decoration on all link states (hover, visited, active, focus)

### Technical
- Added `.nav-separator` CSS styling for navigation divider
- Updated `generate_glossary_page()`, `generate_term_page()`, `generate_resource_page()` functions
- Auto-generate slugs from filename if not present in YAML frontmatter
- Version badge updated to v1.6.0 → v1.6.1

## [1.6.0] - 2026-01-16

### Added
- **Custom Admin Panel** (`/admin`) - Full-featured content management system
  - Excel-like glossary spreadsheet editor with inline editing
  - Rich text Markdown editor for term pages (in progress)
  - Resource editor for What's New and other pages (in progress)
  - GitHub OAuth authentication + dev mode bypass
  - Flask-based backend with REST API
  - Tab navigation, keyboard shortcuts (Ctrl+S, Ctrl+Enter)
  - Bulk operations: sort, search, import/export TSV, find duplicates
  - Auto-save with change tracking

### Technical
- New `/admin` directory with Flask application
- Python dependencies: Flask, PyYAML, requests, PyGithub
- Markdown table parser/generator for glossary files
- Dev mode startup script for local development

### Notes
- Admin panel is work-in-progress (v0.1)
- Currently supports glossary editing only
- Term page and resource editors coming next
- Git commit/push integration to be implemented

## [1.5.1] - 2026-01-16

### Added
- **What's New page** (`/resources/whats-new`) - User-facing content changelog for glossary/term additions
- **What's New helper script** (`scripts/add_whats_new_entry.py`) - Interactive tool for adding entries
- **Template comments** in What's New page showing entry format

### Changed
- **Site icon**: Replaced B logo with 🌐 globe emoji
- **Header navigation**: Now shows "Michael Beijer", "What's New", and GitHub icon
- **Footer background**: Changed from #f3f4f6 to #1a1a1a (dark charcoal)
- **Navigation simplification**: Removed Supervertaler from header (kept in footer)

### Technical
- Added CSS styling for emoji icon and GitHub SVG icon
- GitHub icon matches style from supervertaler.com

## [1.3.1] - 2026-01-07

### Added
- **Glossary pages in search**: Glossary metadata (title, description, tags) now indexed as searchable entities
- **Automated PageFind indexing**: Build script now automatically runs PageFind after generating HTML

### Fixed
- **Search functionality**: Searching for glossary titles now returns the glossary page itself, not just term entries
- **Markdown in table cells**: Markdown now properly renders in glossary table cells (links, formatting)

## [1.3.0] - 2026-01-07

### Added
- **Resources content type**: New category for articles, guides, and reference materials
  - Separate `/resources/` index page with card-based layout
  - Individual resource pages with full markdown rendering
  - Resources tab visible on all index pages (home, glossaries, terms)
- **Markdown in glossary descriptions**: Description field now supports full markdown
  - Bold, italic, links, and bullet lists in "About this glossary" box
  - Use YAML multiline syntax (`description: |`) for rich descriptions
- **Resources tab everywhere**: 📄 Resources tab now appears alongside Glossaries and Terms on all index pages

### Changed
- **Folder structure**: Content now organized under `content/` directory
  - `content/glossaries/` - Multi-term glossary files
  - `content/terms/` - Single-term definition pages  
  - `content/resources/` - Articles and reference materials

### Fixed
- **Bullet list indentation**: Lists in resource pages now properly indented within content margins

## [1.2.0] - 2026-01-06

### Added
- **Clickable footnotes**: References like `[^1]` now link to footnotes and back
  - Added `footnotes` extension to Markdown processor
  - Back-reference arrows (↩) scroll correctly past fixed header
- **Last rebuilt date**: Footer now shows "Last rebuilt: [date]" auto-updated on build
- **Term source link**: Simplified "Edit on GitHub" link replaces verbose About box

### Changed
- **Cleaner term page layout**: Less boxy, more readable design
  - h2 headers: Blue underline instead of gray background boxes
  - h3 headers: Plain bold text, no background
  - Horizontal rules: Gradient fade from blue to transparent
  - Max content width: 800px for better readability
  - Line height: Increased to 1.8 for breathing room
- **Removed verbose "About this term" box**: Replaced with minimal edit link

### Fixed
- **Footnote scroll offset**: `scroll-margin-top: 5rem` prevents anchors landing behind fixed header

## [1.1.0] - 2026-01-04

### Changed
- **License change to CC0**: All glossary data now released under CC0 (Public Domain Dedication)
  - Terminology should be free — facts about language cannot and should not be owned
  - No attribution required (though still appreciated)
  - Code remains MIT licensed
- **LICENSE.md**: Renamed from LICENSE for better GitHub rendering

### Added
- **LICENSE.md**: Comprehensive dual-license file (CC0 for data, MIT for code)
- **Philosophy statement**: "We believe terminology should be free" added to README and footer

## [1.0.9] - 2026-01-04

### Fixed
- **Tags page header**: Icon path and tagline now display correctly on tags.html
  - Icon was pointing to `../mb-icon.svg` instead of `mb-icon.svg` (tags.html is in root)
  - Tagline was only showing on home page, now shows on all pages
- **Root page detection**: `generate_site_header()` now correctly identifies root-level pages (home, tags)

## [1.0.8] - 2026-01-04

### Changed
- **Removed Tags tab**: Tag filtering now integrated directly into Glossaries and Terms tabs
- **Clickable Tags stat**: Stats section "Tags" now links to tags.html reference page
- **Renamed stat**: "Categories" → "Tags" in stats section

## [1.0.7] - 2026-01-04

### Added
- **Clickable tag filtering**: Click any tag in the Glossaries or Terms table to filter the list
  - Filter bar shows active tag with count of matching items
  - Alphabet navigation dims letters with no matches
  - "Clear filter" button to reset
- **Tags in About sections**: Glossary and term detail pages now show tags in the "About" section
- **Tags column in Terms tab**: Terms tab now shows clickable tags instead of description

### Changed
- **New tagline**: "Open-source, GitHub-hosted multilingual terminology database"
- **Removed Domain field**: Domain removed from all glossary files and UI (redundant with folder structure)
- **Column header renamed**: "Category" → "Tags" in both Glossaries and Terms tables

### Removed
- **Domain field**: Removed from all 207 glossary YAML files (folder already indicates domain)
- **Domain in About sections**: Removed Domain row from glossary/term info panels

## [1.0.6] - 2026-01-04

### Added
- **Tag Reference System**: Auto-generated comprehensive tag documentation
  - `TAGS.md`: Human-readable tag reference file at repository root (viewable on GitHub)
  - `tags.json`: Machine-readable JSON registry of all tags with counts
  - `tags.html`: Dedicated webpage listing all 168 tags with naming conventions
  - "View Tag Reference" button in Tags tab header linking to tags.html

### Changed
- **Multi-tag discovery**: Tags tab now indexes actual YAML `tags` field instead of folder categories
  - Glossaries/terms with multiple tags appear under ALL their tags
  - Same glossary can appear under "Medical", "Abbreviations", and "EU" simultaneously
- **Tag naming conventions documented**: Lowercase for generic subjects, capitalize proper nouns only
- Build summary now shows unique tag count

## [1.0.5] - 2026-01-04

### Changed
- **Expanded "About" sections**: Glossary and term pages now show more metadata from YAML frontmatter:
  - Title, Description, Languages, Domain, Terms count, Source URL, Last Updated
- Source links now open in new tab (`target="_blank"`)

## [1.0.4] - 2026-01-04

### Added
- **URL Search Parameter**: Site now supports `?q=searchterm` URL parameter for programmatic search
- Enables integration with external tools like Supervertaler's Superlookup
- Auto-scrolls to search results when query parameter is provided

## [1.0.3] - 2026-01-04

### Added
- **Actionable Tag Cards**: Tags tab now shows clickable links to glossaries and terms instead of just statistics
- Each tag card displays lists of glossary and term links for that category
- Summary line shows total entry count per tag

### Changed
- Tag card layout redesigned with dedicated sections for "📚 Glossaries" and "📄 Terms"
- Grid layout widened from 280px to 320px minimum card width for better readability

## [1.0.2] - 2026-01-04

### Changed
- **Folder restructure**: Moved `terms/` folder from `glossaries/terms/` to root level `terms/`
- Build script now scans both `glossaries/` (for glossaries) and `terms/` (for term pages) directories
- Cleaner separation between glossaries and single-term entries

## [1.0.1] - 2026-01-03

### Added
- **Search result highlighting**: When clicking through from search results, matching terms are highlighted in yellow on the destination page
- **Navigation bar for highlights**: Shows match count with Previous/Next navigation buttons
- **Keyboard shortcuts**: Press N (next), P (previous), or Esc (close) to navigate between highlighted matches
- **Auto-scroll to first match**: Page automatically scrolls to the first highlighted match
- **Version badge**: Header now displays "Beijerterm v1.0.1"

### Changed
- Minimum term count filter (10 terms) to distinguish glossaries from single-term entries
- Single-term entries (< 10 terms) now appear in Terms tab instead of Glossaries tab

## [1.0.0] - 2026-01-03

### Added
- **Tabbed Interface**: Main page now has separate tabs for Glossaries and Terms
  - Glossaries tab: Multi-term terminology lists with tables
  - Terms tab: Individual term pages with definitions and examples
- **Scroll-to-top button**: Blue circular button appears after scrolling 300px, smooth scrolls back to top
- **A-Z alphabet navigation**: Quick jump to glossaries/terms by first letter within each tab
- **Statistics section**: Shows counts for glossaries, term pages, term entries, and categories
- **GitHub source links**: All content links back to source files on GitHub (not wiki)
- **Sidebar navigation**: Markdown sidebar content properly rendered as HTML
- **Pagefind search**: Full-text search across all glossaries and terms
- **Category badges**: Color-coded category labels for each glossary
- **Language indicators**: Shows source → target language pairs

### Fixed
- Source URLs now correctly point to GitHub repository instead of superlookup.wiki
- Sidebar content now renders as HTML instead of raw Markdown
- Terms no longer appear in Glossaries tab (folder-based detection)

### Changed
- Migrated from MediaWiki to static site (GitHub Pages)
- Build system uses Python script (`scripts/build_site.py`) instead of wiki engine
- Site deployed via GitHub Actions workflow

### Technical
- **Stack**: Python build script + Pagefind search + GitHub Pages hosting
- **Data format**: Markdown files with YAML frontmatter in `glossaries/` directory
- **Categories**: agriculture, automotive, aviation, chemistry, construction, energy, financial, food, general, it, legal, medical, technical, textile

## [0.1.0] - 2025-12-xx (Pre-migration)

### Legacy
- Original site hosted on MediaWiki at superlookup.wiki
- Content exported using `wiki_parser.py` and `full_export.py` scripts
- Data converted to static Markdown format using `convert_to_static.py`

---

## Migration Notes

### From MediaWiki to Static Site

The Beijerterm project was migrated from a self-hosted MediaWiki instance to a static site on GitHub Pages. This provides:

1. **Zero hosting costs** - GitHub Pages is free
2. **Better performance** - Static HTML loads faster than dynamic wiki
3. **Version control** - All content changes tracked in Git
4. **Community contributions** - Easy to submit PRs to add/fix terminology
5. **Offline capability** - Site can be downloaded and used offline

### Content Structure

```
glossaries/
├── agriculture/     # Agriculture terminology
├── automotive/      # Automotive/vehicle terms
├── aviation/        # Aviation/aerospace
├── chemistry/       # Chemistry/chemical engineering
├── construction/    # Construction/building
├── energy/          # Energy/utilities
├── financial/       # Finance/accounting
├── food/            # Food industry
├── general/         # General/miscellaneous
├── it/              # Information technology
├── legal/           # Legal/law
├── medical/         # Medical/healthcare
├── technical/       # Technical/engineering
└── textile/         # Textile industry
```

Each `.md` file contains:
- YAML frontmatter (title, slug, languages, term_count, etc.)
- Markdown table with terminology (Dutch | English | Notes)

### Build Process

1. `scripts/build_site.py` reads all Markdown files
2. Generates HTML pages for index, glossaries, and terms
3. Creates search index JSON
4. Copies static assets (CSS, icons)
5. GitHub Actions runs Pagefind to index content
6. Site deployed to GitHub Pages

---

*Beijerterm - Open source multilingual terminology database*
*https://michaelbeijer.github.io/beijerterm/*
