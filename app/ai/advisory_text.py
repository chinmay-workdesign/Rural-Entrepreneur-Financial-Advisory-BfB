"""
Advisory message built only from verified, computed results (no LLM wording, so no number can change).
Blocks: header, NABARD reference, corporation loan, PMEGP, MUDRA, documents, next step.
Translations still need review by native speakers.
"""
from typing import Any, Dict, List, Optional

from app.ai.pmegp_text import format_pmegp_block
from app.finance.formatting import format_inr

LANGS = ("english", "hindi", "kannada", "telugu", "marathi")


def _t(table: Dict[str, str], lang: str) -> str:
    return table.get(lang) or table["english"]


T: Dict[str, Dict[str, str]] = {
    "header": {
        "english": "🌾 *Loan & subsidy options: {trade} ({district})*\nProject cost: *{cost}* • Your own money: *{own}*",
        "hindi": "🌾 *ऋण और सब्सिडी विकल्प: {trade} ({district})*\nपरियोजना लागत: *{cost}* • आपका अपना पैसा: *{own}*",
        "kannada": "🌾 *ಸಾಲ ಮತ್ತು ಸಬ್ಸಿಡಿ ಆಯ್ಕೆಗಳು: {trade} ({district})*\nಯೋಜನಾ ವೆಚ್ಚ: *{cost}* • ನಿಮ್ಮ ಸ್ವಂತ ಹಣ: *{own}*",
        "telugu": "🌾 *రుణ మరియు సబ్సిడీ ఎంపికలు: {trade} ({district})*\nప్రాజెక్ట్ ఖర్చు: *{cost}* • మీ సొంత డబ్బు: *{own}*",
        "marathi": "🌾 *कर्ज व अनुदान पर्याय: {trade} ({district})*\nप्रकल्प खर्च: *{cost}* • आपले स्वतःचे पैसे: *{own}*",
    },
    "nabard": {
        "english": "📊 NABARD Karnataka 2026-27 unit cost for *{unit}*: *{amount}* (booklet page {page}). Banks use this as the reference cost.",
        "hindi": "📊 *{unit}* के लिए NABARD कर्नाटक 2026-27 इकाई लागत: *{amount}* (पुस्तिका पृष्ठ {page})। बैंक इसे संदर्भ लागत मानते हैं।",
        "kannada": "📊 *{unit}* ಗೆ NABARD ಕರ್ನಾಟಕ 2026-27 ಘಟಕ ವೆಚ್ಚ: *{amount}* (ಪುಸ್ತಿಕೆ ಪುಟ {page}). ಬ್ಯಾಂಕುಗಳು ಇದನ್ನು ಉಲ್ಲೇಖ ವೆಚ್ಚವಾಗಿ ಬಳಸುತ್ತವೆ.",
        "telugu": "📊 *{unit}* కోసం NABARD కర్ణాటక 2026-27 యూనిట్ ఖర్చు: *{amount}* (బుక్‌లెట్ పేజీ {page}). బ్యాంకులు దీన్ని సూచన ఖర్చుగా ఉపయోగిస్తాయి.",
        "marathi": "📊 *{unit}* साठी NABARD कर्नाटक 2026-27 युनिट खर्च: *{amount}* (पुस्तिका पान {page}). बँका हा संदर्भ खर्च मानतात.",
    },
    "corp_title": {
        "english": "🏛️ *SCHEME 1: {name}* ({agency})", "hindi": "🏛️ *योजना 1: {name}* ({agency})",
        "kannada": "🏛️ *ಯೋಜನೆ 1: {name}* ({agency})", "telugu": "🏛️ *పథకం 1: {name}* ({agency})",
        "marathi": "🏛️ *योजना १: {name}* ({agency})",
    },
    "corp_title_none": {
        "english": "🏛️ *SCHEME 1: Concessional corporation loan*", "hindi": "🏛️ *योजना 1: रियायती निगम ऋण*",
        "kannada": "🏛️ *ಯೋಜನೆ 1: ರಿಯಾಯಿತಿ ನಿಗಮ ಸಾಲ*", "telugu": "🏛️ *పథకం 1: రాయితీ కార్పొరేషన్ రుణం*",
        "marathi": "🏛️ *योजना १: सवलतीचे महामंडळ कर्ज*",
    },
    "loan": {
        "english": "• *Loan*: {loan} ({pct}% of project cost)", "hindi": "• *ऋण*: {loan} (परियोजना लागत का {pct}%)",
        "kannada": "• *ಸಾಲ*: {loan} (ಯೋಜನಾ ವೆಚ್ಚದ {pct}%)", "telugu": "• *రుణం*: {loan} (ప్రాజెక్ట్ ఖర్చులో {pct}%)",
        "marathi": "• *कर्ज*: {loan} (प्रकल्प खर्चाच्या {pct}%)",
    },
    "share": {
        "english": "• *Balance to be met by you / the agency*: {amount} ({pct}%)",
        "hindi": "• *शेष राशि (आप / एजेंसी द्वारा)*: {amount} ({pct}%)",
        "kannada": "• *ಉಳಿದ ಮೊತ್ತ (ನೀವು / ಸಂಸ್ಥೆ)*: {amount} ({pct}%)",
        "telugu": "• *మిగిలిన మొత్తం (మీరు / సంస్థ)*: {amount} ({pct}%)",
        "marathi": "• *उर्वरित रक्कम (आपण / संस्था)*: {amount} ({pct}%)",
    },
    "interest": {
        "english": "• *Interest*: {rate}% per year", "hindi": "• *ब्याज*: {rate}% प्रति वर्ष",
        "kannada": "• *ಬಡ್ಡಿ*: ವಾರ್ಷಿಕ {rate}%", "telugu": "• *వడ్డీ*: సంవత్సరానికి {rate}%",
        "marathi": "• *व्याज*: वार्षिक {rate}%",
    },
    "repay": {
        "english": "• *Repayment*: {quarters} quarterly instalments of {inst} (about {monthly} a month){morat}",
        "hindi": "• *चुकौती*: {inst} की {quarters} तिमाही किस्तें (लगभग {monthly} प्रति माह){morat}",
        "kannada": "• *ಮರುಪಾವತಿ*: {inst} ರ {quarters} ತ್ರೈಮಾಸಿಕ ಕಂತುಗಳು (ತಿಂಗಳಿಗೆ ಸುಮಾರು {monthly}){morat}",
        "telugu": "• *తిరిగి చెల్లింపు*: {inst} చొప్పున {quarters} త్రైమాసిక వాయిదాలు (నెలకు సుమారు {monthly}){morat}",
        "marathi": "• *परतफेड*: {inst} चे {quarters} तिमाही हप्ते (दरमहा सुमारे {monthly}){morat}",
    },
    "morat": {
        "english": ", after a {m}-month moratorium", "hindi": ", {m} महीने की छूट अवधि के बाद",
        "kannada": ", {m} ತಿಂಗಳ ವಿರಾಮದ ನಂತರ", "telugu": ", {m} నెలల మారటోరియం తర్వాత", "marathi": ", {m} महिन्यांच्या सवलतीनंतर",
    },
    "eligibility": {
        "english": "• *For*: {cat} applicants with family income up to {limit}",
        "hindi": "• *पात्रता*: {cat} आवेदक, पारिवारिक आय {limit} तक",
        "kannada": "• *ಅರ್ಹತೆ*: {cat} ಅರ್ಜಿದಾರರು, ಕುಟುಂಬ ಆದಾಯ {limit} ವರೆಗೆ",
        "telugu": "• *అర్హత*: {cat} దరఖాస్తుదారులు, కుటుంబ ఆదాయం {limit} వరకు",
        "marathi": "• *पात्रता*: {cat} अर्जदार, कुटुंब उत्पन्न {limit} पर्यंत",
    },
    "st_income": {
        "english": "• ⚠️ NSTFDC's site gives two income limits (₹3,00,000, or ₹98,000 rural / ₹1,20,000 urban); the corporation office will confirm.",
        "hindi": "• ⚠️ NSTFDC की वेबसाइट पर दो आय सीमाएँ हैं (₹3,00,000, या ग्रामीण ₹98,000 / शहरी ₹1,20,000); निगम कार्यालय पुष्टि करेगा।",
        "kannada": "• ⚠️ NSTFDC ಜಾಲತಾಣದಲ್ಲಿ ಎರಡು ಆದಾಯ ಮಿತಿಗಳಿವೆ (₹3,00,000, ಅಥವಾ ಗ್ರಾಮೀಣ ₹98,000 / ನಗರ ₹1,20,000); ನಿಗಮದ ಕಚೇರಿ ದೃಢೀಕರಿಸುತ್ತದೆ.",
        "telugu": "• ⚠️ NSTFDC వెబ్‌సైట్‌లో రెండు ఆదాయ పరిమితులు ఉన్నాయి (₹3,00,000, లేదా గ్రామీణ ₹98,000 / పట్టణ ₹1,20,000); కార్పొరేషన్ కార్యాలయం నిర్ధారిస్తుంది.",
        "marathi": "• ⚠️ NSTFDC च्या संकेतस्थळावर दोन उत्पन्न मर्यादा आहेत (₹3,00,000, किंवा ग्रामीण ₹98,000 / शहरी ₹1,20,000); महामंडळ कार्यालय खात्री करेल.",
    },
    "rebate": {
        "english": "• 1% yearly rebate for paying on time.", "hindi": "• समय पर भुगतान पर 1% वार्षिक छूट।",
        "kannada": "• ಸಮಯಕ್ಕೆ ಪಾವತಿಸಿದರೆ ವಾರ್ಷಿಕ 1% ರಿಯಾಯಿತಿ.", "telugu": "• సకాలంలో చెల్లిస్తే సంవత్సరానికి 1% రాయితీ.",
        "marathi": "• वेळेवर परतफेड केल्यास वार्षिक 1% सूट.",
    },
    "no_morat_note": {
        "english": "• Instalment assumes no moratorium; the corporation's site does not state one.",
        "hindi": "• किस्त बिना छूट अवधि मानकर गणना की गई है; निगम की वेबसाइट पर इसका उल्लेख नहीं है।",
        "kannada": "• ವಿರಾಮ ಅವಧಿ ಇಲ್ಲವೆಂದು ಕಂತು ಲೆಕ್ಕಿಸಲಾಗಿದೆ; ನಿಗಮದ ಜಾಲತಾಣದಲ್ಲಿ ಇದರ ಉಲ್ಲೇಖವಿಲ್ಲ.",
        "telugu": "• మారటోరియం లేదని భావించి వాయిదా లెక్కించబడింది; కార్పొరేషన్ వెబ్‌సైట్‌లో దీని ప్రస్తావన లేదు.",
        "marathi": "• सवलत कालावधी नाही असे गृहीत धरून हप्ता मोजला आहे; महामंडळाच्या संकेतस्थळावर त्याचा उल्लेख नाही.",
    },
    "apply_corp": {
        "english": "📍 *How to apply*: through the Karnataka State Channelising Agency (corporation office in {district}) for {agency}.",
        "hindi": "📍 *आवेदन*: {agency} के लिए कर्नाटक राज्य चैनलाइजिंग एजेंसी ({district} में निगम कार्यालय) के माध्यम से।",
        "kannada": "📍 *ಅರ್ಜಿ*: {agency} ಗಾಗಿ ಕರ್ನಾಟಕ ರಾಜ್ಯ ಚಾನೆಲೈಸಿಂಗ್ ಏಜೆನ್ಸಿ ({district} ನಲ್ಲಿರುವ ನಿಗಮ ಕಚೇರಿ) ಮೂಲಕ.",
        "telugu": "📍 *దరఖాస్తు*: {agency} కోసం కర్ణాటక స్టేట్ ఛానలైజింగ్ ఏజెన్సీ ({district} లోని కార్పొరేషన్ కార్యాలయం) ద్వారా.",
        "marathi": "📍 *अर्ज*: {agency} साठी कर्नाटक राज्य चॅनलायझिंग एजन्सी ({district} मधील महामंडळ कार्यालय) मार्फत.",
    },
    "income_above": {
        "english": "❌ *Not eligible*: {agency} lends only to families with income up to {limit}; you stated {income}.",
        "hindi": "❌ *पात्र नहीं*: {agency} केवल {limit} तक आय वाले परिवारों को ऋण देता है; आपने {income} बताया।",
        "kannada": "❌ *ಅರ್ಹರಲ್ಲ*: {agency} ಕೇವಲ {limit} ವರೆಗೆ ಆದಾಯವಿರುವ ಕುಟುಂಬಗಳಿಗೆ ಸಾಲ ನೀಡುತ್ತದೆ; ನೀವು {income} ಎಂದು ತಿಳಿಸಿದ್ದೀರಿ.",
        "telugu": "❌ *అర్హులు కాదు*: {agency} {limit} వరకు ఆదాయం ఉన్న కుటుంబాలకే రుణం ఇస్తుంది; మీరు {income} అని చెప్పారు.",
        "marathi": "❌ *पात्र नाही*: {agency} फक्त {limit} पर्यंत उत्पन्न असलेल्या कुटुंबांना कर्ज देते; आपण {income} सांगितले.",
    },
    "not_verified": {
        "english": "ℹ️ Minority loans (NMDFC) are not yet verified from an official source. Please ask the Karnataka Minorities Development Corporation office for current terms.",
        "hindi": "ℹ️ अल्पसंख्यक ऋण (NMDFC) की शर्तें अभी आधिकारिक स्रोत से सत्यापित नहीं हैं। कृपया कर्नाटक अल्पसंख्यक विकास निगम कार्यालय से वर्तमान शर्तें पूछें।",
        "kannada": "ℹ️ ಅಲ್ಪಸಂಖ್ಯಾತರ ಸಾಲ (NMDFC) ನಿಯಮಗಳನ್ನು ಇನ್ನೂ ಅಧಿಕೃತ ಮೂಲದಿಂದ ಪರಿಶೀಲಿಸಿಲ್ಲ. ದಯವಿಟ್ಟು ಕರ್ನಾಟಕ ಅಲ್ಪಸಂಖ್ಯಾತರ ಅಭಿವೃದ್ಧಿ ನಿಗಮದ ಕಚೇರಿಯಲ್ಲಿ ವಿಚಾರಿಸಿ.",
        "telugu": "ℹ️ మైనారిటీ రుణాల (NMDFC) నిబంధనలు ఇంకా అధికారిక మూలం నుండి ధృవీకరించబడలేదు. దయచేసి కర్ణాటక మైనారిటీల అభివృద్ధి కార్పొరేషన్ కార్యాలయంలో అడగండి.",
        "marathi": "ℹ️ अल्पसंख्याक कर्जाच्या (NMDFC) अटी अद्याप अधिकृत स्रोतातून पडताळलेल्या नाहीत. कृपया कर्नाटक अल्पसंख्याक विकास महामंडळ कार्यालयात विचारा.",
    },
    "general": {
        "english": "ℹ️ The concessional corporation loans are only for SC, ST, Backward Class and Minority applicants. PMEGP and MUDRA below are open to you.",
        "hindi": "ℹ️ रियायती निगम ऋण केवल SC, ST, पिछड़ा वर्ग और अल्पसंख्यक आवेदकों के लिए हैं। नीचे दिए गए PMEGP और MUDRA आपके लिए उपलब्ध हैं।",
        "kannada": "ℹ️ ರಿಯಾಯಿತಿ ನಿಗಮ ಸಾಲಗಳು SC, ST, ಹಿಂದುಳಿದ ವರ್ಗ ಮತ್ತು ಅಲ್ಪಸಂಖ್ಯಾತ ಅರ್ಜಿದಾರರಿಗೆ ಮಾತ್ರ. ಕೆಳಗಿನ PMEGP ಮತ್ತು MUDRA ನಿಮಗೆ ಲಭ್ಯ.",
        "telugu": "ℹ️ రాయితీ కార్పొరేషన్ రుణాలు SC, ST, వెనుకబడిన తరగతులు మరియు మైనారిటీ దరఖాస్తుదారులకు మాత్రమే. కింది PMEGP మరియు MUDRA మీకు అందుబాటులో ఉన్నాయి.",
        "marathi": "ℹ️ सवलतीची महामंडळ कर्जे फक्त SC, ST, मागासवर्ग व अल्पसंख्याक अर्जदारांसाठी आहेत. खालील PMEGP व MUDRA आपल्यासाठी खुले आहेत.",
    },
    "cost_ceiling": {
        "english": "❌ {agency} loans are for projects costing up to ₹50,00,000.",
        "hindi": "❌ {agency} ऋण ₹50,00,000 तक की परियोजनाओं के लिए है।",
        "kannada": "❌ {agency} ಸಾಲ ₹50,00,000 ವರೆಗಿನ ಯೋಜನೆಗಳಿಗೆ ಮಾತ್ರ.",
        "telugu": "❌ {agency} రుణాలు ₹50,00,000 వరకు ఉన్న ప్రాజెక్టులకు మాత్రమే.",
        "marathi": "❌ {agency} कर्ज ₹50,00,000 पर्यंतच्या प्रकल्पांसाठीच आहे.",
    },
    "mudra": {
        "english": ("🏦 *SCHEME 3: MUDRA (PMMY)*: collateral-free bank loan (CGFMU guarantee)\n"
                    "• For a loan up to your project cost ({cost}): {tiers}\n"
                    "• The interest rate and your own share are decided by the bank; the scheme does not fix them.\n"
                    "📍 Apply at any bank branch or on the Udyamimitra portal."),
        "hindi": ("🏦 *योजना 3: MUDRA (PMMY)*: बिना गारंटी बैंक ऋण (CGFMU गारंटी)\n"
                  "• आपकी परियोजना लागत ({cost}) तक के ऋण के लिए: {tiers}\n"
                  "• ब्याज दर और आपका अंशदान बैंक तय करता है; योजना इन्हें तय नहीं करती।\n"
                  "📍 किसी भी बैंक शाखा में या Udyamimitra पोर्टल पर आवेदन करें।"),
        "kannada": ("🏦 *ಯೋಜನೆ 3: MUDRA (PMMY)*: ಜಾಮೀನು ರಹಿತ ಬ್ಯಾಂಕ್ ಸಾಲ (CGFMU ಖಾತರಿ)\n"
                    "• ನಿಮ್ಮ ಯೋಜನಾ ವೆಚ್ಚ ({cost}) ವರೆಗಿನ ಸಾಲಕ್ಕೆ: {tiers}\n"
                    "• ಬಡ್ಡಿ ದರ ಮತ್ತು ನಿಮ್ಮ ಪಾಲನ್ನು ಬ್ಯಾಂಕ್ ನಿರ್ಧರಿಸುತ್ತದೆ; ಯೋಜನೆ ಅವನ್ನು ನಿಗದಿಪಡಿಸುವುದಿಲ್ಲ.\n"
                    "📍 ಯಾವುದೇ ಬ್ಯಾಂಕ್ ಶಾಖೆಯಲ್ಲಿ ಅಥವಾ Udyamimitra ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ."),
        "telugu": ("🏦 *పథకం 3: MUDRA (PMMY)*: హామీ లేని బ్యాంక్ రుణం (CGFMU గ్యారెంటీ)\n"
                   "• మీ ప్రాజెక్ట్ ఖర్చు ({cost}) వరకు రుణానికి: {tiers}\n"
                   "• వడ్డీ రేటు మరియు మీ వాటాను బ్యాంక్ నిర్ణయిస్తుంది; పథకం వాటిని నిర్ణయించదు.\n"
                   "📍 ఏ బ్యాంక్ శాఖలోనైనా లేదా Udyamimitra పోర్టల్‌లో దరఖాస్తు చేయండి."),
        "marathi": ("🏦 *योजना ३: MUDRA (PMMY)*: विनातारण बँक कर्ज (CGFMU हमी)\n"
                    "• आपल्या प्रकल्प खर्चापर्यंत ({cost}) कर्जासाठी: {tiers}\n"
                    "• व्याज दर व आपला वाटा बँक ठरवते; योजना ते ठरवत नाही.\n"
                    "📍 कोणत्याही बँक शाखेत किंवा Udyamimitra पोर्टलवर अर्ज करा."),
    },
    "tarun_plus": {
        "english": " (Tarun Plus only if you have repaid a Tarun loan)", "hindi": " (Tarun Plus केवल Tarun ऋण चुकाने के बाद)",
        "kannada": " (Tarun Plus ಕೇವಲ Tarun ಸಾಲ ತೀರಿಸಿದ ನಂತರ)", "telugu": " (Tarun Plus Tarun రుణం తీర్చిన తర్వాతే)",
        "marathi": " (Tarun Plus फक्त Tarun कर्ज फेडल्यानंतर)",
    },
    "documents": {
        "english": "📝 *Keep ready*: Aadhaar, caste and income certificates, rural area certificate (PMEGP), bank passbook, quotations, the DPR.",
        "hindi": "📝 *तैयार रखें*: आधार, जाति व आय प्रमाण पत्र, ग्रामीण क्षेत्र प्रमाण पत्र (PMEGP), बैंक पासबुक, कोटेशन, DPR।",
        "kannada": "📝 *ಸಿದ್ಧವಾಗಿಡಿ*: ಆಧಾರ್, ಜಾತಿ ಮತ್ತು ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ, ಗ್ರಾಮೀಣ ಪ್ರದೇಶ ಪ್ರಮಾಣಪತ್ರ (PMEGP), ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್, ದರಪಟ್ಟಿ, DPR.",
        "telugu": "📝 *సిద్ధంగా ఉంచుకోండి*: ఆధార్, కుల మరియు ఆదాయ ధృవీకరణ పత్రాలు, గ్రామీణ ప్రాంత పత్రం (PMEGP), బ్యాంక్ పాస్‌బుక్, కొటేషన్లు, DPR.",
        "marathi": "📝 *तयार ठेवा*: आधार, जात व उत्पन्न दाखला, ग्रामीण भाग प्रमाणपत्र (PMEGP), बँक पासबुक, कोटेशन्स, DPR.",
    },
    "next": {
        "english": "🚀 Reply *GENERATE DPR* to get your project report (PDF).",
        "hindi": "🚀 अपनी परियोजना रिपोर्ट (PDF) के लिए *GENERATE DPR* लिखें।",
        "kannada": "🚀 ನಿಮ್ಮ ಯೋಜನಾ ವರದಿ (PDF) ಪಡೆಯಲು *GENERATE DPR* ಎಂದು ಉತ್ತರಿಸಿ.",
        "telugu": "🚀 మీ ప్రాజెక్ట్ నివేదిక (PDF) కోసం *GENERATE DPR* అని రిప్లై ఇవ్వండి.",
        "marathi": "🚀 आपल्या प्रकल्प अहवालासाठी (PDF) *GENERATE DPR* लिहा.",
    },
}

