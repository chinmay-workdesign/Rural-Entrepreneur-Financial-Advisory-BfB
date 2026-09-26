"""
PMEGP section of the advisory message, written from the computed PMEGP result only.
No figure is shown unless it was computed from the applicant's confirmed details.
Translations still need review by native speakers.
"""
from typing import Any, Dict, List

from app.finance.formatting import format_inr

_T: Dict[str, Dict[str, str]] = {
    "title": {"english": "🎁 *SCHEME 2: PMEGP (KVIC / DIC)*", "hindi": "🎁 *योजना 2: PMEGP (KVIC / DIC)*",
              "kannada": "🎁 *ಯೋಜನೆ 2: PMEGP (KVIC / DIC)*", "telugu": "🎁 *పథకం 2: PMEGP (KVIC / DIC)*",
              "marathi": "🎁 *योजना २: PMEGP (KVIC / DIC)*"},
    "special": {"english": "special category", "hindi": "विशेष श्रेणी", "kannada": "ವಿಶೇಷ ವರ್ಗ",
                "telugu": "ప్రత్యేక వర్గం", "marathi": "विशेष प्रवर्ग"},
    "general": {"english": "general category", "hindi": "सामान्य श्रेणी", "kannada": "ಸಾಮಾನ್ಯ ವರ್ಗ",
                "telugu": "సాధారణ వర్గం", "marathi": "सर्वसाधारण प्रवर्ग"},
    "rural": {"english": "rural area", "hindi": "ग्रामीण क्षेत्र", "kannada": "ಗ್ರಾಮೀಣ ಪ್ರದೇಶ",
              "telugu": "గ్రామీణ ప్రాంతం", "marathi": "ग्रामीण भाग"},
    "urban": {"english": "urban area", "hindi": "शहरी क्षेत्र", "kannada": "ನಗರ ಪ್ರದೇಶ",
              "telugu": "పట్టణ ప్రాంతం", "marathi": "शहरी भाग"},
    "subsidy": {"english": "Government subsidy", "hindi": "सरकारी सब्सिडी", "kannada": "ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ",
                "telugu": "ప్రభుత్వ సబ్సిడీ", "marathi": "सरकारी अनुदान"},
    "own": {"english": "Your own contribution", "hindi": "आपका अंशदान", "kannada": "ನಿಮ್ಮ ಸ್ವಂತ ಪಾಲು",
            "telugu": "మీ సొంత వాటా", "marathi": "आपला स्वतःचा वाटा"},
    "bank": {"english": "Bank loan", "hindi": "बैंक ऋण", "kannada": "ಬ್ಯಾಂಕ್ ಸಾಲ", "telugu": "బ్యాంక్ రుణం",
             "marathi": "बँक कर्ज"},
    "bank_note": {
        "english": "(the subsidy is kept in a 3-year deposit, then adjusted against this loan)",
        "hindi": "(सब्सिडी 3 साल जमा रहती है, फिर इस ऋण में समायोजित होती है)",
        "kannada": "(ಸಬ್ಸಿಡಿ 3 ವರ್ಷ ಠೇವಣಿಯಲ್ಲಿದ್ದು ನಂತರ ಈ ಸಾಲಕ್ಕೆ ಹೊಂದಿಸಲಾಗುತ್ತದೆ)",
        "telugu": "(సబ్సిడీ 3 సంవత్సరాలు డిపాజిట్‌లో ఉండి, తర్వాత ఈ రుణానికి సర్దుబాటు అవుతుంది)",
        "marathi": "(अनुदान 3 वर्षे ठेवीत राहते, नंतर या कर्जात समायोजित होते)"},
    "interest": {
        "english": "Interest: bank's normal rate; repayment in 3–7 years",
        "hindi": "ब्याज: बैंक की सामान्य दर; चुकौती 3–7 वर्ष में",
        "kannada": "ಬಡ್ಡಿ: ಬ್ಯಾಂಕಿನ ಸಾಮಾನ್ಯ ದರ; ಮರುಪಾವತಿ 3–7 ವರ್ಷಗಳಲ್ಲಿ",
        "telugu": "వడ్డీ: బ్యాంక్ సాధారణ రేటు; తిరిగి చెల్లింపు 3–7 సంవత్సరాలలో",
        "marathi": "व्याज: बँकेचा सामान्य दर; परतफेड 3–7 वर्षांत"},
    "conditions": {
        "english": "Conditions: new unit only; one person per family; Udyam registration needed",
        "hindi": "शर्तें: केवल नई इकाई; एक परिवार से एक व्यक्ति; उद्यम पंजीकरण ज़रूरी",
        "kannada": "ಷರತ್ತುಗಳು: ಹೊಸ ಘಟಕ ಮಾತ್ರ; ಒಂದು ಕುಟುಂಬಕ್ಕೆ ಒಬ್ಬರು; ಉದ್ಯಮ್ ನೋಂದಣಿ ಅಗತ್ಯ",
        "telugu": "షరతులు: కొత్త యూనిట్ మాత్రమే; కుటుంబానికి ఒక్కరు; ఉద్యమ్ నమోదు అవసరం",
        "marathi": "अटी: फक्त नवीन युनिट; एका कुटुंबातून एक व्यक्ती; उद्यम नोंदणी आवश्यक"},
    "apply": {
        "english": "📍 *How to apply*: KVIC PMEGP portal (www.kviconline.gov.in) — upload DPR, Aadhaar, category and rural-area certificates.",
        "hindi": "📍 *आवेदन कैसे करें*: KVIC PMEGP पोर्टल (www.kviconline.gov.in) — DPR, आधार, वर्ग व ग्रामीण क्षेत्र प्रमाणपत्र अपलोड करें।",
        "kannada": "📍 *ಅರ್ಜಿ ಹೇಗೆ*: KVIC PMEGP ಪೋರ್ಟಲ್ (www.kviconline.gov.in) — DPR, ಆಧಾರ್, ವರ್ಗ ಮತ್ತು ಗ್ರಾಮೀಣ ಪ್ರದೇಶ ಪ್ರಮಾಣಪತ್ರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "telugu": "📍 *దరఖాస్తు ఎలా*: KVIC PMEGP పోర్టల్ (www.kviconline.gov.in) — DPR, ఆధార్, వర్గ మరియు గ్రామీణ ప్రాంత ధృవీకరణ పత్రాలు అప్‌లోడ్ చేయండి.",
        "marathi": "📍 *अर्ज कसा करावा*: KVIC PMEGP पोर्टल (www.kviconline.gov.in) — DPR, आधार, प्रवर्ग व ग्रामीण भाग प्रमाणपत्र अपलोड करा."},
    "not_eligible": {"english": "❌ *Not eligible*", "hindi": "❌ *पात्र नहीं*", "kannada": "❌ *ಅರ್ಹರಲ್ಲ*",
                     "telugu": "❌ *అర్హులు కాదు*", "marathi": "❌ *पात्र नाही*"},
    "tbc": {"english": "to be confirmed by the DIC", "hindi": "DIC से पुष्टि करें", "kannada": "DIC ಯಿಂದ ದೃಢೀಕರಿಸಿ",
            "telugu": "DIC ద్వారా నిర్ధారించుకోండి", "marathi": "DIC कडून खात्री करा"},
    "missing": {
        "english": "The subsidy depends on your category and location; these details are missing, so no amount is shown.",
        "hindi": "सब्सिडी आपके वर्ग और क्षेत्र पर निर्भर है; ये विवरण नहीं हैं, इसलिए कोई राशि नहीं दिखाई गई।",
        "kannada": "ಸಬ್ಸಿಡಿ ನಿಮ್ಮ ವರ್ಗ ಮತ್ತು ಪ್ರದೇಶವನ್ನು ಅವಲಂಬಿಸಿದೆ; ಈ ವಿವರಗಳು ಇಲ್ಲದ ಕಾರಣ ಮೊತ್ತ ತೋರಿಸಿಲ್ಲ.",
        "telugu": "సబ్సిడీ మీ వర్గం మరియు ప్రాంతంపై ఆధారపడి ఉంటుంది; ఈ వివరాలు లేనందున మొత్తం చూపలేదు.",
        "marathi": "अनुदान आपला प्रवर्ग व भाग यावर अवलंबून आहे; ही माहिती नसल्याने रक्कम दाखवलेली नाही."},
}

