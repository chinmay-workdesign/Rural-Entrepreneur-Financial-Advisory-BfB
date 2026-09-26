"""
PMEGP eligibility and means of finance for one applicant.

Every percentage, ceiling and eligibility rule is read from the verified extraction of the
PMEGP Revised Guidelines (data/processed/schemes/pmegp_rules.json). This module owns only the
arithmetic and the mapping from the applicant's stated profile to the applicable rule.
Nothing about the applicant is assumed: without a complete profile no subsidy figure is produced.
"""
import os
import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

_RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "processed", "schemes", "pmegp_rules.json",
)

SPECIAL_SOCIAL_CATEGORIES = {"sc", "st", "obc", "minority"}
SPECIAL_GENDERS = {"female", "transgender"}

# Activity classification used only to apply the guideline's sector rules
_ALLOWED_ANIMAL_HUSBANDRY = [
    "dairy", "cow", "buffalo", "milk", "poultry", "chicken", "broiler", "layer", "egg", "duck",
    "fish", "aquaculture", "prawn", "bee", "apiary", "honey", "sericulture", "silk",
    "ಹೈನು", "ಹಸು", "ಎಮ್ಮೆ", "ಹಾಲು", "ಕೋಳಿ", "ಮೀನು", "ಜೇನು", "ರೇಷ್ಮೆ",
    "डेयरी", "डेअरी", "गाय", "भैंस", "म्हैस", "दूध", "दुग्ध", "मुर्गी", "कुक्कुट", "मछली", "मत्स्य", "मधुमक्खी", "रेशम",
    "పాడి", "ఆవు", "గేదె", "పాలు", "కోళ్ల", "కోడి", "చేపల", "తేనె", "పట్టు",
]
_EXCLUDED_ANIMAL_HUSBANDRY = [
    "goat", "sheep", "pig", "piggery", "ಮೇಕೆ", "ಕುರಿ", "ಹಂದಿ", "बकरी", "भेड़", "सूअर", "शेळी", "मेंढी", "डुक्कर",
    "మేక", "గొర్రె", "పంది",
]
_MANUFACTURING = [
    "flour", "mill", "atta", "tailor", "stitch", "garment", "bakery", "oil", "spice", "masala", "pickle",
    "papad", "food processing", "weav", "handloom", "loom", "carpentry", "furniture", "brick", "agarbatti",
    "candle", "soap", "leather", "pottery", "jaggery",
    "ಹಿಟ್ಟು", "ಗಿರಣಿ", "ಹೊಲಿಗೆ", "ಟೈಲರ", "ಬೇಕರಿ", "ಎಣ್ಣೆ", "ಮಗ್ಗ", "ನೇಕಾರ",
    "चक्की", "आटा", "सिलाई", "दर्जी", "बेकरी", "तेल", "हथकरघा", "पिठाची गिरणी", "शिलाई", "शिवण",
    "పిండి", "మిల్లు", "కుట్టు", "టైలర", "బేకరీ", "నూనె", "మగ్గం", "నేత",
]
_TRADING = [
    "kirana", "grocery", "provision", "general store", "shop", "store", "retail", "stall", "vendor", "trading",
    "ಕಿರಾಣಿ", "ಅಂಗಡಿ", "किराना", "किराणा", "दुकान", "కిరాణా", "దుకాణం", "షాపు",
]


