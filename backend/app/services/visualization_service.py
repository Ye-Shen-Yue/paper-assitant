"""Visualization data builders - works without LLM using local heuristics."""
import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.paper import Paper
from app.models.analysis import PaperSection, PaperEntity, EntityRelationship, PaperReference
from app.models.task import PaperProfile


RELATION_LABELS = {
    "uses": "uses",
    "evaluates_on": "evaluates on",
    "improves": "improves",
    "comparative": "compared with",
    "part_of": "part of",
    "causal": "leads to",
    "co_occurrence": "related to",
}


def build_knowledge_graph(db: Session, paper_id: str) -> Dict:
    """Build knowledge graph data from entities and relationships."""
    entities = db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id).all()
    relationships = db.query(EntityRelationship).filter(EntityRelationship.paper_id == paper_id).all()

    size_map = {
        "research_problem": 3.0, "method": 2.5, "innovation": 2.5,
        "dataset": 2.0, "metric": 1.5, "baseline": 1.5,
        "tool": 1.0, "theory": 2.0,
    }

    # Deduplicate entities by text (keep highest confidence)
    dedup: Dict[str, PaperEntity] = {}
    for ent in entities:
        key = ent.text.strip().lower()
        if ent.confidence < 0.3:
            continue
        if key not in dedup or ent.confidence > dedup[key].confidence:
            dedup[key] = ent
    unique_entities = list(dedup.values())

    # Sort by importance (type weight * confidence) and limit to 40
    unique_entities.sort(
        key=lambda e: size_map.get(e.entity_type, 1.0) * e.confidence,
        reverse=True,
    )
    unique_entities = unique_entities[:40]
    valid_ids = {ent.id for ent in unique_entities}

    nodes = []
    for ent in unique_entities:
        nodes.append({
            "id": ent.id,
            "label": ent.text,
            "node_type": ent.entity_type,
            "size": size_map.get(ent.entity_type, 1.0),
            "metadata": {
                "confidence": ent.confidence,
                "section_id": ent.section_id,
            },
        })

    edges = []
    for rel in relationships:
        if rel.source_entity_id in valid_ids and rel.target_entity_id in valid_ids:
            edges.append({
                "source": rel.source_entity_id,
                "target": rel.target_entity_id,
                "relation": rel.relation_type,
                "label": RELATION_LABELS.get(rel.relation_type, rel.relation_type),
                "weight": rel.confidence,
            })

    return {"nodes": nodes, "edges": edges}


def _safe_mermaid(text: str) -> str:
    """Escape text for safe use in Mermaid labels."""
    text = text.replace('"', "'").replace("\n", " ").strip()
    text = re.sub(r'[<>{}|\\]', '', text)
    return text[:80] if len(text) > 80 else text


