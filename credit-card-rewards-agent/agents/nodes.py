import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from agents.state import AgentState
from agents.prompts import (
    SYSTEM_PROMPT, INTENT_CLASSIFICATION_PROMPT, CLARIFICATION_PROMPT, FINAL_ANSWER_PROMPT
)
from tools.retriever import retrieve_chunks, get_structured_rules, get_transfer_partners, list_all_card_names
from tools.calculator import calculate_reward
from tools.rule_validator import validate_rules
from tools.transfer_calculator import calculate_transfer

load_dotenv()

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
DEFAULT_POINT_VALUE = float(os.getenv("DEFAULT_POINT_VALUE_INR", "1.0"))

_llm = None


def get_llm(temperature: float = 0.0):
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model=CHAT_MODEL, temperature=temperature)
    return _llm


# ---------------------------------------------------------------------------
# Node 1 & 2: Intent Classification (also extracts amount/category/transfer info)
# ---------------------------------------------------------------------------
def intent_classification_node(state: AgentState) -> AgentState:
    llm = get_llm()
    prompt = INTENT_CLASSIFICATION_PROMPT.format(query=state["query"])
    response = llm.invoke(prompt)
    raw = response.content.strip()
    # defensive parsing in case the model wraps JSON in fences despite instructions
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "intent": "missing_information",
            "spend_amount": None,
            "spend_category": None,
            "transfer_points": None,
            "transfer_goal": None,
        }

    state["intent"] = parsed.get("intent", "missing_information")
    state["spend_amount"] = parsed.get("spend_amount")
    state["spend_category"] = (parsed.get("spend_category") or None)
    if state["spend_category"]:
        state["spend_category"] = state["spend_category"].lower()
    state["transfer_points"] = parsed.get("transfer_points")
    state["transfer_goal"] = parsed.get("transfer_goal")

    state.setdefault("point_value_inr", DEFAULT_POINT_VALUE)
    state.setdefault("cards_owned", [])
    return state


# ---------------------------------------------------------------------------
# Node 3: Clarification Node
# ---------------------------------------------------------------------------
def needs_clarification(state: AgentState) -> bool:
    intent = state.get("intent")
    if intent == "missing_information":
        return True
    if intent == "single_transaction" and (not state.get("spend_amount") or not state.get("spend_category")):
        return True
    if intent == "transfer_strategy" and not state.get("transfer_points"):
        return True
    # FIX: a recommendation is meaningless without knowing which cards are in play.
    # Previously cards_owned was never required, so retrieval silently compared
    # every card in the database regardless of what the user selected.
    if intent in ("single_transaction", "transfer_strategy") and not state.get("cards_owned"):
        return True
    return False


def clarification_node(state: AgentState) -> AgentState:
    llm = get_llm()
    prompt = CLARIFICATION_PROMPT.format(
        query=state["query"],
        intent=state.get("intent"),
        spend_amount=state.get("spend_amount"),
        spend_category=state.get("spend_category"),
        # FIX: the prompt needs to know cards_owned is missing, or it will keep
        # re-asking about spend_amount/spend_category even when those are known.
        cards_owned=state.get("cards_owned") or "none provided",
    )
    response = llm.invoke(prompt)
    state["needs_clarification"] = True
    state["clarification_question"] = response.content.strip()
    state["is_final"] = True
    state["final_answer"] = state["clarification_question"]
    return state


# ---------------------------------------------------------------------------
# Node 4: Retrieval Node
# ---------------------------------------------------------------------------
def retrieval_node(state: AgentState) -> AgentState:
    query = state["query"]
    category = state.get("spend_category") or "general"

    vector_chunks = retrieve_chunks(query, k=6)

    # FIX: previously get_structured_rules() was called with no card filter,
    # so it always pulled rules for every card in the category regardless of
    # what the user selected in "Cards you own". Now that cards_owned is
    # required upstream (see needs_clarification), pass it through so the
    # recommendation is actually scoped to the user's own cards.
    owned = state.get("cards_owned") or None  # None = no filter (compare all cards)
    structured_rules = get_structured_rules(category, card_names=owned) if category != "general" else []

    state["vector_chunks"] = vector_chunks
    state["structured_rules"] = structured_rules

    if state.get("intent") == "transfer_strategy" and state.get("cards_owned"):
        options = []
        for card in state["cards_owned"]:
            options.extend(get_transfer_partners(card))
        state["transfer_partner_options"] = options
    elif state.get("intent") == "transfer_strategy":
        # no owned cards specified -- pull transfer partners for all known cards
        options = []
        for card in list_all_card_names():
            options.extend(get_transfer_partners(card))
        state["transfer_partner_options"] = options
    else:
        state["transfer_partner_options"] = []

    return state


# ---------------------------------------------------------------------------
# Node 5: Rule Validation Node
# ---------------------------------------------------------------------------
def rule_validation_node(state: AgentState) -> AgentState:
    result = validate_rules(state.get("structured_rules", []), state.get("vector_chunks", []))
    state["validation_sufficient"] = result.sufficient
    state["validation_reason"] = result.reason
    state["confidence_label"] = result.confidence_label
    return state


