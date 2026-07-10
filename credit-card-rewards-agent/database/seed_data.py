"""
Seeds the structured tables (reward_rules, transfer_partners, card_documents)
with data manually extracted from the sample card documents in data/raw_docs/.

In a production version, this extraction would be done by an LLM extraction
step over the ingested chunks. For this capstone MVP we hand-encode it so the
calculator tool has reliable, structured numbers to work with, while the raw
text still lives in the vector store for retrieval / explanation / citation.
"""

from database.db import init_db, get_session
from database.models import CardDocument, RewardRule, TransferPartner

REWARD_RULES = [
    # Axis Atlas
    dict(card_name="Axis Atlas", spend_category="flights", reward_type="points",
         reward_rate=5, reward_unit="points_per_100_inr", monthly_cap=20000, annual_cap=None,
         exclusion_flag=False, milestone_condition="Rs 3,00,000 annual spend -> 2500 bonus miles; Rs 7,50,000 -> +2500 miles + lounge access",
         source_document="axis_atlas.txt", confidence_score=0.95),
    dict(card_name="Axis Atlas", spend_category="hotels", reward_type="points",
         reward_rate=5, reward_unit="points_per_100_inr", monthly_cap=20000, annual_cap=None,
         exclusion_flag=False, milestone_condition="Shares combined cap with flights",
         source_document="axis_atlas.txt", confidence_score=0.95),
    dict(card_name="Axis Atlas", spend_category="dining", reward_type="points",
         reward_rate=2, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=False, milestone_condition=None,
         source_document="axis_atlas.txt", confidence_score=0.9),
    dict(card_name="Axis Atlas", spend_category="groceries", reward_type="points",
         reward_rate=2, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=False, milestone_condition=None,
         source_document="axis_atlas.txt", confidence_score=0.9),
    dict(card_name="Axis Atlas", spend_category="utilities", reward_type="points",
         reward_rate=0.5, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="axis_atlas.txt", confidence_score=0.9),
    dict(card_name="Axis Atlas", spend_category="rent", reward_type="points",
         reward_rate=0, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="axis_atlas.txt", confidence_score=0.95),
    dict(card_name="Axis Atlas", spend_category="insurance", reward_type="points",
         reward_rate=0.5, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="axis_atlas.txt", confidence_score=0.9),
    dict(card_name="Axis Atlas", spend_category="international", reward_type="points",
         reward_rate=5, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=False, milestone_condition=None,
         source_document="axis_atlas.txt", confidence_score=0.9),

    # HDFC Diners Club Black
    dict(card_name="HDFC Diners Club Black", spend_category="flights", reward_type="points",
         reward_rate=2.22, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=False, milestone_condition="Rs 4,00,000 -> lounge set; Rs 8,00,000 -> 10000 bonus points",
         source_document="hdfc_diners_black.txt", confidence_score=0.85),
    dict(card_name="HDFC Diners Club Black", spend_category="hotels", reward_type="points",
         reward_rate=3.33, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=False, milestone_condition="Rate shown assumes SmartBuy booking channel",
         source_document="hdfc_diners_black.txt", confidence_score=0.8),
    dict(card_name="HDFC Diners Club Black", spend_category="dining", reward_type="points",
         reward_rate=7.33, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=False, milestone_condition="Rate assumes partnered dining program",
         source_document="hdfc_diners_black.txt", confidence_score=0.8),
    dict(card_name="HDFC Diners Club Black", spend_category="groceries", reward_type="points",
         reward_rate=2.22, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=False, milestone_condition=None,
         source_document="hdfc_diners_black.txt", confidence_score=0.85),
    dict(card_name="HDFC Diners Club Black", spend_category="utilities", reward_type="points",
         reward_rate=2.22, reward_unit="points_per_100_inr", monthly_cap=2000, annual_cap=None,
         exclusion_flag=False, milestone_condition=None,
         source_document="hdfc_diners_black.txt", confidence_score=0.85),
    dict(card_name="HDFC Diners Club Black", spend_category="rent", reward_type="points",
         reward_rate=0, reward_unit="points_per_100_inr", monthly_cap=None, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="hdfc_diners_black.txt", confidence_score=0.9),
    dict(card_name="HDFC Diners Club Black", spend_category="insurance", reward_type="points",
         reward_rate=2.22, reward_unit="points_per_100_inr", monthly_cap=5000, annual_cap=None,
         exclusion_flag=False, milestone_condition=None,
         source_document="hdfc_diners_black.txt", confidence_score=0.85),

    # SBI Cashback
    dict(card_name="SBI Cashback", spend_category="flights", reward_type="cashback",
         reward_rate=5, reward_unit="percent_cashback", monthly_cap=5000, annual_cap=None,
         exclusion_flag=False, milestone_condition="Online booking rate; combined Rs 5000/cycle cap across all categories",
         source_document="sbi_cashback.txt", confidence_score=0.9),
    dict(card_name="SBI Cashback", spend_category="hotels", reward_type="cashback",
         reward_rate=5, reward_unit="percent_cashback", monthly_cap=5000, annual_cap=None,
         exclusion_flag=False, milestone_condition="Online booking rate; combined Rs 5000/cycle cap across all categories",
         source_document="sbi_cashback.txt", confidence_score=0.9),
    dict(card_name="SBI Cashback", spend_category="dining", reward_type="cashback",
         reward_rate=1, reward_unit="percent_cashback", monthly_cap=5000, annual_cap=None,
         exclusion_flag=False, milestone_condition="5% if via online food delivery app, else 1%",
         source_document="sbi_cashback.txt", confidence_score=0.85),
    dict(card_name="SBI Cashback", spend_category="groceries", reward_type="cashback",
         reward_rate=5, reward_unit="percent_cashback", monthly_cap=5000, annual_cap=None,
         exclusion_flag=False, milestone_condition="5% online, 1% offline/in-store",
         source_document="sbi_cashback.txt", confidence_score=0.85),
    dict(card_name="SBI Cashback", spend_category="utilities", reward_type="cashback",
         reward_rate=1, reward_unit="percent_cashback", monthly_cap=5000, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="sbi_cashback.txt", confidence_score=0.9),
    dict(card_name="SBI Cashback", spend_category="rent", reward_type="cashback",
         reward_rate=0, reward_unit="percent_cashback", monthly_cap=None, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="sbi_cashback.txt", confidence_score=0.95),
    dict(card_name="SBI Cashback", spend_category="insurance", reward_type="cashback",
         reward_rate=0, reward_unit="percent_cashback", monthly_cap=None, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="sbi_cashback.txt", confidence_score=0.95),
    dict(card_name="SBI Cashback", spend_category="fuel", reward_type="cashback",
         reward_rate=0, reward_unit="percent_cashback", monthly_cap=None, annual_cap=None,
         exclusion_flag=True, milestone_condition=None,
         source_document="sbi_cashback.txt", confidence_score=0.95),
]

