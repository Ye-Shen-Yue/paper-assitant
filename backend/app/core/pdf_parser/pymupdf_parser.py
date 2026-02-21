"""Primary PDF parser using PyMuPDF."""
import re
import fitz  # PyMuPDF
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TextBlock:
    text: str
    font_size: float
    font_name: str
    is_bold: bool
    page_num: int
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1


@dataclass
class ParsedPage:
    page_num: int
    width: float
    height: float
    blocks: List[TextBlock] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ParsedDocument:
    pages: List[ParsedPage] = field(default_factory=list)
    page_count: int = 0
    metadata: Dict = field(default_factory=dict)


def parse_pdf(file_path: str) -> ParsedDocument:
    """Parse a PDF file and extract structured text with font information."""
    doc = fitz.open(file_path)
    parsed = ParsedDocument(page_count=len(doc), metadata=doc.metadata or {})

    for page_num in range(len(doc)):
        page = doc[page_num]
        parsed_page = ParsedPage(
            page_num=page_num,
            width=page.rect.width,
            height=page.rect.height,
            raw_text=page.get_text("text"),
        )

        # Extract text blocks with font info
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        for block in blocks.get("blocks", []):
            if block.get("type") != 0:  # Skip image blocks
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    parsed_page.blocks.append(TextBlock(
                        text=text,
                        font_size=span.get("size", 12.0),
                        font_name=span.get("font", ""),
                        is_bold="Bold" in span.get("font", "") or "bold" in span.get("font", ""),
                        page_num=page_num,
                        bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                    ))

        parsed.pages.append(parsed_page)

    doc.close()
    return parsed


def _find_table_caption(page_text: str, table_bbox: Tuple[float, ...], table_index: int) -> str:
    """Try to find a table caption from page text near the table."""
    # Search for "Table N" patterns in the page text
    patterns = [
        r"(Table\s+\d+[.:]\s*.{5,200}?)(?:\n|$)",
        r"(表\s*\d+[.:：]\s*.{5,200}?)(?:\n|$)",
        r"(TABLE\s+\d+[.:]\s*.{5,200}?)(?:\n|$)",
    ]
    captions = []
    for pattern in patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        captions.extend(matches)

    if captions and table_index < len(captions):
        return captions[table_index].strip()
    elif captions:
        return captions[0].strip()
    return ""


def extract_tables_from_pdf(file_path: str) -> List[Dict]:
    """Extract tables from PDF using PyMuPDF with improved handling."""
    doc = fitz.open(file_path)
    tables = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text")

        # Find tables with better strategy for academic papers
        page_tables = page.find_tables(
            vertical_strategy="lines",
            horizontal_strategy="lines",
        )

        for ti, table in enumerate(page_tables):
            try:
                extracted = table.extract()
                if not extracted or len(extracted) < 2:
                    continue

                # Clean and normalize headers
                raw_headers = [str(h or "").strip() for h in extracted[0]]

                # Filter out empty columns
                non_empty_indices = [i for i, h in enumerate(raw_headers) if h]
                if not non_empty_indices:
                    continue

                headers = [raw_headers[i] for i in non_empty_indices]

                # Process rows, keeping only non-empty columns
                rows = []
                for row in extracted[1:]:
                    # Skip completely empty rows
                    if not any(row):
                        continue

                    # Extract only non-empty columns
                    clean_row = [str(row[i] or "").strip() for i in non_empty_indices]

                    # Skip rows that are all empty or separators
                    if any(c for c in clean_row if c and c not in ['—', '-', '']):
                        rows.append(clean_row)

                # Skip tables with no data rows
                if not rows:
                    continue

                # Find caption
                caption = _find_table_caption(page_text, table.bbox, ti)

                # Clean up caption - remove "Table X" prefix if present
                caption = _clean_caption(caption)

                tables.append({
                    "page": page_num + 1,  # 1-indexed page numbers
                    "headers": headers,
                    "rows": rows,
                    "caption": caption,
                })
            except Exception as e:
                print(f"Warning: Failed to extract table {ti} on page {page_num}: {e}")
                continue

    doc.close()
    return tables


def _clean_caption(caption: str) -> str:
    """Clean up table caption by removing redundant 'Table X' prefix."""
    if not caption:
        return ""

    # Remove common table prefixes
    patterns = [
        r'^Table\s+\d+[.:]?\s*',
        r'^TABLE\s+\d+[.:]?\s*',
        r'^Tab\.?\s+\d+[.:]?\s*',
        r'^表\s*\d+[.:：]?\s*',
    ]

    cleaned = caption
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    return cleaned.strip()
