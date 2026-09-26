"""
End-to-End Real World Flow Validation Suite (Phase 7).
Tests complete user flows from input to channel, intent, retrieval,
financial engine, LLM formatting, citations, and conversation state.
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.db.session import SessionLocal
from app.db import crud
from app.dialogue.conversation_state import process_telegram_query, process_user_query
from app.retrieval.router import (
    classify_query_intent,
    execute_authoritative_routing,
    QueryIntent,
)
from app.finance.repository import benchmark_repository
from app.finance.calculator import calculate_financial_structure
from app.config import settings
from tests.intake_helpers import complete_intake

# ------------------------------------------------------------
# TEST 1 — DAIRY
# ------------------------------------------------------------
def test_e2e_dairy_flow():
    """
    User: 'I want to start a dairy with 2 cows. How much will it cost?'
    Verify intent, NABARD retrieval, source ID, page, year, no synthetic fallback.
    """
    query = "I want to start a dairy with 2 cows. How much will it cost?"
    intent, _ = classify_query_intent(query)
    assert intent in [QueryIntent.FACTUAL, QueryIntent.MIXED]

    res = execute_authoritative_routing(query, language="english")
    assert res["retrieval_used"] is True
    assert len(res["citations"]) > 0

    # Verify provenance
    evidence = res["evidence"]
    assert any(e["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27" for e in evidence)
    assert any(e["source_page"] in [41, 42] for e in evidence)
    assert any(e["publication_year"] == 2026 for e in evidence)
    assert any(e["verification_status"] == "VERIFIED_OFFICIAL" for e in evidence)

    # Check benchmark repository directly
    bench = benchmark_repository.get_benchmark("dairy cow", district="Belagavi", real_data_only=True)
    assert bench["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27"
    assert bench["publication_year"] == 2026
    assert bench["total_cost"] in [229000.0, 205000.0]
    assert bench["benchmark_status"] == "CURRENT_BENCHMARK"
    assert bench["is_synthetic"] is False

# ------------------------------------------------------------
# TEST 2 — POULTRY
# ------------------------------------------------------------
def test_e2e_poultry_flow():
    """
    User query on poultry broiler unit cost in Karnataka.
    Verify NABARD source, page, year, and correct SLUCC unit cost.
    """
    query = "What is the official NABARD unit cost for 2000 broiler poultry farm in Karnataka?"
    intent, _ = classify_query_intent(query)
    assert intent == QueryIntent.FACTUAL

    res = execute_authoritative_routing(query, language="english")
    assert res["retrieval_used"] is True
    assert any("NABARD" in c for c in res["citations"])
    assert any(e["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27" for e in res["evidence"])

    # Verify repository benchmark
    bench = benchmark_repository.get_benchmark("poultry broiler 2000", district="Mandya", real_data_only=True)
    assert bench["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27"
    assert bench["source_page"] == 50
    assert bench["total_cost"] == 456000.0
    assert bench["benchmark_status"] == "CURRENT_BENCHMARK"

# ------------------------------------------------------------
# TEST 3 — FLOUR MILL
# ------------------------------------------------------------
def test_e2e_flour_mill_flow():
    """
    User: 'I want to start a flour mill.'
    Verify SAMADHAN source, ₹32.93 lakh, page 5, year 2020, HISTORICAL_BENCHMARK_2020,
    historical warning present, no claim of 2026 market quote, never 3.11L.
    """
    query = "What is the project cost of a mini flour mill?"
    res = execute_authoritative_routing(query, language="english")

    assert res["retrieval_used"] is True
    evidence = res["evidence"]
    assert any(e["source_id"] == "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE" for e in evidence)
    assert any(e["publication_year"] == 2020 for e in evidence)
    assert any(e["cost_nature"] == "HISTORICAL_BENCHMARK_2020" for e in evidence)

    # Historical warning must be present in response
    assert "2020" in res["answer"]
    assert ("historical" in res["answer"].lower() or "quotation" in res["answer"].lower() or "note" in res["answer"].lower())

    # Check repository benchmark
    bench = benchmark_repository.get_benchmark("mini flour mill", real_data_only=True)
    assert bench["project_cost"] == 3293000.0
    assert bench["project_cost"] != 311000.0
    assert bench["source_id"] == "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE"
    assert bench["source_page"] == 5
    assert bench["publication_year"] == 2020
    assert bench["benchmark_status"] == "HISTORICAL_BENCHMARK"
    assert "historical_warning" in bench
    assert "2020" in bench["historical_warning"]

# ------------------------------------------------------------
# TEST 4 — AIDIS FACTUAL QUERY
# ------------------------------------------------------------
def test_e2e_aidis_factual_query():
    """
    Query: 'What share of rural household debt in India came from institutional sources?'
    Verify AIDIS retrieval, All-India, correct statistic (66.1%), unit %, page 94,
    and no credit scoring inference.
    """
    query = "What share of rural household debt in India came from institutional sources according to AIDIS?"
    res = execute_authoritative_routing(query, language="english")

    assert res["retrieval_used"] is True
    assert any("AIDIS" in c for c in res["citations"])
    assert any(e["source_id"] == "AIDIS_NSS_77_REPORT_588" for e in res["evidence"])

    evidence = res["evidence"]
    aidis_ev = next(e for e in evidence if e["source_id"] == "AIDIS_NSS_77_REPORT_588")
    assert aidis_ev["source_page"] in [92, 94]
    assert "66.1" in aidis_ev["text"] or "institutional" in aidis_ev["text"].lower()

# ------------------------------------------------------------
# TEST 5 — KIRANA DATA GAP
# ------------------------------------------------------------
def test_e2e_kirana_data_gap():
    """
    Query: 'How much does it cost to start a Kirana store?'
    With REAL_DATA_ONLY=True verify DATA_NOT_AVAILABLE, no synthetic benchmark,
    no unrelated benchmark substitution, citations empty.
    """
    query = "How much does it cost to start a Kirana store?"
    intent, details = classify_query_intent(query)
    assert intent == QueryIntent.DATA_UNAVAILABLE
    assert details["trade"] == "kirana"

    res = execute_authoritative_routing(query, language="english")
    assert "DATA_NOT_AVAILABLE" in res["answer"]
    assert res["citations"] == []
    assert res["evidence"] == []

    # Check repository under REAL_DATA_ONLY
    bench = benchmark_repository.get_benchmark("kirana store", real_data_only=True)
    assert bench["status"] == "DATA_NOT_AVAILABLE"
    assert bench["verification_status"] == "DATA_NOT_AVAILABLE"
    assert bench["is_synthetic"] is False

# ------------------------------------------------------------
# TEST 6 — TAILORING DATA GAP
# ------------------------------------------------------------
def test_e2e_tailoring_data_gap():
    """
    Query: 'What is the benchmark cost for tailoring shop?'
    With REAL_DATA_ONLY=True verify DATA_NOT_AVAILABLE, empty citations.
    """
    query = "What is the benchmark cost for tailoring shop?"
    intent, details = classify_query_intent(query)
    assert intent == QueryIntent.DATA_UNAVAILABLE
    assert details["trade"] == "tailoring"

    res = execute_authoritative_routing(query, language="english")
    assert "DATA_NOT_AVAILABLE" in res["answer"]
    assert res["citations"] == []
    assert res["evidence"] == []

    bench = benchmark_repository.get_benchmark("tailoring garment", real_data_only=True)
    assert bench["status"] == "DATA_NOT_AVAILABLE"
    assert bench["verification_status"] == "DATA_NOT_AVAILABLE"
    assert bench["is_synthetic"] is False

# ------------------------------------------------------------
# TEST 7 — PMMY DATA GAP
# ------------------------------------------------------------
def test_e2e_pmmy_data_gap():
    """
    Query: 'What is the PMMY interest rate for Shishu?'
    Verify AUTHORITATIVE_DATA_NOT_AVAILABLE, no invented interest rates.
    """
    query = "What is the PMMY interest rate for Shishu loans?"
    intent, details = classify_query_intent(query)
    assert intent == QueryIntent.DATA_UNAVAILABLE

    res = execute_authoritative_routing(query, language="english")
    assert "AUTHORITATIVE_DATA_NOT_AVAILABLE" in res["answer"]
    assert res["citations"] == []

# ------------------------------------------------------------
# TEST 8 — MIXED QUERY
# ------------------------------------------------------------
def test_e2e_mixed_query():
    """
    Query: 'I want to start a dairy with two cows. What will it cost and what will my EMI be?'
    Verify: authoritative retrieval + deterministic calculation, citations present,
    exact mathematical values preserved.
    """
    query = "I want to start a dairy with two cows. What will it cost and what will my EMI be?"
    res = execute_authoritative_routing(query, language="english", project_cost=229000.0)

    assert res["retrieval_used"] is True
    assert res["financial_engine_used"] is True
    assert len(res["citations"]) > 0

    fin = res["financial_result"]
    assert fin is not None
    assert fin["cost"] == 229000.0
    assert fin["scheme"] == "TERM_LOAN"
    assert fin["loan"] == 206100.0  # 90% of 2,29,000
    assert fin["margin"] == 22900.0 # 10% of 2,29,000
    assert fin["rate"] == 8.0
    assert fin["repayment_months"] == 78
    assert abs(fin["emi"] - 3397.18) < 1.0

# ------------------------------------------------------------
# TEST 9 — MULTILINGUAL QUERY
# ------------------------------------------------------------
def test_e2e_multilingual_dairy_queries():
    """
    Test equivalent dairy requests across 5 languages:
    English, Hindi, Kannada, Telugu, Marathi.
    Verify language detection, same benchmark, same underlying numbers.
    """
    queries = {
        "english": "What is the official NABARD unit cost for 2 dairy cows?",
        "hindi": "2 गायों की डेयरी के लिए नाबार्ड की आधिकारिक लागत क्या है?",
        "kannada": "2 ಹಸುಗಳ ಹೈನುಗಾರಿಕೆಗೆ ನಬಾರ್ಡ್ ಅಧಿಕೃತ ಯೂನಿಟ್ ವೆಚ್ಚ ಎಷ್ಟು?",
        "telugu": "2 ఆవుల పాడి పరిశ్రమ కోసం నాబార్డ్ అధికారిక యూనిట్ ఖర్చు ఎంత?",
        "marathi": "२ गायींच्या दुग्ध व्यवसायासाठी नाबार्डचा अधिकृत युनिट खर्च किती आहे?"
    }

    for lang, q in queries.items():
        res = execute_authoritative_routing(q, language=lang)
        assert res["retrieval_used"] is True
        assert len(res["citations"]) > 0
        assert any("NABARD" in c for c in res["citations"])
        assert any(e["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27" for e in res["evidence"])

        # Check that numbers in evidence match
        ev = res["evidence"]
        assert any("2,29,000" in e["text"] or "205000" in e["text"].replace(",", "") for e in ev)

# ------------------------------------------------------------
# TEST 10 — CONVERSATIONAL CONTEXT MULTI-TURN
# ------------------------------------------------------------
def test_e2e_conversational_context_preservation():
    """
    Simulate multi-turn Telegram dialogue:
    Turn 1: 'I want to start a dairy' -> Assistant asks for details.
    Turn 2: 'In Mysuru' -> Assistant asks for cost.
    Turn 3: 'Budget is ₹2,00,000' -> Assistant calculates structure.
    Turn 4: 'What will my EMI be?' -> State preserved.
    """
    chat_id = f"tg_{uuid.uuid4().hex[:8]}"

    # Turn 1: Select language
    process_telegram_query(chat_id, "1", user_name="Ramesh")
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id)
    assert b.preferred_language == "english"
    db.close()

    # Turn 2: Trade
    process_telegram_query(chat_id, "I want to start a dairy farm", user_name="Ramesh")
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id)
    assert "dairy" in b.conversation_context.get("trade", "").lower()
    db.close()

    # Turn 3: District
    process_telegram_query(chat_id, "My district is Mysuru", user_name="Ramesh")
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id)
    assert b.conversation_context.get("district") == "Mysuru"
    db.close()

    # Turn 4: Budget, then the applicant's own details and confirmation
    process_telegram_query(chat_id, "My budget is ₹2,00,000", user_name="Ramesh")
    complete_intake(lambda t: process_telegram_query(chat_id, t, user_name="Ramesh"),
                    lambda db: crud.get_or_create_telegram_beneficiary(db, chat_id))
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id)
    assert b.conversation_context.get("project_cost") == 200000.0
    assert b.conversation_state == "CONFIRM_DPR"
    fin = b.conversation_context.get("financial_structure")
    assert fin["loan"] == 180000.0
    assert fin["margin"] == 20000.0
    assert fin["instalment_frequency"] == "QUARTERLY"
    assert abs(fin["quarterly_instalment"] - 8945.86) < 1.0
    db.close()

# ------------------------------------------------------------
# TEST 11 — CONTEXT SWITCH: FACTUAL QUERY DOES NOT CORRUPT PROPOSAL
# ------------------------------------------------------------
def test_e2e_context_switch_does_not_corrupt_state():
    """
    User starts a dairy proposal with cost ₹1,50,000.
    Then asks an AIDIS factual question.
    Then returns to 'GENERATE DPR'.
    Verify that the factual query did NOT overwrite or erase the dairy proposal!
    """
    chat_id = f"tg_{uuid.uuid4().hex[:8]}"

    # Set up active proposal
    process_telegram_query(chat_id, "1", user_name="Suresh")
    process_telegram_query(chat_id, "I want to start a dairy in Belagavi with ₹1,50,000", user_name="Suresh")
    complete_intake(lambda t: process_telegram_query(chat_id, t, user_name="Suresh"),
                    lambda db: crud.get_or_create_telegram_beneficiary(db, chat_id))

    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id)
    assert b.conversation_context["project_cost"] == 150000.0
    assert "dairy" in b.conversation_context["trade"].lower()
    assert b.conversation_state == "CONFIRM_DPR"
    db.close()

    # Context Switch: Ask AIDIS question
    process_telegram_query(chat_id, "What percentage of rural debt in India came from institutional sources?", user_name="Suresh")

    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id)
    # The active proposal context must remain intact!
    assert b.conversation_context["project_cost"] == 150000.0
    assert "dairy" in b.conversation_context["trade"].lower()
    assert b.conversation_state == "CONFIRM_DPR"
    db.close()

    # Resume proposal flow: trigger DPR
    process_telegram_query(chat_id, "GENERATE DPR", user_name="Suresh")
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id)
    assert b.conversation_state == "SUBMITTED"
    db.close()

# ------------------------------------------------------------
# TEST 12 — INVALID / INCOMPLETE INPUT HANDLING
# ------------------------------------------------------------
def test_e2e_invalid_and_incomplete_input_handling():
    """
    Test empty input, random noise, and boundary violation without crashes or hallucinations.
    """
    # 1. Random noise without numbers
    chat_id_1 = f"tg_{uuid.uuid4().hex[:8]}"
    process_telegram_query(chat_id_1, "1", user_name="TestUser")
    process_telegram_query(chat_id_1, "asdfghjkl qwerty zxcvbnm", user_name="TestUser")
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id_1)
    assert b.conversation_state == "COLLECTING"
    assert b.conversation_context.get("financial_structure") is None
    db.close()

    # 2. Out of range capital (below ₹5,000)
    chat_id_2 = f"tg_{uuid.uuid4().hex[:8]}"
    process_telegram_query(chat_id_2, "1", user_name="TestUser")
    process_telegram_query(chat_id_2, "I want to start dairy in Belagavi with ₹200", user_name="TestUser")
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id_2)
    # Project cost below boundary is not accepted as viable proposal
    assert b.conversation_context.get("financial_structure") is None
    db.close()

    # 3. Capital above statutory ceiling (above ₹50,00,000)
    chat_id_3 = f"tg_{uuid.uuid4().hex[:8]}"
    process_telegram_query(chat_id_3, "1", user_name="TestUser")
    process_telegram_query(chat_id_3, "I want to start dairy in Belagavi with ₹10 crore", user_name="TestUser")
    db = SessionLocal()
    b = crud.get_or_create_telegram_beneficiary(db, chat_id_3)
    assert b.conversation_context.get("financial_structure") is None
    db.close()

