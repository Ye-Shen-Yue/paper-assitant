"""Entity recognition using local regex/keyword patterns (no LLM required).

Falls back to LLM-based extraction if available, but works fully offline.
"""
import re
from typing import List, Dict, Set


# Keyword patterns for different entity types
DATASET_PATTERNS = [
    r"\b(ImageNet|CIFAR[-\s]?\d+|MNIST|COCO|VOC\s?\d+|SQuAD|GLUE|SuperGLUE|WikiText|Penn\s?Treebank)\b",
    r"\b(WMT[-\s]?\d+|SNLI|MultiNLI|SST[-\s]?\d+|MRPC|QQP|QNLI|RTE|WNLI)\b",
    r"\b(MS[-\s]?COCO|Visual\s?Genome|Flickr\d+k?|LVIS|ADE\d+K?|Cityscapes)\b",
    r"\b(LibriSpeech|Common\s?Voice|AudioSet|VoxCeleb\d?)\b",
    r"\b(WebText|BookCorpus|C4|The\s?Pile|RedPajama|LAION[-\s]?\d+[BMK]?)\b",
]

DATASET_GENERIC = re.compile(
    r"\b([A-Z][\w-]*(?:\s+[A-Z][\w-]*)*)\s+(?:dataset|benchmark|corpus|corpora)\b",
    re.IGNORECASE,
)

METRIC_PATTERNS = [
    r"\b(accuracy|precision|recall|F1[-\s]?score|F[-\s]?measure|AUC[-\s]?ROC|mAP|IoU)\b",
    r"\b(BLEU[-\s]?\d*|ROUGE[-\s]?[LN12]*|METEOR|CIDEr|perplexity|PPL)\b",
    r"\b(top[-\s]?\d+\s+accuracy|mean\s+average\s+precision|average\s+precision)\b",
    r"\b(FID|IS|inception\s+score|Frechet\s+inception\s+distance)\b",
    r"\b(MSE|RMSE|MAE|PSNR|SSIM)\b",
    r"\b(WER|CER|word\s+error\s+rate|character\s+error\s+rate)\b",
    r"\b(EM|exact\s+match)\b",
]

METHOD_PATTERNS = [
    r"\b(Transformer|BERT|GPT[-\s]?\d*|ResNet[-\s]?\d*|VGG[-\s]?\d*|LSTM|GRU|CNN|RNN)\b",
    r"\b(ViT|Vision\s+Transformer|DETR|YOLO(?:v\d)?|Faster\s+R[-\s]?CNN|Mask\s+R[-\s]?CNN)\b",
    r"\b(U[-\s]?Net|GAN|VAE|Diffusion\s+Model|Stable\s+Diffusion|DALL[-\s]?E)\b",
    r"\b(T5|BART|XLNet|RoBERTa|ALBERT|DeBERTa|ELECTRA|LLaMA|Mistral|Qwen)\b",
    r"\b(attention\s+mechanism|self[-\s]?attention|cross[-\s]?attention|multi[-\s]?head\s+attention)\b",
    r"\b(dropout|batch\s+normalization|layer\s+normalization|residual\s+connection)\b",
    r"\b(fine[-\s]?tuning|pre[-\s]?training|transfer\s+learning|few[-\s]?shot|zero[-\s]?shot)\b",
    r"\b(reinforcement\s+learning|supervised\s+learning|unsupervised\s+learning|self[-\s]?supervised)\b",
    r"\b(contrastive\s+learning|knowledge\s+distillation|data\s+augmentation)\b",
    r"\b(gradient\s+descent|Adam|SGD|AdamW)\b",
]

TOOL_PATTERNS = [
    r"\b(PyTorch|TensorFlow|JAX|Keras|Hugging\s?Face|scikit[-\s]?learn|spaCy|NLTK)\b",
    r"\b(NumPy|SciPy|Pandas|OpenCV|CUDA|cuDNN)\b",
    r"\b(NVIDIA\s+[A-Z]\d+|TPU|A100|V100|H100)\b",
]

THEORY_PATTERNS = [
    r"\b(Bayes(?:ian)?\s+(?:theorem|inference|optimization|network))\b",
    r"\b(Markov\s+(?:chain|decision\s+process|random\s+field))\b",
    r"\b(KL[-\s]?divergence|mutual\s+information|information\s+entropy)\b",
    r"\b(optimal\s+transport|Wasserstein\s+distance|variational\s+inference)\b",
]

