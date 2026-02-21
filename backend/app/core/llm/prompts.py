"""All prompt templates for LLM interactions."""

ENTITY_EXTRACTION_PROMPT = """Analyze the following academic paper section and extract key entities.

Section Type: {section_type}
Section Content:
{content}

Extract entities in the following categories:
- research_problem: The core research questions or problems addressed
- method: Algorithms, models, techniques, or approaches used
- dataset: Datasets, benchmarks, or data sources mentioned
- metric: Evaluation metrics (e.g., accuracy, F1, BLEU)
- innovation: Novel contributions or key innovations
- baseline: Baseline methods or compared approaches
- tool: Software tools, libraries, or frameworks
- theory: Theoretical concepts, theorems, or frameworks

Respond in JSON format:
{{
  "entities": [
    {{
      "text": "entity text as it appears",
      "entity_type": "one of the categories above",
      "confidence": 0.0-1.0
    }}
  ]
}}
"""

RELATION_EXTRACTION_PROMPT = """Given the following entities extracted from an academic paper, identify relationships between them.

Entities:
{entities_json}

Paper context:
{context}

Identify relationships of these types:
- causal: "X leads to Y", "because of X, Y happens"
- comparative: "X outperforms Y", "compared to X, Y is better"
- sequential: "first X, then Y"
- uses: "method X uses technique Y"
- improves: "X improves upon Y"
- evaluates_on: "X is evaluated on dataset Y"
- part_of: "X is a component of Y"

Respond in JSON format:
{{
  "relationships": [
    {{
      "source": "source entity text",
      "target": "target entity text",
      "relation_type": "one of the types above",
      "description": "brief description of the relationship",
      "confidence": 0.0-1.0
    }}
  ]
}}
"""

PAPER_PROFILE_PROMPT = """You are an expert academic reviewer. Analyze the following paper and provide a comprehensive profile.

Paper Title: {title}
Abstract: {abstract}

Full Paper Sections:
{sections_text}

Rate the paper on these 5 dimensions (score 1-10 with detailed reasoning):

1. **Innovation Strength**: How novel are the ideas? Are they incremental or groundbreaking?
2. **Method Complexity**: How sophisticated is the methodology? Is it well-designed?
3. **Experiment Sufficiency**: Are experiments comprehensive? Enough baselines, datasets, ablations?
4. **Reproducibility**: Can the work be reproduced? Are details sufficient (code, hyperparams, seeds)?
5. **Impact Prediction**: What is the potential impact on the field?

Respond in JSON format:
{{
  "dimensions": [
    {{
      "dimension": "innovation",
      "score": 8.0,
      "reasoning": "detailed reasoning...",
      "evidence": ["quoted text from paper..."]
    }},
    {{
      "dimension": "method_complexity",
      "score": 7.0,
      "reasoning": "...",
      "evidence": ["..."]
    }},
    {{
      "dimension": "experiment_sufficiency",
      "score": 6.0,
      "reasoning": "...",
      "evidence": ["..."]
    }},
    {{
      "dimension": "reproducibility",
      "score": 5.0,
      "reasoning": "...",
      "evidence": ["..."]
    }},
    {{
      "dimension": "impact_prediction",
      "score": 7.0,
      "reasoning": "...",
      "evidence": ["..."]
    }}
  ],
  "overall_assessment": "A comprehensive 2-3 sentence assessment of the paper."
}}
"""

CONTRIBUTION_EXTRACTION_PROMPT = """Analyze the following paper and extract its contributions at three levels.

Paper Title: {title}
Abstract: {abstract}
Sections:
{sections_text}

Extract contributions at these levels:
1. **Theoretical**: New theorems, frameworks, formulations, or theoretical insights
2. **Technical**: New algorithms, architectures, training procedures, or engineering innovations
3. **Application**: New use cases, datasets, benchmarks, or practical applications

For each contribution, assess its significance as "major", "moderate", or "minor".

Respond in JSON format:
{{
  "contributions": [
    {{
      "level": "theoretical|technical|application",
      "description": "clear description of the contribution",
      "evidence": ["quoted text from paper supporting this"],
      "significance": "major|moderate|minor"
    }}
  ],
  "summary": "A brief summary of the paper's overall contributions."
}}
"""

LIMITATION_IDENTIFICATION_PROMPT = """You are a critical academic reviewer. Identify limitations and potential weaknesses in this paper.

Paper Title: {title}
Abstract: {abstract}
Sections:
{sections_text}

Check for these common issues:
- insufficient_experiments: Small-scale experiments, few datasets, limited evaluation
- missing_ablation: No ablation studies to validate design choices
- outdated_baselines: Comparing against old or weak baselines
- unclear_methodology: Vague descriptions, missing details
- limited_scope: Narrow applicability, strong assumptions
- reproducibility_concern: Missing code, hyperparameters, or implementation details
- overclaiming: Claims not fully supported by evidence

For each limitation, assess severity as "critical", "major", or "minor" and suggest improvements.

Respond in JSON format:
{{
  "limitations": [
    {{
      "category": "one of the categories above",
      "description": "specific description of the limitation",
      "severity": "critical|major|minor",
      "suggestion": "specific improvement suggestion"
    }}
  ],
  "summary": "Overall assessment of the paper's limitations."
}}
"""

