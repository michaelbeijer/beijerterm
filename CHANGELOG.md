# Changelog

All notable changes to the Beijerterm project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
