#!/usr/bin/env python3
"""
Sophisticated MediaWiki Parser for Superlookup

Handles the various formats accumulated over years:
1. Wikitables (glossaries): {| class="wikitable" ... |}
2. Section-based (== Dutch == / == English ==)
3. Bold format ('''Dutch''': ... / '''English''': ...)
4. Simple bullet lists (* term = translation)
5. Plain text definitions ('term' = translation)
6. Multi-column tables (Dutch | English | English | English)
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class PageType(Enum):
    TERM = "term"
    GLOSSARY = "glossary"
    UNKNOWN = "unknown"


@dataclass
class TermEntry:
    """A single term entry with Dutch/English pair"""
    dutch: str
    english: List[str]  # Can have multiple translations
    context: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    

@dataclass
class ParsedPage:
    """Result of parsing a wiki page"""
    title: str
    page_type: PageType
    entries: List[TermEntry]
    categories: List[str]
    external_links: List[str]
    raw_content: str
    metadata: Dict[str, Any]
    parse_warnings: List[str]


class WikiParser:
    """Sophisticated parser for Superlookup wiki content"""
    
    def __init__(self):
        self.warnings = []
        
    def parse(self, title: str, content: str) -> ParsedPage:
        """Main entry point - detect format and parse accordingly"""
        self.warnings = []
        
        # Extract categories
        categories = self._extract_categories(content)
        
        # Extract external links
        external_links = self._extract_external_links(content)
        
        # Determine page type
        page_type = self._detect_page_type(title, content, categories)
        
        # Parse based on detected format
        entries = []
        metadata = {}
        
        if self._has_wikitable(content):
            entries = self._parse_wikitable(content)
            metadata["format"] = "wikitable"
        elif self._has_sections(content):
            entries = self._parse_sections(content)
            metadata["format"] = "sections"
        elif self._has_bold_format(content):
            entries = self._parse_bold_format(content)
            metadata["format"] = "bold"
        elif self._has_bullet_definitions(content):
            entries = self._parse_bullet_definitions(content, title)
            metadata["format"] = "bullets"
        elif self._has_equals_definition(content):
            entries = self._parse_equals_definition(content, title)
            metadata["format"] = "equals"
        else:
            # Try to extract anything useful
            entries = self._parse_freeform(content, title)
            metadata["format"] = "freeform"
            
        return ParsedPage(
            title=title,
            page_type=page_type,
            entries=entries,
            categories=categories,
            external_links=external_links,
            raw_content=content,
            metadata=metadata,
            parse_warnings=self.warnings
        )
    
    def _detect_page_type(self, title: str, content: str, categories: List[str]) -> PageType:
        """Detect if this is a term page or a glossary"""
        if "Terms" in categories:
            return PageType.TERM
        if "Terminology resources" in categories:
            return PageType.GLOSSARY
        if re.search(r'\d+.*terms?\)', title, re.IGNORECASE):
            return PageType.GLOSSARY
        if "glossary" in title.lower():
            return PageType.GLOSSARY
        table_rows = len(re.findall(r'^\|-', content, re.MULTILINE))
        if table_rows > 20:
            return PageType.GLOSSARY
        return PageType.TERM
    
    def _has_wikitable(self, content: str) -> bool:
        return bool(re.search(r'\{\|\s*class\s*=\s*["\']wikitable', content))
    
    def _has_sections(self, content: str) -> bool:
        return bool(re.search(r'==\s*(Dutch|Nederlands)\s*==', content, re.IGNORECASE))
    
    def _has_bold_format(self, content: str) -> bool:
        return bool(re.search(r"'''(Dutch|Nederlands)'''.*:", content, re.IGNORECASE))
    
    def _has_bullet_definitions(self, content: str) -> bool:
        # Check for bullet lists that look like translations (without = or :)
        # e.g., '''title''' followed by * translation lines
        return bool(re.search(r"^'''[^']+'''", content, re.MULTILINE)) or \
               bool(re.search(r'^\*\s*.+', content, re.MULTILINE))
    
    def _has_equals_definition(self, content: str) -> bool:
        return bool(re.search(r"['\"].*['\"]\s*=\s*", content))
    
    def _parse_wikitable(self, content: str) -> List[TermEntry]:
        """Parse wikitable format - handles multi-column tables"""
        entries = []
        table_pattern = r'\{\|.*?\|\}'
        tables = re.findall(table_pattern, content, re.DOTALL)
        
        for table in tables:
            rows = re.split(r'^\|-', table, flags=re.MULTILINE)
            for row in rows[1:]:
                if not row.strip():
                    continue
                cells = self._parse_table_row(row)
                if len(cells) >= 2:
                    dutch = self._clean_cell(cells[0])
                    english = [self._clean_cell(c) for c in cells[1:] if self._clean_cell(c)]
                    if dutch and english:
                        entries.append(TermEntry(dutch=dutch, english=english))
        return entries
    
    def _parse_table_row(self, row: str) -> List[str]:
        """Parse a wikitable row into cells"""
        cells = []
        # Remove colspan markers but keep the content
        row = re.sub(r'colspan\s*=\s*["\']?\d+["\']?\s*\|', '', row)
        lines = row.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('|') and not line.startswith('|}'):
                cell_content = line[1:].strip()
                # Handle inline || separators
                if '||' in cell_content:
                    cells.extend([c.strip() for c in cell_content.split('||')])
                else:
                    cells.append(cell_content)
        return cells
    
    def _clean_cell(self, cell: str) -> str:
        """Clean a table cell value"""
        cell = cell.strip()
        # Remove bold markers
        cell = re.sub(r"'''(.+?)'''", r'\1', cell)
        # Remove wiki links but keep text
        cell = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', cell)
        cell = re.sub(r'\[\[([^\]]+)\]\]', r'\1', cell)
        # Remove reference tags
        cell = re.sub(r'<ref[^>]*>.*?</ref>', '', cell, flags=re.DOTALL)
        cell = re.sub(r'<ref[^>]*/>', '', cell)
        return cell.strip()
    
    def _parse_sections(self, content: str) -> List[TermEntry]:
        """Parse == Dutch == / == English == section format"""
        entries = []
        dutch_match = re.search(r'==\s*(Dutch|Nederlands)\s*==\s*(.*?)(?===|$)', 
                               content, re.DOTALL | re.IGNORECASE)
        english_match = re.search(r'==\s*(English)\s*==\s*(.*?)(?===|$)', 
                                 content, re.DOTALL | re.IGNORECASE)
        
        dutch_terms = []
        english_terms = []
        
        if dutch_match:
            dutch_terms = self._extract_bullet_terms(dutch_match.group(2))
        if english_match:
            english_terms = self._extract_bullet_terms(english_match.group(2))
        
        if dutch_terms and english_terms:
            entries.append(TermEntry(dutch='; '.join(dutch_terms), english=english_terms))
        elif dutch_terms:
            entries.append(TermEntry(dutch='; '.join(dutch_terms), english=['[not found]']))
            self.warnings.append("No English section found")
        return entries
    
    def _extract_bullet_terms(self, section: str) -> List[str]:
        """Extract terms from bullet point lists"""
        terms = []
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                term = line[1:].strip()
                # Remove parenthetical notes at end
                term = re.sub(r'\([^)]+\)\s*$', '', term).strip()
                if term:
                    terms.append(self._clean_cell(term))
        return terms
    
    def _parse_bold_format(self, content: str) -> List[TermEntry]:
        """Parse '''Dutch''': ... / '''English''': ... format"""
        entries = []
        dutch_match = re.search(r"'''(Dutch|Nederlands)'''[:\s]*(.+?)(?='''|$)", 
                               content, re.IGNORECASE | re.DOTALL)
        english_match = re.search(r"'''English'''[:\s]*(.+?)(?='''|\n\n|$)", 
                                 content, re.IGNORECASE | re.DOTALL)
        
        if dutch_match and english_match:
            dutch = self._clean_cell(dutch_match.group(2).strip())
            english = self._clean_cell(english_match.group(1).strip())
            dutch_terms = [d.strip() for d in dutch.split(';')]
            english_terms = [e.strip() for e in english.split(';')]
            entries.append(TermEntry(dutch='; '.join(dutch_terms), english=english_terms))
        
        # Also extract context if present
        context_match = re.search(r"'''Context'''[:\s]*(.+?)(?='''|\n\n|$)", 
                                 content, re.IGNORECASE)
        if context_match and entries:
            entries[0].context = context_match.group(1).strip()
        return entries
    
    def _parse_bullet_definitions(self, content: str, title: str) -> List[TermEntry]:
        """Parse bullet point definitions - various formats"""
        entries = []
        
        # First check for '''term''' followed by bullet translations
        bold_match = re.search(r"^'''([^']+)'''", content, re.MULTILINE)
        if bold_match:
            dutch_term = bold_match.group(1).strip()
            # Get bullet items after the bold term
            bullet_items = self._extract_bullet_terms(content)
            if bullet_items:
                entries.append(TermEntry(dutch=dutch_term, english=bullet_items))
                return entries
        
        # Check for * dutch = english or * dutch: english format
        pattern = r'^\*\s*(.+?)\s*[=:]\s*(.+)$'
        for line in content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                entries.append(TermEntry(
                    dutch=self._clean_cell(match.group(1)), 
                    english=[self._clean_cell(match.group(2))]
                ))
        
        # If no matches but we have bullets, treat title as Dutch, bullets as English
        if not entries:
            bullet_items = self._extract_bullet_terms(content)
            if bullet_items:
                entries.append(TermEntry(dutch=title, english=bullet_items))
        return entries
    
    def _parse_equals_definition(self, content: str, title: str) -> List[TermEntry]:
        """Parse 'term' = definition format"""
        entries = []
        pattern = r"['\"]([^'\"]+)['\"]\s*=\s*(.+?)(?=\[\[Category|\{\{|$)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            dutch = match.group(1).strip()
            english = match.group(2).strip()
            english = re.sub(r'\[\[Category.*', '', english)
            english = re.sub(r'\{\{.*', '', english)
            english = english.strip()
            if '/' in english:
                entries.append(TermEntry(dutch=dutch, english=[e.strip() for e in english.split('/')]))
            else:
                entries.append(TermEntry(dutch=dutch, english=[english]))
        return entries
    
    def _parse_freeform(self, content: str, title: str) -> List[TermEntry]:
        """Last resort - try to extract any term/translation pairs"""
        entries = []
        clean = re.sub(r'\[\[Category:[^\]]+\]\]', '', content)
        clean = re.sub(r'\{\{[^}]+\}\}', '', clean)
        clean = re.sub(r'__[A-Z]+__', '', clean)
        clean = clean.strip()
        
        if not clean:
            self.warnings.append("Page has no parseable content")
            return entries
        
        for line in clean.split('\n'):
            line = line.strip()
            if not line or line.startswith('==') or line.startswith('{|') or line.startswith('|'):
                continue
            for sep in [':', '=']:
                if sep in line:
                    parts = line.split(sep, 1)
                    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                        entries.append(TermEntry(
                            dutch=self._clean_cell(parts[0]), 
                            english=[self._clean_cell(parts[1])]
                        ))
                        break
        
        if not entries:
            self.warnings.append("Could not parse freeform content - using title as Dutch term")
            entries.append(TermEntry(dutch=title, english=['[content not parseable - see raw text]']))
        return entries
    
    def _extract_categories(self, content: str) -> List[str]:
        """Extract category names from wiki content"""
        return re.findall(r'\[\[Category:([^\]|]+)', content)
    
    def _extract_external_links(self, content: str) -> List[str]:
        """Extract external URLs from wiki content"""
        urls = []
        urls.extend(re.findall(r'https?://[^\s\]\|<]+', content))
        urls.extend(re.findall(r'\[(https?://[^\s\]]+)', content))
        return list(set(urls))


def export_parsed_page(page: ParsedPage) -> Dict[str, Any]:
    """Convert ParsedPage to JSON-serializable dict"""
    return {
        'title': page.title,
        'type': page.page_type.value,
        'entries': [
            {
                'dutch': e.dutch, 
                'english': e.english, 
                'context': e.context, 
                'notes': e.notes, 
                'source': e.source
            } 
            for e in page.entries
        ],
        'categories': page.categories,
        'external_links': page.external_links,
        'metadata': page.metadata,
        'warnings': page.parse_warnings,
        'entry_count': len(page.entries)
    }


# Test the parser
if __name__ == '__main__':
    import requests
    
    parser = WikiParser()
    
    # Test pages with different formats
    test_pages = [
        'aan de hand van',           # Bullet list format
        'aanbesteder',               # Section format (== Dutch ==)
        'aankleuring',               # Bold format ('''Dutch''':)
        'ABR-formulier',             # Equals format ('term' = )
        'Aanlooptijd',               # Freeform/notes
        'grenswaarde',               # Section with complex content
        '1,016 Dutch-English technical terms',  # Wikitable
        'Banking glossary (165 Dutch-English terms)',  # Multi-column table
    ]
    
    url = 'https://superlookup.wiki/w/api.php'
    
    for title in test_pages:
        params = {
            'action': 'query',
            'prop': 'revisions',
            'titles': title,
            'rvprop': 'content',
            'rvslots': 'main',
            'format': 'json'
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        
        for page_id, page_data in data['query']['pages'].items():
            if 'revisions' in page_data:
                content = page_data['revisions'][0]['slots']['main']['*']
                
                result = parser.parse(title, content)
                
                print('='*60)
                print(f"PAGE: {title}")
                print(f"TYPE: {result.page_type.value}")
                print(f"FORMAT: {result.metadata.get('format', 'unknown')}")
                print(f"ENTRIES: {len(result.entries)}")
                print(f"CATEGORIES: {result.categories}")
                if result.parse_warnings:
                    print(f"WARNINGS: {result.parse_warnings}")
                print()
                
                # Show first few entries
                for i, entry in enumerate(result.entries[:3]):
                    print(f"  [{i+1}] NL: {entry.dutch}")
                    print(f"      EN: {entry.english}")
                    if entry.context:
                        print(f"      Context: {entry.context}")
                    print()
                    
                if len(result.entries) > 3:
                    print(f"  ... and {len(result.entries) - 3} more entries")
                print()
