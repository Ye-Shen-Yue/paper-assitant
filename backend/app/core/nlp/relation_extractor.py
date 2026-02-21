"""Relationship extraction using co-occurrence and heuristic patterns (no LLM required)."""
import re
from typing import List, Dict, Optional, Set, Tuple


# Patterns that indicate specific relationship types between entities
RELATION_INDICATORS = {
    "uses": [
        r"{src}\s+(?:uses?|utilizes?|employs?|leverages?|applies)\s+{tgt}",
        r"{tgt}\s+(?:is\s+)?(?:used|utilized|employed|applied)\s+(?:by|in|for)\s+{src}",
        r"(?:using|with|via|through)\s+{tgt}",
    ],
    "evaluates_on": [
        r"{src}\s+(?:on|evaluated?\s+on|tested?\s+on|benchmarked?\s+on)\s+{tgt}",
        r"(?:evaluate|test|benchmark)\s+{src}\s+on\s+{tgt}",
        r"(?:results?\s+on|performance\s+on)\s+{tgt}",
    ],
    "improves": [
        r"{src}\s+(?:improves?|outperforms?|surpass(?:es)?|exceeds?|beats?)\s+{tgt}",
        r"{src}\s+(?:achieves?\s+(?:better|higher|superior)\s+(?:\w+\s+)?(?:than|over))\s+{tgt}",
    ],
    "comparative": [
        r"{src}\s+(?:compared?\s+(?:to|with)|vs\.?|versus)\s+{tgt}",
        r"(?:comparison\s+(?:between|of))\s+{src}\s+and\s+{tgt}",
    ],
    "part_of": [
        r"{src}\s+(?:component|module|layer|part)\s+of\s+{tgt}",
        r"{tgt}\s+(?:consists?\s+of|includes?|contains?)\s+{src}",
    ],
}

# Type-based relationship heuristics
TYPE_RELATIONS = {
    ("method", "dataset"): "evaluates_on",
    ("method", "metric"): "evaluates_on",
    ("method", "tool"): "uses",
    ("method", "theory"): "uses",
    ("method", "baseline"): "comparative",
    ("innovation", "method"): "improves",
    ("innovation", "baseline"): "improves",
    ("research_problem", "method"): "causal",
    ("research_problem", "innovation"): "causal",
}


def _entities_co_occur(e1_text: str, e2_text: str, context: str, window: int = 300) -> bool:
    """Check if two entities co-occur within a text window."""
    text_lower = context.lower()
    e1_lower = e1_text.lower()
    e2_lower = e2_text.lower()

    # Find all positions of e1
    pos1 = [m.start() for m in re.finditer(re.escape(e1_lower), text_lower)]
    pos2 = [m.start() for m in re.finditer(re.escape(e2_lower), text_lower)]

    if not pos1 or not pos2:
        return False

    # Check if any pair is within the window
    for p1 in pos1:
        for p2 in pos2:
            if abs(p1 - p2) < window:
                return True
    return False


def _check_pattern_relation(
    src_text: str, tgt_text: str, context: str
) -> Optional[str]:
    """Check if a specific relationship pattern exists between two entities."""
    text_lower = context.lower()
    src_esc = re.escape(src_text.lower())
    tgt_esc = re.escape(tgt_text.lower())

    for rel_type, patterns in RELATION_INDICATORS.items():
        for pattern_template in patterns:
            pattern = pattern_template.replace("{src}", src_esc).replace("{tgt}", tgt_esc)
            if re.search(pattern, text_lower):
                return rel_type
    return None


def extract_relationships(entities: List[Dict], context: str) -> List[Dict]:
    """Extract relationships between entities using co-occurrence and heuristics.

    Works without any LLM API. Uses:
    1. Pattern-based relation detection (e.g. "X outperforms Y")
    2. Co-occurrence within text windows
    3. Type-based heuristics (e.g. method + dataset = evaluates_on)
    """
    if not entities or len(entities) < 2:
        return []

    limited = entities[:40]
    relationships: List[Dict] = []
    seen_pairs: Set[Tuple[str, str]] = set()

    for i, e1 in enumerate(limited):
        for j, e2 in enumerate(limited):
            if i >= j:
                continue

            src_text = e1["text"]
            tgt_text = e2["text"]
            pair_key = (src_text.lower(), tgt_text.lower())
            if pair_key in seen_pairs:
                continue

            # Try pattern-based detection first
            rel_type = _check_pattern_relation(src_text, tgt_text, context)
            if not rel_type:
                rel_type = _check_pattern_relation(tgt_text, src_text, context)
                if rel_type:
                    src_text, tgt_text = tgt_text, src_text

            if rel_type:
                seen_pairs.add(pair_key)
                relationships.append({
                    "source": src_text,
                    "target": tgt_text,
                    "relation_type": rel_type,
                    "description": f"{src_text} {rel_type} {tgt_text}",
                    "confidence": 0.7,
                })
                continue

            # Fall back to co-occurrence + type heuristics
            if _entities_co_occur(src_text, tgt_text, context, window=250):
                type_pair = (e1.get("entity_type", ""), e2.get("entity_type", ""))
                rel_type = TYPE_RELATIONS.get(type_pair)
                if not rel_type:
                    rev_pair = (type_pair[1], type_pair[0])
                    rel_type = TYPE_RELATIONS.get(rev_pair)
                    if rel_type:
                        src_text, tgt_text = tgt_text, src_text

                if rel_type:
                    seen_pairs.add(pair_key)
                    relationships.append({
                        "source": src_text,
                        "target": tgt_text,
                        "relation_type": rel_type,
                        "description": f"{src_text} {rel_type} {tgt_text}",
                        "confidence": 0.5,
                    })

    return relationships
