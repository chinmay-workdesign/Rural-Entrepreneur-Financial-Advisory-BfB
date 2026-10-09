"""
Comprehensive Tests for SerpApi Integration.
Tests client configuration, search extraction, TTL caching,
LIVE_MARKET routing, and unindexed trade web fallback.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.retrieval.models import RetrievedEvidence
from app.retrieval.serpapi_client import SerpApiClient
from app.retrieval.router import (
    QueryIntent,
    classify_query_intent,
    execute_authoritative_routing,
)


MOCK_SERP_PAYLOAD = {
    "answer_box": {
        "title": "Kolar APMC Tomato Mandi Rate",
        "snippet": "Average tomato rate in Kolar APMC is Rs 1,400 to Rs 1,800 per quintal as of today.",
        "link": "https://agmarknet.gov.in/price/tomato-kolar"
    },
    "organic_results": [
        {
            "title": "Daily Mandi Prices Karnataka - Agmarknet",
            "snippet": "Official daily market arrival and price bulletin for agriculture commodities across Karnataka mandis.",
            "link": "https://agmarknet.gov.in/karnataka-daily"
        },
        {
            "title": "Tomato Wholesale Price Trends",
            "snippet": "Wholesale prices in major Karnataka markets remained stable at ₹16/kg.",
            "link": "https://farmerportal.gov.in/prices/tomato"
        }
    ]
}

MOCK_KIRANA_PAYLOAD = {
    "organic_results": [
        {
            "title": "How to Start a Kirana Store in India - Cost Breakdown",
            "snippet": "Estimated initial investment for a small rural kirana store ranges between ₹1,50,000 to ₹3,00,000 including inventory and shelving.",
            "link": "https://msme.gov.in/guides/kirana-setup"
        }
    ]
}


def test_serpapi_client_unconfigured():
    client = SerpApiClient(api_key="")
    assert not client.is_configured()
    assert client.search_raw("tomato mandi price") == []
    assert client.search_as_evidence("tomato mandi price") == []


def test_serpapi_client_search_parsing():
    client = SerpApiClient(api_key="mock_test_key_123")
    assert client.is_configured()

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_SERP_PAYLOAD
        mock_get.return_value = mock_resp

        evidence = client.search_as_evidence("tomato price", max_results=3)

        assert len(evidence) == 3
        # First item from answer box
        assert "Kolar APMC Tomato Mandi Rate" in evidence[0].source_title
        assert "1,400" in evidence[0].text
        assert evidence[0].source_type == "SERPAPI_WEB_SEARCH"
        assert evidence[0].verification_status == "LIVE_WEB_SEARCH"
        assert "agmarknet.gov.in" in evidence[0].source_organization
        assert "(Web Source)" in evidence[0].to_citation_string()


def test_serpapi_client_caching():
    client = SerpApiClient(api_key="mock_test_key_123", ttl_seconds=3600)

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_SERP_PAYLOAD
        mock_get.return_value = mock_resp

        # First call fetches from HTTP
        res1 = client.search_raw("potato price")
        assert len(res1) == 3
        assert mock_get.call_count == 1

        # Second identical call hits memory cache
        res2 = client.search_raw("potato price")
        assert len(res2) == 3
        assert mock_get.call_count == 1  # Not called again!


def test_serpapi_error_handling():
    client = SerpApiClient(api_key="mock_test_key_123")

    with patch("httpx.Client.get") as mock_get:
        mock_get.side_effect = Exception("Connection timeout to serpapi.com")
        results = client.search_raw("onion mandi price")
        assert results == []

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden - Invalid API key"
        mock_get.return_value = mock_resp

        results = client.search_raw("onion mandi price")
        assert results == []


def test_classify_live_market_intent():
    # English queries
    intent1, _ = classify_query_intent("What is the current mandi price of tomato in Kolar?")
    assert intent1 == QueryIntent.LIVE_MARKET

    intent2, _ = classify_query_intent("poultry feed market price today")
    assert intent2 == QueryIntent.LIVE_MARKET

    # Regional language queries
    intent_kn, _ = classify_query_intent("ಇಂದಿನ ಈರುಳ್ಳಿ ಮಂಡಿ ಬೆಲೆ ಎಷ್ಟು?")
    assert intent_kn == QueryIntent.LIVE_MARKET

    intent_hi, _ = classify_query_intent("टमाटर का आज का मंडी भाव क्या है?")
    assert intent_hi == QueryIntent.LIVE_MARKET


def test_router_live_market_execution():
    with patch("app.retrieval.router.serpapi_client.is_configured", return_value=True):
        with patch("app.retrieval.router.serpapi_client.search_as_evidence") as mock_search:
            mock_evidence = [
                RetrievedEvidence(
                    chunk_id="test_serp_1",
                    text="Kolar Tomato Mandi: ₹1,500/quintal modal rate.",
                    source_id="SERPAPI_agmarknet_gov_in",
                    source_title="Kolar APMC Bulletin",
                    source_organization="agmarknet.gov.in",
                    source_page=1,
                    source_type="SERPAPI_WEB_SEARCH",
                    verification_status="LIVE_WEB_SEARCH",
                    relevance_score=0.9,
                    document_hash="hash123",
                    source_url="https://agmarknet.gov.in/kolar"
                )
            ]
            mock_search.return_value = mock_evidence

            res = execute_authoritative_routing("What is the mandi price of tomato?", language="english")

            assert res["intent"] == QueryIntent.LIVE_MARKET.value
            assert res["retrieval_used"] is True
            assert len(res["citations"]) == 1
            assert "agmarknet.gov.in" in res["citations"][0] or "Kolar APMC Bulletin" in res["citations"][0]
            assert "Kolar Tomato Mandi" in res["answer"] or "₹1,500" in res["answer"]


def test_router_unindexed_trade_with_serpapi_fallback():
    with patch("app.retrieval.router.serpapi_client.is_configured", return_value=True):
        with patch("app.retrieval.router.serpapi_client.search_as_evidence") as mock_search:
            mock_evidence = [
                RetrievedEvidence(
                    chunk_id="test_serp_kirana",
                    text="Small Kirana Store estimated initial cost: ₹1.5 - ₹2 Lakhs.",
                    source_id="SERPAPI_msme_gov_in",
                    source_title="MSME Kirana Guide",
                    source_organization="msme.gov.in",
                    source_page=1,
                    source_type="SERPAPI_WEB_SEARCH",
                    verification_status="LIVE_WEB_SEARCH",
                    relevance_score=0.88,
                    document_hash="hashkirana",
                    source_url="https://msme.gov.in/kirana"
                )
            ]
            mock_search.return_value = mock_evidence

            res = execute_authoritative_routing("What is the official cost of a kirana shop?", language="english")

            # Still preserves official gap notice
            assert res["intent"] == QueryIntent.DATA_UNAVAILABLE.value
            assert "DATA_NOT_AVAILABLE" in res["answer"]
            assert "Kirana" in res["answer"]
            # And enriches with SerpApi live market research
            assert "Live Market Research Estimates (SerpApi)" in res["answer"]
            assert "₹1.5 - ₹2 Lakhs" in res["answer"]
            assert len(res["citations"]) == 1


def test_router_web_fallback_disabled_flag():
    with patch("app.retrieval.router.serpapi_client.is_configured", return_value=True):
        with patch("app.retrieval.router.serpapi_client.search_as_evidence") as mock_search:
            # When allow_web_fallback is False, SerpApi is not called
            res = execute_authoritative_routing(
                "What is the official cost of a kirana shop?",
                language="english",
                allow_web_fallback=False
            )
            assert res["intent"] == QueryIntent.DATA_UNAVAILABLE.value
            assert "DATA_NOT_AVAILABLE" in res["answer"]
            assert "Live Market Research Estimates" not in res["answer"]
            assert res["citations"] == []
            assert mock_search.call_count == 0


def test_compound_proposal_and_market_query_classification():
    q = "I want to open a saree shop in my village in Uttar Kannada in Karnataka. I don't know the project cost. Also tell me the cost of 1 meter square of cotton cloth in my area"
    intent, details = classify_query_intent(q)
    assert intent == QueryIntent.LIVE_MARKET
    assert details.get("market_query") is True


def test_router_compound_query_cleans_search_for_serpapi():
    q = "I want to open a saree shop in my village in Uttar Kannada in Karnataka. I don't know the project cost. Also tell me the cost of 1 meter square of cotton cloth in my area"
    with patch("app.retrieval.router.serpapi_client.is_configured", return_value=True):
        with patch("app.retrieval.router.serpapi_client.search_as_evidence") as mock_search:
            mock_evidence = [
                RetrievedEvidence(
                    chunk_id="test_cotton",
                    text="Cotton cloth prices in Karnataka range between ₹60 to ₹120 per meter.",
                    source_id="SERPAPI_indiamart",
                    source_title="IndiaMart Cotton Rates",
                    source_organization="indiamart.com",
                    source_page=1,
                    source_type="SERPAPI_WEB_SEARCH",
                    verification_status="LIVE_WEB_SEARCH",
                    relevance_score=0.9,
                    document_hash="hashcotton",
                    source_url="https://indiamart.com/cotton"
                )
            ]
            mock_search.return_value = mock_evidence

            res = execute_authoritative_routing(q, language="english")

            assert res["intent"] == QueryIntent.LIVE_MARKET.value
            # Verify the search query passed to SerpApi was cleaned and focused
            args, kwargs = mock_search.call_args
            called_query = kwargs.get("query") or args[0]
            assert "cotton cloth" in called_query
            assert "I want to open" not in called_query
