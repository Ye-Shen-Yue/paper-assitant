"""Fallback PDF parser using pdfplumber."""
import pdfplumber
from typing import List, Dict
from app.core.pdf_parser.pymupdf_parser import ParsedDocument, ParsedPage, TextBlock


def parse_pdf_fallback(file_path: str) -> ParsedDocument:
    """Parse PDF using pdfplumber as fallback."""
    parsed = ParsedDocument()

    with pdfplumber.open(file_path) as pdf:
        parsed.page_count = len(pdf.pages)
        parsed.metadata = pdf.metadata or {}

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            parsed_page = ParsedPage(
                page_num=i,
                width=page.width,
                height=page.height,
                raw_text=text,
            )

            # pdfplumber doesn't give font info easily, create basic blocks
            for line in text.split("\n"):
                if line.strip():
                    parsed_page.blocks.append(TextBlock(
                        text=line.strip(),
                        font_size=12.0,
                        font_name="",
                        is_bold=False,
                        page_num=i,
                        bbox=(0, 0, 0, 0),
                    ))

            parsed.pages.append(parsed_page)

    return parsed
