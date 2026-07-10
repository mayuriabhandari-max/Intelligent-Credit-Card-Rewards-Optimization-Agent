"""
Layer 3 support / Node 5 (Rule Validation Node)

Decides whether the retrieved structured rules + vector chunks are strong
enough to base a recommendation on. If not, the agent should say
"I do not have enough information" instead of guessing -- this is the main
anti-hallucination gate in the pipeline.
"""

from dataclasses import dataclass


CONFIDENCE_THRESHOLD = 0.6
MIN_VECTOR_CHUNKS = 1


@dataclass
class ValidationResult:
    sufficient: bool
    reason: str
    confidence_label: str  # High | Medium-High | Medium | Low


def validate_rules(structured_rules: list[dict], vector_chunks: list[dict]) -> ValidationResult:
    if not structured_rules:
        return ValidationResult(
            sufficient=False,
            reason="No structured reward rule was found for this spend category on any known card.",
            confidence_label="Low",
        )

    if len(vector_chunks) < MIN_VECTOR_CHUNKS:
        return ValidationResult(
            sufficient=False,
            reason="No supporting document text was retrieved to corroborate the structured rule.",
            confidence_label="Low",
        )

    avg_confidence = sum(r["confidence_score"] for r in structured_rules) / len(structured_rules)

    if avg_confidence < CONFIDENCE_THRESHOLD:
        return ValidationResult(
            sufficient=False,
            reason=f"Average confidence score of retrieved rules ({avg_confidence:.2f}) "
                   f"is below the acceptance threshold ({CONFIDENCE_THRESHOLD}).",
            confidence_label="Low",
        )

    if avg_confidence >= 0.9:
        label = "High"
    elif avg_confidence >= 0.8:
        label = "Medium-High"
    else:
        label = "Medium"

    return ValidationResult(
        sufficient=True,
        reason="Structured rule(s) found with supporting document evidence.",
        confidence_label=label,
    )
