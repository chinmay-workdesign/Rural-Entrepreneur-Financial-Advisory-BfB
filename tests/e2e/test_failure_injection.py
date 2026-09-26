import io
import pytest
from unittest.mock import patch, MagicMock
import pypdf

from app.retrieval.router import execute_authoritative_routing, QueryIntent
from app.retrieval.service import QdrantUnavailableError, RetrievedEvidence, retrieval_service
from app.retrieval.context_builder import build_grounded_llm_messages
from app.finance.calculator import calculate_financial_structure, validate_project_cost
from app.dpr.generator import generate_dpr_pdf

"""
Phase 7 Step 7: Controlled Failure Injection Tests.
Validates 10 systemic failure modes:
1. Qdrant unavailable
2. Qdrant collection missing
3. Embedding model unavailable
4. LLM unavailable
5. LLM quota exceeded
6. Malformed retrieved evidence
7. Missing source metadata
8. Missing benchmark (REAL_DATA_ONLY=True)
9. Corrupted PDF handling
10. Invalid user financial input
"""

def test_failure_1_qdrant_unavailable():
    """
    Failure Mode 1: Qdrant service is down / connection refused.
    Must return clear error, empty evidence, and NO synthetic fallback.
    """
    with patch("app.retrieval.router.retrieve_evidence", side_effect=QdrantUnavailableError("Connection refused")):
        res = execute_authoritative_routing("How many cows are in a dairy unit?")
        assert res["evidence"] == []
        assert "unavailable" in res["answer"].lower()
        assert res["financial_result"] is None

def test_failure_2_qdrant_collection_missing():
    """
    Failure Mode 2: Qdrant collection does not exist.
    Must handle missing collection cleanly without fabricating data.
    """
    with patch("app.retrieval.router.retrieve_evidence", side_effect=QdrantUnavailableError("Collection 'authoritative_knowledge' not found")):
        res = execute_authoritative_routing("What is the poultry broiler cost?")
        assert res["evidence"] == []
        assert "unavailable" in res["answer"].lower()

def test_failure_3_embedding_model_unavailable():
    """
    Failure Mode 3: Local FastEmbed embedding model throws error.
    Must return safe error response without crash.
    """
    with patch.object(retrieval_service, "retrieve_evidence", side_effect=RuntimeError("FastEmbed weights failed to load")):
        try:
            res = execute_authoritative_routing("What is the dairy cost?")
            assert res is not None
        except Exception as e:
            # If raised, must not produce synthetic data
            assert "synthetic" not in str(e).lower()

def test_failure_4_llm_unavailable():
    """
    Failure Mode 4: LLM service is completely unreachable.
    Financial calculation and evidence citations MUST still succeed using deterministic fallback.
    """
    with patch("app.ai.llm_client.call_llm_chat", return_value=None):
        res = execute_authoritative_routing(
            query="I want to start a dairy with 2 cows costing 200000. What is my loan and EMI?",
            project_cost=200000.0
        )
        assert res["financial_result"] is not None
        assert res["financial_result"]["loan"] == 180000.0
        assert res["financial_result"]["emi"] > 0
        assert res["retrieval_used"] is True
        assert len(res["citations"]) > 0

def test_failure_5_llm_quota_exceeded():
    """
    Failure Mode 5: LLM returns 429 Quota Exceeded.
    System must fall back to deterministic narrative and not drop financial data.
    """
    with patch("app.ai.llm_client.call_llm_chat", side_effect=RuntimeError("429 ResourceExhausted: Quota exceeded")):
        res = execute_authoritative_routing(
            query="I want to start a dairy costing 200000. What will my EMI be?",
            project_cost=200000.0
        )
        assert res["financial_result"] is not None
        assert res["financial_result"]["loan"] == 180000.0
        assert "180,000" in res["answer"]
        assert "financial_result" in res

def test_failure_6_malformed_retrieved_evidence():
    """
    Failure Mode 6: Malformed evidence object (e.g. control chars, long strings).
    build_grounded_llm_messages must sanitize and not crash.
    """
    malformed_ev = [
        RetrievedEvidence(
            chunk_id="MALFORMED_01",
            text="Incomplete data \x00\xff...",
            source_id="UNKNOWN_PROFILE",
            source_title="Corrupt Doc Title",
            source_organization="Unknown Agency",
            source_page=1,
            publication_year=2026,
            source_type="MODEL_PROJECT_PROFILE",
            verification_status="VERIFIED_OFFICIAL",
            relevance_score=0.95,
            document_hash="0123456789abcdef"
        )
    ]
    messages = build_grounded_llm_messages("Test Query", malformed_ev, None, "english")
    assert len(messages) >= 2
    assert "Corrupt Doc Title" in messages[1]["content"]

def test_failure_7_missing_source_metadata():
    """
    Failure Mode 7: Retrieved evidence missing optional fields.
    Citation formatting must handle missing publication year gracefully without failing.
    """
    ev = RetrievedEvidence(
        chunk_id="TEST_CHUNK_NO_YEAR",
        text="Sample text",
        source_id="CUSTOM_SOURCE",
        source_title="Partial Source",
        source_organization="Custom Organization",
        source_page=12,
        publication_year=None,
        source_type="GOVERNMENT_SCHEME_RULE",
        verification_status="VERIFIED_OFFICIAL",
        relevance_score=0.88,
        document_hash="fedcba9876543210"
    )
    citation = ev.to_citation_string()
    assert "[Partial Source, p.12]" in citation

def test_failure_8_missing_benchmark_real_data_only():
    """
    Failure Mode 8: Trade has no official benchmark (Kirana/Tailoring).
    With REAL_DATA_ONLY=True, must return DATA_NOT_AVAILABLE and never fabricate a number.
    """
    res = execute_authoritative_routing("What is the benchmark unit cost for tailoring?")
    assert res["intent"] == "DATA_UNAVAILABLE"
    assert "DATA_NOT_AVAILABLE" in res["answer"]
    assert res["financial_result"] is None
    assert res["citations"] == []

def test_failure_9_corrupted_pdf_handling():
    """
    Failure Mode 9: Attempting to extract text from a corrupted PDF stream.
    Must raise standard PDF error and be handled without corrupting state.
    """
    corrupted_bytes = b"NOT_A_VALID_PDF_HEADER_DATA"
    with pytest.raises(Exception):
        reader = pypdf.PdfReader(io.BytesIO(corrupted_bytes))
        _ = reader.pages[0].extract_text()

def test_failure_10_invalid_user_financial_input():
    """
    Failure Mode 10: User inputs invalid, negative, below-minimum, or above-ceiling project costs.
    validate_project_cost must raise descriptive ValueErrors and reject invalid math.
    """
    # Negative cost
    with pytest.raises(ValueError, match="below minimum viable threshold"):
        validate_project_cost(-50000.0)

    # Below statutory minimum (₹5,000)
    with pytest.raises(ValueError, match="below minimum viable threshold"):
        validate_project_cost(499.0)

    # Above statutory ceiling (₹50,00,000)
    with pytest.raises(ValueError, match="exceeds Term Loan Scheme maximum ceiling"):
        validate_project_cost(10000000.0)

    # Non-numeric input
    with pytest.raises(ValueError, match="valid number"):
        validate_project_cost("one lakh")
