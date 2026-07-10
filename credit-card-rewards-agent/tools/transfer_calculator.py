"""
Tool used by the Point Transfer Strategy use case (Use Case 3).
Calculates how many partner units a given number of card points converts to,
respecting minimum/maximum transfer limits from the transfer_partners table.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TransferResult:
    card_name: str
    partner_name: str
    partner_type: str
    points_requested: float
    points_transferable: float
    partner_units_received: float
    within_limits: bool
    limit_notes: str


def calculate_transfer(
    card_name: str,
    partner_name: str,
    partner_type: str,
    points_requested: float,
    transfer_ratio_points: float,
    transfer_ratio_partner_units: float,
    minimum_points: Optional[float],
    maximum_points: Optional[float],
) -> TransferResult:
    notes = []
    points_transferable = points_requested
    within_limits = True

    if minimum_points is not None and points_requested < minimum_points:
        within_limits = False
        notes.append(
            f"Requested {points_requested:.0f} points is below the minimum transfer "
            f"threshold of {minimum_points:.0f} for {partner_name}. No transfer can be made "
            f"until you have at least the minimum."
        )
        points_transferable = 0

    if maximum_points is not None and points_requested > maximum_points:
        within_limits = False
        points_transferable = maximum_points
        notes.append(
            f"Requested {points_requested:.0f} points exceeds the maximum yearly transfer "
            f"limit of {maximum_points:.0f} for {partner_name}. Only {maximum_points:.0f} "
            f"points can be transferred; the remainder would need to wait for the next cycle."
        )

    partner_units = 0.0
    if transfer_ratio_points > 0:
        partner_units = (points_transferable / transfer_ratio_points) * transfer_ratio_partner_units

    return TransferResult(
        card_name=card_name,
        partner_name=partner_name,
        partner_type=partner_type,
        points_requested=points_requested,
        points_transferable=points_transferable,
        partner_units_received=round(partner_units, 2),
        within_limits=within_limits,
        limit_notes=" ".join(notes) if notes else "Requested transfer is within min/max limits.",
    )