# ---------------------------------------------------------------------------
# Node 6: Calculation Node
# ---------------------------------------------------------------------------
def calculation_node(state: AgentState) -> AgentState:
    if not state.get("validation_sufficient"):
        state["calc_results"] = []
        state["transfer_results"] = []
        return state

    calc_results = []
    spend_amount = state.get("spend_amount") or 0

    for rule in state.get("structured_rules", []):
        result = calculate_reward(
            card_name=rule["card_name"],
            spend_category=rule["spend_category"],
            spend_amount=spend_amount,
            reward_type=rule["reward_type"],
            reward_rate=rule["reward_rate"],
            reward_unit=rule["reward_unit"],
            monthly_cap=rule["monthly_cap"],
            exclusion_flag=rule["exclusion_flag"],
            point_value_inr=state.get("point_value_inr", DEFAULT_POINT_VALUE),
        )
        calc_results.append(result.__dict__)

    state["calc_results"] = calc_results

    # Transfer strategy calculations
    transfer_results = []
    if state.get("intent") == "transfer_strategy" and state.get("transfer_points"):
        for opt in state.get("transfer_partner_options", []):
            tr = calculate_transfer(
                card_name=opt["card_name"],
                partner_name=opt["partner_name"],
                partner_type=opt["partner_type"],
                points_requested=state["transfer_points"],
                transfer_ratio_points=opt["transfer_ratio_points"],
                transfer_ratio_partner_units=opt["transfer_ratio_partner_units"],
                minimum_points=opt["minimum_points"],
                maximum_points=opt["maximum_points"],
            )
            transfer_results.append(tr.__dict__)
    state["transfer_results"] = transfer_results

    return state


# ---------------------------------------------------------------------------
# Node 7: Comparison Node
# ---------------------------------------------------------------------------
def comparison_node(state: AgentState) -> AgentState:
    calc_results = state.get("calc_results", [])
    ranked = sorted(calc_results, key=lambda r: r["reward_value_inr"], reverse=True)
    state["ranked_cards"] = ranked
    return state


# ---------------------------------------------------------------------------
# Node 8: Guardrail Node
# ---------------------------------------------------------------------------
def guardrail_node(state: AgentState) -> AgentState:
    flags = []

    if state.get("validation_sufficient") and not state.get("vector_chunks"):
        flags.append("No retrieved document evidence backs this answer.")

    if state.get("validation_sufficient"):
        for r in state.get("calc_results", []):
            if r.get("cap_applied") and "cap" not in r.get("notes", "").lower():
                flags.append(f"Cap applied for {r['card_name']} but not mentioned in notes.")
        exclusions_present = any(r.get("exclusion_flag") for r in state.get("structured_rules", []))
        if exclusions_present:
            flags.append("Exclusion applies to at least one card for this category -- must be surfaced to user.")

    if state.get("intent") == "transfer_strategy" and not state.get("approved", False):
        flags.append("Transfer strategy requires human approval before finalizing routing.")

    state["guardrail_flags"] = flags
    state["guardrail_passed"] = True  # flags are informational; they get surfaced in the final answer
    return state


# ---------------------------------------------------------------------------
# Node 9: Human Approval Node (gate)
# ---------------------------------------------------------------------------
def requires_human_approval(state: AgentState) -> bool:
    return state.get("intent") == "transfer_strategy"


def human_approval_node(state: AgentState) -> AgentState:
    """If not yet approved, halts the graph and asks for confirmation.
    The calling layer (API/Streamlit) should re-invoke the graph with
    state['approved'] = True once the user confirms."""
    if not state.get("approved", False):
        state["requires_approval"] = True
        state["is_final"] = True
        state["final_answer"] = (
            "Before I calculate the point transfer routing, please confirm: "
            "I will use the currently retrieved partner transfer ratios and caps, "
            "and assume your redemption goal is "
            f"{state.get('transfer_goal') or 'the one you specified'}. "
            "Point transfers are often irreversible -- reply 'confirm' to proceed, "
            "or clarify your goal first."
        )
    else:
        state["requires_approval"] = False
    return state


# ---------------------------------------------------------------------------
# Node 10: Final Answer Node
# ---------------------------------------------------------------------------
def final_answer_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.2)
    prompt = FINAL_ANSWER_PROMPT.format(
        system_prompt=SYSTEM_PROMPT,
        query=state["query"],
        intent=state.get("intent"),
        structured_rules=json.dumps(state.get("structured_rules", []), indent=2),
        vector_chunks=json.dumps(
            [{"card": c["metadata"].get("card_name"), "text": c["text"][:400]} for c in state.get("vector_chunks", [])],
            indent=2,
        ),
        calc_results=json.dumps(state.get("calc_results", []), indent=2),
        transfer_results=json.dumps(state.get("transfer_results", []), indent=2),
        ranked_cards=json.dumps(state.get("ranked_cards", []), indent=2),
        validation_sufficient=state.get("validation_sufficient"),
        validation_reason=state.get("validation_reason"),
        confidence_label=state.get("confidence_label"),
        guardrail_flags=json.dumps(state.get("guardrail_flags", [])),
    )
    response = llm.invoke(prompt)
    state["final_answer"] = response.content.strip()
    state["is_final"] = True
    return state
