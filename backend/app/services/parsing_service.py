"""Paper parsing service - orchestrates the full PDF parsing pipeline."""
import uuid
from typing import Optional

from app.models.paper import Paper
from app.models.analysis import PaperSection, PaperEntity, PaperReference, PaperTable
from app.core.pdf_parser.pymupdf_parser import parse_pdf, extract_tables_from_pdf
from app.core.pdf_parser.layout_analyzer import analyze_layout, detect_language
from app.core.pdf_parser.reference_parser import parse_references
from app.tasks.worker import update_task_progress, complete_task, fail_task, get_new_db


def run_parsing_pipeline(paper_id: str, task_id: str):
    """Run the full parsing pipeline for a paper. Runs in a thread pool."""
    db = get_new_db()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            fail_task(db, task_id, f"Paper not found: {paper_id}")
            return

        paper.parsing_status = "parsing"
        db.commit()

        # Step 1: Parse PDF
        update_task_progress(db, task_id, 0.1, "Parsing PDF structure...")
        parsed_doc = parse_pdf(paper.pdf_path)
        paper.page_count = parsed_doc.page_count
        db.commit()

        # Step 2: Analyze layout and detect sections
        update_task_progress(db, task_id, 0.3, "Analyzing document layout...")
        result = analyze_layout(parsed_doc)
        if isinstance(result, tuple):
            sections_data, language = result
        else:
            sections_data = result
            full_text = "\n".join(p.raw_text for p in parsed_doc.pages)
            language = detect_language(full_text)

        paper.language = language

        # Extract title and abstract from sections
        for sec in sections_data:
            if sec["section_type"] == "title" and sec["content"]:
                paper.title = sec["content"][:500]
            if sec["section_type"] == "abstract" and sec["content"]:
                paper.abstract = sec["content"][:5000]
        db.commit()

        # Step 3: Store sections
        update_task_progress(db, task_id, 0.5, "Storing parsed sections...")
        for i, sec_data in enumerate(sections_data):
            section = PaperSection(
                id=str(uuid.uuid4()),
                paper_id=paper_id,
                section_type=sec_data["section_type"],
                heading=sec_data.get("heading", ""),
                content=sec_data.get("content", ""),
                page_start=sec_data.get("page_start", 0),
                page_end=sec_data.get("page_end", 0),
                order=i,
            )
            db.add(section)
        db.commit()

        # Step 4: Extract tables
        update_task_progress(db, task_id, 0.7, "Extracting tables...")
        try:
            tables_data = extract_tables_from_pdf(paper.pdf_path)
            for tbl in tables_data:
                table = PaperTable(
                    id=str(uuid.uuid4()),
                    paper_id=paper_id,
                    caption=tbl.get("caption", ""),
                    headers=tbl.get("headers", []),
                    rows=tbl.get("rows", []),
                    page=tbl.get("page", 0),
                )
                db.add(table)
            db.commit()
        except Exception as e:
            print(f"Table extraction warning: {e}")

        # Step 5: Parse references
        update_task_progress(db, task_id, 0.85, "Parsing references...")
        ref_sections = [s for s in sections_data if s["section_type"] == "references"]
        if ref_sections:
            refs_data = parse_references(ref_sections[0]["content"])
            for ref_data in refs_data:
                ref = PaperReference(
                    id=str(uuid.uuid4()),
                    paper_id=paper_id,
                    raw_text=ref_data.get("raw_text", ""),
                    title=ref_data.get("title"),
                    authors=ref_data.get("authors", []),
                    year=ref_data.get("year"),
                    venue=ref_data.get("venue"),
                    doi=ref_data.get("doi"),
                    order=ref_data.get("order", 0),
                )
                db.add(ref)
            db.commit()

        # Done
        paper.parsing_status = "completed"
        db.commit()
        complete_task(db, task_id)

    except Exception as e:
        try:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                paper.parsing_status = "failed"
                db.commit()
            fail_task(db, task_id, str(e))
        except Exception:
            pass
        import traceback
        traceback.print_exc()
    finally:
        db.close()
