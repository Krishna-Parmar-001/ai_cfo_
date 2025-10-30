# credit_score_service/utils/scoring.py
from typing import Dict, Tuple
from math import floor

WEIGHTS = {
    "revenue_growth_rate": 250,
    "burn_rate": 200,       # used as (1 - burn_rate) * weight
    "profitability": 200,
    "liquidity": 150,
    "debt_ratio": 200       # used as (1 - debt_ratio) * weight
}

def compute_score_and_breakdown(factors: Dict[str, float]) -> Tuple[int, Dict[str, Dict]]:
    """
    Given factor values (0..1), compute:
      - final integer score clamped between 300 and 900 (as spec)
      - detailed breakdown: each factor => {"value": x, "points": y}
    """
    rgr = factors.get("revenue_growth_rate", 0.0)
    burn = factors.get("burn_rate", 0.0)
    profit = factors.get("profitability", 0.0)
    liquidity = factors.get("liquidity", 0.0)
    debt = factors.get("debt_ratio", 0.0)

    # Weighted contributions
    c_rgr = rgr * WEIGHTS["revenue_growth_rate"]
    c_burn = (1.0 - burn) * WEIGHTS["burn_rate"]
    c_profit = profit * WEIGHTS["profitability"]
    c_liquidity = liquidity * WEIGHTS["liquidity"]
    c_debt = (1.0 - debt) * WEIGHTS["debt_ratio"]

    raw_score = c_rgr + c_burn + c_profit + c_liquidity + c_debt

    # clamp and convert
    score = int(min(900, max(300, floor(raw_score))))

    breakdown = {
        "revenue_growth_rate": {"value": round(rgr, 4), "points": int(round(c_rgr))},
        "burn_rate": {"value": round(burn, 4), "points": int(round(c_burn))},
        "profitability": {"value": round(profit, 4), "points": int(round(c_profit))},
        "liquidity": {"value": round(liquidity, 4), "points": int(round(c_liquidity))},
        "debt_ratio": {"value": round(debt, 4), "points": int(round(c_debt))}
    }

    return score, breakdown
