"""Table generation service using Kimi to generate LaTeX tables from paper content."""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import json
import re

from app.models.paper import Paper
from app.models.analysis import PaperSection
from app.core.llm.client import LLMClient


TABLE_GENERATION_PROMPT = """You are an expert academic research assistant. Analyze the following research paper and extract key information into well-formatted LaTeX tables.

Paper Title: {title}
Abstract: {abstract}

Paper Content:
{paper_content}

Please analyze this paper and create **2-4 LaTeX tables** that capture the most important information. For each table, provide:

1. **table_title**: A descriptive title for the table
2. **latex_code**: Valid LaTeX table code (using `booktabs` style with `\toprule`, `\midrule`, `\bottomrule`)
3. **explanation**: A detailed explanation of what the table shows and its significance

Focus on extracting:
- Method comparisons (if multiple methods are compared)
- Experimental results and performance metrics
- Dataset or benchmark information
- Key parameters or configurations

Respond in JSON format:
{{
  "tables": [
    {{
      "table_title": "Table 1: Comparison of Methods",
      "latex_code": "\\begin{{table}}[htbp]\n\\centering\n\\caption{{Comparison of Methods}}\n\\begin{{tabular}}{{lccc}}\n\\toprule\nMethod & Accuracy & F1 Score & Params \\\\\n\\midrule\nMethod A & 85.2 & 84.1 & 10M \\\\\nMethod B & 87.5 & 86.3 & 15M \\\\\n\\bottomrule\n\\end{{tabular}}\n\\end{{table}}",
      "explanation": "This table compares different methods..."
    }}
  ]
}}

Important:
- Use proper LaTeX syntax
- Use `booktabs` style (\toprule, \midrule, \bottomrule)
- Ensure the LaTeX code is complete and compilable
- Make tables informative and well-structured
"""


class TableGenerationService:
    """Service for generating LaTeX tables using Kimi AI."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMClient()

    def _get_paper_content(self, paper: Paper, max_length: int = 6000) -> str:
        """Extract paper content from sections."""
        sections = (
            self.db.query(PaperSection)
            .filter(PaperSection.paper_id == paper.id)
            .order_by(PaperSection.order)
            .all()
        )

        content_parts = []
        total_length = 0

        # Prioritize important sections
        priority_order = ['methods', 'experiments', 'results', 'abstract', 'introduction']

        for priority in priority_order:
            for section in sections:
                if section.section_type == priority or (section.heading and priority in section.heading.lower()):
                    section_text = f"\n## {section.heading or section.section_type}\n{section.content}\n"
                    if total_length + len(section_text) > max_length:
                        remaining = max_length - total_length
                        if remaining > 100:
                            content_parts.append(section_text[:remaining] + "\n...")
                        break
                    content_parts.append(section_text)
                    total_length += len(section_text)

        # Add remaining sections if space allows
        for section in sections:
            if section.section_type not in priority_order:
                section_text = f"\n## {section.heading or section.section_type}\n{section.content}\n"
                if total_length + len(section_text) > max_length:
                    break
                content_parts.append(section_text)
                total_length += len(section_text)

        return "".join(content_parts)

    def generate_tables(self, paper: Paper) -> List[Dict]:
        """Generate LaTeX tables from paper content using Kimi."""
        paper_content = self._get_paper_content(paper)

        prompt = TABLE_GENERATION_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract or "No abstract available",
            paper_content=paper_content,
        )

        try:
            # Use chat_json to get structured output
            response = self.llm.chat_json(
                prompt=prompt,
                system_prompt="You are an expert at creating academic tables. Generate well-structured LaTeX tables with booktabs styling.",
                temperature=0.3,
                max_tokens=4096,
            )

            tables = response.get("tables", [])

            # Validate and clean up LaTeX code
            for table in tables:
                latex = table.get("latex_code", "")
                # Ensure proper escaping
                latex = self._clean_latex(latex)
                table["latex_code"] = latex

            return tables

        except Exception as e:
            print(f"Table generation failed: {e}")
            # Return a fallback table
            return [{
                "table_title": "Error: Could not generate tables",
                "latex_code": "\\begin{table}[htbp]\n\\centering\n\\caption{Error}\n\\begin{tabular}{l}\n\\toprule\nError: " + str(e).replace("_", "\\_") + " \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}",
                "explanation": "Failed to generate tables from the paper content."
            }]

    def _clean_latex(self, latex: str) -> str:
        """Clean up LaTeX code for proper rendering."""
        if not latex:
            return ""

        # Remove markdown code blocks if present
        latex = re.sub(r'^```latex\s*', '', latex, flags=re.MULTILINE)
        latex = re.sub(r'```\s*$', '', latex, flags=re.MULTILINE)

        # Ensure proper escaping of special characters in content
        # (but not in LaTeX commands)
        return latex.strip()

    def explain_table(self, table_data: Dict) -> str:
        """Generate explanation for a specific table."""
        latex_code = table_data.get("latex_code", "")
        table_title = table_data.get("table_title", "Table")

        prompt = f"""Analyze this LaTeX table and provide a detailed explanation:

Table Title: {table_title}

LaTeX Code:
{latex_code}

Please provide:
1. What this table represents
2. Key findings or patterns in the data
3. The significance of this information in the research context
4. Any notable comparisons or trends

Be concise but informative."""

        try:
            explanation = self.llm.chat(
                prompt=prompt,
                system_prompt="You are an expert at analyzing academic tables.",
                temperature=0.3,
                max_tokens=1024,
            )
            return explanation
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"
