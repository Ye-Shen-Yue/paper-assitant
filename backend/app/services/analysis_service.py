"""Analysis service - paper profiling, contributions, limitations.

Entity extraction and relationship extraction work fully offline.
Profiling, contributions, and limitations try LLM first, fall back to local heuristics.
"""
import re
import uuid
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.paper import Paper
from app.models.analysis import PaperSection, PaperEntity, EntityRelationship
from app.models.task import PaperProfile, PaperContribution, PaperLimitation
from app.core.nlp.entity_recognizer import extract_entities
from app.core.nlp.relation_extractor import extract_relationships
from app.tasks.worker import update_task_progress, complete_task, fail_task, get_new_db


def _get_sections_text(db: Session, paper_id: str) -> str:
    """Get concatenated sections text."""
    sections = (
        db.query(PaperSection)
        .filter(PaperSection.paper_id == paper_id)
        .order_by(PaperSection.order)
        .all()
    )
    parts = []
    for s in sections:
        if s.section_type not in ("title", "references"):
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


def run_entity_extraction(paper_id: str, task_id: str):
    """Extract entities and relationships from all sections."""
    db = get_new_db()
    try:
        update_task_progress(db, task_id, 0.1, "Extracting entities...")

        sections = (
            db.query(PaperSection)
            .filter(PaperSection.paper_id == paper_id)
            .order_by(PaperSection.order)
            .all()
        )

        all_entities = []
        for i, section in enumerate(sections):
            if section.section_type in ("title", "references"):
                continue
            progress = 0.1 + (0.5 * i / max(len(sections), 1))
            update_task_progress(db, task_id, progress, f"Extracting entities from {section.heading}...")

            entities = extract_entities(section.section_type, section.content)
            for ent in entities:
                entity = PaperEntity(
                    id=str(uuid.uuid4()),
                    paper_id=paper_id,
                    section_id=section.id,
                    text=ent["text"],
                    entity_type=ent["entity_type"],
                    confidence=ent["confidence"],
                )
                db.add(entity)
                all_entities.append({
                    "id": entity.id,
                    "text": ent["text"],
                    "entity_type": ent["entity_type"],
                })
        db.commit()

        # Extract relationships
        update_task_progress(db, task_id, 0.7, "Extracting relationships...")
        context = _get_sections_text(db, paper_id)
        rels = extract_relationships(all_entities, context)

        entity_map = {e["text"]: e["id"] for e in all_entities}
        for rel in rels:
            source_id = entity_map.get(rel["source"])
            target_id = entity_map.get(rel["target"])
            if source_id and target_id:
                db.add(EntityRelationship(
                    id=str(uuid.uuid4()),
                    paper_id=paper_id,
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relation_type=rel["relation_type"],
                    description=rel["description"],
                    confidence=rel["confidence"],
                ))
        db.commit()
        complete_task(db, task_id)
    except Exception as e:
        fail_task(db, task_id, str(e))
        import traceback; traceback.print_exc()
    finally:
        db.close()


def _local_paper_profiling(db: Session, paper_id: str) -> Dict:
    """Generate paper profile using local heuristics (no LLM)."""
    from app.services.visualization_service import _estimate_radar_scores
    scores = _estimate_radar_scores(db, paper_id)
    dim_names = ["innovation", "method_complexity", "experiment_sufficiency", "reproducibility", "impact_prediction"]
    dim_labels = ["Innovation", "Method Complexity", "Experiment Sufficiency", "Reproducibility", "Impact Prediction"]
    dimensions = []
    for i, name in enumerate(dim_names):
        dimensions.append({
            "dimension": name,
            "score": scores[i],
            "reasoning": f"Estimated from paper structure and extracted entities ({dim_labels[i]})",
        })
    return {
        "overall_assessment": "Profile generated using local heuristics (no LLM). Scores are estimated from paper structure, entity counts, and content analysis.",
        "dimensions": dimensions,
    }


