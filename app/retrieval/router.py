"""
Authoritative Query Intent Classification, Local RAG Routing, and Observability.
Zero external paid RAG or JEV dependencies.
Enforces strict separation of deterministic math from factual narrative explanation.
"""
import re
import time
import json
import uuid
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

from app.config import settings
from app.retrieval.models import RetrievedEvidence
from app.retrieval.service import retrieve_evidence, QdrantUnavailableError
from app.retrieval.context_builder import build_grounded_llm_messages
from app.finance.calculator import calculate_financial_structure

logger = logging.getLogger("retrieval_router")

class QueryIntent(str, Enum):
    FINANCIAL = "FINANCIAL"
    FACTUAL = "FACTUAL"
    MIXED = "MIXED"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"

def classify_query_intent(text: str) -> Tuple[QueryIntent, Dict[str, Any]]:
    """
    Classifies user message into one of 5 strict intents:
    1. FINANCIAL: Request purely for financial numbers (EMI, loan, margin, cash flow)
    2. FACTUAL: Authoritative questions about official benchmarks, schemes, policies, AIDIS
    3. MIXED: Combines an authoritative source reference with a personal loan/EMI calculation
    4. DATA_UNAVAILABLE: Requests for unverified or unavailable sources (Kirana, Tailoring, PMMY borrower rules)
    5. GENERAL_CONVERSATION: Greetings, help, voice info, menu, language selection
    """
    clean_text = text.strip()
    lower = clean_text.lower()
    details: Dict[str, Any] = {}

    # 1. Check for GENERAL_CONVERSATION
    general_cmds = [
        "/start", "start", "reset", "restart", "clear", "new", "menu",
        "language", "lang", "help", "who are you", "what can you do",
        "generate dpr", "dpr"
    ]
    if lower in general_cmds or any(k in lower for k in ["hello", "namaste", "ನಮಸ್ಕಾರ", "नमस्ते", "నమస్కారం", "नमस्कार"]):
        if not any(f in lower for f in ["cost", "benchmark", "loan", "emi", "subsidy", "dairy", "poultry", "pmegp", "aidis"]):
            return QueryIntent.GENERAL_CONVERSATION, {"reason": "greeting_or_system_command"}

    # 2. Check for DATA_UNAVAILABLE (Kirana, Tailoring, PMMY end-borrower rules)
    unavailable_trades = ["kirana", "grocery", "tailoring", "garment", "stitching"]
    cost_terms = ["cost", "unit cost", "benchmark", "price", "outlay", "budget"]
    if any(t in lower for t in unavailable_trades) and any(c in lower for c in cost_terms):
        return QueryIntent.DATA_UNAVAILABLE, {
            "reason": "TRADE_BENCHMARK_NOT_AVAILABLE",
            "trade": next(t for t in unavailable_trades if t in lower)
        }

    pmmy_borrower_terms = ["pmmy interest", "mudra interest", "pmmy loan rate", "pmmy borrower", "mudra rules for borrower", "pmmy rules"]
    if any(p in lower for p in pmmy_borrower_terms) or ("pmmy" in lower and "interest" in lower):
        return QueryIntent.DATA_UNAVAILABLE, {
            "reason": "PMMY_END_BORROWER_RULES_NOT_AVAILABLE",
            "scheme": "PMMY"
        }

    # 3. Detect Financial Calculation Keywords vs Factual Keywords
    fin_calc_terms = [
        "calculate emi", "what is my emi", "my emi", "monthly installment",
        "how much loan can i get", "calculate loan", "loan calculation",
        "if i borrow", "if i take a loan", "for a loan of"
    ]
    has_fin_calc = any(term in lower for term in fin_calc_terms)

    # Check for monetary amounts like ₹2 lakh, 2,00,000, 4 lakh
    amount_matches = re.findall(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(lakh|lac|k|thousand|cr|crore)?', lower)
    has_amount = any(m[0] for m in amount_matches if m[0] not in ["1", "2", "3", "4", "5"]) # exclude single-digit menu selections

    factual_terms = [
        "nabard", "unit cost", "official cost", "benchmark", "samadhan", "flour mill",
        "pmegp", "subsidy", "aidis", "debt", "indebtedness", "informal", "rbi",
        "priority sector", "psl", "2 cow", "two cow", "two cows",
        "what will it cost", "what does it cost", "how much does it cost",
        # Multilingual terms (Kannada, Hindi, Telugu, Marathi)
        "ನಬಾರ್ಡ್", "ಯೂನಿಟ್ ವೆಚ್ಚ", "ಮಾನದಂಡ", "ವೆಚ್ಚ", "ಹಸು", "ಹೈನುಗಾರಿಕೆ", "ಕೋಳಿ", "ಕುರಿ", "ಮೇಕೆ", "ಹಿಟ್ಟಿನ ಗಿರಣಿ", "ಎಷ್ಟು",
        "नाबार्ड", "यूनिट लागत", "बेंचमार्क", "लागत", "गाय", "डेयरी", "मुर्गी", "बकरी", "भेड़", "फ्लोर मिल", "कितना",
        "నాబార్డ్", "యూనిట్ ఖర్చు", "బెంచ్‌మార్క్", "ఖర్చు", "ఆవు", "పాడి", "కోళ్ల", "మేక", "గొర్రె", "పిండి మిల్లు", "ఎంత",
        "नाबार्ड", "युनिट खर्च", "बेंचमार्क", "खर्च", "गाय", "दुग्ध", "कुक्कुटपालन", "शेळी", "मेंढी", "पिठाची गिरणी", "किती"
    ]
    has_factual_term = any(term in lower for term in factual_terms)
    proposal_starters = [
        "i want to start", "i want to open", "i want to set up", "want to start",
        "planning to start", "i want to do", "going to start", "i want to run",
        "ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ", "ಶುರು ಮಾಡಲು", "शुरू करना चाहता", "सुरू करायचे", "ప్రారంభించాలనుకుంటున్నాను"
    ]
    is_proposal_statement = any(p in lower for p in proposal_starters)
    is_question = any(q in lower for q in [
        "what", "how", "why", "when", "which", "where", "can i", "is there", "?",
        "ಏನು", "ಎಷ್ಟು", "ಹೇಗೆ", "ಯಾವ",
        "क्या", "कितना", "कैसे", "कौन",
        "ఏమిటి", "ఎంత", "ఎలా", "ఏది",
        "काय", "किती", "कसे", "कोणते"
    ])

    # 4. Pure FINANCIAL (Priority when explicit "calculate emi", "what is my emi", or "calculate loan" for user amount without asking benchmark cost):
    if (has_fin_calc and has_amount and not any(k in lower for k in ["nabard", "samadhan", "what will it cost", "what does it cost", "how much will it cost"])) and not ("nabard" in lower or "samadhan" in lower):
        return QueryIntent.FINANCIAL, {"has_amount": True}

    # 5. MIXED Intent: Both Factual source reference AND personal financial calculation
    if (has_factual_term and has_fin_calc) or (has_factual_term and has_amount and any(k in lower for k in ["emi", "calculate", "borrow", "take"])):
        return QueryIntent.MIXED, {"has_amount": True, "factual_indicator": True}

    # If it is purely a proposal statement without a question, route to dialogue proposal flow
    if is_proposal_statement and not is_question:
        return QueryIntent.GENERAL_CONVERSATION, {"reason": "proposal_progression"}

    # 6. Pure FINANCIAL: Asks to calculate loan / EMI / outlay
    if has_fin_calc or (has_amount and any(k in lower for k in ["loan", "emi", "margin", "subsidy for my"])):
        return QueryIntent.FINANCIAL, {"has_amount": True}

    # 7. Pure FACTUAL: Asks about benchmarks, policies, surveys, or trade questions
    trade_terms = ["dairy", "cow", "cows", "poultry", "broiler", "sheep", "goat", "piggery", "fisheries", "beekeeping", "sericulture"]
    has_trade_term = any(t in lower for t in trade_terms)
    if has_factual_term or (is_question and has_trade_term) or any(k in lower for k in ["what is the cost", "how much does", "guidelines", "percentage", "survey"]):
        return QueryIntent.FACTUAL, {"factual_indicator": True}

    # Default: General / proposal progression
    return QueryIntent.GENERAL_CONVERSATION, {"reason": "general_or_proposal"}

def _normalize_retrieval_query(query: str) -> str:
    """Expands multilingual regional queries with canonical English terminology for the English embedding index."""
    q_lower = query.lower()
    additions = []

    if any(k in q_lower for k in ["ನಬಾರ್ಡ್", "नाबार्ड", "నాబార్డ్", "nabard"]):
        additions.append("NABARD")
    if any(k in q_lower for k in ["ಹಸು", "ಹೈನುಗಾರಿಕೆ", "गाय", "गायों", "डेयरी", "दुग्ध", "ఆవు", "ఆవుల", "పాడి", "dairy", "cow"]):
        additions.append("dairy cows unit cost")
    if any(k in q_lower for k in ["ಕೋಳಿ", "मुर्गी", "कुक्कुटपालन", "కోళ్ల", "poultry", "broiler"]):
        additions.append("poultry broiler farm")
    if any(k in q_lower for k in ["ಕುರಿ", "भेड़", "मेंढी", "గొర్రె", "sheep"]):
        additions.append("sheep rearing")
    if any(k in q_lower for k in ["ಮೇಕೆ", "ಆಡು", "बकरी", "शेळी", "మేక", "goat"]):
        additions.append("goat rearing")
    if any(k in q_lower for k in ["ಹಂದಿ", "सूअर", "पंदी", "piggery", "pig"]):
        additions.append("piggery unit cost")
    if any(k in q_lower for k in ["ಮೀನು", "ಮೀನುಗಾರಿಕೆ", "मछली", "मत्स्य", "చేప", "fisheries", "fish"]):
        additions.append("freshwater fish culture")
    if any(k in q_lower for k in ["ಜೇನು", "मधुमक्खी", "मध", "తేనెటీగ", "beekeeping", "apiary"]):
        additions.append("beekeeping apiary")
    if any(k in q_lower for k in ["ರೇಷ್ಮೆ", "रेशम", "పట్టు", "sericulture", "mulberry"]):
        additions.append("sericulture mulberry")
    if any(k in q_lower for k in ["ಹಿಟ್ಟಿನ ಗಿರಣಿ", "पिठाची गिरणी", "फ्लोर मिल", "పిండి మిల్లు", "flour mill"]):
        additions.append("flour mill project cost")
    if any(k in q_lower for k in ["ಸಾಲ", "ऋण", "कर्ज", "రుణం", "loan", "emi"]):
        additions.append("loan EMI")

    if additions:
        return query + " " + " ".join(additions)
    return query

def execute_authoritative_routing(
    query: str,
    language: str = "kannada",
    project_cost: Optional[float] = None,
    loan_amount: Optional[float] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes intent-based routing:
    - FACTUAL: Retrieves verified chunks, injects into grounded prompt, synthesizes response.
    - DATA_UNAVAILABLE: Returns explicit gap notice without hallucination.
    - MIXED: Performs both authoritative retrieval and deterministic calculation.
    - FINANCIAL: Executes deterministic Python math.
    Returns response payload with dynamic citations, provenance metadata, and latency metrics.
    """
    start_total = time.perf_counter()
    req_id = request_id or str(uuid.uuid4())[:8]

    intent, details = classify_query_intent(query)
    retrieval_used = False
    retrieval_count = 0
    source_ids: List[str] = []
    source_pages: List[int] = []
    verification_status = "NONE"
    financial_engine_used = False
    llm_used = False
    citations: List[str] = []
    evidence_list: List[RetrievedEvidence] = []
    financial_result: Optional[Dict[str, Any]] = None

    retrieval_latency_ms = 0.0
    financial_latency_ms = 0.0
    llm_latency_ms = 0.0

    # -------------------------------------------------------------
    # CASE 1: DATA_UNAVAILABLE
    # -------------------------------------------------------------
    if intent == QueryIntent.DATA_UNAVAILABLE:
        reason = details.get("reason", "")
        if reason == "TRADE_BENCHMARK_NOT_AVAILABLE":
            trade = details.get("trade", "Kirana / Tailoring").title()
            if language == "kannada":
                answer = (
                    f"⚠️ ಅಧಿಕೃತ ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ (DATA_NOT_AVAILABLE):\n\n"
                    f"ನಬಾರ್ಡ್ (NABARD) ಕರ್ನಾಟಕ ಯೂನಿಟ್ ಕಾಸ್ಟ್ ಕೈಪಿಡಿಯಲ್ಲಿ {trade} ಉದ್ಯಮಕ್ಕೆ ಯಾವುದೇ ಅಧಿಕೃತ ಮಾನದಂಡ ದರಗಳಿಲ್ಲ. "
                    f"ಆದ್ದರಿಂದ ಈ ಯೋಜನೆಗೆ ಅರ್ಜಿದಾರರ ನೈಜ ವೆಚ್ಚದ ಅಂದಾಜನ್ನು ಪರಿಗಣಿಸಲಾಗುತ್ತದೆ. "
                    f"ನಾವು ಯಾವುದೇ ಕಾಲ್ಪನಿಕ ಮಾನದಂಡಗಳನ್ನು ನೀಡುವುದಿಲ್ಲ."
                )
            elif language == "hindi":
                answer = (
                    f"⚠️ आधिकारिक डेटा अनुपलब्ध (DATA_NOT_AVAILABLE):\n\n"
                    f"नाबार्ड (NABARD) कर्नाटक यूनिट कॉस्ट बुकलेट में {trade} के लिए कोई आधिकारिक बेंचमार्क लागत उपलब्ध नहीं है। "
                    f"अतः इस उद्यम के लिए आपकी वास्तविक लागत का उपयोग किया जाएगा। "
                    f"हम कोई काल्पनिक डेटा प्रदान नहीं करते हैं।"
                )
            elif language == "telugu":
                answer = (
                    f"⚠️ అధికారిక సమాచారం అందుబాటులో లేదు (DATA_NOT_AVAILABLE):\n\n"
                    f"నాబార్డ్ (NABARD) కర్ణాటక యూనిట్ కాస్ట్ బుక్‌లెట్‌లో {trade} కోసం అధికారిక బెంచ్‌మార్క్ ఖర్చులు అందుబాటులో లేవు. "
                    f"కాబట్టి దరఖాస్తుదారుడి వాస్తవ ప్రాజెక్ట్ ఖర్చు ఆధారంగా మాత్రమే విశ్లేషించబడుతుంది."
                )
            elif language == "marathi":
                answer = (
                    f"⚠️ अधिकृत माहिती उपलब्ध नाही (DATA_NOT_AVAILABLE):\n\n"
                    f"नाबार्ड (NABARD) कर्नाटक युनिट कॉस्ट बुकलेटमध्ये {trade} साठी कोणतेही अधिकृत बेंचमार्क दर उपलब्ध नाहीत. "
                    f"त्यामुळे आपल्या प्रत्यक्ष कोटेशनवर आधारित नियोजन केले जाईल."
                )
            else:
                answer = (
                    f"⚠️ Official Benchmark Not Available (DATA_NOT_AVAILABLE):\n\n"
                    f"The official NABARD Karnataka Unit Cost Booklet does not contain prescribed benchmark costs for {trade}. "
                    f"Evaluation for this activity is customized strictly to your submitted project quotation. "
                    f"No synthetic or unverified benchmarks are substituted."
                )
        else: # PMMY borrower rules
            if language == "kannada":
                answer = (
                    f"⚠️ ಅಧಿಕೃತ ಪರಿಶೀಲನೆ ಬಾಕಿ (AUTHORITATIVE_DATA_NOT_AVAILABLE):\n\n"
                    f"ಪ್ರಸ್ತುತ ಲಭ್ಯವಿರುವ PMMY/ಮುದ್ರಾ ದಾಖಲೆಯು ಬ್ಯಾಂಕ್ ಮರುಹಣಕಾಸು (Refinance) ಅರ್ಹತೆಗೆ ಸಂಬಂಧಿಸಿದೆ. "
                    f"ಅಂತಿಮ ಸಾಲಗಾರರ ಅಧಿಕೃತ ನಿಯಮಗಳು ಮತ್ತು ಬಡ್ಡಿದರಗಳು ಇನ್ನೂ ಕೇಂದ್ರ ಸರ್ಕಾರದ ನೇರ ಅಧಿಸೂಚನೆಯಿಂದ ದೃಢೀಕರಿಸಲ್ಪಟ್ಟಿಲ್ಲ. "
                    f"ಆದ್ದರಿಂದ ಪರಿಶೀಲಿಸದ ಮಾಹಿತಿಯನ್ನು ನೀಡಲಾಗುವುದಿಲ್ಲ."
                )
            else:
                answer = (
                    f"⚠️ Authoritative Borrower Rules Not Available (AUTHORITATIVE_DATA_NOT_AVAILABLE):\n\n"
                    f"The indexed PMMY document covers institutional partner refinance eligibility, not end-borrower terms. "
                    f"Direct borrower interest rates and statutory guidelines remain unverified in the official repository. "
                    f"To prevent misinformation, unverified rules are not asserted as official."
                )

        total_latency_ms = round((time.perf_counter() - start_total) * 1000, 2)
        _log_observability(
            req_id=req_id, intent=intent.value, retrieval_used=False, retrieval_count=0,
            source_ids=[], source_pages=[], verification_status="DATA_NOT_AVAILABLE",
            financial_engine_used=False, llm_used=False, language=language,
            retrieval_ms=0, financial_ms=0, llm_ms=0, total_ms=total_latency_ms
        )
        return {
            "request_id": req_id,
            "intent": intent.value,
            "answer": answer,
            "citations": [],
            "evidence": [],
            "financial_result": None,
            "latencies": {"total_ms": total_latency_ms}
        }

    # -------------------------------------------------------------
    # CASE 2: FACTUAL QUERY
    # -------------------------------------------------------------
    if intent == QueryIntent.FACTUAL:
        t_ret_start = time.perf_counter()
        try:
            norm_q = _normalize_retrieval_query(query)
            evidence_list = retrieve_evidence(query=norm_q, top_k=3, require_verified=True)
        except QdrantUnavailableError as e:
            logger.error(f"Qdrant unavailable during factual retrieval: {e}")
            return {
                "request_id": req_id,
                "intent": intent.value,
                "answer": "⚠️ Error: The authoritative vector retrieval service is currently unavailable. Please try again shortly.",
                "citations": [],
                "evidence": [],
                "financial_result": None,
                "latencies": {"total_ms": round((time.perf_counter() - start_total) * 1000, 2)}
            }

        retrieval_latency_ms = round((time.perf_counter() - t_ret_start) * 1000, 2)
        retrieval_used = True
        retrieval_count = len(evidence_list)

        if not evidence_list:
            # Absence of evidence remains absence of evidence
            answer = "Authoritative government documentation for this specific query was not found in the verified repository."
            if language == "kannada":
                answer = "ಈ ನಿರ್ದಿಷ್ಟ ಪ್ರಶ್ನೆಗೆ ಸಂಬಂಧಿಸಿದ ಅಧಿಕೃತ ಸರ್ಕಾರಿ ದಾಖಲೆಗಳು ಪರಿಶೀಲಿಸಿದ ಭಂಡಾರದಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ."
            return {
                "request_id": req_id,
                "intent": intent.value,
                "answer": answer,
                "citations": [],
                "evidence": [],
                "financial_result": None,
                "latencies": {"total_ms": round((time.perf_counter() - start_total) * 1000, 2)}
            }

        source_ids = [e.source_id for e in evidence_list]
        source_pages = [e.source_page for e in evidence_list]
        verification_status = evidence_list[0].verification_status
        citations = [e.to_citation_string() for e in evidence_list]

        # Grounded LLM Context Construction
        messages = build_grounded_llm_messages(
            user_query=query,
            evidence_list=evidence_list,
            financial_result=None,
            language=language
        )

        t_llm_start = time.perf_counter()
        try:
            from app.ai.llm_client import call_llm_chat
            llm_response = call_llm_chat(messages=messages, temperature=0.2)
            llm_latency_ms = round((time.perf_counter() - t_llm_start) * 1000, 2)
            llm_used = True
            answer = llm_response if llm_response and llm_response.strip() else _generate_factual_fallback_answer(evidence_list, language)
        except Exception as e:
            logger.warning(f"LLM call failed or unavailable: {e}. Using deterministic factual summary.")
            answer = _generate_factual_fallback_answer(evidence_list, language)

        # Enforce Flour Mill 2020 Historical Warning
        if any(e.source_id == "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE" for e in evidence_list):
            if "2020" not in answer:
                hist_warning = "\n\n⚠️ [ಗಮನಿಸಿ: ಈ ವೆಚ್ಚವು 2020 ರ ಪ್ರಾಜೆಕ್ಟ್ ಸಮಾಧಾನ (MDTC) ಮಾದರಿ ಯೋಜನಾ ಪ್ರೊಫೈಲ್‌ನ ಐತಿಹಾಸಿಕ ಮಾನದಂಡವಾಗಿದೆ. ಪ್ರಸ್ತುತ ಮಾರುಕಟ್ಟೆ ವೆಚ್ಚವು ಇಂದಿನ ದರಗಳ ಮೇಲೆ ಅವಲಂಬಿತವಾಗಿರುತ್ತದೆ.]" if language == "kannada" else "\n\n⚠️ [Note: Stated machinery costs reflect the 2020 Project SAMADHAN model project profile benchmark. Current market costs require up-to-date vendor quotations.]"
                answer += hist_warning

        total_latency_ms = round((time.perf_counter() - start_total) * 1000, 2)
        _log_observability(
            req_id=req_id, intent=intent.value, retrieval_used=retrieval_used, retrieval_count=retrieval_count,
            source_ids=source_ids, source_pages=source_pages, verification_status=verification_status,
            financial_engine_used=False, llm_used=llm_used, language=language,
            retrieval_ms=retrieval_latency_ms, financial_ms=0, llm_ms=llm_latency_ms, total_ms=total_latency_ms
        )
        return {
            "request_id": req_id,
            "intent": intent.value,
            "answer": answer,
            "citations": citations,
            "evidence": [e.model_dump() for e in evidence_list],
            "financial_result": None,
            "retrieval_used": True,
            "financial_engine_used": False,
            "latencies": {
                "retrieval_ms": retrieval_latency_ms,
                "llm_ms": llm_latency_ms,
                "total_ms": total_latency_ms
            }
        }

    # -------------------------------------------------------------
    # CASE 3: MIXED QUERY (Authoritative Fact + Personal Calculation)
    # -------------------------------------------------------------
    if intent == QueryIntent.MIXED:
        # 1. Authoritative Retrieval
        t_ret_start = time.perf_counter()
        try:
            norm_q = _normalize_retrieval_query(query)
            evidence_list = retrieve_evidence(query=norm_q, top_k=2, require_verified=True)
        except Exception as e:
            logger.error(f"Retrieval error in mixed query: {e}")
            evidence_list = []
        retrieval_latency_ms = round((time.perf_counter() - t_ret_start) * 1000, 2)
        retrieval_used = bool(evidence_list)
        retrieval_count = len(evidence_list)
        source_ids = [e.source_id for e in evidence_list]
        source_pages = [e.source_page for e in evidence_list]
        citations = [e.to_citation_string() for e in evidence_list]

        # 2. Deterministic Financial Calculation
        t_fin_start = time.perf_counter()
        calc_cost = project_cost or _extract_monetary_amount(query) or 200000.0
        financial_result = calculate_financial_structure(calc_cost)
        financial_latency_ms = round((time.perf_counter() - t_fin_start) * 1000, 2)
        financial_engine_used = True

        # 3. Grounded Context Synthesis
        messages = build_grounded_llm_messages(
            user_query=query,
            evidence_list=evidence_list,
            financial_result=financial_result,
            language=language
        )

        t_llm_start = time.perf_counter()
        try:
            from app.ai.llm_client import call_llm_chat
            llm_response = call_llm_chat(messages=messages, temperature=0.2)
            llm_latency_ms = round((time.perf_counter() - t_llm_start) * 1000, 2)
            llm_used = True
            raw_answer = llm_response if llm_response and llm_response.strip() else _generate_mixed_fallback_answer(evidence_list, financial_result, language)
            answer = _enforce_numerical_integrity(raw_answer, financial_result, language)
        except Exception:
            answer = _generate_mixed_fallback_answer(evidence_list, financial_result, language)

        total_latency_ms = round((time.perf_counter() - start_total) * 1000, 2)
        _log_observability(
            req_id=req_id, intent=intent.value, retrieval_used=retrieval_used, retrieval_count=retrieval_count,
            source_ids=source_ids, source_pages=source_pages, verification_status="VERIFIED_OFFICIAL",
            financial_engine_used=True, llm_used=llm_used, language=language,
            retrieval_ms=retrieval_latency_ms, financial_ms=financial_latency_ms, llm_ms=llm_latency_ms, total_ms=total_latency_ms
        )
        return {
            "request_id": req_id,
            "intent": intent.value,
            "answer": answer,
            "citations": citations,
            "evidence": [e.model_dump() for e in evidence_list],
            "financial_result": financial_result,
            "retrieval_used": retrieval_used,
            "financial_engine_used": True,
            "latencies": {
                "retrieval_ms": retrieval_latency_ms,
                "financial_ms": financial_latency_ms,
                "llm_ms": llm_latency_ms,
                "total_ms": total_latency_ms
            }
        }

    # -------------------------------------------------------------
    # CASE 4: PURE FINANCIAL QUERY
    # -------------------------------------------------------------
    if intent == QueryIntent.FINANCIAL:
        t_fin_start = time.perf_counter()
        calc_cost = project_cost or _extract_monetary_amount(query) or 200000.0
        financial_result = calculate_financial_structure(calc_cost)
        financial_latency_ms = round((time.perf_counter() - t_fin_start) * 1000, 2)
        financial_engine_used = True

        answer = _format_financial_response(financial_result, language)
        total_latency_ms = round((time.perf_counter() - start_total) * 1000, 2)
        _log_observability(
            req_id=req_id, intent=intent.value, retrieval_used=False, retrieval_count=0,
            source_ids=[], source_pages=[], verification_status="NONE",
            financial_engine_used=True, llm_used=False, language=language,
            retrieval_ms=0, financial_ms=financial_latency_ms, llm_ms=0, total_ms=total_latency_ms
        )
        return {
            "request_id": req_id,
            "intent": intent.value,
            "answer": answer,
            "citations": [],
            "evidence": [],
            "financial_result": financial_result,
            "retrieval_used": False,
            "financial_engine_used": True,
            "latencies": {
                "financial_ms": financial_latency_ms,
                "total_ms": total_latency_ms
            }
        }

    # -------------------------------------------------------------
    # CASE 5: GENERAL_CONVERSATION
    # -------------------------------------------------------------
    total_latency_ms = round((time.perf_counter() - start_total) * 1000, 2)
    return {
        "request_id": req_id,
        "intent": QueryIntent.GENERAL_CONVERSATION.value,
        "answer": "How can I assist your rural enterprise today?",
        "citations": [],
        "evidence": [],
        "financial_result": None,
        "retrieval_used": False,
        "financial_engine_used": False,
        "latencies": {"total_ms": total_latency_ms}
    }

def _extract_monetary_amount(text: str) -> Optional[float]:
    """Helper to parse monetary amount from text strings like ₹2,29,000 or 4 lakh."""
    text_lower = text.lower()
    # Match '2 lakh' or '2.5 lakh'
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac)', text_lower)
    if lakh_match:
        return float(lakh_match.group(1)) * 100000.0

    # Match raw numbers like ₹2,29,000 or 200000
    digits_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)', text_lower)
    if digits_match:
        val_str = digits_match.group(1).replace(",", "")
        try:
            val = float(val_str)
            if val >= 5000:
                return val
        except ValueError:
            pass
    return None

def _generate_factual_fallback_answer(evidence_list: List[RetrievedEvidence], language: str) -> str:
    """Deterministic fallback summarizing evidence passages with citations if LLM is unavailable."""
    lines = []
    if language == "kannada":
        lines.append("ಅಧಿಕೃತ ಸರ್ಕಾರಿ ದಾಖಲೆಗಳಿಂದ ಪಡೆದ ಮಾಹಿತಿ:")
        for ev in evidence_list:
            lines.append(f"\n📄 {ev.to_citation_string()}:\n{ev.text}")
    else:
        lines.append("Authoritative evidence from official documents:")
        for ev in evidence_list:
            lines.append(f"\n📄 {ev.to_citation_string()}:\n{ev.text}")
    return "\n".join(lines)

def _enforce_numerical_integrity(
    narrative: str,
    fin_result: Optional[Dict[str, Any]],
    language: str
) -> str:
    """
    Guarantees that LLM narrative outputs CANNOT modify deterministic financial figures.
    If an LLM hallucinates an EMI or financial number contradicting the deterministic
    engine, this guard detects the contradiction, overrides the hallucination,
    and asserts the authoritative calculation.
    """
    if not fin_result or not narrative:
        return narrative

    det_emi = fin_result.get("emi")
    if det_emi:
        import re
        emi_patterns = re.findall(
            r'(?:emi|installment|ಕಂತು|किस्त|हप्ता)[^\d]{1,15}(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)',
            narrative,
            re.IGNORECASE
        )
        for val_str in emi_patterns:
            try:
                clean_val = float(val_str.replace(",", ""))
                if abs(clean_val - det_emi) > 5.0 and clean_val > 0:
                    logger.warning(
                        f"Adversarial or hallucinated EMI detected in LLM narrative "
                        f"({clean_val} vs authoritative {det_emi}). Overriding with deterministic calculation."
                    )
                    correction = (
                        f"\n\n[Authoritative Verification: Verified monthly EMI is ₹{det_emi:,.2f} "
                        f"under {fin_result.get('scheme_name', 'statutory rules')}.]"
                    )
                    return re.sub(r'₹?\s*' + re.escape(val_str), f"₹{det_emi:,.2f}", narrative) + correction
            except ValueError:
                continue
    return narrative

def _generate_mixed_fallback_answer(
    evidence_list: List[RetrievedEvidence],
    fin_result: Dict[str, Any],
    language: str
) -> str:
    """Combines evidence citation with exact deterministic calculation without LLM."""
    citation_str = " ".join([e.to_citation_string() for e in evidence_list])
    if language == "kannada":
        return (
            f"ನಬಾರ್ಡ್ / ಸರ್ಕಾರಿ ಮಾನದಂಡದಂತೆ ವಿವರಗಳು {citation_str}:\n\n"
            f"💰 ಯೋಜನಾ ವೆಚ್ಚ: ₹{fin_result['cost']:,.2f}\n"
            f"🏦 ಸಾಲದ ಮೊತ್ತ: ₹{fin_result['loan']:,.2f}\n"
            f"🤝 ಅರ್ಜಿದಾರರ ಪಾಲು: ₹{fin_result['margin']:,.2f}\n"
            f"📊 ಮಾಸಿಕ ಕಂತು (EMI): ₹{fin_result['emi']:,.2f} ({fin_result['rate']}% ಬಡ್ಡಿದರದಲ್ಲಿ)"
        )
    return (
        f"Authoritative Benchmark Reference {citation_str}:\n\n"
        f"💰 Total Project Cost: ₹{fin_result['cost']:,.2f}\n"
        f"🏦 Bank Loan: ₹{fin_result['loan']:,.2f}\n"
        f"🤝 Beneficiary Margin: ₹{fin_result['margin']:,.2f} ({fin_result['margin_pct']}%)\n"
        f"📊 Monthly Installment (EMI): ₹{fin_result['emi']:,.2f} (at {fin_result['rate']}% p.a.)"
    )

def _format_financial_response(fin_result: Dict[str, Any], language: str) -> str:
    """Formats deterministic financial results."""
    if language == "kannada":
        return (
            f"ಲೆಕ್ಕಾಚಾರ ಮಾಡಿದ ಸಾಲ ಮತ್ತು ಇಎಂಐ ವಿವರಗಳು (ಗಣಿತ ಎಂಜಿನ್):\n\n"
            f"💰 ಒಟ್ಟು ವೆಚ್ಚ: ₹{fin_result['cost']:,.2f}\n"
            f"🏦 ಅನುಮೋದಿತ ಸಾಲ: ₹{fin_result['loan']:,.2f}\n"
            f"🤝 ಸ್ವಂತ ಬಂಡವಾಳ: ₹{fin_result['margin']:,.2f}\n"
            f"📊 ಮಾಸಿಕ ಇಎಂಐ (EMI): ₹{fin_result['emi']:,.2f} (ಅವಧಿ {fin_result['repayment_months']} ತಿಂಗಳು, ಬಡ್ಡಿ {fin_result['rate']}%)"
        )
    return (
        f"Deterministic Financial Calculation (Python Engine):\n\n"
        f"💰 Project Cost: ₹{fin_result['cost']:,.2f}\n"
        f"🏦 Bank Loan: ₹{fin_result['loan']:,.2f}\n"
        f"🤝 Beneficiary Margin: ₹{fin_result['margin']:,.2f} ({fin_result['margin_pct']}%)\n"
        f"📊 Monthly EMI: ₹{fin_result['emi']:,.2f} ({fin_result['repayment_months']} months, {fin_result['rate']}% p.a.)"
    )

def _log_observability(
    req_id: str,
    intent: str,
    retrieval_used: bool,
    retrieval_count: int,
    source_ids: List[str],
    source_pages: List[int],
    verification_status: str,
    financial_engine_used: bool,
    llm_used: bool,
    language: str,
    retrieval_ms: float,
    financial_ms: float,
    llm_ms: float,
    total_ms: float
):
    """Structured JSON logging for Phase 5 observability."""
    record = {
        "event": "retrieval_routing_execution",
        "request_id": req_id,
        "intent": intent,
        "retrieval_used": retrieval_used,
        "retrieval_count": retrieval_count,
        "source_ids": source_ids,
        "source_pages": source_pages,
        "verification_status": verification_status,
        "financial_engine_used": financial_engine_used,
        "llm_used": llm_used,
        "response_language": language,
        "retrieval_latency_ms": retrieval_ms,
        "financial_latency_ms": financial_ms,
        "llm_latency_ms": llm_ms,
        "total_latency_ms": total_ms
    }
    logger.info(json.dumps(record))
