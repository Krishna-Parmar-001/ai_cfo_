# credit_score_service/schemas.py
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class CreditScoreResponse(BaseModel):
    company_id: str
    score: int
    last_updated: datetime
    breakdown: Dict[str, Any]

class RankedStartupItem(BaseModel):
    company_id: str
    company_name: str
    industry: str
    score: int
    growth_rate: float

class RecalcResponse(BaseModel):
    message: str
    company_id: str
    new_score: int
