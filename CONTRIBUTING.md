# Contributing to Beijerterm Glossaries

Thank you for your interest in contributing! This project aims to build the world's largest open-source multilingual terminology database.

## Our Philosophy

**We believe terminology should be free.**

Lexical data, translations, and terminology are facts about language. Facts cannot and should not be owned. By contributing to Beijerterm, you're helping build a free, open resource for translators, linguists, and language learners worldwide.

All glossary data in Beijerterm is released under **CC0 (Public Domain Dedication)** — use it however you want, no attribution required.

## Ways to Contribute

### 1. Add a New Glossary

The easiest way to contribute:

1. Fork this repository
2. Create a new `.md` file in the appropriate category folder under `glossaries/`
3. Follow the format below
4. Submit a Pull Request

### 2. Improve Existing Glossaries

- Fix typos or errors
- Add missing terms
- Improve translations
- Add notes or context

### 3. Add New Categories

If you have glossaries that don't fit existing categories:

1. Create a new folder under `glossaries/`
2. Add a `_category.yaml` file with metadata
3. Add your glossary files

## Glossary File Format

Each glossary is a Markdown file with YAML frontmatter:

```markdown
---
title: Your Glossary Title
slug: your-glossary-slug
description: A brief description of what this glossary contains
source_lang: nl
target_lang: en
domain: category-name
term_count: 100
source_url: https://original-source.com/
author: Original Author or Your Name
license: CC0
last_updated: 2025-01-01
tags:
  - relevant
  - tags
---

# Your Glossary Title

Optional introductory text about the glossary.

## Terms

| Source | Target | Notes |
|--------|--------|-------|
| term1 | translation1 | optional notes |
| term2 | translation2 | |
```

### Required Fields

- `title`: Human-readable name
- `slug`: URL-friendly identifier (lowercase, hyphens)
- `source_lang`: ISO 639-1 code (e.g., `nl`, `en`, `de`)
- `target_lang`: ISO 639-1 code
- `domain`: Category slug (must match folder name)

### Optional Fields

- `description`: Longer description
- `term_count`: Number of terms (auto-calculated if omitted)
- `source_url`: Original source URL
- `author`: Creator/compiler
- `license`: License (default: CC0, public domain)
- `last_updated`: Date in YYYY-MM-DD format
- `tags`: Array of relevant tags
- `extra_languages`: Array of additional language codes for multilingual glossaries

## Category Metadata

Each category folder should have a `_category.yaml`:

```yaml
name: Category Name
slug: category-slug
description: What this category contains
icon: 📚
color: "#3498db"
```

## Table Format

### Basic (bilingual)

```markdown
| Dutch | English | Notes |
|-------|---------|-------|
| term  | term    | notes |
```

### Multilingual

```markdown
| English | Dutch | German | French | Notes |
|---------|-------|--------|--------|-------|
| term    | term  | term   | term   | notes |
```

## Licensing

**All glossary data in Beijerterm is released under CC0 (Public Domain Dedication).**

This means:
- ✅ Use for any purpose (personal, commercial, academic)
- ✅ Modify, transform, and build upon freely
- ✅ No attribution required (though appreciated!)
- ✅ No restrictions whatsoever

**Why CC0?** Terminology is facts about language. Facts should be free. We want maximum usability for translators and language professionals worldwide.

**About sources**: Many glossaries are compiled, processed, and enhanced from various online sources. We acknowledge original sources in the `source_url` field, but our processed compilations are released freely. If you believe any content should not be included, please open an issue.

## Quality Guidelines

1. **Accuracy**: Verify translations before submitting
2. **Consistency**: Follow existing formatting conventions
3. **Attribution**: Always credit original sources
4. **Completeness**: Include notes for ambiguous terms

## Questions?

Open an issue on GitHub if you have questions or need help.