CATEGORY_NAMES = {
    "sc": {"english": "SC", "hindi": "SC", "kannada": "SC", "telugu": "SC", "marathi": "SC"},
    "obc": {"english": "Backward Class (OBC)", "hindi": "पिछड़ा वर्ग (OBC)", "kannada": "ಹಿಂದುಳಿದ ವರ್ಗ (OBC)",
            "telugu": "వెనుకబడిన తరగతి (BC/OBC)", "marathi": "मागासवर्ग (OBC)"},
    "st": {"english": "ST", "hindi": "ST", "kannada": "ST", "telugu": "ST", "marathi": "ST"},
}
CORP_SOURCE = {
    "NSFDC": "_Source: nsfdc.nic.in (updated 23.09.2026)_",
    "NBCFDC": "_Source: NBCFDC Pattern of Finance, w.e.f. 01.04.2025_",
    "NSTFDC": "_Source: nstfdc.tribal.gov.in (Term Loan / AMSY pages)_",
}
MUDRA_TIER_LABELS = {
    "Shishu": "Shishu (≤ ₹50,000)", "Kishore": "Kishore (₹50,000 – ₹5,00,000)",
    "Tarun": "Tarun (₹5,00,000 – ₹10,00,000)", "Tarun Plus": "Tarun Plus (₹10,00,000 – ₹20,00,000)",
}


