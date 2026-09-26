"""
Rule-based readers for intake answers (typed text or voice-note transcripts).
Used directly when Gemini is unavailable and to read short answers to a known question.
Every reader returns None when the answer does not clearly state the value: nothing is guessed.
"""
import re
from typing import Dict, List, Optional, Tuple

# ---------------- helpers ----------------

_INDIC_DIGITS = {}
for _base in (0x0966, 0x0CE6, 0x0C66):  # Devanagari, Kannada, Telugu digits
    for _i in range(10):
        _INDIC_DIGITS[chr(_base + _i)] = str(_i)
_DIGIT_TABLE = str.maketrans(_INDIC_DIGITS)


def to_ascii_digits(text: str) -> str:
    return (text or "").translate(_DIGIT_TABLE)


def has_keyword(text_lower: str, keyword: str) -> bool:
    """Latin keywords must stand alone (so 'age' does not match 'village'); Indic keywords match as substrings."""
    if keyword.isascii():
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text_lower) is not None
    return keyword in text_lower


def _first_match(text: str, table: List[Tuple[str, List[str]]]) -> Optional[str]:
    lower = (text or "").lower()
    for value, keywords in table:
        if any(has_keyword(lower, k) for k in keywords):
            return value
    return None


def tokens(text: str) -> List[str]:
    return [t for t in re.split(r"[\s,.!?।॥;:()\"'*_-]+", (text or "").lower()) if t]


# ---------------- amounts ----------------

_MULTIPLIERS = [
    (10000000.0, ["crores", "crore", "cr", "ಕೋಟಿ", "करोड़", "करोड", "कोटी", "కోట్ల", "కోటి"]),
    (100000.0, ["lakhs", "lakh", "lacs", "lac", "ಲಕ್ಷ", "लाख", "లక్ష"]),
    (1000.0, ["thousand", "k", "ಸಾವಿರ", "हज़ार", "हजार", "వేల", "వేలు", "వెయ్యి"]),
]

_NUMBER_WORDS = {
    # English
    "half": 0.5, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "fifty": 50,
    # Hindi / Marathi
    "एक": 1, "दो": 2, "दोन": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "पाच": 5, "छह": 6, "सहा": 6,
    "सात": 7, "आठ": 8, "नौ": 9, "नऊ": 9, "दस": 10, "दहा": 10, "डेढ़": 1.5, "डेढ": 1.5, "दीड": 1.5,
    "ढाई": 2.5, "अडीच": 2.5, "पचास": 50, "पन्नास": 50,
    # Kannada
    "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5, "ಆರು": 6, "ಏಳು": 7, "ಎಂಟು": 8,
    "ಒಂಬತ್ತು": 9, "ಹತ್ತು": 10, "ಒಂದೂವರೆ": 1.5, "ಎರಡೂವರೆ": 2.5, "ಐವತ್ತು": 50,
    # Telugu
    "ఒకటి": 1, "ఒక": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5, "ఆరు": 6, "ఏడు": 7,
    "ఎనిమిది": 8, "తొమ్మిది": 9, "పది": 10, "ఒకటిన్నర": 1.5, "రెండున్నర": 2.5, "యాభై": 50,
}

_ZERO_PHRASES = [
    "zero", "nothing", "none", "nil", "no money", "ಏನೂ ಇಲ್ಲ", "ಸೊನ್ನೆ", "कुछ नहीं", "कुछ भी नहीं", "शून्य",
    "ఏమీ లేదు", "సున్నా", "काही नाही", "काहीच नाही",
]

_MULT_ALT = "|".join(sorted((re.escape(w) for _, ws in _MULTIPLIERS for w in ws), key=len, reverse=True))
_NUM_RE = re.compile(rf"(\d+(?:,\d+)*(?:\.\d+)?)\s*({_MULT_ALT})?")
_WORD_ALT = "|".join(sorted((re.escape(w) for w in _NUMBER_WORDS), key=len, reverse=True))
_WORD_NUM_RE = re.compile(rf"({_WORD_ALT})\s*({_MULT_ALT})")


