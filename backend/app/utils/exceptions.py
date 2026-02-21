class ScholarLensError(Exception):
    """Base exception for ScholarLens."""
    def __init__(self, message: str, error_code: str = "UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class PDFParsingError(ScholarLensError):
    def __init__(self, message: str = "Failed to parse PDF"):
        super().__init__(message, "PDF_PARSING_ERROR")


class LLMError(ScholarLensError):
    def __init__(self, message: str = "LLM request failed"):
        super().__init__(message, "LLM_ERROR")


class PaperNotFoundError(ScholarLensError):
    def __init__(self, paper_id: str):
        super().__init__(f"Paper not found: {paper_id}", "PAPER_NOT_FOUND")


class TaskNotFoundError(ScholarLensError):
    def __init__(self, task_id: str):
        super().__init__(f"Task not found: {task_id}", "TASK_NOT_FOUND")
