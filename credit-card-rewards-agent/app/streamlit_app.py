"""
Stage 3 UI: Streamlit chat app.

Run with:  streamlit run app/streamlit_app.py

This calls the LangGraph agent directly (no need to run the FastAPI server
separately, though you can point this at the API instead by swapping
run_graph() for a requests.post call to http://localhost:8000/chat).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from database.db import init_db
from agents.graph import get_graph

st.set_page_config(page_title="Credit Card Rewards Optimizer", page_icon="💳")
init_db()
graph = get_graph()

st.title("💳 Credit Card Rewards Optimization Agent")
st.caption("RAG + LangGraph agent demo — grounded in retrieved card rules, not memory.")

with st.sidebar:
    st.header("Your profile")
    cards_owned = st.multiselect(
        "Cards you own",
        ["Axis Atlas", "HDFC Diners Club Black", "SBI Cashback"],
        default=["Axis Atlas", "HDFC Diners Club Black", "SBI Cashback"],
    )
    point_value = st.number_input("Assumed value per point/mile (INR)", min_value=0.1, value=1.0, step=0.1)
    st.divider()
    st.markdown(
        "**Try asking:**\n"
        "- I am spending Rs 50000 on flights, which card should I use?\n"
        "- Which card is best for rent payment?\n"
        "- I have 40000 points, should I transfer to hotel or airline partners?"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_transfer_points" not in st.session_state:
    st.session_state.pending_transfer_points = None
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about your credit card rewards...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    approved = False
    if st.session_state.awaiting_approval and user_input.strip().lower() in ("confirm", "yes", "approve", "approved"):
        approved = True

    state = {
        "user_id": "streamlit_user",
        "query": user_input,
        "cards_owned": cards_owned,
        "point_value_inr": point_value,
        "approved": approved,
    }
    if st.session_state.pending_transfer_points is not None:
        state["transfer_points"] = st.session_state.pending_transfer_points

    with st.spinner("Retrieving rules and calculating..."):
        result = graph.invoke(state)

    answer = result.get("final_answer", "")
    st.session_state.awaiting_approval = result.get("requires_approval", False)
    if result.get("transfer_points"):
        st.session_state.pending_transfer_points = result.get("transfer_points")

    with st.chat_message("assistant"):
        st.markdown(answer)
        if result.get("confidence_label"):
            st.caption(f"Confidence: {result['confidence_label']} | Intent: {result.get('intent')}")
        if result.get("guardrail_flags"):
            with st.expander("Guardrail notes"):
                for f in result["guardrail_flags"]:
                    st.write(f"- {f}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
