"""
Grounded LLM Context and Prompt Builder (Local FastEmbed + Qdrant RAG).
Combines User Query + Deterministic Financial Result + Retrieved Authoritative Evidence.
Strictly separates immutable deterministic math from contextual narrative explanation.
"""
from typing import List, Dict, Any, Optional
from app.retrieval.models import RetrievedEvidence

GROUNDED_SYSTEM_INSTRUCTIONS = """You are the Rural Enterprise Financial Advisor for India.
You provide verified, bank-grounded advisory to rural micro-entrepreneurs.

CRITICAL INVARIANTS:
1. MATHEMATICAL INTEGRITY: You MUST NEVER recalculate, estimate, or modify any financial numbers provided in the DETERMINISTIC FINANCIAL RESULT section. The loan amount, beneficiary margin, EMI, interest rate, and DSCR are pre-computed by a deterministic Python engine. Always use these exact numbers.
2. EVIDENCE GROUNDING: Only assert policy rules, subsidies, eligibility criteria, and benchmark costs that are explicitly supported by the RETRIEVED AUTHORITATIVE EVIDENCE section. Do NOT invent missing rules or government schemes.
3. CITATION REQUIREMENT: Whenever referencing an official parameter, cite the exact source and page number from the evidence using the format: [Source Name, p.XX].
4. HISTORICAL FLOUR MILL NOTICE: If discussing the Flour Mill benchmark (₹32.93 Lakhs), you MUST explicitly state that this is a historical 2020 benchmark from Project SAMADHAN (MDTC), reflecting 2020 equipment prices, and not a current market quotation.
5. DATA GAPS (TAILORING / KIRANA): If the user asks about Tailoring or Kirana benchmarks, state clearly that authoritative government/NABARD unit cost data is currently DATA_NOT_AVAILABLE in the official repository, and the evaluation is based on the applicant's customized outlay.
6. AIDIS MACRO CONTEXT ONLY: Survey statistics from AIDIS (such as rural indebtedness or informal interest rates) are macro-economic context and MUST NEVER be used to dictate an individual borrower's loan size or interest rate.
7. LANGUAGE & TONE: Be supportive, simple, and encouraging for rural entrepreneurs. Answer in the applicant's requested language.
8. LIVE WEB EVIDENCE: If evidence items have verification status LIVE_WEB_SEARCH, explain that these findings come from live web data and provide realistic market indications, but remind the applicant to obtain physical vendor quotations.
"""

def build_grounded_llm_messages(
    user_query: str,
    evidence_list: List[RetrievedEvidence],
    financial_result: Optional[Dict[str, Any]] = None,
    language: str = "kannada"
) -> List[Dict[str, str]]:
    """
    Constructs a strict message list for Google Gemini or other LLMs.
    """
    # 1. Format Retrieved Evidence
    evidence_blocks = []
    if evidence_list:
        for idx, ev in enumerate(evidence_list, 1):
            citation = ev.to_citation_string()
            status_warning = ""
            if ev.verification_status == "LIVE_WEB_SEARCH":
                status_warning = " [STATUS: LIVE_WEB_SEARCH - REAL-TIME WEB DATA, ADVISE PHYSICAL VENDOR VERIFICATION]"
            elif ev.verification_status != "VERIFIED_OFFICIAL":
                status_warning = f" [STATUS: {ev.verification_status} - USE CAUTION, UNVERIFIED FOR END-BORROWERS]"
            
            nature_note = ""
            if ev.cost_nature == "HISTORICAL_BENCHMARK_2020":
                nature_note = " [NOTE: Historical 2020 benchmark, not current spot market quotation]"

            evidence_blocks.append(
                f"--- EVIDENCE ITEM {idx} {citation}{status_warning}{nature_note} ---\n"
                f"Source: {ev.source_title} ({ev.source_organization}, Page {ev.source_page})\n"
                f"Verification: {ev.verification_status}\n"
                f"Content:\n{ev.text}\n"
            )
        evidence_text = "\n".join(evidence_blocks)
    else:
        evidence_text = "No direct authoritative document passages retrieved for this specific query."

    # 2. Format Deterministic Financial Result
    fin_text = "No project financial calculation requested in this step."
    if financial_result:
        fin_text = (
            f"Scheme: {financial_result.get('scheme_name', 'Rural Scheme')}\n"
            f"Total Project Outlay: ₹{financial_result.get('cost', 0.0):,.2f}\n"
            f"Concessional Bank Loan: ₹{financial_result.get('loan', 0.0):,.2f}\n"
            f"Entrepreneur Margin (Own Contribution): ₹{financial_result.get('margin', 0.0):,.2f} ({financial_result.get('margin_pct', 0.0)}%)\n"
            f"Annual Interest Rate: {financial_result.get('rate', 0.0):.2f}% p.a. (Reducing Balance)\n"
            f"Active Repayment Tenure: {financial_result.get('repayment_months', 0)} months (after {financial_result.get('morat', 0)} months moratorium)\n"
            f"Monthly Installment (EMI): ₹{financial_result.get('emi', 0.0):,.2f}\n"
            f"Total Interest: ₹{financial_result.get('total_interest', 0.0):,.2f}\n"
            f"Total Repayable: ₹{financial_result.get('total_repayable', 0.0):,.2f}\n"
            f"(THESE NUMBERS ARE IMMUTABLE FACTS DETERMINED BY PYTHON ENGINE. DO NOT ALTER.)"
        )

    user_prompt = (
        f"USER QUESTION / REQUEST:\n{user_query}\n\n"
        f"DETERMINISTIC FINANCIAL RESULT (IMMUTABLE MATHEMATICS):\n{fin_text}\n\n"
        f"RETRIEVED AUTHORITATIVE EVIDENCE:\n{evidence_text}\n\n"
        f"Please provide an accurate, grounded, helpful advisory response in {language.capitalize()} language. "
        f"Cite sources using [Source Name, p.XX] format."
    )

    return [
        {"role": "system", "content": GROUNDED_SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": user_prompt}
    ]
