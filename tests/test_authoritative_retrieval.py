"""
Unit and Integration Test Suite for Local Authoritative Knowledge Retrieval (FastEmbed + Qdrant).
Implements all 15 required Phase 5 scenarios:
1. Dairy factual query
2. Poultry factual query
3. Flour Mill factual query
4. PMEGP factual query
5. AIDIS factual query
6. Tailoring DATA_NOT_AVAILABLE
7. Kirana DATA_NOT_AVAILABLE
8. PMMY unverified handling
9. Dairy financial calculation
10. Mixed dairy query
11. Flour Mill historical warning
12. Citation generation
13. REAL_DATA_ONLY synthetic fallback prevention
14. Qdrant unavailable behavior
15. Voice -> STT -> retrieval routing
"""
import pytest
from unittest.mock import patch, MagicMock
from app.config import settings
from app.retrieval.service import retrieve_evidence, EvidenceRetrievalService, QdrantUnavailableError
from app.retrieval.models import RetrievedEvidence
from app.retrieval.context_builder import build_grounded_llm_messages
from app.retrieval.router import (
    classify_query_intent,
    execute_authoritative_routing,
    QueryIntent,
)
from app.finance.repository import BenchmarkRepository

# 1. Dairy factual query
def test_dairy_factual_query():
    res = execute_authoritative_routing("What is the NABARD cost for a 2 cow dairy unit?", language="english")
    assert res["intent"] == QueryIntent.FACTUAL.value
    assert len(res["citations"]) >= 1
    assert any("NABARD" in c and "p.41" in c for c in res["citations"])
    assert any("2,29,000" in e["text"] or "2,05,000" in e["text"] for e in res["evidence"])

# 2. Poultry factual query
def test_poultry_factual_query():
    res = execute_authoritative_routing("What is the NABARD unit cost for 2000 broiler poultry?", language="english")
    assert res["intent"] == QueryIntent.FACTUAL.value
    assert len(res["citations"]) >= 1
    assert any("NABARD" in c and "p.50" in c for c in res["citations"])
    assert any("4,56,000" in e["text"] for e in res["evidence"])

# 3. Flour Mill factual query
def test_flour_mill_factual_query():
    res = execute_authoritative_routing("What is the mini flour mill machinery cost in project profile?", language="english")
    assert res["intent"] == QueryIntent.FACTUAL.value
    assert any("SAMADHAN" in c or "Flour Mill" in c for c in res["citations"])
    assert any("32.93" in e["text"] for e in res["evidence"])

# 4. PMEGP factual query
def test_pmegp_factual_query():
    res = execute_authoritative_routing("What subsidy does PMEGP provide in rural area?", language="english")
    assert res["intent"] == QueryIntent.FACTUAL.value
    assert any("PMEGP" in c for c in res["citations"])
    assert any("35%" in e["text"] for e in res["evidence"])

# 5. AIDIS factual query
def test_aidis_factual_query():
    res = execute_authoritative_routing("What does AIDIS say about rural indebtedness?", language="english")
    assert res["intent"] == QueryIntent.FACTUAL.value
    assert any("AIDIS" in c for c in res["citations"])
    assert any("48.1%" in e["text"] or "non-institutional" in e["text"] or "67.2%" in e["text"] for e in res["evidence"])

# 6. Tailoring DATA_NOT_AVAILABLE
def test_tailoring_data_not_available():
    res = execute_authoritative_routing("What is the official benchmark cost for tailoring unit?", language="english")
    assert res["intent"] == QueryIntent.DATA_UNAVAILABLE.value
    assert "DATA_NOT_AVAILABLE" in res["answer"]
    assert "Tailoring" in res["answer"]
    assert res["citations"] == []
    assert res["evidence"] == []

# 7. Kirana DATA_NOT_AVAILABLE
def test_kirana_data_not_available():
    res = execute_authoritative_routing("What is the official cost of a kirana shop?", language="english")
    assert res["intent"] == QueryIntent.DATA_UNAVAILABLE.value
    assert "DATA_NOT_AVAILABLE" in res["answer"]
    assert "Kirana" in res["answer"]
    assert res["citations"] == []
    # Ensures semantic similarity does not return dairy or poultry chunks
    assert res["evidence"] == []

