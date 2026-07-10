"""
Layer 4: Tool Use -- Calculator Tool

Given a structured reward rule (from the reward_rules table) and a spend
amount, computes the actual reward value in rupees. The LLM never does this
math itself -- it calls this function and reports the result, which is how
the project avoids hallucinated numbers.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CalculationResult:
    card_name: str
    spend_category: str
    spend_amount: float
    reward_type: str            # points | cashback
    raw_reward: float           # points earned, or cashback INR earned (pre-cap)
    cap_applied: bool
    capped_reward: float        # reward_value after applying cap
    point_value_inr: float
    reward_value_inr: float     # final INR value of the reward
    effective_return_pct: float
    exclusion_flag: bool
    notes: str


def calculate_reward(
    card_name: str,
    spend_category: str,
    spend_amount: float,
    reward_type: str,
    reward_rate: float,
    reward_unit: str,
    monthly_cap: Optional[float],
    exclusion_flag: bool,
    point_value_inr: float = 1.0,
) -> CalculationResult:
    """
    reward_unit is one of:
      - "points_per_100_inr": reward_rate points earned per Rs 100 spent
      - "percent_cashback": reward_rate is a cashback percentage (e.g. 5 = 5%)
    monthly_cap is expressed in the same unit as the reward itself
      (points for points-based cards, INR for cashback cards).
    """
    notes = []

    if reward_unit == "points_per_100_inr":
        raw_points = (spend_amount / 100.0) * reward_rate
        raw_reward_value_inr = raw_points * point_value_inr
        capped_points = raw_points
        cap_applied = False
        if monthly_cap is not None and raw_points > monthly_cap:
            capped_points = monthly_cap
            cap_applied = True
            notes.append(
                f"Monthly cap of {monthly_cap:.0f} points applies; "
                f"{raw_points - monthly_cap:.0f} points beyond the cap are not counted "
                f"in this estimate (may still earn at a lower standard rate -- verify with issuer)."
            )
        capped_value_inr = capped_points * point_value_inr
        raw_reward = raw_points
        capped_reward = capped_points

    elif reward_unit == "percent_cashback":
        raw_cashback_inr = spend_amount * (reward_rate / 100.0)
        cap_applied = False
        capped_cashback_inr = raw_cashback_inr
        if monthly_cap is not None and raw_cashback_inr > monthly_cap:
            capped_cashback_inr = monthly_cap
            cap_applied = True
            notes.append(
                f"Monthly cashback cap of Rs {monthly_cap:.0f} applies; "
                f"the uncapped estimate would have been Rs {raw_cashback_inr:.0f}."
            )
        raw_reward_value_inr = raw_cashback_inr
        capped_value_inr = capped_cashback_inr
        raw_reward = raw_cashback_inr
        capped_reward = capped_cashback_inr

    else:
        raise ValueError(f"Unsupported reward_unit: {reward_unit}")

    if exclusion_flag:
        notes.append(
            "This spend category is flagged as excluded or reduced-rate in the retrieved "
            "card terms. The reward shown reflects the reduced/excluded rate, not the "
            "card's standard accelerated rate."
        )

    effective_return_pct = (capped_value_inr / spend_amount * 100.0) if spend_amount > 0 else 0.0

    return CalculationResult(
        card_name=card_name,
        spend_category=spend_category,
        spend_amount=spend_amount,
        reward_type=reward_type,
        raw_reward=round(raw_reward, 2),
        cap_applied=cap_applied,
        capped_reward=round(capped_reward, 2),
        point_value_inr=point_value_inr,
        reward_value_inr=round(capped_value_inr, 2),
        effective_return_pct=round(effective_return_pct, 2),
        exclusion_flag=exclusion_flag,
        notes=" ".join(notes) if notes else "No caps or exclusions affected this estimate.",
    )
