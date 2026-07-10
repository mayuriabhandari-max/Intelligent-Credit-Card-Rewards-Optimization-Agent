# Credit Card Rewards Optimization Agent (Capstone MVP)

A RAG + LangGraph agent that recommends which credit card to use for a
transaction, grounded in retrieved card terms rather than memory. Built to
match the capstone spec's Stage 1 + Stage 2 scope (RAG, structured reward
rules, calculator tool, memory, multi-turn clarification, human approval for
point transfers, and basic guardrails/monitoring).

Uses the **OpenAI API** (chat + embeddings) instead of Anthropic.

## What's implemented vs. the original spec

| Spec item | This implementation |
|---|---|
| PostgreSQL + pgvector | **SQLite** (structured tables) + **Chroma** (vector store) — same roles, zero infra to install for a local demo. Swappable later. |
| PDF ingestion | `rag/ingest_docs.py` reads `.txt` **and** `.pdf` from `data/raw_docs/` (PyPDF for PDFs). Three sample synthetic card-rule docs are included as `.txt` so the demo runs out of the box. |
| Structured reward rules table | `database/seed_data.py` seeds `reward_rules` / `transfer_partners` (hand-extracted here; swap for an LLM extraction step in production). |
| Calculator tool | `tools/calculator.py` |
| Retriever tool | `tools/retriever.py` (hybrid: vector chunks + structured SQL lookup) |
| Rule validator tool | `tools/rule_validator.py` (anti-hallucination gate) |
| Transfer calculator tool | `tools/transfer_calculator.py` |
| LangGraph workflow (10 nodes from spec) | `agents/graph.py` + `agents/nodes.py` |
| Human approval for transfers | `human_approval_node` — halts the graph and asks for "confirm" before computing a transfer route |
| Guardrails | `guardrail_node` — flags missing evidence, unmentioned caps, exclusions, missing approval |
| Monitoring | `recommendation_logs` SQLite table, populated per request in `backend/main.py` (swap in LangSmith/Phoenix callbacks for full tracing) |
| Streamlit UI | `app/streamlit_app.py` |
| FastAPI backend | `backend/main.py` |

## Setup (VS Code)

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your OpenAI key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...

# 4. Seed the structured database (reward_rules, transfer_partners)
python -m database.seed_data

# 5. Ingest the sample card documents into the vector store
python -m rag.ingest_docs
```

## Run

**Option A — Streamlit demo (recommended for the capstone demo):**
```bash
streamlit run app/streamlit_app.py
```

**Option B — FastAPI backend (for programmatic / Postman testing):**
```bash
uvicorn backend.main:app --reload
# then POST to http://localhost:8000/chat
# {"query": "I am spending Rs 50000 on flights, which card should I use?"}
```

## Testing

```bash
# Pure logic tests, no API key needed
python tests/test_calculator.py

# Needs OPENAI_API_KEY + steps 4 & 5 above completed first
python tests/test_retrieval.py
```

## Adding your own cards

Drop a `.txt` or `.pdf` file into `data/raw_docs/` (a `CARD NAME:`, `ISSUER:`,
`DOCUMENT TYPE:`, `EFFECTIVE DATE:` header block at the top is recommended —
see the sample files), then:
1. Re-run `python -m rag.ingest_docs` to embed it into Chroma.
2. Add matching rows to `database/seed_data.py` (`REWARD_RULES` /
   `TRANSFER_PARTNERS`) so the calculator tool has structured numbers to work
   with — the vector store alone is used for explanation/citation, not math.

## Folder structure

```
credit-card-rewards-agent/
  app/streamlit_app.py
  backend/main.py
  agents/          graph.py nodes.py state.py prompts.py
  tools/           calculator.py retriever.py rule_validator.py transfer_calculator.py
  rag/             ingest_docs.py chunk_documents.py
  database/        models.py db.py seed_data.py
  data/raw_docs/   sample card documents
  tests/
```

## Notes

- The three sample card documents in `data/raw_docs/` are **synthetic** data
  created for this learning project — they do not reflect real, current bank
  terms. Swap in real (redacted/legally-obtained) card PDFs before using this
  for anything beyond a demo.
- The system prompt (`agents/prompts.py`) explicitly instructs the model not
  to invent rates, exclusions, or partners, and to say "not enough
  information" when retrieval is weak — this is the core anti-hallucination
  guardrail described in the spec.





---------------------------
(base) PS C:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent> (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& "c:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent\.venv\Scripts\Activate.ps1")
(.venv) (base) PS C:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent> pip install -r requirements.txt                                                                                                                      
(.venv) (base) PS C:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent> python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY')[-8:])"                                        
KxvBSJIA              
(.venv) (base) PS C:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent> python -c "from dotenv import load_dotenv; load_dotenv(); import os; from openai import OpenAI; client=OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print(client.models.list())"

(.venv) (base) PS C:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent> streamlit run app\streamlit_app.py                                