# 8. PMMY unverified handling
def test_pmmy_unverified_handling():
    # A. Borrower interest rate question returns DATA_UNAVAILABLE / unverified status
    res = execute_authoritative_routing("What is the PMMY interest rate for borrower?", language="english")
    assert res["intent"] == QueryIntent.DATA_UNAVAILABLE.value
    assert "AUTHORITATIVE_DATA_NOT_AVAILABLE" in res["answer"] or "unverified" in res["answer"].lower()

    # B. Verified filter strictly rejects PMMY partner refinance eligibility
    verified_results = retrieve_evidence("PMMY MUDRA refinance eligibility for partner banks", top_k=3, require_verified=True)
    for r in verified_results:
        assert r.source_id != "PMMY_PARTNER_ELIGIBILITY"

    # C. Unverified retrieval preserves NEEDS_SOURCE_VERIFICATION
    unverified = retrieve_evidence("PMMY MUDRA refinance eligibility", top_k=3, require_verified=False)
    pmmy_match = next((r for r in unverified if r.source_id == "PMMY_PARTNER_ELIGIBILITY"), None)
    if pmmy_match:
        assert pmmy_match.verification_status == "NEEDS_SOURCE_VERIFICATION"

# 9. Dairy financial calculation
def test_dairy_financial_calculation():
    res = execute_authoritative_routing("Calculate EMI for dairy loan of ₹2 lakh", language="english")
    assert res["intent"] == QueryIntent.FINANCIAL.value
    assert res["financial_result"] is not None
    assert res["financial_result"]["cost"] == 200000.0
    assert res["financial_result"]["emi"] > 0
    assert res["financial_result"]["margin"] > 0
    assert res["retrieval_used"] is False

# 10. Mixed dairy query
def test_mixed_dairy_query():
    res = execute_authoritative_routing(
        "NABARD says dairy costs ₹2.29 lakh. I want to borrow ₹2 lakh. Calculate EMI.",
        language="english"
    )
    assert res["intent"] == QueryIntent.MIXED.value
    assert res["financial_result"] is not None
    assert res["financial_result"]["cost"] in [200000.0, 229000.0]
    assert res["financial_result"]["emi"] > 0
    assert len(res["citations"]) >= 1
    assert any("NABARD" in c for c in res["citations"])

# 11. Flour Mill historical warning
def test_flour_mill_historical_warning():
    res = execute_authoritative_routing("How much does a mini flour mill cost?", language="english")
    assert "2020" in res["answer"]
    assert "SAMADHAN" in res["answer"] or any("SAMADHAN" in c for c in res["citations"])

