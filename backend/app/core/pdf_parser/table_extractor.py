"""Table extraction from PDF."""
from typing import List, Dict
import pdfplumber


def extract_tables_pdfplumber(file_path: str) -> List[Dict]:
    """Extract tables using pdfplumber (more robust for complex tables)."""
    tables = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for table in page_tables:
                if not table or len(table) < 2:
                    continue
                headers = [str(cell or "") for cell in table[0]]
                rows = [[str(cell or "") for cell in row] for row in table[1:]]
                tables.append({
                    "page": i,
                    "headers": headers,
                    "rows": rows,
                    "caption": "",
                })

    return tables
