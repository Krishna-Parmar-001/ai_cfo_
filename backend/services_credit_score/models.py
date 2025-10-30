# credit_score_service/models.py
from pydantic import BaseModel, Field
from typing import Any, Dict
from datetime import datetime

class FactorPoints(BaseModel):
    value: float
    points: int

class Breakdown(BaseModel):
    revenue_growth_rate: FactorPoints
    burn_rate: FactorPoints
    profitability: FactorPoints
    liquidity: FactorPoints | None = None
    debt_ratio: FactorPoints | None = None

class CreditScoreDocument(BaseModel):
    company_id: str
    company_name: str
    industry: str
    score: int
    last_updated: datetime
    breakdown: Breakdown

class ScoreFactorsHistory(BaseModel):
    company_id: str
    timestamp: datetime
    factors: Dict[str, float]