AUTO_REVIEW_PROMPT = """You are a senior reviewer at a top-tier {venue_type} conference (e.g., NeurIPS, ICML, ACL).
Write a structured review for the following paper.

Paper Title: {title}
Abstract: {abstract}
Full Paper:
{sections_text}

Write a comprehensive review following this structure:
1. **Summary** (200 words): What does the paper do? What is the main contribution?
2. **Strengths** (3-5 points): What are the paper's strong points?
3. **Weaknesses** (3-5 points): What are the issues? Include specific improvement suggestions.
4. **Questions to Authors** (2-3 questions): What would you ask the authors?
5. **Overall Recommendation**: accept / weak_accept / borderline / weak_reject / reject
6. **Confidence**: Your confidence in this review (1-5)

Language: {language}

Respond in JSON format:
{{
  "summary": "...",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1 with suggestion", "weakness 2 with suggestion", "weakness 3 with suggestion"],
  "questions_to_authors": ["question 1", "question 2"],
  "overall_recommendation": "accept|weak_accept|borderline|weak_reject|reject",
  "confidence": 3.5
}}
"""

CONTROVERSY_DETECTION_PROMPT = """Analyze the following paper for potential inconsistencies between claims and evidence.

Paper Title: {title}
Sections:
{sections_text}

For each major claim in the paper, check:
1. Is the claim supported by the experimental evidence?
2. Are there any exaggerations (e.g., "state-of-the-art" with limited baselines)?
3. Do figures/tables support the textual claims?

Respond in JSON format:
{{
  "claims": [
    {{
      "claim": "the specific claim made",
      "evidence_for": ["evidence supporting the claim"],
      "evidence_against": ["evidence contradicting or weakening the claim"],
      "consistency_score": 0.0-1.0,
      "assessment": "brief assessment"
    }}
  ],
  "overall_consistency": 0.0-1.0
}}
"""

REPRODUCIBILITY_CHECK_PROMPT = """Evaluate the reproducibility of the following paper.

Paper Title: {title}
Sections:
{sections_text}

Check for the following reproducibility criteria:
1. Code availability (link provided?)
2. Dataset availability (public? described?)
3. Hyperparameter details (learning rate, batch size, etc.)
4. Random seed specification
5. Computing environment details (GPU type, training time)
6. Evaluation protocol clarity
7. Statistical significance reporting
8. Model architecture details sufficient for reimplementation

Respond in JSON format:
{{
  "checklist": [
    {{
      "criterion": "criterion name",
      "status": "met|partially_met|not_met|not_applicable",
      "details": "specific details found or missing"
    }}
  ],
  "overall_score": 0.0-1.0,
  "summary": "Overall reproducibility assessment"
}}
"""

FLOWCHART_GENERATION_PROMPT = """Based on the methodology section of this paper, generate a Mermaid flowchart diagram.

Paper Title: {title}
Methods Section:
{methods_text}

Generate a Mermaid flowchart that shows the method pipeline:
- Input data/preprocessing steps
- Core algorithm/model components
- Training/inference flow
- Output/evaluation

Use Mermaid graph TD (top-down) syntax. Keep node labels concise.
Include subgraphs for major components.

Respond in JSON format:
{{
  "mermaid_code": "graph TD\\n    A[Input] --> B[Processing]\\n    ...",
  "steps": [
    {{"id": "A", "label": "Input", "description": "detailed description"}},
    {{"id": "B", "label": "Processing", "description": "detailed description"}}
  ]
}}
"""

TIMELINE_GENERATION_PROMPT = """Based on the related work and references in this paper, generate an innovation timeline.

Paper Title: {title}
Related Work Section:
{related_work_text}

References:
{references_text}

Create a timeline of key developments leading to this paper's contribution.
Include the current paper's position in the timeline.

Respond in JSON format:
{{
  "entries": [
    {{
      "year": 2020,
      "event": "Description of the development",
      "category": "method|dataset|benchmark|theory",
      "related_paper": "Paper title if applicable"
    }}
  ],
  "current_paper_position": {{
    "year": 2024,
    "description": "How this paper fits in the timeline"
  }}
}}
"""

# Chat prompts for interactive AI assistant
PAPER_CHAT_PROMPT = """You are an expert academic research assistant helping a user understand a research paper.

Paper Title: {title}
Paper Abstract: {abstract}

Paper Content:
{paper_content}

You are having a conversation with the user about this paper. Answer their questions accurately based on the paper content provided.
If the user asks about something not in the paper, be honest that it's not covered.
Be concise but thorough in your explanations. Use bullet points for clarity when appropriate.

Previous conversation:
{conversation_history}

User's question: {question}

Respond in a helpful, academic tone. If the user selected specific text from the paper, focus your answer on that selection.
"""

PAPER_SUMMARIZE_PROMPT = """Provide a concise summary of the following research paper.

Paper Title: {title}
Paper Content:
{paper_content}

Provide:
1. A one-sentence summary of the main contribution
2. 3-5 key points covering the problem, method, and results
3. Who this paper would be most useful for

Language: {language}
"""

PAPER_TRANSLATE_PROMPT = """Translate the following academic text to {target_language}.

Text to translate:
{text}

Requirements:
- Maintain academic tone and precision
- Keep technical terms accurate (you may keep English terms in parentheses if they are standard in the field)
- Preserve the structure and formatting
- Ensure the translation is natural and fluent

Provide only the translated text without explanations.
"""

PAPER_EXPLAIN_PROMPT = """Explain the following content from a research paper in simple terms.

Paper Title: {title}
Context: {context}

Content to explain:
{text}

Provide:
1. A simplified explanation suitable for someone with general CS/ML knowledge
2. Key concepts or terms explained
3. Why this matters in the broader context of the paper

Language: {language}
"""

PAPER_CRITIQUE_PROMPT = """Provide a critical analysis of the following research paper content.

Paper Title: {title}
Paper Content:
{paper_content}

Focus on:
1. Strengths of the approach
2. Potential weaknesses or limitations
3. Questions that remain unanswered
4. Suggestions for improvement or future work

Be constructive and specific in your critique.
Language: {language}
"""
