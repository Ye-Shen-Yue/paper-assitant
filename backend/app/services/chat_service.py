"""Chat service for AI assistant interactions."""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

from app.models.paper import Paper
from app.models.analysis import PaperSection
from app.core.llm.client import LLMClient
from app.core.llm.prompts import (
    PAPER_CHAT_PROMPT,
    PAPER_SUMMARIZE_PROMPT,
    PAPER_TRANSLATE_PROMPT,
    PAPER_EXPLAIN_PROMPT,
    PAPER_CRITIQUE_PROMPT,
)


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMClient()

    def _get_paper_content(self, paper: Paper, max_length: int = 8000) -> str:
        """Extract paper content from sections."""
        sections = (
            self.db.query(PaperSection)
            .filter(PaperSection.paper_id == paper.id)
            .order_by(PaperSection.order)
            .all()
        )

        content_parts = []
        total_length = 0

        for section in sections:
            section_text = f"\n## {section.heading or section.section_type}\n{section.content}\n"
            if total_length + len(section_text) > max_length:
                remaining = max_length - total_length
                if remaining > 100:
                    content_parts.append(section_text[:remaining] + "\n...")
                break
            content_parts.append(section_text)
            total_length += len(section_text)

        return "".join(content_parts)

    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for prompt."""
        formatted = []
        for msg in history[-5:]:  # Keep last 5 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prefix = "User" if role == "user" else "Assistant"
            formatted.append(f"{prefix}: {content}")
        return "\n".join(formatted)

    def chat(
        self,
        paper: Paper,
        message: str,
        history: Optional[List[Dict]] = None,
        selected_text: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """Handle a chat message about the paper."""
        paper_content = self._get_paper_content(paper)
        conversation_history = self._format_conversation_history(history or [])

        # If there's selected text, prepend it to the question
        question = message
        if selected_text:
            question = f"[Selected text: \"{selected_text}\"]\n\n{message}"

        prompt = PAPER_CHAT_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract or "No abstract available",
            paper_content=paper_content,
            conversation_history=conversation_history,
            question=question,
        )

        try:
            response = self.llm.chat(prompt)
            return response
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}. Please try again."

    def summarize(self, paper: Paper, language: str = "en") -> str:
        """Generate a summary of the paper."""
        paper_content = self._get_paper_content(paper, max_length=6000)

        prompt = PAPER_SUMMARIZE_PROMPT.format(
            title=paper.title,
            paper_content=paper_content,
            language=language,
        )

        try:
            response = self.llm.chat(prompt)
            return response
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def translate(self, text: str, target_language: str = "zh") -> str:
        """Translate text to target language."""
        prompt = PAPER_TRANSLATE_PROMPT.format(
            target_language="Chinese" if target_language == "zh" else "English",
            text=text,
        )

        try:
            response = self.llm.chat(prompt)
            return response
        except Exception as e:
            return f"Error translating: {str(e)}"

    def explain(self, text: str, context: str, language: str = "en") -> str:
        """Explain text in simple terms."""
        prompt = PAPER_EXPLAIN_PROMPT.format(
            title=context,
            context=context,
            text=text,
            language=language,
        )

        try:
            response = self.llm.chat(prompt)
            return response
        except Exception as e:
            return f"Error explaining: {str(e)}"

    def critique(self, paper: Paper, language: str = "en") -> str:
        """Provide critical analysis of the paper."""
        paper_content = self._get_paper_content(paper, max_length=6000)

        prompt = PAPER_CRITIQUE_PROMPT.format(
            title=paper.title,
            paper_content=paper_content,
            language=language,
        )

        try:
            response = self.llm.chat(prompt)
            return response
        except Exception as e:
            return f"Error generating critique: {str(e)}"