@lru_cache(maxsize=1)
def _rules() -> Dict[str, Dict[str, Any]]:
    with open(_RULES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {r["rule_id"]: r for r in data.get("rules", [])}


def _rule_value(rule_id: str) -> Any:
    return _rules()[rule_id]["value"]


def classify_activity(trade: Optional[str]) -> str:
    """Returns 'animal_husbandry_allowed', 'animal_husbandry_excluded', 'manufacturing', 'trading' or 'unknown'."""
    t = (trade or "").lower()
    if not t:
        return "unknown"
    if any(w in t for w in _ALLOWED_ANIMAL_HUSBANDRY):
        return "animal_husbandry_allowed"
    if any(w in t for w in _EXCLUDED_ANIMAL_HUSBANDRY):
        return "animal_husbandry_excluded"
    if any(w in t for w in _MANUFACTURING):
        return "manufacturing"
    if any(w in t for w in _TRADING):
        return "trading"
    return "unknown"


def is_special_category(profile: Dict[str, Any]) -> Optional[bool]:
    """Special category per para 3.2(i). None when the profile does not yet say enough to decide."""
    category = profile.get("social_category")
    gender = profile.get("gender")
    special_status = profile.get("special_status")
    if category in SPECIAL_SOCIAL_CATEGORIES or gender in SPECIAL_GENDERS or special_status is True:
        return True
    if category == "general" and gender == "male" and special_status is False:
        return False
    return None


def education_threshold(activity: str) -> float:
    """Project cost above which VIII pass is needed (para 4.1(iii)): ₹10 lakh manufacturing, ₹5 lakh otherwise."""
    return 1000000.0 if activity == "manufacturing" else 500000.0


def education_question_needed(project_cost: Optional[float], trade: Optional[str]) -> bool:
    if not project_cost:
        return False
    return float(project_cost) > education_threshold(classify_activity(trade))


def compute_pmegp(cost: float, trade: Optional[str], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """PMEGP position for this applicant. Amounts are None unless eligibility and category are known."""
    rules = _rules()
    profile = profile or {}
    activity = classify_activity(trade)

    result: Dict[str, Any] = {
        "name": "Prime Minister's Employment Generation Programme (PMEGP)",
        "agency": "KVIC / KVIB / District Industries Centre (DIC)",
        "type": "Credit-Linked Capital Margin Subsidy",
        "source_id": "PMEGP_REVISED_GUIDELINES_2023",
        "source_organization": "Ministry of MSME, Government of India",
        "source_page": 4,
        "publication_year": 2023,
        "verification_status": "VERIFIED_OFFICIAL",
        "source_type": "GOVERNMENT_SCHEME_RULE",
        "activity_class": activity,
        "eligible": None,
        "ineligible_reasons": [],
        "ineligible_codes": [],
        "conditions": [
            "New unit only; units that already took a government subsidy are not eligible (para 4.1).",
            "Only one person per family (self and spouse) (para 4.1, note 1).",
            "Unit must be registered on the Udyam portal (para 4.1(vi)).",
        ],
        "category_basis": None,
        "area_type": profile.get("area_type"),
        "subsidy_pct": None,
        "subsidy_amount": None,
        "own_contribution_pct": None,
        "own_contribution": None,
        "bank_loan_pct": None,
        "bank_loan": None,
        "interest_rate": "Bank's normal rate (para 8.4)",
        "tenure": "3 to 7 years after the bank's moratorium (para 8.4)",
        "how_to_redeem": [
            "Apply online on the KVIC PMEGP portal (www.kviconline.gov.in).",
            "Upload the DPR, Aadhaar, caste/special-category certificate and rural-area certificate.",
            "Complete the Entrepreneurship Development Programme (EDP) training.",
        ],
    }

    reasons: List[str] = []
    codes: List[str] = []
    age = profile.get("age")
    min_age = rules["PMEGP_MIN_AGE_ELIGIBILITY"]["value"]
    if isinstance(age, (int, float)) and age < min_age:
        reasons.append(f"Applicant must be above {min_age} years of age (para 4.1(i), page 5).")
        codes.append("age")

    if activity == "trading":
        reasons.append(
            "Plain trading shops are not eligible in Karnataka. Only outlets selling KVI/PMEGP products, "
            "or shops backed by your own manufacturing or service unit, are allowed (para 4.1(iv), page 6)."
        )
        codes.append("trading")
    elif activity == "animal_husbandry_excluded":
        reasons.append(
            "Animal husbandry is on the PMEGP negative list; only dairy, poultry, aquaculture and bee/sericulture "
            "are allowed (para 30(iv), page 28)."
        )
        codes.append("animal_husbandry")

    edu = profile.get("education_8th_pass")
    if edu is False and cost > education_threshold(activity):
        reasons.append(
            "Projects above ₹10 lakh (manufacturing) or ₹5 lakh (business/service) need at least 8th standard "
            "pass (para 4.1(iii), page 6)."
        )
        codes.append("education")

    if reasons:
        result["eligible"] = False
        result["ineligible_reasons"] = reasons
        result["ineligible_codes"] = codes
        return result

    special = is_special_category(profile)
    area = profile.get("area_type")
    if special is None or area not in ("rural", "urban"):
        # Not enough stated information to pick the applicable rate: never default it.
        return result

    basis = "SPECIAL" if special else "GENERAL"
    area_key = area.upper()
    subsidy_pct = float(_rule_value(f"PMEGP_MARGIN_MONEY_SUBSIDY_{area_key}_{basis}"))
    own_pct = float(_rule_value(f"PMEGP_OWN_CONTRIBUTION_{area_key}_{basis}"))
    bank_pct = float(_rule_value(f"PMEGP_BANK_FINANCE_{basis}"))

    # Subsidy is admissible only up to the sector ceiling (para 3.2 notes 1, 2 and 4)
    if activity == "manufacturing":
        subsidy_base = min(cost, float(_rule_value("PMEGP_MAX_PROJECT_COST_MANUFACTURING")))
    elif cost <= float(_rule_value("PMEGP_MAX_PROJECT_COST_SERVICE_BUSINESS")):
        subsidy_base = cost
    else:
        subsidy_base = None
        result["conditions"].append(
            "Subsidy is admissible up to ₹20 lakh project cost for business/service units and ₹50 lakh for "
            "manufacturing; confirm with the DIC which applies to your activity (para 3.2, page 5)."
        )

    result.update({
        "eligible": True,
        "category_basis": basis.lower(),
        "subsidy_pct": subsidy_pct,
        "subsidy_amount": round(subsidy_base * subsidy_pct / 100.0, 2) if subsidy_base is not None else None,
        "own_contribution_pct": own_pct,
        "own_contribution": round(cost * own_pct / 100.0, 2),
        "bank_loan_pct": bank_pct,
        "bank_loan": round(cost * bank_pct / 100.0, 2),
    })
    if activity == "unknown":
        result["conditions"].append(
            "The DIC/KVIC must confirm your activity is not on the negative list (para 30)."
        )
    return result