def _multiplier(word: Optional[str]) -> float:
    if not word:
        return 1.0
    for factor, words in _MULTIPLIERS:
        if word in words:
            return factor
    return 1.0


def _valid_unit(text: str, end: int, word: Optional[str]) -> bool:
    # Single-letter Latin units ('k', 'cr') must not be the start of a longer word ('kg', 'crop')
    if word and word.isascii() and len(word) <= 2:
        return not (end < len(text) and text[end].isalpha())
    return True


def parse_amount(text: str, allow_zero: bool = False) -> Optional[float]:
    """Reads the first rupee amount: '2 lakh', '₹1,20,000', '1.5 ಲಕ್ಷ', 'दो लाख', '50 thousand'."""
    t = to_ascii_digits(text).lower()
    candidates: List[Tuple[int, float]] = []
    for m in _NUM_RE.finditer(t):
        unit = m.group(2)
        if unit and not _valid_unit(t, m.end(2), unit):
            unit = None
        try:
            value = float(m.group(1).replace(",", "")) * _multiplier(unit)
        except ValueError:
            continue
        candidates.append((m.start(), value))
    for m in _WORD_NUM_RE.finditer(t):
        if _valid_unit(t, m.end(2), m.group(2)):
            candidates.append((m.start(), _NUMBER_WORDS[m.group(1)] * _multiplier(m.group(2))))
    candidates.sort()
    for _, value in candidates:
        if value > 0:
            return round(value, 2)
    if allow_zero and (any(v == 0 for _, v in candidates) or any(has_keyword(t, z) for z in _ZERO_PHRASES)):
        return 0.0
    return None


def parse_age(text: str) -> Optional[int]:
    t = to_ascii_digits(text)
    for m in re.finditer(r"(?<![\d.,])(\d{1,3})(?![\d.,])", t):
        value = int(m.group(1))
        if 10 <= value <= 100:
            return value
    return None


# ---------------- categorical answers ----------------

_GENDER = [
    ("transgender", ["transgender", "trans", "third gender", "ಮಂಗಳಮುಖಿ", "ತೃತೀಯ ಲಿಂಗ", "ट्रांसजेंडर", "किन्नर",
                     "तृतीय लिंग", "तृतीयपंथी", "ट्रान्सजेंडर", "ట్రాన్స్‌జెండర్", "ట్రాన్స్"]),
    ("female", ["female", "woman", "women", "lady", "girl", "ಮಹಿಳೆ", "ಹೆಣ್ಣು", "ಸ್ತ್ರೀ", "महिला", "औरत", "स्त्री",
                "लड़की", "बाई", "మహిళ", "స్త్రీ"]),
    ("male", ["male", "man", "men", "gents", "boy", "ಪುರುಷ", "ಗಂಡು", "पुरुष", "आदमी", "मर्द", "పురుష", "మగ"]),
]

