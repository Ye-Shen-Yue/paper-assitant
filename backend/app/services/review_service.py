"""Review service - auto-review, controversy detection, reproducibility.

Tries LLM first, falls back to local heuristic analysis.
"""
import re
import uuid
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.paper import Paper
from app.models.analysis import PaperSection, PaperEntity, PaperReference
from app.models.task import PaperReview
from app.tasks.worker import update_task_progress, complete_task, fail_task, get_new_db


def _get_sections_text(db: Session, paper_id: str) -> str:
    sections = (
        db.query(PaperSection)
        .filter(PaperSection.paper_id == paper_id)
        .order_by(PaperSection.order)
        .all()
    )
    parts = []
    for s in sections:
        if s.section_type != "references":
            parts.append(f"## {s.heading}\n{s.content}")
    text = "\n\n".join(parts)
    return text[:15000] if len(text) > 15000 else text


def _try_llm_call(prompt: str) -> Dict:
    """Try to call LLM, return None if unavailable."""
    try:
        from app.core.llm.client import get_llm_client
        client = get_llm_client()
        return client.chat_json(prompt)
    except Exception:
        return None


def _local_review(db: Session, paper_id: str) -> Dict:
    """Generate a basic review using local heuristics."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    sections = db.query(PaperSection).filter(PaperSection.paper_id == paper_id).order_by(PaperSection.order).all()
    entities = db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id).all()
    refs = db.query(PaperReference).filter(PaperReference.paper_id == paper_id).all()

    section_types = {s.section_type for s in sections}
    entity_types = {e.entity_type for e in entities}
    full_text = " ".join(s.content or "" for s in sections).lower()
    total_len = sum(len(s.content or "") for s in sections)

    strengths = []
    weaknesses = []
    questions = []

    # Structural analysis
    if "abstract" in section_types:
        strengths.append("Paper has a clear abstract section")
    else:
        weaknesses.append("No clear abstract section detected")

    if "methods" in section_types:
        strengths.append("Dedicated methodology section present")
    else:
        weaknesses.append("No dedicated methodology section found")

    if "experiments" in section_types or "results" in section_types:
        strengths.append("Experimental evaluation section present")
    else:
        weaknesses.append("No experimental evaluation section detected")

    if "related_work" in section_types:
        strengths.append("Related work section provides context")

    # Reference analysis
    if len(refs) > 30:
        strengths.append(f"Comprehensive references ({len(refs)} citations)")
    elif len(refs) > 15:
        strengths.append(f"Adequate references ({len(refs)} citations)")
    elif len(refs) > 0:
        weaknesses.append(f"Limited references ({len(refs)} citations)")
    else:
        weaknesses.append("No references detected")

    # Entity-based analysis
    if "dataset" in entity_types:
        datasets = [e.text for e in entities if e.entity_type == "dataset"]
        strengths.append(f"Evaluates on datasets: {', '.join(datasets[:3])}")
    else:
        weaknesses.append("No standard benchmark datasets detected")
        questions.append("What datasets were used for evaluation?")

    if "metric" in entity_types:
        metrics = [e.text for e in entities if e.entity_type == "metric"]
        strengths.append(f"Uses evaluation metrics: {', '.join(metrics[:3])}")

    if "baseline" in entity_types:
        baselines = [e.text for e in entities if e.entity_type == "baseline"]
        strengths.append(f"Compares with baselines: {', '.join(baselines[:3])}")
    else:
        questions.append("What baselines were compared against?")

    # Reproducibility
    if re.search(r"github\.com|code\s+(?:is\s+)?available|open[-\s]?source", full_text):
        strengths.append("Code availability mentioned")
    else:
        weaknesses.append("No code or reproducibility resources mentioned")

    # Content depth
    if total_len > 30000:
        strengths.append("Thorough and detailed paper")
    elif total_len < 5000:
        weaknesses.append("Paper content appears brief")

    # Summary
    summary = f"This paper presents {paper.title}. " if paper else "Paper analysis: "
    summary += f"The paper contains {len(sections)} sections with {len(entities)} identified entities and {len(refs)} references. "
    summary += "This is an automated structural review based on local analysis."

    # Recommendation based on balance
    score = len(strengths) - len(weaknesses)
    if score >= 3:
        recommendation = "weak_accept"
    elif score >= 1:
        recommendation = "borderline"
    elif score >= -1:
        recommendation = "borderline"
    else:
        recommendation = "weak_reject"

    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "questions_to_authors": questions,
        "overall_recommendation": recommendation,
        "confidence": 2.0,
    }


def _local_reproducibility_check(db: Session, paper_id: str) -> Dict:
    """Check reproducibility using local heuristics."""
    sections = db.query(PaperSection).filter(PaperSection.paper_id == paper_id).all()
    entities = db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id).all()
    full_text = " ".join(s.content or "" for s in sections).lower()

    checklist = []
    score_sum = 0.0
    total = 0

    checks = [
        ("Code availability", r"github\.com|gitlab\.com|code\s+(?:is\s+)?available|open[-\s]?source|repository"),
        ("Hyperparameters reported", r"hyperparameter|learning\s+rate|batch\s+size|epoch|optimizer"),
        ("Dataset described", r"dataset|training\s+(?:data|set)|test\s+(?:data|set)|validation"),
        ("Hardware/environment specified", r"GPU|TPU|NVIDIA|CUDA|hardware|environment|machine"),
        ("Random seeds mentioned", r"random\s+seed|seed\s*=|reproducib"),
        ("Training details provided", r"training\s+(?:detail|procedure|process)|fine[-\s]?tun"),
        ("Evaluation protocol clear", r"evaluation\s+(?:protocol|metric|procedure)|cross[-\s]?validation|test\s+split"),
    ]

    for criterion, pattern in checks:
        total += 1
        if re.search(pattern, full_text):
            checklist.append({"criterion": criterion, "status": "met", "details": "Found in paper text"})
            score_sum += 1.0
        else:
            checklist.append({"criterion": criterion, "status": "not_met", "details": "Not found in paper text"})

    overall_score = score_sum / total if total > 0 else 0.0

    return {
        "checklist": checklist,
        "overall_score": overall_score,
    }


def _local_controversy(db: Session, paper_id: str) -> Dict:
    """Detect potential controversies using local heuristics."""
    sections = db.query(PaperSection).filter(PaperSection.paper_id == paper_id).all()
    full_text = " ".join(s.content or "" for s in sections).lower()

    claims = []
    # Look for strong claims
    claim_patterns = [
        r"(?:we\s+(?:achieve|obtain|demonstrate|show)\s+)(?:state[-\s]?of[-\s]?the[-\s]?art|sota|best|superior)(.{5,100}?)(?:\.|$)",
        r"(?:significantly|substantially|dramatically)\s+(?:outperform|improve|better)(.{5,100}?)(?:\.|$)",
        r"(?:first|novel|unique)\s+(?:to\s+)?(?:propose|introduce|present)(.{5,100}?)(?:\.|$)",
    ]

    for pattern in claim_patterns:
        for m in re.finditer(pattern, full_text, re.IGNORECASE):
            claim_text = m.group(0).strip().capitalize()
            if len(claim_text) > 20:
                claims.append({
                    "claim": claim_text[:200],
                    "consistency_score": 0.7,
                    "assessment": "Strong claim detected - verify with experimental evidence",
                })

    return {
        "claims": claims[:5],
        "overall_consistency": 0.7 if claims else 1.0,
    }


def run_review_generation(
    paper_id: str, task_id: str,
    language: str = "en", venue_type: str = "AI/ML",
):
    """Generate a full auto-review. Tries LLM, falls back to local heuristics."""
    db = get_new_db()
    try:
        update_task_progress(db, task_id, 0.05, "Preparing review...")

        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            fail_task(db, task_id, "Paper not found")
            return

        sections_text = _get_sections_text(db, paper_id)

        # Try LLM-based review
        review_result = None
        controversy_result = None
        repro_result = None

        try:
            from app.core.llm.prompts import (
                AUTO_REVIEW_PROMPT,
                CONTROVERSY_DETECTION_PROMPT,
                REPRODUCIBILITY_CHECK_PROMPT,
            )

            update_task_progress(db, task_id, 0.1, "Generating review...")
            review_prompt = AUTO_REVIEW_PROMPT.format(
                venue_type=venue_type, title=paper.title,
                abstract=paper.abstract or "", sections_text=sections_text, language=language,
            )
            review_result = _try_llm_call(review_prompt)

            if review_result:
                update_task_progress(db, task_id, 0.4, "Detecting controversies...")
                controversy_prompt = CONTROVERSY_DETECTION_PROMPT.format(
                    title=paper.title, sections_text=sections_text,
                )
                controversy_result = _try_llm_call(controversy_prompt)

                update_task_progress(db, task_id, 0.7, "Checking reproducibility...")
                repro_prompt = REPRODUCIBILITY_CHECK_PROMPT.format(
                    title=paper.title, sections_text=sections_text,
                )
                repro_result = _try_llm_call(repro_prompt)
        except Exception:
            pass

        # Fall back to local analysis
        if not review_result:
            update_task_progress(db, task_id, 0.3, "Using local analysis...")
            review_result = _local_review(db, paper_id)

        if not controversy_result:
            controversy_result = _local_controversy(db, paper_id)

        if not repro_result:
            repro_result = _local_reproducibility_check(db, paper_id)

        # Store results
        update_task_progress(db, task_id, 0.9, "Saving review...")
        db.query(PaperReview).filter(PaperReview.paper_id == paper_id).delete()

        review = PaperReview(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            summary=review_result.get("summary", ""),
            strengths=review_result.get("strengths", []),
            weaknesses=review_result.get("weaknesses", []),
            questions_to_authors=review_result.get("questions_to_authors", []),
            overall_recommendation=review_result.get("overall_recommendation", "borderline"),
            confidence=float(review_result.get("confidence", 3.0)),
            controversy_claims=controversy_result.get("claims", []),
            reproducibility_checklist=repro_result.get("checklist", []),
            reproducibility_score=float(repro_result.get("overall_score", 0.0)),
        )
        db.add(review)
        db.commit()

        complete_task(db, task_id)
    except Exception as e:
        fail_task(db, task_id, str(e))
        import traceback; traceback.print_exc()
    finally:
        db.close()
