"""Layout analysis for detecting paper sections from parsed PDF."""
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter

from app.core.pdf_parser.pymupdf_parser import ParsedDocument, TextBlock


# Common section heading patterns (more comprehensive)
SECTION_PATTERNS = {
    "abstract": [
        r"^abstract\s*$",
        r"^摘\s*要\s*$",
        r"^summary\s*$",
    ],
    "introduction": [
        r"^(?:[\d.]+\s*)?introduction\s*$",
        r"^(?:[\d.]+\s*)?引\s*言\s*$",
        r"^(?:[\d.]+\s*)?绪\s*论\s*$",
        r"^(?:[\d.]+\s*)?overview\s*$",
    ],
    "related_work": [
        r"^(?:[\d.]+\s*)?related\s+work[s]?\s*$",
        r"^(?:[\d.]+\s*)?background\s*$",
        r"^(?:[\d.]+\s*)?background\s+and\s+related\s+work\s*$",
        r"^(?:[\d.]+\s*)?literature\s+review\s*$",
        r"^(?:[\d.]+\s*)?previous\s+work\s*$",
        r"^(?:[\d.]+\s*)?prior\s+work\s*$",
        r"^(?:[\d.]+\s*)?相关工作\s*$",
        r"^(?:[\d.]+\s*)?研究背景\s*$",
    ],
    "methods": [
        r"^(?:[\d.]+\s*)?method(?:s|ology)?\s*$",
        r"^(?:[\d.]+\s*)?approach\s*$",
        r"^(?:[\d.]+\s*)?(?:proposed\s+)?(?:method|framework|model|system|architecture)\s*$",
        r"^(?:[\d.]+\s*)?(?:our\s+)?(?:method|approach|framework|model)\s*$",
        r"^(?:[\d.]+\s*)?technical\s+approach\s*$",
        r"^(?:[\d.]+\s*)?problem\s+(?:formulation|definition|setup)\s*$",
        r"^(?:[\d.]+\s*)?方法\s*$",
        r"^(?:[\d.]+\s*)?模型\s*$",
    ],
    "experiments": [
        r"^(?:[\d.]+\s*)?experiments?\s*$",
        r"^(?:[\d.]+\s*)?experimental\s+(?:setup|results?|settings?|evaluation)\s*$",
        r"^(?:[\d.]+\s*)?evaluation\s*$",
        r"^(?:[\d.]+\s*)?empirical\s+(?:study|evaluation|results?)\s*$",
        r"^(?:[\d.]+\s*)?实验\s*$",
        r"^(?:[\d.]+\s*)?实验设置\s*$",
    ],
    "results": [
        r"^(?:[\d.]+\s*)?results?\s*$",
        r"^(?:[\d.]+\s*)?results?\s+and\s+(?:discussion|analysis)\s*$",
        r"^(?:[\d.]+\s*)?main\s+results?\s*$",
        r"^(?:[\d.]+\s*)?findings?\s*$",
        r"^(?:[\d.]+\s*)?结果\s*$",
        r"^(?:[\d.]+\s*)?实验结果\s*$",
    ],
    "discussion": [
        r"^(?:[\d.]+\s*)?discussion\s*$",
        r"^(?:[\d.]+\s*)?analysis\s*$",
        r"^(?:[\d.]+\s*)?discussion\s+and\s+(?:analysis|future\s+work)\s*$",
        r"^(?:[\d.]+\s*)?ablation\s+stud(?:y|ies)\s*$",
        r"^(?:[\d.]+\s*)?讨论\s*$",
        r"^(?:[\d.]+\s*)?分析\s*$",
    ],
    "conclusion": [
        r"^(?:[\d.]+\s*)?conclusions?\s*$",
        r"^(?:[\d.]+\s*)?(?:conclusion|summary)\s+and\s+future\s+work\s*$",
        r"^(?:[\d.]+\s*)?concluding\s+remarks?\s*$",
        r"^(?:[\d.]+\s*)?future\s+work\s*$",
        r"^(?:[\d.]+\s*)?结论\s*$",
        r"^(?:[\d.]+\s*)?总结\s*$",
    ],
    "acknowledgments": [
        r"^acknowledgm?ents?\s*$",
        r"^致\s*谢\s*$",
    ],
    "appendix": [
        r"^(?:[\d.]+\s*)?appendix\s*(?:[a-z])?\s*$",
        r"^(?:[\d.]+\s*)?supplementary\s+(?:material|information)\s*$",
        r"^附\s*录\s*$",
    ],
    "references": [
        r"^references?\s*$",
        r"^bibliography\s*$",
        r"^参考文献\s*$",
    ],
}

