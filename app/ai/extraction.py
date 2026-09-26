import re
import json
import logging
from typing import Dict, Any, Optional
from .llm_client import call_llm_chat
from app.finance.multi_schemes import get_all_eligible_schemes
from app.ai.advisory_text import build_advisory

logger = logging.getLogger("ai_extraction")

EXTRACTION_SYSTEM_PROMPT = """You are an AI data extractor for a rural micro-enterprise lending portal in India.
Your job is to read the user's message (which may be in English, Hindi, Kannada, Telugu, Marathi, or code-mixed) and extract:
1. "trade": the specific business or micro-enterprise (e.g. Kirana stall, Dairy cow, Tailoring, Flour mill, Weaving).
2. "district": district in India (e.g. Belagavi, Mysuru, Dharwad, Guntur, Warangal, Pune, Nagpur, etc. or null if unknown).
3. "state": Indian state (e.g. Karnataka, Andhra Pradesh, Telangana, Maharashtra, Uttar Pradesh, etc. or null if unknown).
4. "available_capital": the money or savings the user says they have on hand (numeric, or null).
5. "project_cost": total estimated cost or capital needed for the venture (numeric, or null).
6. "language": language of interaction (e.g. kannada, hindi, telugu, marathi, english, tamil).

CRITICAL INSTRUCTIONS:
- You must NEVER compute, calculate, or estimate loan amounts, EMIs, or interest rates.
- Only extract explicitly mentioned or directly implied numerical values.
- Respond with STRICT JSON matching this schema:
{
  "trade": "string or null",
  "district": "string or null",
  "state": "string or null",
  "available_capital": number or null,
  "project_cost": number or null,
  "language": "string"
}
"""