def _extract_method_steps(content: str, db: Session, paper_id: str) -> List[Dict]:
    """Extract method steps from section content using heuristics."""
    steps = []

    # Strategy 1: Look for numbered steps (broad patterns)
    numbered = re.findall(
        r"(?:^|\n)\s*(?:step\s+)?(?:\(?\d+[.):\s]|\d+\.\s)(.{10,200}?)(?:\.|$)",
        content, re.IGNORECASE | re.MULTILINE,
    )
    if len(numbered) >= 3:
        for i, desc in enumerate(numbered[:10]):
            steps.append({"label": desc.strip(), "order": i})
        return steps

    # Strategy 2: Look for ordinal words (First, Second, ... / Finally)
    ordinal_pattern = r"(?:^|\.\s+)((?:First|Second|Third|Fourth|Fifth|Finally|Next|Then|Subsequently|Afterwards)[,\s]+.{10,200}?)(?:\.|$)"
    ordinals = re.findall(ordinal_pattern, content, re.IGNORECASE | re.MULTILINE)
    if len(ordinals) >= 2:
        for i, desc in enumerate(ordinals[:8]):
            steps.append({"label": desc.strip()[:100], "order": i})
        return steps

    # Strategy 3: Look for subsection headings (### inserted by layout_analyzer)
    subsections = re.findall(r"###\s+(.{5,100})", content)
    if len(subsections) >= 2:
        return [{"label": s.strip(), "order": i} for i, s in enumerate(subsections)]

    # Strategy 4: Extract sentences with method action verbs
    sentences = re.split(r'(?<=[.!?])\s+', content)
    action_pattern = re.compile(
        r"\b(?:we|our|this)\b.{0,30}\b(?:propos|design|implement|develop|introduc|train|evaluat|extract|comput|apply|use|employ|leverag|adopt|construct|build|generat|optimiz|learn|predict|classif|encod|decod|transform|fine-tun|pre-train)",
        re.IGNORECASE,
    )
    action_steps = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 20 and action_pattern.search(sent):
            action_steps.append(sent[:120])
    if len(action_steps) >= 2:
        for i, desc in enumerate(action_steps[:8]):
            steps.append({"label": desc, "order": i})
        return steps

    # Strategy 5: Extract key entities as steps
    entities = (
        db.query(PaperEntity)
        .filter(
            PaperEntity.paper_id == paper_id,
            PaperEntity.entity_type.in_(["method", "innovation"]),
        )
        .all()
    )
    if entities:
        seen = set()
        for ent in entities[:8]:
            if ent.text.lower() not in seen:
                seen.add(ent.text.lower())
                steps.append({"label": ent.text, "order": len(steps)})
        if len(steps) >= 2:
            return steps

    # Strategy 6: Fallback - split by sentences, take meaningful ones
    for i, sent in enumerate(sentences[:10]):
        sent = sent.strip()
        if len(sent) > 30:
            steps.append({"label": sent[:100], "order": len(steps)})
            if len(steps) >= 6:
                break

    return steps


def build_method_flowchart(db: Session, paper_id: str) -> Dict:
    """Generate Mermaid flowchart from methods section using local heuristics."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return {"mermaid_code": "", "steps": []}

    # Query ALL methods/experiments sections and concatenate
    methods_sections = (
        db.query(PaperSection)
        .filter(
            PaperSection.paper_id == paper_id,
            PaperSection.section_type.in_(["methods", "experiments"]),
        )
        .order_by(PaperSection.order)
        .all()
    )

    if not methods_sections:
        # Fallback: try introduction or any non-reference section
        methods_sections = (
            db.query(PaperSection)
            .filter(
                PaperSection.paper_id == paper_id,
                PaperSection.section_type.in_(["introduction", "other", "discussion"]),
            )
            .order_by(PaperSection.order)
            .all()
        )

    if not methods_sections:
        return {"mermaid_code": "graph TD\n    A[No methods section found]", "steps": []}

    # Concatenate all section content with subsection markers
    combined_content = ""
    for sec in methods_sections:
        if sec.heading:
            combined_content += f"\n### {sec.heading}\n"
        combined_content += (sec.content or "") + "\n"

    steps = _extract_method_steps(combined_content, db, paper_id)

    if not steps:
        return {
            "mermaid_code": f"graph TD\n    A[\"{_safe_mermaid(paper.title[:60])}\"]",
            "steps": [],
        }

    mermaid_lines = ["graph TD"]
    for i, step in enumerate(steps):
        node_id = chr(65 + i) if i < 26 else f"N{i}"
        safe_label = _safe_mermaid(step["label"])
        mermaid_lines.append(f"    {node_id}[\"{safe_label}\"]")

    for i in range(len(steps) - 1):
        src = chr(65 + i) if i < 26 else f"N{i}"
        tgt = chr(65 + i + 1) if i + 1 < 26 else f"N{i+1}"
        mermaid_lines.append(f"    {src} --> {tgt}")

    return {
        "mermaid_code": "\n".join(mermaid_lines),
        "steps": steps,
    }


def build_innovation_timeline(db: Session, paper_id: str) -> Dict:
    """Build innovation timeline from references (no LLM needed)."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return {"entries": [], "current_paper_position": {}}

    refs = db.query(PaperReference).filter(PaperReference.paper_id == paper_id).order_by(PaperReference.order).all()

    entries = []
    for ref in refs:
        year = ref.year
        if not year:
            year_match = re.search(r"\b(19|20)\d{2}\b", ref.raw_text or "")
            if year_match:
                year = int(year_match.group(0))

        if year:
            title = ref.title or ref.raw_text[:100] if ref.raw_text else f"Reference {ref.order}"
            entries.append({
                "year": year,
                "title": title,
                "description": ref.raw_text[:200] if ref.raw_text else "",
                "is_current_paper": False,
            })

    # Sort by year
    entries.sort(key=lambda e: e["year"])

    # Add current paper
    current_year = paper.year or 2024
    current_entry = {
        "year": current_year,
        "title": paper.title or "Current Paper",
        "description": "This paper",
        "is_current_paper": True,
    }

    return {
        "entries": entries,
        "current_paper_position": current_entry,
    }


