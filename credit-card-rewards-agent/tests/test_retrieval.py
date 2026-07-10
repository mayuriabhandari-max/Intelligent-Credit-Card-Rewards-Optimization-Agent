"""
These tests require:
  1. OPENAI_API_KEY set in your environment (.env)
  2. database/seed_data.py already run (structured tables populated)
  3. rag/ingest_docs.py already run (Chroma collection populated)

Run with: python -m pytest tests/test_retrieval.py -v
(or just: python tests/test_retrieval.py)
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.retriever import get_structured_rules, retrieve_chunks, get_transfer_partners


def test_structured_rules_flights():
    rules = get_structured_rules("flights")
    card_names = {r["card_name"] for r in rules}
    assert "Axis Atlas" in card_names
    assert "HDFC Diners Club Black" in card_names
    assert "SBI Cashback" in card_names


def test_structured_rules_rent_all_excluded():
    rules = get_structured_rules("rent")
    assert all(r["exclusion_flag"] for r in rules)


def test_transfer_partners_axis():
    partners = get_transfer_partners("Axis Atlas")
    names = {p["partner_name"] for p in partners}
    assert "Air Voyage Miles" in names
    assert "GlobalStay Hotel Points" in names


def test_vector_retrieval_flights():
    chunks = retrieve_chunks("flight reward rate accelerated", k=3)
    assert len(chunks) > 0


if __name__ == "__main__":
    test_structured_rules_flights()
    test_structured_rules_rent_all_excluded()
    test_transfer_partners_axis()
    test_vector_retrieval_flights()
    print("All retrieval tests passed.")