def find_heading_font_size(doc: ParsedDocument) -> Tuple[float, float]:
    """Determine body and heading font sizes."""
    font_sizes = Counter()
    for page in doc.pages:
        for block in page.blocks:
            if len(block.text.strip()) > 3:
                font_sizes[round(block.font_size, 1)] += len(block.text)

    if not font_sizes:
        return 12.0, 14.0

    # Body text is the most common font size
    body_size = font_sizes.most_common(1)[0][0]

    # Heading is typically 1-4pt larger than body
    heading_candidates = [
        size for size in font_sizes
        if body_size < size <= body_size + 6
    ]

    heading_size = min(heading_candidates) if heading_candidates else body_size + 1.5
    return body_size, heading_size


def classify_section(heading_text: str) -> str:
    """Classify a heading into a section type."""
    clean = heading_text.strip().lower()
    # Remove numbering like "1.", "1.1", "II.", "A.", etc.
    clean = re.sub(r"^[\d.]+\s*", "", clean)
    clean = re.sub(r"^[ivxlcdm]+[.\s]+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^[a-z][.\s]+", "", clean, flags=re.IGNORECASE)
    clean = clean.strip()

    for section_type, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, clean, re.IGNORECASE):
                return section_type
    return "other"


def _is_numbered_heading(text: str) -> bool:
    """Check if text looks like a numbered section heading (e.g. '3.1 Method')."""
    text = text.strip()
    # Match patterns like "1.", "1.1", "1.1.1", "II.", "A."
    if re.match(r"^\d+(\.\d+)*\.?\s+\S", text) and len(text) < 150:
        return True
    if re.match(r"^[IVXLCDM]+\.\s+\S", text) and len(text) < 150:
        return True
    return False


def _merge_adjacent_blocks(blocks: List[TextBlock]) -> List[TextBlock]:
    """Merge adjacent text blocks on the same line with same font properties."""
    if not blocks:
        return blocks
    merged = [blocks[0]]
    for b in blocks[1:]:
        prev = merged[-1]
        # Same line (close y-coordinates), same font size, same bold
        if (abs(b.bbox[1] - prev.bbox[1]) < 3
                and abs(b.font_size - prev.font_size) < 0.5
                and b.is_bold == prev.is_bold
                and b.page_num == prev.page_num):
            merged[-1] = TextBlock(
                text=prev.text + " " + b.text,
                font_size=prev.font_size,
                font_name=prev.font_name,
                is_bold=prev.is_bold,
                page_num=prev.page_num,
                bbox=(prev.bbox[0], prev.bbox[1], b.bbox[2], b.bbox[3]),
            )
        else:
            merged.append(b)
    return merged