def build_radar_data(db: Session, paper_id: str) -> Dict:
    """Build radar chart data from paper profile."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    profile = db.query(PaperProfile).filter(PaperProfile.paper_id == paper_id).first()

    if not profile:
        # Generate basic scores from available data
        scores = _estimate_radar_scores(db, paper_id)
        return {
            "dimensions": ["Innovation", "Method Complexity", "Experiment Sufficiency", "Reproducibility", "Impact"],
            "scores": scores,
            "max_score": 10.0,
            "paper_title": paper.title if paper else "Unknown",
        }

    return {
        "dimensions": ["Innovation", "Method Complexity", "Experiment Sufficiency", "Reproducibility", "Impact"],
        "scores": [
            profile.innovation_score,
            profile.method_complexity_score,
            profile.experiment_sufficiency_score,
            profile.reproducibility_score,
            profile.impact_prediction_score,
        ],
        "max_score": 10.0,
        "paper_title": paper.title if paper else "Unknown",
    }


def _estimate_radar_scores(db: Session, paper_id: str) -> List[float]:
    """Estimate radar scores from available data without LLM."""
    sections = db.query(PaperSection).filter(PaperSection.paper_id == paper_id).all()
    entities = db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id).all()
    refs = db.query(PaperReference).filter(PaperReference.paper_id == paper_id).all()

    section_types = {s.section_type for s in sections}
    total_content = sum(len(s.content or "") for s in sections)
    entity_types = {e.entity_type for e in entities}

    # Innovation: based on innovation entities and novel method mentions
    innovation = 3.0
    if "innovation" in entity_types:
        innovation += 2.0
    if any(e.entity_type == "method" for e in entities):
        innovation += 1.5
    innovation = min(innovation, 10.0)

    # Method complexity: based on method entities and section length
    method_score = 3.0
    if "methods" in section_types:
        method_sections = [s for s in sections if s.section_type == "methods"]
        method_len = sum(len(s.content or "") for s in method_sections)
        if method_len > 2000:
            method_score += 2.0
        if method_len > 5000:
            method_score += 1.5
    method_count = sum(1 for e in entities if e.entity_type == "method")
    method_score += min(method_count * 0.5, 3.0)
    method_score = min(method_score, 10.0)

    # Experiment sufficiency: based on datasets, metrics, tables
    exp_score = 3.0
    if "experiments" in section_types or "results" in section_types:
        exp_score += 2.0
    dataset_count = sum(1 for e in entities if e.entity_type == "dataset")
    metric_count = sum(1 for e in entities if e.entity_type == "metric")
    exp_score += min(dataset_count * 0.8, 2.0)
    exp_score += min(metric_count * 0.5, 2.0)
    exp_score = min(exp_score, 10.0)

    # Reproducibility: based on tools, code mentions, detail level
    repro_score = 3.0
    if "tool" in entity_types:
        repro_score += 2.0
    full_text = " ".join(s.content or "" for s in sections).lower()
    if re.search(r"github\.com|code\s+(?:is\s+)?available|open[-\s]?source", full_text):
        repro_score += 2.5
    if re.search(r"hyperparameter|learning\s+rate|batch\s+size|epoch", full_text):
        repro_score += 1.0
    repro_score = min(repro_score, 10.0)

    # Impact: based on reference count and content volume
    impact_score = 3.0
    if len(refs) > 20:
        impact_score += 1.5
    if len(refs) > 40:
        impact_score += 1.0
    if total_content > 20000:
        impact_score += 1.5
    if "baseline" in entity_types:
        impact_score += 1.0
    impact_score = min(impact_score, 10.0)

    return [
        round(innovation, 1),
        round(method_score, 1),
        round(exp_score, 1),
        round(repro_score, 1),
        round(impact_score, 1),
    ]