_REASONS: Dict[str, Dict[str, str]] = {
    "age": {
        "english": "Applicant must be above 18 years (para 4.1(i)).",
        "hindi": "आवेदक की उम्र 18 वर्ष से अधिक होनी चाहिए (पैरा 4.1(i))।",
        "kannada": "ಅರ್ಜಿದಾರರು 18 ವರ್ಷ ಮೇಲ್ಪಟ್ಟಿರಬೇಕು (ಪ್ಯಾರಾ 4.1(i)).",
        "telugu": "దరఖాస్తుదారుడు 18 సంవత్సరాలు పైబడి ఉండాలి (పేరా 4.1(i)).",
        "marathi": "अर्जदाराचे वय 18 वर्षांपेक्षा जास्त असावे (परिच्छेद 4.1(i))."},
    "trading": {
        "english": "Plain trading shops (like kirana) are not eligible in Karnataka; only shops selling KVI/PMEGP products or backed by your own manufacturing/service unit (para 4.1(iv)).",
        "hindi": "कर्नाटक में साधारण व्यापार की दुकानें (जैसे किराना) पात्र नहीं हैं; केवल KVI/PMEGP उत्पाद बेचने वाली या अपनी निर्माण/सेवा इकाई से जुड़ी दुकानें (पैरा 4.1(iv))।",
        "kannada": "ಕರ್ನಾಟಕದಲ್ಲಿ ಸಾಮಾನ್ಯ ವ್ಯಾಪಾರ ಅಂಗಡಿಗಳು (ಕಿರಾಣಿಯಂತಹ) ಅರ್ಹವಲ್ಲ; KVI/PMEGP ಉತ್ಪನ್ನ ಮಾರುವ ಅಥವಾ ನಿಮ್ಮದೇ ಉತ್ಪಾದನಾ/ಸೇವಾ ಘಟಕದೊಂದಿಗಿನ ಅಂಗಡಿಗಳು ಮಾತ್ರ (ಪ್ಯಾರಾ 4.1(iv)).",
        "telugu": "కర్ణాటకలో సాధారణ వ్యాపార దుకాణాలు (కిరాణా వంటివి) అర్హం కాదు; KVI/PMEGP ఉత్పత్తులు అమ్మే లేదా మీ సొంత తయారీ/సేవా యూనిట్‌తో ఉన్న దుకాణాలు మాత్రమే (పేరా 4.1(iv)).",
        "marathi": "कर्नाटकात साधी व्यापारी दुकाने (किराणासारखी) पात्र नाहीत; फक्त KVI/PMEGP उत्पादने विकणारी किंवा स्वतःच्या उत्पादन/सेवा युनिटशी जोडलेली दुकाने (परिच्छेद 4.1(iv))."},
    "animal_husbandry": {
        "english": "Animal husbandry is excluded except dairy, poultry, fish farming and bee-keeping/sericulture (para 30(iv)).",
        "hindi": "पशुपालन शामिल नहीं है, सिवाय डेयरी, मुर्गी पालन, मछली पालन और मधुमक्खी/रेशम पालन के (पैरा 30(iv))।",
        "kannada": "ಹೈನು, ಕೋಳಿ, ಮೀನು ಸಾಕಣೆ ಮತ್ತು ಜೇನು/ರೇಷ್ಮೆ ಹೊರತುಪಡಿಸಿ ಪಶುಸಂಗೋಪನೆ ಅರ್ಹವಲ್ಲ (ಪ್ಯಾರಾ 30(iv)).",
        "telugu": "పాడి, కోళ్లు, చేపల పెంపకం, తేనెటీగ/పట్టు పెంపకం తప్ప పశుపోషణ అర్హం కాదు (పేరా 30(iv)).",
        "marathi": "दुग्ध, कुक्कुटपालन, मत्स्यपालन व मधमाशी/रेशीम सोडून पशुपालन पात्र नाही (परिच्छेद 30(iv))."},
    "education": {
        "english": "Projects above ₹10 lakh (manufacturing) or ₹5 lakh (business/service) need 8th standard pass (para 4.1(iii)).",
        "hindi": "₹10 लाख (निर्माण) या ₹5 लाख (व्यवसाय/सेवा) से अधिक की परियोजनाओं के लिए 8वीं पास ज़रूरी है (पैरा 4.1(iii))।",
        "kannada": "₹10 ಲಕ್ಷ (ಉತ್ಪಾದನೆ) ಅಥವಾ ₹5 ಲಕ್ಷ (ವ್ಯಾಪಾರ/ಸೇವೆ) ಮೀರಿದ ಯೋಜನೆಗಳಿಗೆ 8ನೇ ತರಗತಿ ಪಾಸ್ ಅಗತ್ಯ (ಪ್ಯಾರಾ 4.1(iii)).",
        "telugu": "₹10 లక్షలు (తయారీ) లేదా ₹5 లక్షలు (వ్యాపారం/సేవ) మించిన ప్రాజెక్టులకు 8వ తరగతి పాస్ అవసరం (పేరా 4.1(iii)).",
        "marathi": "₹10 लाख (उत्पादन) किंवा ₹5 लाख (व्यवसाय/सेवा) पेक्षा जास्त प्रकल्पांसाठी 8वी उत्तीर्ण आवश्यक (परिच्छेद 4.1(iii))."},
}