def _match_patterns(text: str, patterns: List[str], entity_type: str, seen: Set[str]) -> List[Dict]:
    """Match regex patterns and return unique entities."""
    results = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            matched = m.group(1) if m.lastindex else m.group(0)
            key = matched.lower().strip()
            if key not in seen and len(key) > 1:
                seen.add(key)
                results.append({
                    "text": matched.strip(),
                    "entity_type": entity_type,
                    "confidence": 0.8,
                })
    return results


def _extract_research_problems(text: str, seen: Set[str]) -> List[Dict]:
    """Extract research problems from text using heuristic patterns."""
    results = []
    problem_patterns = [
        r"(?:we\s+(?:address|tackle|study|investigate|focus\s+on|propose\s+a\s+solution\s+(?:to|for)))\s+(?:the\s+)?(?:problem\s+of\s+)?(.{10,80}?)(?:\.|,|\band\b)",
        r"(?:the\s+(?:problem|task|challenge)\s+of)\s+(.{10,80}?)(?:\.|,)",
        r"(?:this\s+(?:paper|work|study)\s+(?:addresses|tackles|focuses\s+on|investigates))\s+(.{10,80}?)(?:\.|,)",
    ]
    for pattern in problem_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            matched = m.group(1).strip()
            key = matched.lower()
            if key not in seen and 10 < len(matched) < 200:
                seen.add(key)
                results.append({
                    "text": matched,
                    "entity_type": "research_problem",
                    "confidence": 0.6,
                })
    return results


def _extract_baselines(text: str, seen: Set[str]) -> List[Dict]:
    """Extract baseline methods mentioned in comparisons."""
    results = []
    baseline_patterns = [
        r"(?:compared?\s+(?:with|to|against)|baseline[s]?(?:\s+(?:include|are))?)[:\s]+(.{5,200}?)(?:\.|$)",
        r"(?:outperform[s]?|surpass(?:es)?|exceed[s]?)\s+(.{5,80}?)(?:\s+(?:by|on|in|with)\b|\.|,)",
    ]
    for pattern in baseline_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            raw = m.group(1).strip()
            # Split by comma/and to get individual baselines
            parts = re.split(r",\s*|\s+and\s+", raw)
            for part in parts:
                part = part.strip().rstrip(".")
                key = part.lower()
                if key not in seen and 2 < len(part) < 80 and not part[0].islower():
                    seen.add(key)
                    results.append({
                        "text": part,
                        "entity_type": "baseline",
                        "confidence": 0.6,
                    })
    return results


def extract_entities(section_type: str, content: str) -> List[Dict]:
    """Extract entities from a paper section using local regex patterns.

    Works without any LLM API. Recognizes datasets, metrics, methods,
    tools, theories, research problems, and baselines.
    """
    if not content or len(content.strip()) < 30:
        return []

    text = content[:12000]
    seen: Set[str] = set()
    entities: List[Dict] = []

    # Extract known entity types via patterns
    entities.extend(_match_patterns(text, DATASET_PATTERNS, "dataset", seen))
    entities.extend(_match_patterns(text, METRIC_PATTERNS, "metric", seen))
    entities.extend(_match_patterns(text, METHOD_PATTERNS, "method", seen))
    entities.extend(_match_patterns(text, TOOL_PATTERNS, "tool", seen))
    entities.extend(_match_patterns(text, THEORY_PATTERNS, "theory", seen))

    # Generic dataset mentions (e.g. "XYZ dataset")
    for m in DATASET_GENERIC.finditer(text):
        name = m.group(1).strip()
        key = name.lower()
        if key not in seen and len(name) > 2:
            seen.add(key)
            entities.append({
                "text": name,
                "entity_type": "dataset",
                "confidence": 0.65,
            })

    # Research problems (from intro/abstract sections)
    if section_type in ("abstract", "introduction", "other"):
        entities.extend(_extract_research_problems(text, seen))

    # Baselines (from experiments/results sections)
    if section_type in ("experiments", "results", "discussion", "other"):
        entities.extend(_extract_baselines(text, seen))

    return entities
