# Superlookup

[![Version](https://img.shields.io/badge/version-v1.0.1-blue.svg)](https://github.com/michaelbeijer/superlookup/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/hosted-GitHub%20Pages-orange.svg)](https://michaelbeijer.github.io/superlookup/)

**An open-source, GitHub-hosted multilingual terminology database.**

Every glossary is a Markdown file. Full-text search powered by Pagefind.

 **Live site**: [michaelbeijer.github.io/superlookup](https://michaelbeijer.github.io/superlookup/)

##  Features

-  **One file per glossary** - Easy to browse, download, contribute
-  **Full-text search** - Search across ALL terms, translations, and notes
-  **Multilingual** - Any language pair supported
-  **Human-readable** - Markdown tables with YAML metadata
-  **Version controlled** - Full history of every change
-  **Free hosting** - GitHub Pages
-  **Search highlighting** - Click through from search to see matches highlighted

##  Structure

```
Superlookup/
 glossaries/
    automotive/
       _category.yaml       # Category metadata
       land-rover-dictionary.md
       autowoordenboek.md
    aviation/
       _category.yaml
       schiphol-glossary.md
       easa-glossary.md
    medical/
       ...
    ...
 site/
    styles.css
    sv-icon.svg
 scripts/
    build_site.py            # Generates HTML from Markdown
 .github/
     workflows/
         deploy.yaml          # Auto-deploy on push
```

##  Glossary File Format

Each glossary is a Markdown file with YAML frontmatter:

```markdown
---
title: Amsterdam Airport Schiphol Glossary
slug: schiphol-glossary
description: Aviation terminology from Amsterdam Schiphol Airport
source_lang: nl
target_lang: en
domain: aviation
term_count: 2143
source_url: https://www.schiphol.nl/
author: Schiphol Group
license: CC-BY-4.0
last_updated: 2025-06-15
---

| Dutch | English | Notes |
|-------|---------|-------|
| bagageband | baggage carousel | also: bagagecarrousel |
| vertrekhal | departure hall | |
| aankomsthal | arrivals hall | |
| douane | customs | |
| paspoortcontrole | passport control | |
```

##  Search

Pagefind indexes all glossary content at build time, enabling:

- Full-text search across ALL terms
- Filter by language, domain, or glossary
- Instant results (client-side, no server needed)
- Works offline once loaded
- **NEW**: Search result highlighting with keyboard navigation (N/P/Esc)

##  Local Development

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Build the site
python scripts/build_site.py

# Run Pagefind indexing
npx pagefind --site _site

# Serve locally
npx serve _site
```

##  Contributing

1. Fork this repository
2. Add or edit glossaries in `glossaries/`
3. Submit a Pull Request

### Adding a new glossary

1. Choose the appropriate category folder (or create one)
2. Create a new `.md` file with YAML frontmatter
3. Add terms in the Markdown table format
4. Submit PR

##  Versioning

Superlookup uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes to data format or API
- **MINOR** (x.1.x): New features (backward compatible)
- **PATCH** (x.x.1): Bug fixes and minor improvements

Current version: **v1.0.1** (see [CHANGELOG.md](CHANGELOG.md))

##  License

- **Code**: MIT License
- **Glossary data**: Various (see individual glossary files)

##  Acknowledgments

Inspired by [superlookup.wiki](https://superlookup.wiki) - one of the world's largest collections of specialist multilingual terminology.

---

Created by [Michael Beijer](https://michaelbeijer.co.uk)  Part of the [Supervertaler](https://supervertaler.com) ecosystem