SOURCE_LINE = "_Source: PMEGP Revised Guidelines, Ministry of MSME (para 3.2, 4.1, 8.1)_"


def _t(key: str, lang: str) -> str:
    table = _T[key]
    return table.get(lang) or table["english"]


def _money(pct: float, amount, lang: str) -> str:
    value = format_inr(amount) if amount is not None else _t("tbc", lang)
    return f"{pct:g}% = {value}"


def format_pmegp_block(pmegp: Dict[str, Any], lang: str) -> str:
    lines: List[str] = []
    if pmegp.get("eligible") is False:
        lines.append(f"{_t('title', lang)}\n{_t('not_eligible', lang)}:")
        for code in pmegp.get("ineligible_codes") or []:
            lines.append(f"• {(_REASONS[code].get(lang) or _REASONS[code]['english'])}")
    elif pmegp.get("eligible") and pmegp.get("subsidy_pct") is not None:
        basis = _t(pmegp["category_basis"], lang)
        area = _t(pmegp["area_type"], lang)
        lines.append(f"{_t('title', lang)} — {basis}, {area}")
        lines.append(f"• *{_t('subsidy', lang)}*: {_money(pmegp['subsidy_pct'], pmegp.get('subsidy_amount'), lang)}")
        lines.append(f"• *{_t('own', lang)}*: {_money(pmegp['own_contribution_pct'], pmegp.get('own_contribution'), lang)}")
        lines.append(f"• *{_t('bank', lang)}*: {_money(pmegp['bank_loan_pct'], pmegp.get('bank_loan'), lang)} {_t('bank_note', lang)}")
        lines.append(f"• {_t('interest', lang)}")
        lines.append(f"• {_t('conditions', lang)}")
        lines.append(_t("apply", lang))
    else:
        lines.append(_t("title", lang))
        lines.append(_t("missing", lang))
    lines.append(SOURCE_LINE)
    return "\n".join(lines)
