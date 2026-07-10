from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):
    # conversation
    user_id: str
    query: str
    chat_history: list[dict]          # [{"role": "user"/"assistant", "content": str}]

    # user profile / memory
    cards_owned: list[str]
    preferred_reward_type: Optional[str]   # cashback | airline_miles | hotel_points
    point_value_inr: float

    # intent + extraction
    intent: str   # single_transaction | monthly_optimization | transfer_strategy | card_comparison | missing_information | general
    spend_amount: Optional[float]
    spend_category: Optional[str]
    transfer_points: Optional[float]
    transfer_goal: Optional[str]          # hotel | airline | cashback

    # clarification
    needs_clarification: bool
    clarification_question: Optional[str]

    # retrieval
    structured_rules: list[dict]
    vector_chunks: list[dict]
    transfer_partner_options: list[dict]

    # validation
    validation_sufficient: bool
    validation_reason: str
    confidence_label: str

    # calculation
    calc_results: list[dict]
    transfer_results: list[dict]

    # comparison
    ranked_cards: list[dict]

    # guardrails
    guardrail_flags: list[str]
    guardrail_passed: bool

    # human approval (for transfer strategy)
    requires_approval: bool
    approved: bool

    # output
    final_answer: str
    is_final: bool