_CATEGORY = [
    # ST before SC: "अनुसूचित जनजाति" contains "जाति"
    ("st", ["st", "s.t", "s.t.", "scheduled tribe", "tribe", "tribal", "ಪರಿಶಿಷ್ಟ ಪಂಗಡ", "ಎಸ್ಟಿ", "ಎಸ್.ಟಿ",
            "अनुसूचित जनजाति", "जनजाति", "आदिवासी", "एसटी", "एस.टी", "షెడ్యూల్డ్ తెగ", "ఎస్టీ", "గిరిజన",
            "अनुसूचित जमाती", "जमाती"]),
    ("sc", ["sc", "s.c", "s.c.", "scheduled caste", "dalit", "ಪರಿಶಿಷ್ಟ ಜಾತಿ", "ಎಸ್ಸಿ", "ಎಸ್.ಸಿ",
            "अनुसूचित जाति", "अनुसूचित जाती", "एससी", "एस.सी", "షెడ్యూల్డ్ కులం", "ఎస్సీ"]),
    ("obc", ["obc", "o.b.c", "bc", "backward", "ಹಿಂದುಳಿದ", "ಒಬಿಸಿ", "ಓಬಿಸಿ", "पिछड़ा", "पिछडा", "ओबीसी",
             "బీసీ", "ఓబీసీ", "వెనుకబడిన", "इतर मागास", "मागासवर्गीय", "मागास"]),
    ("minority", ["minority", "muslim", "christian", "sikh", "buddhist", "jain", "parsi", "ಅಲ್ಪಸಂಖ್ಯಾತ",
                  "ಮುಸ್ಲಿಂ", "ಕ್ರಿಶ್ಚಿಯನ್", "ಜೈನ", "अल्पसंख्यक", "अल्पसंख्याक", "मुस्लिम", "ईसाई", "सिख",
                  "बौद्ध", "जैन", "మైనారిటీ", "ముస్లిం", "క్రైస్తవ"]),
    ("general", ["general", "gen", "open", "oc", "unreserved", "gm", "ಸಾಮಾನ್ಯ", "ಜನರಲ್", "सामान्य", "जनरल",
                 "खुला", "खुल्ला", "सर्वसाधारण", "ओपन", "సాధారణ", "జనరల్", "ఓసీ", "ఓపెన్"]),
]

_AREA = [
    # "Nagar panchayat" is an urban local body even though it contains "panchayat"
    ("urban", ["nagar panchayat", "town panchayat", "ನಗರ ಪಂಚಾಯತ್", "ಪಟ್ಟಣ ಪಂಚಾಯತ್", "नगर पंचायत",
               "నగర పంచాయతీ"]),
    ("rural", ["rural", "village", "gram panchayat", "panchayat", "ಗ್ರಾಮ", "ಹಳ್ಳಿ", "ಪಂಚಾಯತ", "ಪಂಚಾಯಿತಿ",
               "गाँव", "गांव", "ग्राम", "पंचायत", "गाव", "खेडे", "గ్రామ", "పల్లె", "పంచాయతీ"]),
    ("urban", ["urban", "town", "city", "municipality", "municipal", "corporation", "ನಗರ", "ಪಟ್ಟಣ", "ಪುರಸಭೆ",
               "ಪಾಲಿಕೆ", "शहर", "नगर", "कस्बा", "नगरपालिका", "नगरपरिषद", "నగర", "పట్టణ", "మున్సిప"]),
]

_YES = {"yes", "y", "yeah", "yep", "ok", "okay", "correct", "right", "sure", "haan", "ha", "han", "ಹೌದು",
        "ಸರಿ", "हाँ", "हां", "हा", "जी", "सही", "ठीक", "అవును", "సరే", "సరి", "होय", "हो", "बरोबर"}
_NO = {"no", "n", "nope", "not", "wrong", "nahi", "ಇಲ್ಲ", "ಬೇಡ", "ತಪ್ಪು", "नहीं", "नही", "ना", "गलत",
       "లేదు", "కాదు", "తప్పు", "నో", "नाही", "नको", "चूक"}


def parse_gender(text: str) -> Optional[str]:
    return _first_match(text, _GENDER)


def parse_category(text: str) -> Optional[str]:
    return _first_match(text, _CATEGORY)


def parse_area(text: str) -> Optional[str]:
    return _first_match(text, _AREA)


def parse_yes_no(text: str) -> Optional[str]:
    words = tokens(text)
    if not words or len(words) > 8:
        return None
    if any(w in _NO for w in words):
        return "no"
    if any(w in _YES for w in words):
        return "yes"
    return None


def parse_bool(text: str) -> Optional[bool]:
    answer = parse_yes_no(text)
    return None if answer is None else answer == "yes"