def run_paper_profiling(paper_id: str, task_id: str):
    """Generate 5-dimension paper profile. Tries LLM, falls back to local."""
    db = get_new_db()
    try:
        update_task_progress(db, task_id, 0.1, "Generating paper profile...")

        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            fail_task(db, task_id, "Paper not found")
            return

        # Try LLM first
        result = None
        try:
            from app.core.llm.prompts import PAPER_PROFILE_PROMPT
            sections_text = _get_sections_text(db, paper_id)
            prompt = PAPER_PROFILE_PROMPT.format(
                title=paper.title, abstract=paper.abstract or "", sections_text=sections_text,
            )
            update_task_progress(db, task_id, 0.3, "Calling LLM for profiling...")
            result = _try_llm_call(prompt)
        except Exception:
            pass

        if not result:
            update_task_progress(db, task_id, 0.5, "Using local analysis...")
            result = _local_paper_profiling(db, paper_id)

        dimensions = result.get("dimensions", [])
        db.query(PaperProfile).filter(PaperProfile.paper_id == paper_id).delete()

        profile = PaperProfile(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            overall_assessment=result.get("overall_assessment", ""),
            dimensions_detail=dimensions,
        )

        for dim in dimensions:
            name = dim.get("dimension", "").lower()
            score = float(dim.get("score", 0))
            if "innovation" in name:
                profile.innovation_score = score
            elif "method" in name or "complexity" in name:
                profile.method_complexity_score = score
            elif "experiment" in name:
                profile.experiment_sufficiency_score = score
            elif "reproduc" in name:
                profile.reproducibility_score = score
            elif "impact" in name:
                profile.impact_prediction_score = score

        db.add(profile)
        db.commit()
        complete_task(db, task_id)
    except Exception as e:
        fail_task(db, task_id, str(e))
        import traceback; traceback.print_exc()
    finally:
        db.close()


