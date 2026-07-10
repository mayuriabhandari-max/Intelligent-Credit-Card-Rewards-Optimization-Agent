"""
Layer 3+ / Section 9: LangGraph Workflow Design

Wires the nodes in agents/nodes.py into the graph described in the capstone
spec:

  user_input -> intent_classification -> [clarification?] -> retrieval
             -> rule_validation -> calculation -> comparison -> guardrail
             -> [human_approval if transfer_strategy] -> final_answer
"""

from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.nodes import (
    intent_classification_node,
    needs_clarification,
    clarification_node,
    retrieval_node,
    rule_validation_node,
    calculation_node,
    comparison_node,
    guardrail_node,
    requires_human_approval,
    human_approval_node,
    final_answer_node,
)


def route_after_intent(state: AgentState) -> str:
    return "clarification" if needs_clarification(state) else "retrieval"


def route_after_guardrail(state: AgentState) -> str:
    return "human_approval" if requires_human_approval(state) else "generate_final_answer"


def route_after_approval(state: AgentState) -> str:
    return END if state.get("requires_approval") else "generate_final_answer"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intent_classification", intent_classification_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("rule_validation", rule_validation_node)
    graph.add_node("calculation", calculation_node)
    graph.add_node("comparison", comparison_node)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("generate_final_answer", final_answer_node)

    graph.set_entry_point("intent_classification")

    graph.add_conditional_edges(
        "intent_classification",
        route_after_intent,
        {"clarification": "clarification", "retrieval": "retrieval"},
    )
    graph.add_edge("clarification", END)

    graph.add_edge("retrieval", "rule_validation")
    graph.add_edge("rule_validation", "calculation")
    graph.add_edge("calculation", "comparison")
    graph.add_edge("comparison", "guardrail")

    graph.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {"human_approval": "human_approval", "generate_final_answer": "generate_final_answer"},
    )

    graph.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {END: END, "generate_final_answer": "generate_final_answer"},
    )

    graph.add_edge("generate_final_answer", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
