"""案件领域模型。字段来自现有 SQLite 与类案检索调用。"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CaseCause(str, Enum):
    """常见案由；未知案由仍由 API 以字符串传递。"""

    CONTRACT = "合同纠纷"
    FINANCIAL_LOAN = "金融借款合同纠纷"
    LABOR = "劳动争议"
    CONSUMER = "消费者权益纠纷"
    OTHER = "其他"


class CaseInfo(BaseModel):
    id: str
    case_no: Optional[str] = None
    title: str
    client: str = ""
    case_type: str = ""
    amount: Optional[float] = None
    court: Optional[str] = None
    status: str = "draft"
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None


class CaseSearchResult(BaseModel):
    case_id: str
    case_no: str = ""
    title: str = ""
    cause: str = ""
    court: str = ""
    level: str = ""
    judgment_date: str = ""
    snippet: str = ""
    score: float = 0.0
    cited_articles: List[str] = Field(default_factory=list)
    similarity_to_query: float = 0.0
    category: str = "case"