def _local_contribution_extraction(db: Session, paper_id: str) -> List[Dict]:
    """Extract contributions using local heuristics."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    sections = db.query(PaperSection).filter(PaperSection.paper_id == paper_id).order_by(PaperSection.order).all()
    entities = db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id).all()

    contributions = []
    full_text = " ".join(s.content or "" for s in sections).lower()

    # Check for contribution patterns in abstract/introduction
    contrib_patterns = [
        r"(?:we\s+(?:propose|present|introduce|develop|design))\s+(.{10,150}?)(?:\.|,)",
        r"(?:our\s+(?:main\s+)?contributions?\s+(?:are|include)[:\s]+)(.{10,200}?)(?:\.|$)",
        r"(?:this\s+(?:paper|work)\s+(?:proposes?|presents?|introduces?))\s+(.{10,150}?)(?:\.|,)",
        r"(?:the\s+key\s+(?:contribution|novelty)\s+(?:of\s+this\s+(?:paper|work)\s+)?is)\s+(.{10,150}?)(?:\.|,)",
    ]

    for pattern in contrib_patterns:
        for m in re.finditer(pattern, full_text, re.IGNORECASE):
            desc = m.group(1).strip()
            if len(desc) > 15:
                contributions.append({
                    "level": "technical",
                    "description": desc.capitalize(),
                    "evidence": [],
                    "significance": "moderate",
                })

    # Add contributions from innovation entities
    innovation_entities = [e for e in entities if e.entity_type == "innovation"]
    for ent in innovation_entities[:3]:
        contributions.append({
            "level": "technical",
            "description": f"Novel approach: {ent.text}",
            "evidence": [],
            "significance": "moderate",
        })

    # Add method-based contributions
    method_entities = [e for e in entities if e.entity_type == "method"]
    if method_entities and not contributions:
        contributions.append({
            "level": "technical",
            "description": f"Applies methods including: {', '.join(e.text for e in method_entities[:5])}",
            "evidence": [],
            "significance": "moderate",
        })

    if not contributions:
        contributions.append({
            "level": "technical",
            "description": paper.title or "Research contribution (details require LLM analysis)",
            "evidence": [],
            "significance": "moderate",
        })

    return contributions


def run_contribution_extraction(paper_id: str, task_id: str):
    """Extract paper contributions. Tries LLM, falls back to local."""
    db = get_new_db()
    try:
        update_task_progress(db, task_id, 0.1, "Extracting contributions...")

        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            fail_task(db, task_id, "Paper not found")
            return

        contribs = None
        try:
            from app.core.llm.prompts import CONTRIBUTION_EXTRACTION_PROMPT
            sections_text = _get_sections_text(db, paper_id)
            prompt = CONTRIBUTION_EXTRACTION_PROMPT.format(
                title=paper.title, abstract=paper.abstract or "", sections_text=sections_text,
            )
            update_task_progress(db, task_id, 0.4, "Calling LLM...")
            result = _try_llm_call(prompt)
            if result:
                contribs = result.get("contributions", [])
        except Exception:
            pass

        if not contribs:
            update_task_progress(db, task_id, 0.5, "Using local analysis...")
            contribs = _local_contribution_extraction(db, paper_id)

        db.query(PaperContribution).filter(PaperContribution.paper_id == paper_id).delete()
        for contrib in contribs:
            db.add(PaperContribution(
                id=str(uuid.uuid4()),
                paper_id=paper_id,
                level=contrib.get("level", "technical"),
                description=contrib.get("description", ""),
                evidence=contrib.get("evidence", []),
                significance=contrib.get("significance", "moderate"),
            ))
        db.commit()
        complete_task(db, task_id)
    except Exception as e:
        fail_task(db, task_id, str(e))
        import traceback; traceback.print_exc()
    finally:
        db.close()


def _local_limitation_identification(db: Session, paper_id: str) -> List[Dict]:
    """Identify limitations using local heuristics."""
    sections = db.query(PaperSection).filter(PaperSection.paper_id == paper_id).order_by(PaperSection.order).all()
    entities = db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id).all()

    limitations = []
    full_text = " ".join(s.content or "" for s in sections).lower()
    section_types = {s.section_type for s in sections}
    entity_types = {e.entity_type for e in entities}

    # Check for explicit limitation mentions
    lim_patterns = [
        r"(?:limitation[s]?\s+(?:of\s+)?(?:this|our)\s+(?:work|study|approach|method))[:\s]+(.{10,200}?)(?:\.|$)",
        r"(?:however|nevertheless|although|despite)[,\s]+(.{10,150}?)(?:\.|$)",
        r"(?:future\s+work\s+(?:could|should|will|may)\s+)(.{10,150}?)(?:\.|$)",
    ]

    for pattern in lim_patterns:
        for m in re.finditer(pattern, full_text, re.IGNORECASE):
            desc = m.group(1).strip()
            if len(desc) > 15:
                limitations.append({
                    "category": "methodology",
                    "description": desc.capitalize(),
                    "severity": "minor",
                    "suggestion": "",
                })

    # Structural checks
    if "dataset" not in entity_types:
        limitations.append({
            "category": "data",
            "description": "No standard benchmark datasets detected in the paper",
            "severity": "minor",
            "suggestion": "Consider evaluating on well-known benchmark datasets",
        })

    if not re.search(r"github\.com|code\s+(?:is\s+)?available|open[-\s]?source", full_text):
        limitations.append({
            "category": "reproducibility",
            "description": "No code availability or open-source repository mentioned",
            "severity": "minor",
            "suggestion": "Consider releasing source code for reproducibility",
        })

    if "experiments" not in section_types and "results" not in section_types:
        limitations.append({
            "category": "evaluation",
            "description": "No dedicated experiments or results section detected",
            "severity": "major",
            "suggestion": "Add experimental evaluation to validate the approach",
        })

    if not limitations:
        limitations.append({
            "category": "other",
            "description": "Detailed limitation analysis requires LLM. Configure QWEN_API_KEY for deeper analysis.",
            "severity": "minor",
            "suggestion": "Set a valid API key in backend/.env for comprehensive analysis",
        })

    return limitations


def run_limitation_identification(paper_id: str, task_id: str):
    """Identify paper limitations. Tries LLM, falls back to local."""
    db = get_new_db()
    try:
        update_task_progress(db, task_id, 0.1, "Identifying limitations...")

        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            fail_task(db, task_id, "Paper not found")
            return

        lims = None
        try:
            from app.core.llm.prompts import LIMITATION_IDENTIFICATION_PROMPT
            sections_text = _get_sections_text(db, paper_id)
            prompt = LIMITATION_IDENTIFICATION_PROMPT.format(
                title=paper.title, abstract=paper.abstract or "", sections_text=sections_text,
            )
            update_task_progress(db, task_id, 0.4, "Calling LLM...")
            result = _try_llm_call(prompt)
            if result:
                lims = result.get("limitations", [])
        except Exception:
            pass

        if not lims:
            update_task_progress(db, task_id, 0.5, "Using local analysis...")
            lims = _local_limitation_identification(db, paper_id)

        db.query(PaperLimitation).filter(PaperLimitation.paper_id == paper_id).delete()
        for lim in lims:
            db.add(PaperLimitation(
                id=str(uuid.uuid4()),
                paper_id=paper_id,
                category=lim.get("category", "other"),
                description=lim.get("description", ""),
                severity=lim.get("severity", "minor"),
                suggestion=lim.get("suggestion", ""),
            ))
        db.commit()
        complete_task(db, task_id)
    except Exception as e:
        fail_task(db, task_id, str(e))
        import traceback; traceback.print_exc()
    finally:
        db.close()
