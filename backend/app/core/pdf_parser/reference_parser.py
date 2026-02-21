"""Reference/bibliography parser."""
import re
from typing import List, Dict, Optional


def parse_references(text: str) -> List[Dict]:
    """Parse reference section text into structured references."""
    references = []

    # Split by common reference patterns
    # Pattern 1: [1] Author, Title...
    # Pattern 2: 1. Author, Title...
    ref_blocks = re.split(r"\n\s*(?:\[(\d+)\]|(\d+)\.\s)", text)

    # Reconstruct blocks
    current_ref = ""
    ref_num = 0
    for block in ref_blocks:
        if block is None:
            continue
        if block.strip().isdigit():
            if current_ref.strip():
                references.append(_parse_single_reference(current_ref.strip(), ref_num))
            ref_num = int(block.strip())
            current_ref = ""
        else:
            current_ref += block

    if current_ref.strip():
        references.append(_parse_single_reference(current_ref.strip(), ref_num))

    # If no structured refs found, try line-by-line
    if not references:
        lines = text.strip().split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) > 20:  # Minimum length for a reference
                references.append(_parse_single_reference(line, i + 1))

    return references


def _parse_single_reference(text: str, order: int) -> Dict:
    """Parse a single reference string."""
    ref = {
        "raw_text": text,
        "title": None,
        "authors": [],
        "year": None,
        "venue": None,
        "doi": None,
        "order": order,
    }

    # Extract year
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    if year_match:
        ref["year"] = int(year_match.group())

    # Extract DOI
    doi_match = re.search(r"(10\.\d{4,}/[^\s]+)", text)
    if doi_match:
        ref["doi"] = doi_match.group(1).rstrip(".")

    # Try to extract title (usually in quotes or after authors)
    title_match = re.search(r'["""](.+?)["""]', text)
    if title_match:
        ref["title"] = title_match.group(1)
    else:
        # Try: Authors. Title. Venue, Year.
        parts = re.split(r"\.\s+", text, maxsplit=3)
        if len(parts) >= 2:
            ref["title"] = parts[1].strip() if len(parts[1]) > 10 else None

    # Extract authors (before the year or title)
    if year_match:
        author_text = text[:year_match.start()].strip().rstrip(",.(")
    else:
        author_text = text[:50]

    # Split authors by "and", ",", "&"
    if author_text:
        authors = re.split(r"\s+and\s+|,\s*|\s*&\s*", author_text)
        ref["authors"] = [a.strip() for a in authors if a.strip() and len(a.strip()) > 1][:10]

    return ref
