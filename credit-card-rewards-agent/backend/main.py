import time
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from database.db import init_db, get_session
from database.models import RecommendationLog
from agents.graph import get_graph

app = FastAPI(title="Credit Card Rewards Optimization Agent")

init_db()
graph = get_graph()


class ChatRequest(BaseModel):
    user_id: str = "demo_user"
    query: str
    cards_owned: Optional[list[str]] = None
    point_value_inr: Optional[float] = None
    approved: Optional[bool] = False           # set True on the follow-up turn to confirm a transfer
    transfer_points: Optional[float] = None    # can be re-supplied on the follow-up turn


class ChatResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    needs_clarification: bool = False
    requires_approval: bool = False
    confidence_label: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    start = time.time()

    initial_state = {
        "user_id": req.user_id,
        "query": req.query,
        "cards_owned": req.cards_owned or [],
        "point_value_inr": req.point_value_inr or 1.0,
        "approved": req.approved or False,
    }
    if req.transfer_points is not None:
        initial_state["transfer_points"] = req.transfer_points

    result = graph.invoke(initial_state)

    latency_ms = (time.time() - start) * 1000

    # --- Monitoring: log this turn (Layer/Node: monitoring) ---
    session = get_session()
    try:
        ranked = result.get("ranked_cards", [])
        best = ranked[0] if ranked else None
        log = RecommendationLog(
            user_id=req.user_id,
            query_text=req.query,
            intent=result.get("intent"),
            retrieved_chunks_summary=json.dumps(
                [c["metadata"].get("card_name") for c in result.get("vector_chunks", [])]
            ),
            recommended_card=best["card_name"] if best else None,
            estimated_value=best["reward_value_inr"] if best else None,
            confidence_score=result.get("confidence_label"),
            guardrail_flags=json.dumps(result.get("guardrail_flags", [])),
            latency_ms=latency_ms,
            token_usage=None,  # wire up real token accounting via LangSmith/callbacks if desired
        )
        session.add(log)
        session.commit()
    finally:
        session.close()

    return ChatResponse(
        answer=result.get("final_answer", ""),
        intent=result.get("intent"),
        needs_clarification=result.get("needs_clarification", False),
        requires_approval=result.get("requires_approval", False),
        confidence_label=result.get("confidence_label"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
