"""
Layer 2: Retrieval Tool

Combines:
  (a) vector search over the Chroma collection of card-document chunks
      (unstructured evidence, used for explanation / citation), and
  (b) structured lookup against the reward_rules table
      (used by the calculator tool for exact numbers).

This is the "hybrid retrieval" mentioned in the tech stack section.
"""

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import chromadb

from database.db import get_session
from database.models import RewardRule, TransferPartner

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_store")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = "card_document_chunks"

_embeddings = None
_client = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return _embeddings


def _get_collection():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client.get_or_create_collection(name=COLLECTION_NAME)


def retrieve_chunks(query: str, k: int = 6, card_name: str | None = None) -> list[dict]:
    """Vector search over card document chunks. Optionally filter by card_name."""
    collection = _get_collection()
    query_vector = _get_embeddings().embed_query(query)

    where = {"card_name": card_name} if card_name else None
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=where,
    )

    chunks = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for i in range(len(ids)):
        chunks.append({
            "chunk_id": ids[i],
            "text": docs[i],
            "metadata": metas[i],
            "distance": dists[i],
        })
    return chunks


def get_structured_rules(spend_category: str, card_names: list[str] | None = None) -> list[dict]:
    """Structured lookup: exact reward rules for a category, optionally filtered by card."""
    session = get_session()
    try:
        q = session.query(RewardRule).filter(RewardRule.spend_category == spend_category.lower())
        if card_names:
            q = q.filter(RewardRule.card_name.in_(card_names))
        rows = q.all()
        return [
            {
                "card_name": r.card_name,
                "spend_category": r.spend_category,
                "reward_type": r.reward_type,
                "reward_rate": r.reward_rate,
                "reward_unit": r.reward_unit,
                "monthly_cap": r.monthly_cap,
                "annual_cap": r.annual_cap,
                "exclusion_flag": r.exclusion_flag,
                "milestone_condition": r.milestone_condition,
                "source_document": r.source_document,
                "confidence_score": r.confidence_score,
            }
            for r in rows
        ]
    finally:
        session.close()


def get_transfer_partners(card_name: str) -> list[dict]:
    session = get_session()
    try:
        rows = session.query(TransferPartner).filter(TransferPartner.card_name == card_name).all()
        return [
            {
                "card_name": r.card_name,
                "partner_name": r.partner_name,
                "partner_type": r.partner_type,
                "transfer_ratio_points": r.transfer_ratio_points,
                "transfer_ratio_partner_units": r.transfer_ratio_partner_units,
                "minimum_points": r.minimum_points,
                "maximum_points": r.maximum_points,
                "source_document": r.source_document,
            }
            for r in rows
        ]
    finally:
        session.close()


def list_all_card_names() -> list[str]:
    session = get_session()
    try:
        rows = session.query(RewardRule.card_name).distinct().all()
        return sorted({r[0] for r in rows})
    finally:
        session.close()