TRANSFER_PARTNERS = [
    dict(card_name="Axis Atlas", partner_name="Air Voyage Miles", partner_type="airline",
         transfer_ratio_points=1, transfer_ratio_partner_units=1,
         minimum_points=1000, maximum_points=200000,
         effective_date="2026-01-01", source_document="axis_atlas.txt"),
    dict(card_name="Axis Atlas", partner_name="GlobalStay Hotel Points", partner_type="hotel",
         transfer_ratio_points=2, transfer_ratio_partner_units=1,
         minimum_points=2000, maximum_points=100000,
         effective_date="2026-01-01", source_document="axis_atlas.txt"),
    dict(card_name="HDFC Diners Club Black", partner_name="Air Voyage Miles", partner_type="airline",
         transfer_ratio_points=3, transfer_ratio_partner_units=1,
         minimum_points=3000, maximum_points=150000,
         effective_date="2026-01-01", source_document="hdfc_diners_black.txt"),
    dict(card_name="HDFC Diners Club Black", partner_name="GlobalStay Hotel Points", partner_type="hotel",
         transfer_ratio_points=3, transfer_ratio_partner_units=1,
         minimum_points=3000, maximum_points=120000,
         effective_date="2026-01-01", source_document="hdfc_diners_black.txt"),
    # SBI Cashback has no transfer program -- intentionally omitted.
]

CARD_DOCS = [
    dict(card_name="Axis Atlas", issuer="Axis Bank", document_type="Reward Program Terms",
         effective_date="2026-01-01", source_path="data/raw_docs/axis_atlas.txt"),
    dict(card_name="HDFC Diners Club Black", issuer="HDFC Bank", document_type="Reward Program Terms",
         effective_date="2026-01-01", source_path="data/raw_docs/hdfc_diners_black.txt"),
    dict(card_name="SBI Cashback", issuer="State Bank of India", document_type="Reward Program Terms",
         effective_date="2026-01-01", source_path="data/raw_docs/sbi_cashback.txt"),
]


def seed():
    init_db()
    session = get_session()
    try:
        if session.query(RewardRule).count() == 0:
            for row in REWARD_RULES:
                session.add(RewardRule(**row))
        if session.query(TransferPartner).count() == 0:
            for row in TRANSFER_PARTNERS:
                session.add(TransferPartner(**row))
        if session.query(CardDocument).count() == 0:
            for row in CARD_DOCS:
                session.add(CardDocument(**row))
        session.commit()
        print("Seed complete: reward_rules, transfer_partners, card_documents populated.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