def _pct(value: float) -> str:
    return f"{value:g}"


def corporation_block(corp: Dict[str, Any], lang: str, district: str, income: Optional[float]) -> str:
    if not corp.get("available"):
        code = corp.get("reason_code")
        lines = [_t(T["corp_title_none"], lang)]
        if code == "income_above_limit":
            limit = corp.get("income_limit") or 0.0
            lines.append(_t(T["income_above"], lang).format(agency=corp.get("agency"), limit=format_inr(limit),
                                                             income=format_inr(income) if income is not None else "—"))
        elif code == "not_verified":
            lines.append(_t(T["not_verified"], lang))
        elif code == "cost_above_ceiling":
            lines.append(_t(T["cost_ceiling"], lang).format(agency=corp.get("agency")))
        else:
            lines.append(_t(T["general"], lang))
        return "\n".join(lines)

    agency = corp["agency"]
    lines = [
        _t(T["corp_title"], lang).format(name=corp["scheme_name"], agency=agency),
        _t(T["loan"], lang).format(loan=format_inr(corp["loan"]), pct=_pct(corp["loan_pct"])),
        _t(T["share"], lang).format(amount=format_inr(corp["margin"]), pct=_pct(corp["margin_pct"])),
        _t(T["interest"], lang).format(rate=_pct(corp["rate"])),
        _t(T["repay"], lang).format(
            quarters=corp["repayment_quarters"], inst=format_inr(corp["quarterly_instalment"]),
            monthly=format_inr(corp["quarterly_instalment"] / 3.0),
            morat=_t(T["morat"], lang).format(m=corp["morat"]) if corp.get("morat") else ""),
    ]
    category = corp.get("category")
    if category in ("sc", "obc"):
        lines.append(_t(T["eligibility"], lang).format(cat=_t(CATEGORY_NAMES[category], lang), limit=format_inr(corp["income_limit"])))
    if agency == "NSTFDC":
        lines.append(_t(T["st_income"], lang))
        lines.append(_t(T["no_morat_note"], lang))
    if agency == "NBCFDC":
        lines.append(_t(T["rebate"], lang))
    lines.append(_t(T["apply_corp"], lang).format(district=district, agency=agency))
    lines.append(CORP_SOURCE[agency])
    return "\n".join(lines)


