from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PaperSummary(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    upload_date: datetime
    parsing_status: str
    language: str
    page_count: int

    class Config:
        from_attributes = True


class PaperSectionSchema(BaseModel):
    id: str
    section_type: str
    heading: str
    content: str
    page_start: int
    page_end: int
    order: int

    class Config:
        from_attributes = True


class PaperEntitySchema(BaseModel):
    id: str
    text: str
    entity_type: str
    section_id: Optional[str] = None
    start_char: int
    end_char: int
    confidence: float

    class Config:
        from_attributes = True


class ReferenceSchema(BaseModel):
    id: str
    raw_text: str
    title: Optional[str] = None
    authors: List[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    order: int

    class Config:
        from_attributes = True


class ExtractedTableSchema(BaseModel):
    id: str
    caption: str
    headers: List[str]
    rows: List[List[str]]
    page: int

    class Config:
        from_attributes = True


class PaperDetail(PaperSummary):
    sections: List[PaperSectionSchema] = []
    entities: List[PaperEntitySchema] = []
    references: List[ReferenceSchema] = []
    tables: List[ExtractedTableSchema] = []
    doi: Optional[str] = None
    venue: Optional[str] = None
    year: Optional[int] = None
    keywords: List[str] = []
    pdf_path: str = ""
    file_size: int = 0


class PaperCreateResponse(BaseModel):
    paper_id: str
    task_id: str
    message: str