def analyze_layout(doc: ParsedDocument) -> Tuple[List[Dict], str]:
    """Analyze document layout and extract sections."""
    if not doc.pages:
        return [], "en"

    body_size, heading_size = find_heading_font_size(doc)
    full_text = "\n".join(p.raw_text for p in doc.pages)
    language = detect_language(full_text)

    sections: List[Dict] = []
    current_section: Optional[Dict] = None

    # First pass: find title (largest font on first page)
    if doc.pages:
        first_page = doc.pages[0]
        max_font = max((b.font_size for b in first_page.blocks), default=body_size)
        if max_font > heading_size:
            title_blocks = [b for b in first_page.blocks if abs(b.font_size - max_font) < 1.0]
            title_text = " ".join(b.text for b in title_blocks[:5])
            sections.append({
                "section_type": "title",
                "heading": title_text.strip(),
                "content": title_text.strip(),
                "page_start": 0,
                "page_end": 0,
            })

    # Second pass: merge blocks per page, then detect sections
    all_blocks: List[TextBlock] = []
    for page in doc.pages:
        merged = _merge_adjacent_blocks(page.blocks)
        all_blocks.extend(merged)

    for block in all_blocks:
        text = block.text.strip()
        if not text:
            continue

        # Determine if this block is a heading
        is_heading = False
        section_type = "other"

        # Check 1: Font-based heading detection (larger or bold)
        if block.font_size >= heading_size and len(text) < 200:
            if block.is_bold or block.font_size > body_size + 0.5:
                is_heading = True
                section_type = classify_section(text)

        # Check 2: Numbered heading pattern (even at body font size)
        if not is_heading and _is_numbered_heading(text):
            candidate_type = classify_section(text)
            if candidate_type != "other":
                is_heading = True
                section_type = candidate_type

        # Check 3: Bold text at body size that matches known section names
        if not is_heading and block.is_bold and len(text) < 100:
            candidate_type = classify_section(text)
            if candidate_type != "other":
                is_heading = True
                section_type = candidate_type

        # Check 4: ALL-CAPS text that matches known section names
        if not is_heading and text.isupper() and len(text) < 100:
            candidate_type = classify_section(text)
            if candidate_type != "other":
                is_heading = True
                section_type = candidate_type

        if is_heading and section_type != "other":
            # Save previous section
            if current_section and current_section.get("_collecting"):
                current_section.pop("_collecting")
                if current_section["content"].strip():
                    sections.append(current_section)

            current_section = {
                "section_type": section_type,
                "heading": text,
                "content": "",
                "page_start": block.page_num,
                "page_end": block.page_num,
                "_collecting": True,
            }
        elif is_heading and section_type == "other" and block.font_size > heading_size:
            # Subsection heading with unknown type - keep as subsection of current
            if current_section and current_section.get("_collecting"):
                current_section["content"] += f"\n### {text}\n"
                current_section["page_end"] = block.page_num
            else:
                current_section = {
                    "section_type": "other",
                    "heading": text,
                    "content": "",
                    "page_start": block.page_num,
                    "page_end": block.page_num,
                    "_collecting": True,
                }
        elif current_section and current_section.get("_collecting"):
            current_section["content"] += text + " "
            current_section["page_end"] = block.page_num

    # Save last section
    if current_section and current_section.get("_collecting"):
        current_section.pop("_collecting")
        if current_section["content"].strip():
            sections.append(current_section)

    # If very few sections detected, try text-based fallback
    named_sections = [s for s in sections if s["section_type"] not in ("title", "other")]
    if len(named_sections) < 2:
        text_sections = _extract_sections_from_text(full_text, language)
        if len(text_sections) > len(named_sections):
            # Keep title, replace the rest
            title_sections = [s for s in sections if s["section_type"] == "title"]
            sections = title_sections + text_sections

    # Try to extract abstract if not found
    has_abstract = any(s["section_type"] == "abstract" for s in sections)
    if not has_abstract:
        abstract_match = re.search(
            r"(?:abstract|摘\s*要)[:\s—\-]*(.+?)(?=\n\s*(?:[\d.]+\s*)?(?:introduction|引言|keywords|关键词|1\s))",
            full_text,
            re.IGNORECASE | re.DOTALL,
        )
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            if len(abstract_text) > 50:
                insert_pos = 1 if sections and sections[0]["section_type"] == "title" else 0
                sections.insert(insert_pos, {
                    "section_type": "abstract",
                    "heading": "Abstract",
                    "content": abstract_text,
                    "page_start": 0,
                    "page_end": 0,
                })

    # If still no sections at all, create a single full-text section
    if len(sections) <= 1:
        sections.append({
            "section_type": "other",
            "heading": "Full Text",
            "content": full_text,
            "page_start": 0,
            "page_end": doc.page_count - 1,
        })

    return sections, language


def _extract_sections_from_text(full_text: str, language: str) -> List[Dict]:
    """Fallback: extract sections by scanning raw text for heading patterns."""
    lines = full_text.split("\n")
    sections: List[Dict] = []
    current: Optional[Dict] = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                current["content"] += "\n"
            continue

        # Check if line looks like a section heading
        section_type = classify_section(stripped)

        # Also check numbered headings like "1 Introduction" or "3. Methods"
        if section_type == "other" and re.match(r"^\d+(\.\d+)*\.?\s+\S", stripped):
            after_num = re.sub(r"^\d+(\.\d+)*\.?\s+", "", stripped)
            section_type = classify_section(after_num)

        is_heading = (
            section_type != "other"
            and len(stripped) < 100
        )

        if is_heading:
            if current and current["content"].strip():
                sections.append(current)
            current = {
                "section_type": section_type,
                "heading": stripped,
                "content": "",
                "page_start": 0,
                "page_end": 0,
            }
        elif current:
            current["content"] += stripped + " "

    if current and current["content"].strip():
        sections.append(current)

    return sections


def detect_language(text: str) -> str:
    """Detect if text is primarily Chinese or English."""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total_chars = len(text.strip())
    if total_chars == 0:
        return "en"
    if chinese_chars / total_chars > 0.3:
        return "zh"
    return "en"
