"""RiskLens 公共 Pydantic 模型。"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .case import CaseCause, CaseInfo, CaseSearchResult


class SourceType(str, Enum):
    UPLOAD = "upload"
    SEED = "seed"
    OBSIDIAN = "obsidian"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentInfo(BaseModel):
    id: str
    name: str
    source: SourceType = SourceType.UPLOAD
    file_path: Optional[str] = None
    size: int = 0
    chunks_count: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    error: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    owner_user_id: Optional[str] = None
    visibility: str = "shared"


class Chunk(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    chunk_id: str
    text: str
    score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    law_name: str = ""
    article_no: str = ""
    citation: str = ""
    category: str = "law"


class Citation(BaseModel):
    id: int
    law_name: str
    article_no: str = ""
    article_text: str
    source_chunk_id: Union[str, List[str]]
    similarity: float = 0.0
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    publisher: Optional[str] = None
    law_status: Optional[str] = None
    decree: Optional[str] = None
    effective_date: Optional[str] = None


__all__ = [
    "CaseCause",
    "CaseInfo",
    "CaseSearchResult",
    "Chunk",
    "Citation",
    "DocumentInfo",
    "DocumentStatus",
    "SearchResult",
    "SourceType",
]