def extract_entrepreneur_details(user_text: str) -> Dict[str, Any]:
    """Extract structured entrepreneur parameters from conversational input."""
    from app.config import settings
    from app.ai.gemini_client import is_gemini_configured

    if not is_gemini_configured():
        return fallback_regex_extractor(user_text)

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"User message: {user_text}"}
    ]

    try:
        raw_output = call_llm_chat(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        if raw_output and raw_output.strip():
            # Clean possible markdown wrapping
            clean_json = raw_output.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?", "", clean_json)
                clean_json = re.sub(r"```$", "", clean_json).strip()
            data = json.loads(clean_json)
            return data
    except Exception as e:
        logger.warning(f"LLM extraction failed or returned invalid JSON ({e}). Using regex heuristics.")

    return fallback_regex_extractor(user_text)

def fallback_regex_extractor(text: str) -> Dict[str, Any]:
    """Heuristic regex extractor when LLM API is unavailable or offline. Returns None for missing fields."""
    numbers = [float(n.replace(',', '')) for n in re.findall(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', text, re.I) if float(n.replace(',', '')) > 500]

    project_cost = numbers[0] if numbers else None
    capital = numbers[1] if len(numbers) > 1 else None

    trade = None
    lower_t = text.lower()
    if any(w in lower_t for w in ["kirana", "grocery", "provision", "store", "stall", "shop", "కిరాణా", "किराणा", "किराना", "ಕಿರಾಣಿ", "ಅಂಗಡಿ", "दुकान"]):
        trade = "Kirana Store"
    elif any(w in lower_t for w in ["dairy", "cow", "milk", "buffalo", "cattle", "ಹಸು", "ಹೈನುಗಾರಿಕೆ", "ఆవు", "పాడి", "गाय", "दूध", "डेअरी"]):
        trade = "Dairy Farming"
    elif any(w in lower_t for w in ["tailor", "tailoring", "garment", "clothes", "ಹೊಲಿಗೆ", "కుట్టు", "शिलाई"]):
        trade = "Tailoring Unit"
    elif any(w in lower_t for w in ["poultry", "chicken", "broiler", "egg", "ಕೋಳಿ", "కోళ్ళు", "कुक्कुटपालन"]):
        trade = "Poultry Farm"
    elif any(w in lower_t for w in ["flour", "mill", "atta", "ಹಿಟ್ಟು", "ಗಿರಣಿ", "గిర్ని", "चक्की"]):
        trade = "Flour Mill"
    elif any(w in lower_t for w in ["weave", "weaver", "loom", "handloom", "ಮಗ್ಗ", "మగ్గం", "हातमाग"]):
        trade = "Handloom Weaving"

    district = None
    state = None
    # Karnataka
    if "belagavi" in lower_t or "belgaum" in lower_t or "ಬೆಳಗಾವಿ" in text:
        district, state = "Belagavi", "Karnataka"
    elif "mysuru" in lower_t or "mysore" in lower_t or "ಮೈಸೂರು" in text:
        district, state = "Mysuru", "Karnataka"
    elif "dharwad" in lower_t or "hubballi" in lower_t or "ಧಾರವಾಡ" in text:
        district, state = "Dharwad", "Karnataka"
    elif "mandya" in lower_t or "ಮಂಡ್ಯ" in text:
        district, state = "Mandya", "Karnataka"
    elif "shivamogga" in lower_t or "shimoga" in lower_t or "ಶಿವಮೊಗ್ಗ" in text:
        district, state = "Shivamogga", "Karnataka"
    elif "hassan" in lower_t or "ಹಾಸನ" in text:
        district, state = "Hassan", "Karnataka"
    # Andhra Pradesh / Telangana
    elif "guntur" in lower_t or "గుంటూరు" in text:
        district, state = "Guntur", "Andhra Pradesh"
    elif "vijayawada" in lower_t or "విజయవాడ" in text:
        district, state = "Vijayawada", "Andhra Pradesh"
    elif "visakhapatnam" in lower_t or "vizag" in lower_t or "విశాఖపట్నం" in text:
        district, state = "Visakhapatnam", "Andhra Pradesh"
    elif "warangal" in lower_t or "వరంగల్" in text:
        district, state = "Warangal", "Telangana"
    elif "kurnool" in lower_t or "కర్నూలు" in text:
        district, state = "Kurnool", "Andhra Pradesh"
    elif "hyderabad" in lower_t or "హైదరాబాద్" in text:
        district, state = "Hyderabad", "Telangana"
    # Maharashtra
    elif "pune" in lower_t or "पुणे" in text:
        district, state = "Pune", "Maharashtra"
    elif "nagpur" in lower_t or "नागपूर" in text:
        district, state = "Nagpur", "Maharashtra"
    elif "nashik" in lower_t or "नाशिक" in text:
        district, state = "Nashik", "Maharashtra"
    elif "kolhapur" in lower_t or "कोल्हापूर" in text:
        district, state = "Kolhapur", "Maharashtra"
    elif "solapur" in lower_t or "सोलापूर" in text:
        district, state = "Solapur", "Maharashtra"

    # Language detection (returns None if no clear script detected, preserving user's chosen language)
    try:
        from app.dialogue.conversation_state import detect_message_language
        lang = detect_message_language(text)
    except Exception:
        lang = None

    return {
        "trade": trade,
        "district": district,
        "state": state or ("Karnataka" if district else None),
        "available_capital": capital,
        "project_cost": project_cost,
        "language": lang
    }

def generate_advisory_message(
    financial_data: Dict[str, Any],
    trade: str,
    district: str,
    nabard_context: Optional[str] = None,
    language: str = "english",
    state: str = "Karnataka",
    available_capital: Optional[float] = None,
    multi_schemes: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    benchmark: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Advisory message from verified, computed results only. It is assembled from fixed templates in the
    user's language rather than written by an LLM, so no figure can be altered or invented.
    """
    cost = float(financial_data["cost"])
    if not multi_schemes:
        multi_schemes = get_all_eligible_schemes(
            cost=cost, trade=trade, district=district, state=state,
            available_capital=available_capital, profile=profile,
        )
    return build_advisory(trade, district, cost, available_capital, multi_schemes, language, benchmark=benchmark)
