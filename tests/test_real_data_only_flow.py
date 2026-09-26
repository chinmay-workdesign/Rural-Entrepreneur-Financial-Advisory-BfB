"""
REAL_DATA_ONLY conversational and DPR behaviour.

1. REAL_DATA_ONLY defaults to True
2. Trade without an official benchmark: loan maths from the user's budget, no DSCR, explicit notice
3. Verified NABARD trade: NABARD unit cost quoted, no DSCR, no notice
4. 'GENERATE DPR' without trade/district/budget asks for them instead of assuming values
5. DPR PDF for a trade without an official benchmark: no reference cost, no DSCR
"""
import io
import uuid
from unittest.mock import patch

from pypdf import PdfReader

from app.config import Settings
from app.db import crud
from app.db.session import SessionLocal
from app.dialogue.conversation_state import NO_BENCHMARK_NOTICE, process_user_query
from app.dpr.generator import generate_dpr_pdf
from tests.intake_helpers import complete_intake


def _new_phone() -> str:
    return f"91{uuid.uuid4().int % 10000000000:010d}"


def _run(phone: str, text: str) -> list:
    """Run one user turn and return every text message the bot sent."""
    with patch("app.dialogue.conversation_state.send_channel_text") as sent:
        process_user_query(phone, text)
    return [c.args[1] for c in sent.call_args_list]


def _run_to_advice(phone: str, text: str) -> list:
    """Opening message plus the intake answers and confirmation; returns every message sent."""
    messages = _run(phone, text)
    complete_intake(lambda t: messages.extend(_run(phone, t)), lambda db: crud.get_or_create_beneficiary(db, phone))
    return messages


def _has_notice(messages: list) -> bool:
    return any(notice in m for m in messages for notice in NO_BENCHMARK_NOTICE.values())


# 1. REAL_DATA_ONLY defaults to True
def test_real_data_only_defaults_to_true(monkeypatch):
    monkeypatch.delenv("REAL_DATA_ONLY", raising=False)
    assert Settings(_env_file=None).REAL_DATA_ONLY is True


# 2. No official benchmark: loan maths kept, DSCR omitted, notice appended
def test_no_benchmark_trade_gets_loan_maths_without_dscr():
    phone = _new_phone()
    messages = _run_to_advice(phone, "I want to start a kirana stall in Belagavi with ₹1,20,000")

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, phone)
        ctx = beneficiary.conversation_context
        assert beneficiary.conversation_state == "CONFIRM_DPR"
        assert ctx["financial_structure"]["loan"] == 108000.0
        assert ctx["benchmark_available"] is False
        assert "dscr" not in ctx["cashflows"]

        proposals = [p for p in crud.get_proposals(db, status="DRAFT") if p.beneficiary_id == beneficiary.id]
        assert len(proposals) == 1
        assert proposals[0].projected_dscr is None
    finally:
        db.close()

    assert _has_notice(messages)


# 3. Verified NABARD trade: NABARD unit cost quoted, no DSCR, no notice
def test_verified_trade_quotes_nabard_cost_and_has_no_notice():
    phone = _new_phone()
    messages = _run_to_advice(phone, "I want to start a dairy with 2 cows in Dharwad with ₹2,29,000")

    db = SessionLocal()
    try:
        ctx = crud.get_or_create_beneficiary(db, phone).conversation_context
        assert ctx["benchmark_available"] is True
        assert "dscr" not in ctx["cashflows"]
    finally:
        db.close()

    assert not _has_notice(messages)
    assert any("NABARD Karnataka 2026-27 unit cost" in m and "2,29,000" in m for m in messages)


# 4. DPR request with nothing known: ask, never assume a budget
def test_generate_dpr_without_details_asks_instead_of_assuming():
    phone = _new_phone()
    db = SessionLocal()
    try:
        crud.get_or_create_beneficiary(db, phone, default_lang="english")
    finally:
        db.close()

    with patch("app.dialogue.conversation_state.generate_dpr_pdf") as pdf:
        messages = _run(phone, "GENERATE DPR")
    pdf.assert_not_called()

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, phone)
        assert beneficiary.conversation_state == "COLLECTING"
        assert "financial_structure" not in (beneficiary.conversation_context or {})
        assert not [p for p in crud.get_proposals(db) if p.beneficiary_id == beneficiary.id]
    finally:
        db.close()

    assert messages
    assert not any("Generating your bank-ready" in m for m in messages)


# 5. DPR PDF without official benchmark omits DSCR projections
def test_dpr_pdf_without_benchmark_omits_dscr():
    proposal = {
        "id": "22222222-3333-4444-5555-666666666666",
        "business_trade": "Kirana Stall",
        "scheme_tier": "MICRO_FINANCE",
        "project_cost": 120000.0,
        "sanctioned_loan": 108000.0,
        "beneficiary_margin": 12000.0,
        "monthly_emi": 3584.22,
        "projected_dscr": None,
        "status": "DRAFT",
    }
    beneficiary = {
        "id": "beneficiary-uuid-2",
        "full_name": "Test Applicant",
        "whatsapp_number": "919800000000",
        "district": "Belagavi",
        "state": "Karnataka",
        "preferred_language": "english",
    }

    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf_bytes)).pages)
    compact = "".join(text.split())  # narrow table cells wrap words across lines

    assert "Not available" in text
    assert "Not computed" in text
    assert "Year 1 (70%)" not in text
    assert "DATA_NOT_AVAILABLE" in compact