_NAME_PREFIX = re.compile(
    r"^\s*(my name is|my name's|name is|i am|i'm|this is|name|ನನ್ನ ಹೆಸರು|ನನ್ನ ಹೆಸರ|मेरा नाम|नाम|"
    r"నా పేరు|పేరు|माझं नाव|माझे नाव|माझ नाव|नाव)\s*[:\-]?\s*",
    re.IGNORECASE,
)
_NAME_SUFFIX = re.compile(r"\s*(ಆಗಿದೆ|ಇದೆ|है|हैं|हूँ|हूं|आहे|అండి|ಅಂತ|అని)\s*[.!]*\s*$")


def parse_name(text: str) -> Optional[str]:
    name = _NAME_SUFFIX.sub("", _NAME_PREFIX.sub("", (text or "").strip()))
    name = name.strip(" .,!?:;\"'")
    if not name or re.search(r"\d", to_ascii_digits(name)):
        return None
    words = name.split()
    if not 1 <= len(words) <= 6 or len(name) > 80:
        return None
    return " ".join(w.capitalize() if w.isascii() else w for w in words)


# ---------------- Karnataka districts ----------------

KARNATAKA_DISTRICTS: Dict[str, List[str]] = {
    "Bagalkote": ["bagalkote", "bagalkot", "ಬಾಗಲಕೋಟೆ", "ಬಾಗಲಕೋಟ", "बागलकोट"],
    "Ballari": ["ballari", "bellary", "ಬಳ್ಳಾರಿ", "बल्लारी", "बेल्लारी", "బళ్లారి"],
    "Belagavi": ["belagavi", "belgaum", "belgavi", "ಬೆಳಗಾವಿ", "ಬೆಳಗಾಂ", "बेलगावी", "बेळगाव", "बेलगाम",
                 "बेलगांव", "బెళగావి", "బెల్గాం"],
    "Bengaluru Rural": ["bengaluru rural", "bangalore rural", "ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ"],
    "Bengaluru Urban": ["bengaluru urban", "bangalore urban", "bengaluru", "bangalore", "ಬೆಂಗಳೂರು ನಗರ",
                        "ಬೆಂಗಳೂರು", "बेंगलुरु", "बेंगलूरु", "बंगलौर", "बंगळूर", "బెంగళూరు"],
    "Bidar": ["bidar", "ಬೀದರ್", "ಬೀದರ", "बीदर", "బీదర్"],
    "Chamarajanagar": ["chamarajanagar", "chamarajanagara", "ಚಾಮರಾಜನಗರ", "चामराजनगर"],
    "Chikkaballapur": ["chikkaballapur", "chikkaballapura", "chickballapur", "ಚಿಕ್ಕಬಳ್ಳಾಪುರ", "चिक्कबल्लापुर"],
    "Chikkamagaluru": ["chikkamagaluru", "chikmagalur", "chikkamagalur", "ಚಿಕ್ಕಮಗಳೂರು", "चिकमंगलूर"],
    "Chitradurga": ["chitradurga", "ಚಿತ್ರದುರ್ಗ", "चित्रदुर्ग", "చిత్రదుర్గ"],
    "Dakshina Kannada": ["dakshina kannada", "south canara", "mangaluru", "mangalore", "ದಕ್ಷಿಣ ಕನ್ನಡ",
                         "ಮಂಗಳೂರು", "दक्षिण कन्नड", "मंगलुरु", "मंगलोर"],
    "Davanagere": ["davanagere", "davangere", "ದಾವಣಗೆರೆ", "दावणगेरे"],
    "Dharwad": ["dharwad", "dharwar", "hubballi", "hubli", "ಧಾರವಾಡ", "ಹುಬ್ಬಳ್ಳಿ", "धारवाड", "धारवाड़",
                "हुबली", "ధార్వాడ్"],
    "Gadag": ["gadag", "ಗದಗ", "गदग"],
    "Hassan": ["hassan", "ಹಾಸನ", "हासन"],
    "Haveri": ["haveri", "ಹಾವೇರಿ", "हावेरी"],
    "Kalaburagi": ["kalaburagi", "gulbarga", "ಕಲಬುರಗಿ", "ಗುಲ್ಬರ್ಗಾ", "कलबुर्गी", "गुलबर्गा", "కలబురగి", "గుల్బర్గా"],
    "Kodagu": ["kodagu", "coorg", "madikeri", "ಕೊಡಗು", "ಮಡಿಕೇರಿ", "कोडगु", "कूर्ग"],
    "Kolar": ["kolar", "ಕೋಲಾರ", "कोलार", "కోలార్"],
    "Koppal": ["koppal", "ಕೊಪ್ಪಳ", "कोप्पल"],
    "Mandya": ["mandya", "ಮಂಡ್ಯ", "मंड्या", "मांड्या"],
    "Mysuru": ["mysuru", "mysore", "ಮೈಸೂರು", "मैसूरु", "मैसूर", "म्हैसूर", "మైసూరు"],
    "Raichur": ["raichur", "ರಾಯಚೂರು", "रायचूर", "రాయచూర్"],
    "Ramanagara": ["ramanagara", "ramanagaram", "bengaluru south", "ರಾಮನಗರ", "ಬೆಂಗಳೂರು ದಕ್ಷಿಣ", "रामनगर"],
    "Shivamogga": ["shivamogga", "shimoga", "ಶಿವಮೊಗ್ಗ", "शिवमोग्गा", "शिमोगा"],
    "Tumakuru": ["tumakuru", "tumkur", "ತುಮಕೂರು", "तुमकुरु", "तुमकूर"],
    "Udupi": ["udupi", "ಉಡುಪಿ", "उडुपी"],
    "Uttara Kannada": ["uttara kannada", "north canara", "karwar", "ಉತ್ತರ ಕನ್ನಡ", "ಕಾರವಾರ", "उत्तर कन्नड",
                       "कारवार"],
    "Vijayanagara": ["vijayanagara", "hosapete", "hospet", "ವಿಜಯನಗರ", "ಹೊಸಪೇಟೆ", "होसपेट"],
    "Vijayapura": ["vijayapura", "bijapur", "ವಿಜಯಪುರ", "ಬಿಜಾಪುರ", "विजयपुरा", "बीजापुर", "విజయపుర"],
    "Yadgir": ["yadgir", "yadagiri", "ಯಾದಗಿರಿ", "यादगीर", "యాద్గిర్"],
}