def mudra_block(mudra: Dict[str, Any], cost: float, lang: str) -> str:
    tiers = " / ".join(MUDRA_TIER_LABELS[t] for t in mudra.get("possible_tiers") or [])
    if mudra.get("tarun_plus_condition"):
        tiers += _t(T["tarun_plus"], lang)
    return _t(T["mudra"], lang).format(cost=format_inr(cost), tiers=tiers) + "\n_Source: PIB, Ministry of Finance, 29.10.2024_"


def build_advisory(trade: str, district: str, cost: float, own_money: Optional[float], multi_schemes: Dict[str, Any],
                   lang: str, benchmark: Optional[Dict[str, Any]] = None) -> str:
    lang = lang if lang in LANGS else "english"
    divider = "━━━━━━━━━━━━━━━━━━━━━"
    parts: List[str] = [
        _t(T["header"], lang).format(trade=trade, district=district, cost=format_inr(cost),
                                    own=format_inr(own_money) if own_money is not None else "—"),
    ]
    # Only NABARD's own unit cost is quoted as a NABARD reference (other profiles are not government unit costs)
    if benchmark and benchmark.get("total_cost") and benchmark.get("source_id") == "NABARD_KA_UC_BOOKLET_2026_27":
        parts.append(_t(T["nabard"], lang).format(unit=benchmark.get("sub_activity") or benchmark.get("activity"),
                                                 amount=format_inr(benchmark["total_cost"]),
                                                 page=benchmark.get("source_page")))
    parts += [
        divider,
        corporation_block(multi_schemes["primary_sca"], lang, district,
                          (multi_schemes.get("profile") or {}).get("annual_family_income")),
        divider,
        format_pmegp_block(multi_schemes["pmegp"], lang),
        divider,
        mudra_block(multi_schemes["mudra"], cost, lang),
        divider,
        _t(T["documents"], lang),
        _t(T["next"], lang),
    ]
    return "\n\n".join(parts)
