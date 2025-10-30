# credit_score_service/mock_data.py
import random
from typing import Dict

def generate_mock_financial_data(seed: int | None = None) -> Dict[str, float]:
    """
    Return mock financial metrics in the shape described in the spec.
    Each value is between 0 and 1 (except where noted).
    """
    if seed is not None:
        random.seed(seed)
    return {
        "revenue_growth_rate": random.uniform(0.3, 1.0),
        "burn_rate": random.uniform(0.1, 0.9),
        "profitability": random.uniform(0.0, 1.0),
        "liquidity": random.uniform(0.2, 1.0),
        "debt_ratio": random.uniform(0.0, 0.8)
    }
