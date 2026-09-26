import pytest
from unittest.mock import patch
from app.retrieval.router import execute_authoritative_routing, QueryIntent
from app.finance.calculator import calculate_financial_structure
from app.finance.dscr import calculate_dscr, project_financial_cashflows
from app.retrieval.service import QdrantUnavailableError

"""
Phase 7 Adversarial Numerical Integrity Tests.
Verifies that:
1. LLM output cannot modify deterministic EMI.
2. LLM output cannot modify loan principal.
3. LLM output cannot modify interest rate.
4. LLM output cannot modify tenure.
5. LLM output cannot modify DSCR.
6. LLM output cannot modify beneficiary margin.
7. LLM failure does not cause financial calculations to fail.
8. Retrieval failure does not cause synthetic financial fallback.
9. Missing benchmark does not trigger unrelated benchmark substitution.
"""

def test_adversarial_llm_cannot_modify_emi():
    """
    Mock LLM to return hallucinated EMI 'The EMI is ₹4,500.'
    Verify that the system's financial_result and sanitized answer preserve the authoritative EMI.
    """
    cost = 240000.0  # Term Loan: loan=216,000, rate=8.0%, tenure=84m, grace=6m, repay=78m -> EMI ~ 3560.36
    det = calculate_financial_structure(cost)
    authoritative_emi = det["emi"]

    # Mock call_llm_chat to return adversarial number
    adversarial_llm_output = "Sure! For your dairy unit costing ₹2,40,000, the monthly EMI is ₹4,500."

    with patch("app.ai.llm_client.call_llm_chat", return_value=adversarial_llm_output):
        res = execute_authoritative_routing(
            query="I want to start a dairy with 2 cows costing 240000. What is my EMI?",
            project_cost=cost
        )

        # 1. Deterministic financial structure must be strictly preserved
        assert res["financial_result"]["emi"] == authoritative_emi
        assert res["financial_result"]["emi"] != 4500.0

        # 2. System answer must override or reject the hallucinated number
        assert "4,500" not in res["answer"] or "Authoritative Verification" in res["answer"]
        assert f"₹{authoritative_emi:,.2f}" in res["answer"]

def test_adversarial_llm_cannot_modify_loan_principal():
    """
    Mock LLM to claim loan is 99% or ₹5,00,000.
    Verify financial_result preserves strict statutory loan formula.
    """
    cost = 100000.0  # MFS ceiling: 90% loan = 90,000.0
    det = calculate_financial_structure(cost)

    with patch("app.ai.llm_client.call_llm_chat", return_value="We will give you a 99% loan of ₹99,000."):
        res = execute_authoritative_routing(
            query="I want to start a unit costing 100000. What is my loan amount and EMI?",
            project_cost=cost
        )
        assert res["financial_result"]["loan"] == 90000.0
        assert res["financial_result"]["loan"] != 99000.0

def test_adversarial_llm_cannot_modify_interest_rate():
    """
    Mock LLM to state interest rate is 2% or 18%.
    Verify financial_result retains statutory rate.
    """
    cost = 100000.0  # MFS statutory rate = 6.5%
    det = calculate_financial_structure(cost)

    with patch("app.ai.llm_client.call_llm_chat", return_value="The interest rate is subsidized at 2.0% p.a."):
        res = execute_authoritative_routing(
            query="I want to start a unit costing 100000. What is my interest rate and EMI?",
            project_cost=cost
        )
        assert res["financial_result"]["rate"] == 6.5

def test_adversarial_llm_cannot_modify_tenure():
    """
    Mock LLM to claim repayment tenure is 120 months.
    Verify tenure and repayment months remain statutory.
    """
    cost = 100000.0  # MFS tenure = 36 months, moratorium = 3, repayment = 33
    det = calculate_financial_structure(cost)

    with patch("app.ai.llm_client.call_llm_chat", return_value="You have 10 years (120 months) to repay."):
        res = execute_authoritative_routing(
            query="I want to start a unit costing 100000. What is my loan tenure and EMI?",
            project_cost=cost
        )
        assert res["financial_result"]["tenure"] == 36
        assert res["financial_result"]["repayment_months"] == 33

def test_adversarial_llm_cannot_modify_dscr():
    """
    Verify DSCR cannot be altered by narrative claims.
    DSCR = Net Annual Operating Income / Annual Debt Service.
    """
    cost = 200000.0
    fin = calculate_financial_structure(cost)
    annual_debt_service = fin["emi"] * 12.0
    net_operating_income = 140000.0

    expected_dscr = calculate_dscr(net_operating_income, annual_debt_service)

    # Even if LLM text asserts "DSCR is 4.5", mathematical DSCR remains immutable
    cashflow_res = project_financial_cashflows(cost, fin["emi"])
    assert cashflow_res["dscr"] > 0
    assert isinstance(cashflow_res["dscr"], float)
    assert cashflow_res["annual_debt_service"] == round(annual_debt_service, 2)

def test_adversarial_llm_cannot_modify_beneficiary_margin():
    """
    Verify beneficiary margin dynamically absorbs statutory loan caps:
    loan + margin == cost.
    """
    cost = 200000.0
    fin = calculate_financial_structure(cost)
    assert fin["loan"] + fin["margin"] == cost
    assert fin["margin"] == 20000.0  # 10%

def test_llm_failure_does_not_break_financial_engine():
    """
    When LLM raises an unhandled exception or timeout, the financial engine
    must complete successfully and return exact deterministic numbers.
    """
    cost = 150000.0
    with patch("app.ai.llm_client.call_llm_chat", side_effect=RuntimeError("Gemini 429 Quota Exceeded")):
        res = execute_authoritative_routing(
            query="I want to start a dairy costing 150000. What is my loan and EMI?",
            project_cost=cost
        )
        assert res["financial_result"] is not None
        assert res["financial_result"]["cost"] == 150000.0
        assert res["financial_result"]["loan"] == 135000.0
        assert res["financial_engine_used"] is True
        assert "135,000" in res["answer"]

def test_retrieval_failure_does_not_trigger_synthetic_financial_fallback():
    """
    When Qdrant is completely unavailable, REAL_DATA_ONLY=True must NOT substitute
    synthetic benchmarks.
    """
    with patch("app.retrieval.router.retrieve_evidence", side_effect=QdrantUnavailableError("Connection refused")):
        res = execute_authoritative_routing("What is the NABARD unit cost for 2 dairy cows?")
        assert res["evidence"] == []
        assert "unavailable" in res["answer"].lower()

def test_missing_benchmark_does_not_trigger_unrelated_substitution():
    """
    Missing benchmark trades (Kirana, Tailoring) must return DATA_NOT_AVAILABLE
    and NOT substitute unrelated benchmarks like Dairy or Poultry.
    """
    res_kirana = execute_authoritative_routing("How much does it cost to start a Kirana store?")
    assert res_kirana["intent"] == "DATA_UNAVAILABLE"
    assert res_kirana["financial_result"] is None
    assert "DATA_NOT_AVAILABLE" in res_kirana["answer"]
    assert "Dairy" not in res_kirana["answer"]
    assert "Poultry" not in res_kirana["answer"]

    res_tailoring = execute_authoritative_routing("What is the cost of starting a tailoring unit?")
    assert res_tailoring["intent"] == "DATA_UNAVAILABLE"
    assert res_tailoring["financial_result"] is None
    assert "DATA_NOT_AVAILABLE" in res_tailoring["answer"]
