"""
Applicant intake: collects every detail the advice and the DPR depend on in a few grouped questions
(business; about you; location and money; conditional extras), then asks the applicant to confirm them.
A partial answer keeps what was stated and asks only for the rest. Nothing is assumed or defaulted.

Context layout: enterprise fields (trade, district, state, project_cost, available_capital) sit at the
top level of the conversation context; applicant fields sit under context["profile"].
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.dialogue import intake_parsing as P
from app.dialogue.intake_text import (QUESTIONS, LABELS, VALUE_LABELS, FIELD_KEYWORDS, MESSAGES, GROUP_QUESTIONS,
                                      text_for)
from app.finance.calculator import MIN_PROJECT_COST, TLS_MAX_COST
from app.finance.pmegp import education_question_needed
from app.finance.formatting import format_inr

logger = logging.getLogger("intake")

ENTERPRISE_FIELDS = ("trade", "district", "project_cost", "available_capital")
BASE_ORDER = [
    "trade", "district", "project_cost", "full_name", "age", "gender", "social_category",
    "area_type", "annual_family_income", "available_capital",
]
AMOUNT_FIELDS = ("project_cost", "annual_family_income", "available_capital")
GENDERS = {"male", "female", "transgender"}
CATEGORIES = {"general", "sc", "st", "obc", "minority"}
CATEGORY_ALIASES = {"bc": "obc", "open": "general", "gen": "general", "oc": "general"}
AREAS = {"rural", "urban"}


# ---------------- field access ----------------

def get_value(context: Dict[str, Any], field: str) -> Any:
    if field in ENTERPRISE_FIELDS:
        return context.get(field)
    return (context.get("profile") or {}).get(field)


def set_value(context: Dict[str, Any], field: str, value: Any) -> None:
    if field in ENTERPRISE_FIELDS:
        context[field] = value
    else:
        profile = dict(context.get("profile") or {})
        profile[field] = value
        context["profile"] = profile


def required_fields(context: Dict[str, Any]) -> List[str]:
    fields = list(BASE_ORDER)
    profile = context.get("profile") or {}
    # Only a general-category man can still qualify as "special" through ex-serviceman / disability status
    if profile.get("social_category") == "general" and profile.get("gender") == "male":
        fields.insert(fields.index("social_category") + 1, "special_status")
    if education_question_needed(context.get("project_cost"), context.get("trade")):
        fields.append("education_8th_pass")
    return fields


def next_missing(context: Dict[str, Any]) -> Optional[str]:
    for field in required_fields(context):
        if get_value(context, field) is None:
            return field
    return None


def question(field: str, lang: str) -> str:
    return text_for(QUESTIONS[field], lang)


# Questions are asked in groups of related details
GROUPS = [
    ("business", ["trade", "district", "project_cost"]),
    ("about_you", ["full_name", "age", "gender", "social_category"]),
    ("location_money", ["area_type", "annual_family_income", "available_capital"]),
    ("extra", ["special_status", "education_8th_pass"]),
]


def next_group(context: Dict[str, Any]) -> Optional[Tuple[str, List[str], List[str]]]:
    """(group id, required fields of the group, missing ones) for the first group with anything missing."""
    required = set(required_fields(context))
    for group, fields in GROUPS:
        needed = [f for f in fields if f in required]
        missing = [f for f in needed if get_value(context, f) is None]
        if missing:
            return group, needed, missing
    return None


def next_prompt(context: Dict[str, Any], lang: str) -> Optional[Tuple[str, List[str]]]:
    """The message asking for the next missing details, and the fields it asks for."""
    nxt = next_group(context)
    if not nxt:
        return None
    group, needed, missing = nxt
    if group in GROUP_QUESTIONS and missing == needed:
        return text_for(GROUP_QUESTIONS[group], lang), missing
    header = text_for(MESSAGES["almost_done" if group == "extra" and missing == needed else "also_tell"], lang)
    return header + "\n\n" + "\n\n".join(question(f, lang) for f in missing), missing


# ---------------- reading answers ----------------

_EXTRACTION_PROMPT = """You read applicant details for a rural business loan advisory in Karnataka, India.
The message may be English, Kannada, Hindi, Telugu, Marathi or mixed, and may be a voice-note transcript.
{hint}
Return STRICT JSON with exactly these keys. Use null for anything NOT clearly stated in this message:
{{
  "trade": "business the user wants to start",
  "district": "district name in English (if a town or taluk is named, give its district)",
  "state": "Indian state of that district",
  "project_cost": number (total project cost in rupees),
  "available_capital": number (the user's own money to invest; 0 if they say they have none),
  "full_name": "the applicant's own name",
  "gender": "male" | "female" | "transgender",
  "age": integer (years),
  "social_category": "general" | "sc" | "st" | "obc" | "minority",
  "area_type": "rural" (village / gram panchayat) | "urban" (town / city / municipality),
  "annual_family_income": number (yearly family income in rupees),
  "special_status": true if they say they are an ex-serviceman or a person with disability, false if they say they are not,
  "education_8th_pass": true if they passed 8th standard or higher, false if not,
  "confirmation": "yes" if the message only confirms or agrees, "no" if it only rejects, else null
}}
Rules:
- Convert amounts to rupees: "2 lakh" = 200000, "50 thousand" = 50000, "1.5 lakh" = 150000.
- Never guess. Do not infer gender, category, age, area, income or name from the language, the business, a name, or anything not explicitly said.
- Put one amount in one field only. A bare amount or number answers the question being asked.
"""


def _gemini_extract(text: str, pending: List[str]) -> Optional[Dict[str, Any]]:
    from app.ai.gemini_client import is_gemini_configured
    from app.ai.llm_client import call_llm_chat

    if not is_gemini_configured():
        return None
    if len(pending) == 1:
        hint = (f"The user is answering this question: \"{question(pending[0], 'english')}\". "
                f"A short answer (a number, a word, yes/no) refers to that question.")
    elif pending:
        asked = " | ".join(question(f, "english") for f in pending)
        hint = (f"The user is answering these questions, possibly all at once and in any order: {asked}. "
                f"Map each stated value to its question; leave unanswered ones null.")
    else:
        hint = "The user may give several details at once."
    raw = call_llm_chat(
        messages=[
            {"role": "system", "content": _EXTRACTION_PROMPT.format(hint=hint)},
            {"role": "user", "content": text},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    if not raw:
        return None
    try:
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip()).strip()
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except (ValueError, TypeError):
        logger.warning("Intake extraction returned invalid JSON; using rule-based readers.")
        return None


def _parse_field(field: str, text: str) -> Any:
    if field == "trade":
        from app.ai.extraction import fallback_regex_extractor
        trade = fallback_regex_extractor(text).get("trade")
        if trade:
            return trade
        words = text.strip().split()
        return text.strip() if 1 <= len(words) <= 6 and not re.search(r"\d", P.to_ascii_digits(text)) else None
    if field == "district":
        return P.normalize_district(text) or P.outside_karnataka_place(text)
    if field in AMOUNT_FIELDS:
        return P.parse_amount(text, allow_zero=(field == "available_capital"))
    if field == "age":
        return P.parse_age(text)
    if field == "gender":
        return P.parse_gender(text)
    if field == "social_category":
        return P.parse_category(text)
    if field == "area_type":
        return P.parse_area(text)
    if field in ("special_status", "education_8th_pass"):
        return P.parse_bool(text)
    if field == "full_name":
        return P.parse_name(text)
    return None


def match_field_name(text: str) -> Optional[str]:
    lower = (text or "").lower()
    for field, keywords in FIELD_KEYWORDS.items():
        if any(P.has_keyword(lower, k) for k in keywords):
            return field
    return None


_SEGMENT_SPLIT = re.compile(r"[,;\n।]+|\s+(?:and|और|ಮತ್ತು|మరియు|आणि)\s+")


def _segments(text: str) -> List[str]:
    return [seg.strip() for seg in _SEGMENT_SPLIT.split(text or "") if seg and seg.strip()]


def _read_several(text: str, pending: List[str]) -> Dict[str, Any]:
    """
    Reads answers to several questions from one message. Only unambiguous values are taken: a value that
    could belong to more than one question (two amounts, two yes/no answers) needs its label, and a name
    is only taken from its own comma-separated part. Anything unclear is asked again, never guessed.
    """
    data: Dict[str, Any] = {}
    segments = _segments(text)
    for field, reader in (("gender", P.parse_gender), ("social_category", P.parse_category), ("area_type", P.parse_area)):
        if field in pending:
            data[field] = reader(text)
    if "age" in pending:
        data["age"] = P.parse_age(text)

    for group_fields in ([f for f in pending if f in AMOUNT_FIELDS], [f for f in pending if f in ("special_status", "education_8th_pass")]):
        if len(group_fields) == 1:
            data[group_fields[0]] = _parse_field(group_fields[0], text)
        elif len(group_fields) > 1:
            unlabeled = []
            for seg in segments:
                named = match_field_name(seg)
                if named in group_fields and data.get(named) is None:
                    data[named] = _parse_field(named, seg)
                elif named is None and _parse_field(group_fields[0], seg) is not None:
                    unlabeled.append(seg)
            # Unlabelled values given in the order the questions were numbered, one per question
            still = [f for f in group_fields if data.get(f) is None]
            if still and len(unlabeled) == len(still):
                for field, seg in zip(still, unlabeled):
                    data[field] = _parse_field(field, seg)

    if "full_name" in pending and len(segments) > 1:
        for seg in segments:
            if (not re.search(r"\d", P.to_ascii_digits(seg)) and not P.parse_gender(seg) and not P.parse_category(seg)
                    and not P.parse_area(seg)):
                data["full_name"] = P.parse_name(seg)
                break

    if not any(v is not None for v in data.values()) and pending and len(segments) <= 1:
        # A single short reply answers the first question listed
        data[pending[0]] = _parse_field(pending[0], text)
    return data


def _rule_based_extract(text: str, pending: List[str]) -> Dict[str, Any]:
    if pending:
        data: Dict[str, Any] = _read_several(text, pending) if len(pending) > 1 else {pending[0]: _parse_field(pending[0], text)}
        if "full_name" not in pending:
            # Places and businesses named alongside the answer are explicit, so read them too
            data.setdefault("district", P.normalize_district(text) or P.outside_karnataka_place(text))
            from app.ai.extraction import fallback_regex_extractor
            data.setdefault("trade", fallback_regex_extractor(text).get("trade"))
        return data

    data: Dict[str, Any] = {}
    # A correction such as "age 35" or "ಆದಾಯ 2 ಲಕ್ಷ": field name plus value
    named = match_field_name(text)
    if named and named != "full_name":
        data[named] = _parse_field(named, text)
    # An opening message such as "dairy in Belagavi, project cost 2 lakh"
    from app.ai.extraction import fallback_regex_extractor
    opening = fallback_regex_extractor(text)
    data.setdefault("trade", opening.get("trade"))
    if not any(data.get(f) is not None for f in AMOUNT_FIELDS):
        data["project_cost"] = opening.get("project_cost")
    district = P.normalize_district(text)
    data.setdefault("district", district or P.outside_karnataka_place(text))
    for field, reader in (("gender", P.parse_gender), ("social_category", P.parse_category), ("area_type", P.parse_area)):
        data.setdefault(field, reader(text))
    data["confirmation"] = P.parse_yes_no(text)
    return data


def _clean(data: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only well-formed values; anything malformed is treated as not stated."""
    out: Dict[str, Any] = {}

    def text_value(v, max_len=80):
        return v.strip() if isinstance(v, str) and v.strip() and len(v.strip()) <= max_len else None

    out["trade"] = text_value(data.get("trade"), 60)
    out["district"] = text_value(data.get("district"), 60)
    out["state"] = text_value(data.get("state"), 40)
    out["full_name"] = P.parse_name(data["full_name"]) if isinstance(data.get("full_name"), str) else None
    for field in AMOUNT_FIELDS:
        v = data.get(field)
        if isinstance(v, str):
            v = P.parse_amount(v, allow_zero=(field == "available_capital"))
        ok = isinstance(v, (int, float)) and not isinstance(v, bool) and (v > 0 or (field == "available_capital" and v == 0))
        out[field] = float(v) if ok else None
    age = data.get("age")
    if isinstance(age, str):
        age = P.parse_age(age)
    out["age"] = int(age) if isinstance(age, (int, float)) and not isinstance(age, bool) and 10 <= age <= 100 else None
    gender = str(data.get("gender") or "").lower()
    out["gender"] = gender if gender in GENDERS else None
    category = str(data.get("social_category") or "").lower()
    category = CATEGORY_ALIASES.get(category, category)
    out["social_category"] = category if category in CATEGORIES else None
    area = str(data.get("area_type") or "").lower()
    out["area_type"] = area if area in AREAS else None
    for field in ("special_status", "education_8th_pass"):
        out[field] = data.get(field) if isinstance(data.get(field), bool) else None
    confirmation = str(data.get("confirmation") or "").lower()
    out["confirmation"] = confirmation if confirmation in ("yes", "no") else None
    return out


def extract_answers(text: str, pending: Any) -> Dict[str, Any]:
    """
    Reads everything the message states. `pending` is the field or fields just asked for.
    Gemini first; rule-based readers when it is unavailable or leaves an asked field empty.
    """
    pending_list: List[str] = [pending] if isinstance(pending, str) else list(pending or [])
    gemini = _gemini_extract(text, pending_list)
    if gemini is None:
        return _clean(_rule_based_extract(text, pending_list))

    data = _clean(gemini)
    if pending_list and any(data.get(f) is None for f in pending_list):
        fallback = _clean(_rule_based_extract(text, pending_list))
        taken_amounts = [data.get(f) for f in AMOUNT_FIELDS if data.get(f) is not None]
        for field in pending_list:
            value = fallback.get(field)
            if data.get(field) is None and value is not None and not (field in AMOUNT_FIELDS and value in taken_amounts):
                data[field] = value
    if data.get("confirmation") is None:
        data["confirmation"] = P.parse_yes_no(text)
    return data


# ---------------- applying answers ----------------

def apply_answers(context: Dict[str, Any], data: Dict[str, Any]) -> Tuple[List[str], Optional[Tuple[str, str]]]:
    """
    Stores the stated values. Returns (updated field names, issue) where issue is
    ("out_of_coverage", place), ("district_unrecognised", place) or ("invalid_cost", "").
    """
    updated: List[str] = []
    issue: Optional[Tuple[str, str]] = None

    district_text, state_text = data.get("district"), data.get("state")
    if district_text or (state_text and state_text.strip().lower() != "karnataka"):
        canonical = P.normalize_district(district_text or "")
        if canonical and (not state_text or state_text.strip().lower() == "karnataka"):
            if context.get("district") != canonical:
                updated.append("district")
            context["district"], context["state"] = canonical, "Karnataka"
        elif (state_text and state_text.strip().lower() != "karnataka") or P.mentions_outside_karnataka(district_text or ""):
            issue = ("out_of_coverage", district_text or state_text)
        else:
            issue = ("district_unrecognised", district_text)

    cost = data.get("project_cost")
    if cost is not None:
        if MIN_PROJECT_COST <= cost <= TLS_MAX_COST:
            if context.get("project_cost") != cost:
                updated.append("project_cost")
            context["project_cost"] = cost
        else:
            issue = issue or ("invalid_cost", "")

    for field in ("trade", "available_capital", "full_name", "gender", "age", "social_category", "area_type",
                  "annual_family_income", "special_status", "education_8th_pass"):
        value = data.get(field)
        if value is not None and get_value(context, field) != value:
            set_value(context, field, value)
            updated.append(field)
    return updated, issue


def issue_message(issue: Tuple[str, str], lang: str) -> str:
    kind, place = issue
    return text_for(MESSAGES[kind], lang).format(place=place or "")


# ---------------- confirmation summary ----------------

def display_value(field: str, value: Any, lang: str) -> str:
    if field in AMOUNT_FIELDS:
        return format_inr(value)
    if field in ("gender", "area_type", "social_category"):
        return text_for(VALUE_LABELS[field].get(value, {"english": str(value)}), lang)
    if isinstance(value, bool):
        return text_for(VALUE_LABELS["bool"]["yes" if value else "no"], lang)
    return str(value)


def summary(context: Dict[str, Any], lang: str) -> str:
    lines = [text_for(MESSAGES["confirm_header"], lang)]
    for field in required_fields(context):
        value = get_value(context, field)
        if value is not None:
            lines.append(f"• {text_for(LABELS[field], lang)}: {display_value(field, value, lang)}")
    lines.append("")
    lines.append(text_for(MESSAGES["confirm_footer"], lang))
    return "\n".join(lines)


def profile_for_records(context: Dict[str, Any]) -> Dict[str, Any]:
    """Applicant details exactly as stated, for the DPR and the SCA dashboard."""
    profile = dict(context.get("profile") or {})
    profile["available_capital"] = context.get("available_capital")
    return profile