# Places outside Karnataka that users in border areas commonly name
OUTSIDE_KARNATAKA = [
    "maharashtra", "महाराष्ट्र", "andhra", "ఆంధ్ర", "telangana", "తెలంగాణ", "tamil nadu", "kerala", "goa",
    "kolhapur", "कोल्हापूर", "कोल्हापुर", "pune", "पुणे", "nagpur", "नागपूर", "nashik", "नाशिक",
    "solapur", "सोलापूर", "sangli", "सांगली", "satara", "सातारा", "mumbai", "मुंबई",
    "guntur", "గుంటూరు", "vijayawada", "విజయవాడ", "visakhapatnam", "విశాఖపట్నం", "warangal", "వరంగల్",
    "kurnool", "కర్నూలు", "anantapur", "అనంతపురం", "hyderabad", "హైదరాబాద్", "chennai", "hosur",
]

_DISTRICT_ALIASES = sorted(
    ((alias, name) for name, aliases in KARNATAKA_DISTRICTS.items() for alias in aliases),
    key=lambda pair: len(pair[0]), reverse=True,
)


def normalize_district(text: str) -> Optional[str]:
    """Canonical Karnataka district named in the text (longest alias wins), else None."""
    lower = (text or "").lower()
    for alias, name in _DISTRICT_ALIASES:
        if has_keyword(lower, alias):
            return name
    return None


def outside_karnataka_place(text: str) -> Optional[str]:
    """The place outside Karnataka named in the text, if any."""
    lower = (text or "").lower()
    for place in OUTSIDE_KARNATAKA:
        if has_keyword(lower, place):
            return place.title() if place.isascii() else place
    return None


def mentions_outside_karnataka(text: str) -> bool:
    return outside_karnataka_place(text) is not None