# 12. Citation generation
def test_citation_generation():
    ev = RetrievedEvidence(
        chunk_id="chunk-test",
        text="Sample NABARD evidence",
        source_id="NABARD_KA_UC_BOOKLET_2026_27",
        source_title="Karnataka Unit Cost Booklet",
        source_organization="NABARD Karnataka Regional Office",
        source_page=41,
        publication_year=2026,
        source_type="UNIT_COST_SCHEDULE",
        verification_status="VERIFIED_OFFICIAL",
        relevance_score=0.95,
        document_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert ev.to_citation_string() == "[NABARD Karnataka Unit Cost Booklet 2026, p.41]"

# 13. REAL_DATA_ONLY synthetic fallback prevention
def test_real_data_only_synthetic_fallback_prevention():
    repo = BenchmarkRepository()
    with patch.object(settings, "REAL_DATA_ONLY", True):
        # Querying an unavailable category under REAL_DATA_ONLY=True must NEVER return synthetic dict
        res_kirana = repo.get_benchmark("Kirana Store", "Belagavi")
        assert res_kirana is not None
        assert res_kirana.get("status") == "DATA_NOT_AVAILABLE"
        assert res_kirana.get("unit_cost") is None

        res_tailoring = repo.get_benchmark("Tailoring Unit", "Belagavi")
        assert res_tailoring is not None
        assert res_tailoring.get("status") == "DATA_NOT_AVAILABLE"
        assert res_tailoring.get("unit_cost") is None

        # Verified category must return real NABARD benchmark
        res_dairy = repo.get_benchmark("Dairy Farming", "Belagavi")
        assert res_dairy is not None
        assert res_dairy["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27"
        assert res_dairy["source_page"] == 41

# 14. Qdrant unavailable behavior
def test_qdrant_unavailable_behavior():
    with patch("app.retrieval.service.QdrantClient", side_effect=Exception("Connection refused")):
        service = EvidenceRetrievalService(qdrant_url="http://invalid-qdrant-host:6333")
        with pytest.raises(QdrantUnavailableError) as exc_info:
            service.retrieve_evidence("2 cow dairy unit cost")
        assert "Qdrant vector database is unavailable" in str(exc_info.value)

# 15. Voice -> STT -> retrieval routing
def test_voice_stt_retrieval_routing():
    # Simulate text received from STT transcription of a voice note asking a factual question
    voice_transcript = "What is the NABARD cost for a 2 cow dairy unit?"
    intent, _ = classify_query_intent(voice_transcript)
    assert intent == QueryIntent.FACTUAL

    res = execute_authoritative_routing(voice_transcript, language="english")
    assert res["intent"] == QueryIntent.FACTUAL.value
    assert len(res["citations"]) >= 1
    assert any("NABARD" in c for c in res["citations"])

# 16. Financial isolation: LLM output contradiction resistance
def test_llm_financial_contradiction_resistance():
    """
    Verifies that even if an LLM hallucinates an arbitrary number (e.g. ₹99,999 EMI),
    the structured financial result and sanction figures remain strictly determined
    by the deterministic Python financial engine.
    """
    hallucinated_llm_response = (
        "Based on my analysis, your EMI will be ₹99,999 per month and your loan is ₹10,00,000."
    )
    with patch("app.ai.llm_client.call_llm_chat", return_value=hallucinated_llm_response):
        res = execute_authoritative_routing(
            "NABARD says dairy costs ₹2.29 lakh. I want to borrow ₹2 lakh. Calculate EMI.",
            language="english"
        )
        assert res["intent"] == QueryIntent.MIXED.value
        # The structured mathematical result must NEVER adopt the hallucinated number
        assert res["financial_result"]["emi"] == 3397.18
        assert res["financial_result"]["emi"] != 99999
        assert res["financial_result"]["loan"] <= 229000.0

# 17. Expanded NABARD activity retrieval
@pytest.mark.parametrize("query,expected_page,keyword", [
    ("NABARD Bannur sheep rearing unit cost 10 plus 1", 56, "Sheep"),
    ("NABARD goat rearing 10 does 1 buck unit cost", 60, "Goat"),
    ("NABARD pig rearing cum fattening unit cost 3 sows 1 boar", 64, "Pig"),
    ("NABARD freshwater fish culture in new ponds unit cost", 68, "Fish"),
    ("NABARD apiary beekeeping 10 colony unit cost", 30, "Bee"),
    ("NABARD sericulture mulberry garden establishment cost", 34, "Mulberry"),
])
def test_expanded_nabard_activity_retrieval(query, expected_page, keyword):
    service = EvidenceRetrievalService()
    results = service.retrieve_evidence(query, top_k=3, require_verified=True)
    assert len(results) >= 1
    top = results[0]
    assert top.source_id == "NABARD_KA_UC_BOOKLET_2026_27"
    assert top.source_page == expected_page
    assert top.verification_status == "VERIFIED_OFFICIAL"
    assert keyword.lower() in top.text.lower()

# 18. Expanded AIDIS national statistics retrieval
def test_expanded_aidis_national_statistics_retrieval():
    service = EvidenceRetrievalService()
    results = service.retrieve_evidence(
        "All-India rural incidence of indebtedness percentage AIDIS",
        top_k=3,
        require_verified=True
    )
    assert len(results) >= 1
    top = results[0]
    assert top.source_id == "AIDIS_NSS_77_REPORT_588"
    assert top.source_page in [16, 92]
    assert "35.0%" in top.text or "indebtedness" in top.text.lower()

# 19. Expanded BenchmarkRepository activities
def test_expanded_benchmark_repository_activities():
    repo = BenchmarkRepository()
    for activity, exp_cost, exp_page in [
        ("sheep rearing", 111000.0, 56),
        ("goat rearing", 113000.0, 60),
        ("piggery farming", 164000.0, 64),
        ("inland fisheries", 829000.0, 68),
        ("beekeeping apiary", 62800.0, 30),
        ("sericulture mulberry", 225000.0, 34),
    ]:
        b = repo.get_benchmark(activity, real_data_only=True)
        assert b["verification_status"] == "VERIFIED"
        assert b["benchmark_status"] == "CURRENT_BENCHMARK"
        assert b["cost_nature"] == "NABARD_UNIT_COST"
        assert b["total_cost"] == exp_cost
        assert b["source_page"] == exp_page
        assert b["is_synthetic"] is False

# 20. Flour Mill historical governance flag
def test_flour_mill_historical_governance():
    repo = BenchmarkRepository()
    b = repo.get_benchmark("mini flour mill", real_data_only=True)
    assert b["verification_status"] == "VERIFIED"
    assert b["benchmark_status"] == "HISTORICAL_BENCHMARK"
    assert b["cost_nature"] == "HISTORICAL_BENCHMARK_2020"
    assert "historical_warning" in b
    assert "2020" in b["historical_warning"]

# 21. DPR generation with expanded activities
def test_dpr_generation_expanded_activities():
    from app.dpr.generator import generate_dpr_pdf
    proposal = {
        "id": "test-sheep-1234",
        "business_trade": "Sheep Rearing",
        "project_cost": 111000.0,
        "scheme_tier": "MICRO_FINANCE",
        "beneficiary_margin": 11100.0,
        "sanctioned_loan": 99900.0,
        "monthly_emi": 3060.0,
        "projected_dscr": 1.65,
    }
    beneficiary = {
        "full_name": "Ramesh Shepherd",
        "district": "Rural District",
        "state": "Karnataka",
        "whatsapp_number": "919876543210"
    }
    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

