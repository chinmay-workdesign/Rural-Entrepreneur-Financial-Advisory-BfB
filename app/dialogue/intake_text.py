"""
Intake questions and messages in the five supported languages.
Every question can be answered by typing or by a voice note, so options are given as words to say.
Translations still need review by native speakers.
"""
from typing import Dict

QUESTIONS: Dict[str, Dict[str, str]] = {
    "trade": {
        "english": "🏪 Which business do you want to start? (for example: dairy, poultry, tailoring, flour mill, kirana shop)",
        "hindi": "🏪 आप कौन सा व्यवसाय शुरू करना चाहते हैं? (जैसे: डेयरी, मुर्गी पालन, सिलाई, आटा चक्की, किराना दुकान)",
        "kannada": "🏪 ನೀವು ಯಾವ ವ್ಯಾಪಾರ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ? (ಉದಾ: ಹೈನುಗಾರಿಕೆ, ಕೋಳಿ ಸಾಕಣೆ, ಹೊಲಿಗೆ, ಹಿಟ್ಟಿನ ಗಿರಣಿ, ಕಿರಾಣಿ ಅಂಗಡಿ)",
        "telugu": "🏪 మీరు ఏ వ్యాపారం ప్రారంభించాలనుకుంటున్నారు? (ఉదా: పాడి, కోళ్ల పెంపకం, కుట్టు పని, పిండి మిల్లు, కిరాణా దుకాణం)",
        "marathi": "🏪 आपण कोणता व्यवसाय सुरू करू इच्छिता? (उदा: दुग्ध व्यवसाय, कुक्कुटपालन, शिलाई, पिठाची गिरणी, किराणा दुकान)",
    },
    "district": {
        "english": "📍 In which district of Karnataka will the business be set up?",
        "hindi": "📍 व्यवसाय कर्नाटक के किस जिले में लगेगा?",
        "kannada": "📍 ಈ ವ್ಯಾಪಾರವನ್ನು ಕರ್ನಾಟಕದ ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ ಪ್ರಾರಂಭಿಸುತ್ತೀರಿ?",
        "telugu": "📍 ఈ వ్యాపారాన్ని కర్ణాటకలోని ఏ జిల్లాలో ప్రారంభిస్తారు?",
        "marathi": "📍 हा व्यवसाय कर्नाटकातील कोणत्या जिल्ह्यात सुरू करणार आहात?",
    },
    "project_cost": {
        "english": "💰 What is the total cost of the project — machines, animals, shed, stock, everything together? (for example: 2 lakh)",
        "hindi": "💰 परियोजना की कुल लागत कितनी है — मशीन, पशु, शेड, माल सब मिलाकर? (जैसे: 2 लाख)",
        "kannada": "💰 ಯೋಜನೆಯ ಒಟ್ಟು ವೆಚ್ಚ ಎಷ್ಟು — ಯಂತ್ರ, ಜಾನುವಾರು, ಶೆಡ್, ಸರಕು ಎಲ್ಲಾ ಸೇರಿ? (ಉದಾ: 2 ಲಕ್ಷ)",
        "telugu": "💰 ప్రాజెక్ట్ మొత్తం ఖర్చు ఎంత — యంత్రాలు, పశువులు, షెడ్, సరుకు అన్నీ కలిపి? (ఉదా: 2 లక్షలు)",
        "marathi": "💰 प्रकल्पाचा एकूण खर्च किती — यंत्रे, जनावरे, शेड, माल सर्व मिळून? (उदा: 2 लाख)",
    },
    "full_name": {
        "english": "👤 What is your full name, as written on your Aadhaar card?",
        "hindi": "👤 आपका पूरा नाम क्या है, जैसा आधार कार्ड पर लिखा है?",
        "kannada": "👤 ಆಧಾರ್ ಕಾರ್ಡ್‌ನಲ್ಲಿರುವಂತೆ ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ಏನು?",
        "telugu": "👤 ఆధార్ కార్డులో ఉన్నట్లుగా మీ పూర్తి పేరు ఏమిటి?",
        "marathi": "👤 आधार कार्डवर लिहिल्याप्रमाणे आपले पूर्ण नाव काय आहे?",
    },
    "gender": {
        "english": "🙋 Are you a man, a woman, or transgender? (PMEGP gives a higher subsidy to women and transgender applicants.)",
        "hindi": "🙋 आप पुरुष हैं, महिला हैं या ट्रांसजेंडर? (PMEGP में महिलाओं और ट्रांसजेंडर आवेदकों को अधिक सब्सिडी मिलती है।)",
        "kannada": "🙋 ನೀವು ಪುರುಷರೇ, ಮಹಿಳೆಯೇ ಅಥವಾ ತೃತೀಯ ಲಿಂಗಿಯೇ? (PMEGP ಯಲ್ಲಿ ಮಹಿಳೆಯರು ಮತ್ತು ತೃತೀಯ ಲಿಂಗಿಗಳಿಗೆ ಹೆಚ್ಚು ಸಬ್ಸಿಡಿ ಸಿಗುತ್ತದೆ.)",
        "telugu": "🙋 మీరు పురుషుడా, మహిళా లేదా ట్రాన్స్‌జెండరా? (PMEGP లో మహిళలు, ట్రాన్స్‌జెండర్లకు ఎక్కువ సబ్సిడీ వస్తుంది.)",
        "marathi": "🙋 आपण पुरुष, महिला की ट्रान्सजेंडर आहात? (PMEGP मध्ये महिला व ट्रान्सजेंडर अर्जदारांना जास्त अनुदान मिळते.)",
    },
    "age": {
        "english": "🎂 How old are you? (PMEGP requires the applicant to be above 18.)",
        "hindi": "🎂 आपकी उम्र कितनी है? (PMEGP के लिए 18 वर्ष से अधिक होना आवश्यक है।)",
        "kannada": "🎂 ನಿಮ್ಮ ವಯಸ್ಸು ಎಷ್ಟು? (PMEGP ಗೆ 18 ವರ್ಷ ಮೇಲ್ಪಟ್ಟಿರಬೇಕು.)",
        "telugu": "🎂 మీ వయస్సు ఎంత? (PMEGP కి 18 సంవత్సరాలు పైబడి ఉండాలి.)",
        "marathi": "🎂 आपले वय किती आहे? (PMEGP साठी 18 वर्षांपेक्षा जास्त वय आवश्यक आहे.)",
    },
    "social_category": {
        "english": "🏷️ Which social category do you belong to: General, SC, ST, OBC or Minority? (Subsidy rates depend on it.)",
        "hindi": "🏷️ आप किस सामाजिक वर्ग से हैं: सामान्य, SC, ST, OBC या अल्पसंख्यक? (सब्सिडी की दर इसी पर निर्भर है।)",
        "kannada": "🏷️ ನೀವು ಯಾವ ಸಾಮಾಜಿಕ ವರ್ಗಕ್ಕೆ ಸೇರಿದವರು: ಸಾಮಾನ್ಯ, SC, ST, OBC (ಹಿಂದುಳಿದ ವರ್ಗ) ಅಥವಾ ಅಲ್ಪಸಂಖ್ಯಾತ? (ಸಬ್ಸಿಡಿ ದರ ಇದರ ಮೇಲೆ ಅವಲಂಬಿತ.)",
        "telugu": "🏷️ మీరు ఏ సామాజిక వర్గానికి చెందినవారు: జనరల్, SC, ST, BC/OBC లేదా మైనారిటీ? (సబ్సిడీ రేటు దీనిపై ఆధారపడి ఉంటుంది.)",
        "marathi": "🏷️ आपण कोणत्या सामाजिक प्रवर्गात आहात: खुला (सर्वसाधारण), SC, ST, OBC की अल्पसंख्याक? (अनुदानाचा दर यावर अवलंबून आहे.)",
    },
    "area_type": {
        "english": "🏘️ Will the business be in a village (under a Gram Panchayat) or in a town/city (under a Municipality)? Say 'village' or 'town'. (Subsidy rates differ.)",
        "hindi": "🏘️ व्यवसाय गाँव (ग्राम पंचायत) में होगा या शहर/कस्बे (नगरपालिका) में? 'गाँव' या 'शहर' बोलें। (सब्सिडी दर अलग है।)",
        "kannada": "🏘️ ವ್ಯಾಪಾರ ಹಳ್ಳಿಯಲ್ಲಿ (ಗ್ರಾಮ ಪಂಚಾಯತ್) ಇರುತ್ತದೆಯೇ ಅಥವಾ ಪಟ್ಟಣ/ನಗರದಲ್ಲಿ (ಪುರಸಭೆ/ನಗರಸಭೆ)? 'ಹಳ್ಳಿ' ಅಥವಾ 'ಪಟ್ಟಣ' ಎಂದು ಹೇಳಿ. (ಸಬ್ಸಿಡಿ ದರ ಬೇರೆ.)",
        "telugu": "🏘️ వ్యాపారం గ్రామంలో (గ్రామ పంచాయతీ) ఉంటుందా లేదా పట్టణం/నగరంలో (మున్సిపాలిటీ)? 'గ్రామం' లేదా 'పట్టణం' అని చెప్పండి. (సబ్సిడీ రేటు వేరు.)",
        "marathi": "🏘️ व्यवसाय गावात (ग्रामपंचायत) असेल की शहरात (नगरपालिका)? 'गाव' किंवा 'शहर' सांगा. (अनुदानाचा दर वेगळा आहे.)",
    },
    "annual_family_income": {
        "english": "💵 What is your family's total income in one year, from all sources? (for example: 1.5 lakh)",
        "hindi": "💵 सभी स्रोतों से आपके परिवार की सालाना कुल आय कितनी है? (जैसे: 1.5 लाख)",
        "kannada": "💵 ಎಲ್ಲಾ ಮೂಲಗಳಿಂದ ನಿಮ್ಮ ಕುಟುಂಬದ ವಾರ್ಷಿಕ ಒಟ್ಟು ಆದಾಯ ಎಷ್ಟು? (ಉದಾ: 1.5 ಲಕ್ಷ)",
        "telugu": "💵 అన్ని మార్గాల నుండి మీ కుటుంబ వార్షిక మొత్తం ఆదాయం ఎంత? (ఉదా: 1.5 లక్షలు)",
        "marathi": "💵 सर्व मार्गांनी आपल्या कुटुंबाचे वार्षिक एकूण उत्पन्न किती आहे? (उदा: 1.5 लाख)",
    },
    "available_capital": {
        "english": "🪙 How much of your own money can you put into the business? (Say 0 if none.)",
        "hindi": "🪙 आप अपना कितना पैसा व्यवसाय में लगा सकते हैं? (कुछ नहीं तो 0 बोलें।)",
        "kannada": "🪙 ವ್ಯಾಪಾರಕ್ಕೆ ನಿಮ್ಮ ಸ್ವಂತ ಹಣ ಎಷ್ಟು ಹಾಕಬಲ್ಲಿರಿ? (ಇಲ್ಲದಿದ್ದರೆ 0 ಎಂದು ಹೇಳಿ.)",
        "telugu": "🪙 వ్యాపారంలో మీ సొంత డబ్బు ఎంత పెట్టగలరు? (లేకపోతే 0 అని చెప్పండి.)",
        "marathi": "🪙 व्यवसायात आपले स्वतःचे किती पैसे गुंतवू शकता? (नसल्यास 0 सांगा.)",
    },
    "special_status": {
        "english": "🎖️ Are you an ex-serviceman or a person with a disability? (Yes or No — this can raise your PMEGP subsidy.)",
        "hindi": "🎖️ क्या आप भूतपूर्व सैनिक या दिव्यांग हैं? (हाँ या नहीं — इससे PMEGP सब्सिडी बढ़ सकती है।)",
        "kannada": "🎖️ ನೀವು ಮಾಜಿ ಸೈನಿಕರೇ ಅಥವಾ ಅಂಗವಿಕಲರೇ? (ಹೌದು ಅಥವಾ ಇಲ್ಲ — ಇದರಿಂದ PMEGP ಸಬ್ಸಿಡಿ ಹೆಚ್ಚಾಗಬಹುದು.)",
        "telugu": "🎖️ మీరు మాజీ సైనికులా లేదా దివ్యాంగులా? (అవును లేదా కాదు — దీనివల్ల PMEGP సబ్సిడీ పెరగవచ్చు.)",
        "marathi": "🎖️ आपण माजी सैनिक किंवा दिव्यांग आहात का? (होय किंवा नाही — यामुळे PMEGP अनुदान वाढू शकते.)",
    },
    "education_8th_pass": {
        "english": "📚 Have you passed 8th standard or higher? (Yes or No — PMEGP needs this for larger projects.)",
        "hindi": "📚 क्या आपने 8वीं कक्षा या उससे ऊपर पास की है? (हाँ या नहीं — बड़ी परियोजनाओं के लिए PMEGP में यह ज़रूरी है।)",
        "kannada": "📚 ನೀವು 8ನೇ ತರಗತಿ ಅಥವಾ ಅದಕ್ಕಿಂತ ಹೆಚ್ಚು ಪಾಸಾಗಿದ್ದೀರಾ? (ಹೌದು ಅಥವಾ ಇಲ್ಲ — ದೊಡ್ಡ ಯೋಜನೆಗಳಿಗೆ PMEGP ಯಲ್ಲಿ ಇದು ಅಗತ್ಯ.)",
        "telugu": "📚 మీరు 8వ తరగతి లేదా అంతకంటే ఎక్కువ పాసయ్యారా? (అవును లేదా కాదు — పెద్ద ప్రాజెక్టులకు PMEGP లో ఇది అవసరం.)",
        "marathi": "📚 आपण 8वी किंवा त्यापेक्षा जास्त शिक्षण पूर्ण केले आहे का? (होय किंवा नाही — मोठ्या प्रकल्पांसाठी PMEGP मध्ये हे आवश्यक आहे.)",
    },
}

LABELS: Dict[str, Dict[str, str]] = {
    "trade": {"english": "Business", "hindi": "व्यवसाय", "kannada": "ವ್ಯಾಪಾರ", "telugu": "వ్యాపారం", "marathi": "व्यवसाय"},
    "district": {"english": "District", "hindi": "जिला", "kannada": "ಜಿಲ್ಲೆ", "telugu": "జిల్లా", "marathi": "जिल्हा"},
    "project_cost": {"english": "Total project cost", "hindi": "कुल परियोजना लागत", "kannada": "ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚ", "telugu": "మొత్తం ప్రాజెక్ట్ ఖర్చు", "marathi": "एकूण प्रकल्प खर्च"},
    "full_name": {"english": "Name", "hindi": "नाम", "kannada": "ಹೆಸರು", "telugu": "పేరు", "marathi": "नाव"},
    "gender": {"english": "Gender", "hindi": "लिंग", "kannada": "ಲಿಂಗ", "telugu": "లింగం", "marathi": "लिंग"},
    "age": {"english": "Age", "hindi": "उम्र", "kannada": "ವಯಸ್ಸು", "telugu": "వయస్సు", "marathi": "वय"},
    "social_category": {"english": "Social category", "hindi": "सामाजिक वर्ग", "kannada": "ಸಾಮಾಜಿಕ ವರ್ಗ", "telugu": "సామాజిక వర్గం", "marathi": "सामाजिक प्रवर्ग"},
    "area_type": {"english": "Location", "hindi": "क्षेत्र", "kannada": "ಪ್ರದೇಶ", "telugu": "ప్రాంతం", "marathi": "क्षेत्र"},
    "annual_family_income": {"english": "Annual family income", "hindi": "परिवार की वार्षिक आय", "kannada": "ಕುಟುಂಬದ ವಾರ್ಷಿಕ ಆದಾಯ", "telugu": "కుటుంబ వార్షిక ఆదాయం", "marathi": "कुटुंबाचे वार्षिक उत्पन्न"},
    "available_capital": {"english": "Own money to invest", "hindi": "अपना निवेश", "kannada": "ಸ್ವಂತ ಹೂಡಿಕೆ", "telugu": "సొంత పెట్టుబడి", "marathi": "स्वतःची गुंतवणूक"},
    "special_status": {"english": "Ex-serviceman / disability", "hindi": "भूतपूर्व सैनिक / दिव्यांग", "kannada": "ಮಾಜಿ ಸೈನಿಕ / ಅಂಗವಿಕಲ", "telugu": "మాజీ సైనికుడు / దివ్యాంగ", "marathi": "माजी सैनिक / दिव्यांग"},
    "education_8th_pass": {"english": "8th standard pass", "hindi": "8वीं पास", "kannada": "8ನೇ ತರಗತಿ ಪಾಸ್", "telugu": "8వ తరగతి పాస్", "marathi": "8वी उत्तीर्ण"},
}

VALUE_LABELS: Dict[str, Dict[str, Dict[str, str]]] = {
    "gender": {
        "male": {"english": "Man", "hindi": "पुरुष", "kannada": "ಪುರುಷ", "telugu": "పురుషుడు", "marathi": "पुरुष"},
        "female": {"english": "Woman", "hindi": "महिला", "kannada": "ಮಹಿಳೆ", "telugu": "మహిళ", "marathi": "महिला"},
        "transgender": {"english": "Transgender", "hindi": "ट्रांसजेंडर", "kannada": "ತೃತೀಯ ಲಿಂಗಿ", "telugu": "ట్రాన్స్‌జెండర్", "marathi": "ट्रान्सजेंडर"},
    },
    "area_type": {
        "rural": {"english": "Village (Gram Panchayat)", "hindi": "गाँव (ग्राम पंचायत)", "kannada": "ಹಳ್ಳಿ (ಗ್ರಾಮ ಪಂಚಾಯತ್)", "telugu": "గ్రామం (పంచాయతీ)", "marathi": "गाव (ग्रामपंचायत)"},
        "urban": {"english": "Town / city (Municipality)", "hindi": "शहर (नगरपालिका)", "kannada": "ಪಟ್ಟಣ (ಪುರಸಭೆ)", "telugu": "పట్టణం (మున్సిపాలిటీ)", "marathi": "शहर (नगरपालिका)"},
    },
    "social_category": {
        "general": {"english": "General", "hindi": "सामान्य", "kannada": "ಸಾಮಾನ್ಯ", "telugu": "జనరల్", "marathi": "खुला"},
        "sc": {"english": "SC", "hindi": "SC", "kannada": "SC", "telugu": "SC", "marathi": "SC"},
        "st": {"english": "ST", "hindi": "ST", "kannada": "ST", "telugu": "ST", "marathi": "ST"},
        "obc": {"english": "OBC", "hindi": "OBC", "kannada": "OBC", "telugu": "BC/OBC", "marathi": "OBC"},
        "minority": {"english": "Minority", "hindi": "अल्पसंख्यक", "kannada": "ಅಲ್ಪಸಂಖ್ಯಾತ", "telugu": "మైనారిటీ", "marathi": "अल्पसंख्याक"},
    },
    "bool": {
        "yes": {"english": "Yes", "hindi": "हाँ", "kannada": "ಹೌದು", "telugu": "అవును", "marathi": "होय"},
        "no": {"english": "No", "hindi": "नहीं", "kannada": "ಇಲ್ಲ", "telugu": "కాదు", "marathi": "नाही"},
    },
}

# Words a user may say to name a detail they want to correct (checked in this order)
FIELD_KEYWORDS: Dict[str, list] = {
    "available_capital": ["own money", "own contribution", "savings", "invest", "ಸ್ವಂತ", "ಉಳಿತಾಯ", "ಹೂಡಿಕೆ",
                          "अपना पैसा", "बचत", "निवेश", "సొంత", "పొదుపు", "పెట్టుబడి", "स्वतःचे", "गुंतवणूक"],
    "annual_family_income": ["income", "salary", "earning", "ಆದಾಯ", "आय", "आमदनी", "कमाई", "ఆదాయం", "उत्पन्न"],
    "project_cost": ["project cost", "total cost", "cost", "budget", "ವೆಚ್ಚ", "ಬಜೆಟ್", "लागत", "बजट", "ఖర్చు",
                     "బడ్జెట్", "खर्च"],
    "full_name": ["name", "ಹೆಸರು", "नाम", "పేరు", "नाव"],
    "gender": ["gender", "sex", "ಲಿಂಗ", "लिंग", "లింగం"],
    "age": ["age", "years old", "ವಯಸ್ಸು", "उम्र", "आयु", "వయస్సు", "వయసు", "वय"],
    "social_category": ["category", "caste", "ಜಾತಿ", "ವರ್ಗ", "जाति", "वर्ग", "కులం", "వర్గం", "जात", "प्रवर्ग"],
    "education_8th_pass": ["education", "school", "8th", "standard", "ಶಿಕ್ಷಣ", "ತರಗತಿ", "शिक्षा", "कक्षा",
                           "విద్య", "తరగతి", "शिक्षण", "इयत्ता"],
    "special_status": ["ex-serviceman", "ex serviceman", "disability", "disabled", "ಮಾಜಿ ಸೈನಿಕ", "ಅಂಗವಿಕಲ",
                       "भूतपूर्व", "दिव्यांग", "विकलांग", "మాజీ సైనిక", "దివ్యాంగ", "माजी सैनिक"],
    "area_type": ["village", "town", "city", "area", "location", "rural", "urban", "ಹಳ್ಳಿ", "ಪಟ್ಟಣ", "ಪ್ರದೇಶ",
                  "गाँव", "गांव", "शहर", "क्षेत्र", "గ్రామం", "పట్టణం", "ప్రాంతం", "गाव"],
    "district": ["district", "ಜಿಲ್ಲೆ", "जिला", "జిల్లా", "जिल्हा"],
    "trade": ["business", "trade", "activity", "ವ್ಯಾಪಾರ", "ಉದ್ಯಮ", "व्यवसाय", "धंधा", "వ్యాపారం", "उद्योग"],
}

MESSAGES: Dict[str, Dict[str, str]] = {
    "confirm_header": {
        "english": "📋 *Please check your details:*",
        "hindi": "📋 *कृपया अपना विवरण जाँचें:*",
        "kannada": "📋 *ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ:*",
        "telugu": "📋 *దయచేసి మీ వివరాలు సరిచూసుకోండి:*",
        "marathi": "📋 *कृपया आपली माहिती तपासा:*",
    },
    "confirm_footer": {
        "english": "✅ If everything is correct, say *YES*.\n✏️ If something is wrong, tell me what to change (for example: 'age 35').",
        "hindi": "✅ सब सही है तो *हाँ* बोलें।\n✏️ कुछ गलत है तो बताएं क्या बदलना है (जैसे: 'उम्र 35')।",
        "kannada": "✅ ಎಲ್ಲವೂ ಸರಿಯಿದ್ದರೆ *ಹೌದು* ಎಂದು ಹೇಳಿ.\n✏️ ಏನಾದರೂ ತಪ್ಪಿದ್ದರೆ ಏನನ್ನು ಬದಲಿಸಬೇಕು ಎಂದು ತಿಳಿಸಿ (ಉದಾ: 'ವಯಸ್ಸು 35').",
        "telugu": "✅ అన్నీ సరిగ్గా ఉంటే *అవును* అని చెప్పండి.\n✏️ ఏదైనా తప్పు ఉంటే ఏమి మార్చాలో చెప్పండి (ఉదా: 'వయస్సు 35').",
        "marathi": "✅ सर्व बरोबर असल्यास *होय* सांगा.\n✏️ काही चुकीचे असल्यास काय बदलायचे ते सांगा (उदा: 'वय 35').",
    },
    "which_field": {
        "english": "✏️ Which detail should I change? Say its name, for example: *age*, *income* or *district*.",
        "hindi": "✏️ कौन सा विवरण बदलना है? उसका नाम बोलें, जैसे: *उम्र*, *आय* या *जिला*।",
        "kannada": "✏️ ಯಾವ ವಿವರ ಬದಲಿಸಬೇಕು? ಅದರ ಹೆಸರು ಹೇಳಿ, ಉದಾ: *ವಯಸ್ಸು*, *ಆದಾಯ* ಅಥವಾ *ಜಿಲ್ಲೆ*.",
        "telugu": "✏️ ఏ వివరం మార్చాలి? దాని పేరు చెప్పండి, ఉదా: *వయస్సు*, *ఆదాయం* లేదా *జిల్లా*.",
        "marathi": "✏️ कोणती माहिती बदलायची? तिचे नाव सांगा, उदा: *वय*, *उत्पन्न* किंवा *जिल्हा*.",
    },
    "not_understood": {
        "english": "🤔 Sorry, I didn't catch that.",
        "hindi": "🤔 क्षमा करें, मैं समझ नहीं पाया।",
        "kannada": "🤔 ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ.",
        "telugu": "🤔 క్షమించండి, నాకు అర్థం కాలేదు.",
        "marathi": "🤔 क्षमस्व, मला समजले नाही.",
    },
    "out_of_coverage": {
        "english": "📍 Sorry — right now I can only advise for businesses in *Karnataka*, because the official NABARD cost data I use is for Karnataka. {place} is outside Karnataka. Please tell me a Karnataka district.",
        "hindi": "📍 क्षमा करें — अभी मैं केवल *कर्नाटक* के व्यवसायों के लिए सलाह दे सकता हूँ, क्योंकि मेरे पास NABARD का आधिकारिक लागत डेटा कर्नाटक का है। {place} कर्नाटक से बाहर है। कृपया कर्नाटक का कोई जिला बताएं।",
        "kannada": "📍 ಕ್ಷಮಿಸಿ — ಸದ್ಯಕ್ಕೆ ನಾನು *ಕರ್ನಾಟಕದ* ವ್ಯಾಪಾರಗಳಿಗೆ ಮಾತ್ರ ಸಲಹೆ ನೀಡಬಲ್ಲೆ, ಏಕೆಂದರೆ ನನ್ನ ಬಳಿಯಿರುವ NABARD ಅಧಿಕೃತ ವೆಚ್ಚ ಮಾಹಿತಿ ಕರ್ನಾಟಕದ್ದು. {place} ಕರ್ನಾಟಕದ ಹೊರಗಿದೆ. ದಯವಿಟ್ಟು ಕರ್ನಾಟಕದ ಜಿಲ್ಲೆಯನ್ನು ತಿಳಿಸಿ.",
        "telugu": "📍 క్షమించండి — ప్రస్తుతం నేను *కర్ణాటక*లోని వ్యాపారాలకు మాత్రమే సలహా ఇవ్వగలను, ఎందుకంటే నా దగ్గర ఉన్న NABARD అధికారిక ఖర్చు సమాచారం కర్ణాటకది. {place} కర్ణాటక బయట ఉంది. దయచేసి కర్ణాటకలోని జిల్లా చెప్పండి.",
        "marathi": "📍 क्षमस्व — सध्या मी फक्त *कर्नाटकातील* व्यवसायांसाठी सल्ला देऊ शकतो, कारण माझ्याकडील NABARD चा अधिकृत खर्च डेटा कर्नाटकचा आहे. {place} कर्नाटकाबाहेर आहे. कृपया कर्नाटकातील जिल्हा सांगा.",
    },
    "district_unrecognised": {
        "english": "📍 I couldn't match '{place}' to a Karnataka district. Please say the district name (for example: Belagavi, Dharwad, Mysuru).",
        "hindi": "📍 '{place}' को मैं कर्नाटक के किसी जिले से नहीं मिला पाया। कृपया जिले का नाम बताएं (जैसे: बेलगावी, धारवाड़, मैसूरु)।",
        "kannada": "📍 '{place}' ಅನ್ನು ಕರ್ನಾಟಕದ ಯಾವುದೇ ಜಿಲ್ಲೆಯೊಂದಿಗೆ ಹೊಂದಿಸಲು ಆಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಜಿಲ್ಲೆಯ ಹೆಸರು ಹೇಳಿ (ಉದಾ: ಬೆಳಗಾವಿ, ಧಾರವಾಡ, ಮೈಸೂರು).",
        "telugu": "📍 '{place}' ని కర్ణాటకలోని ఏ జిల్లాతోనూ సరిపోల్చలేకపోయాను. దయచేసి జిల్లా పేరు చెప్పండి (ఉదా: బెళగావి, ధార్వాడ్, మైసూరు).",
        "marathi": "📍 '{place}' हे कर्नाटकातील कोणत्याही जिल्ह्याशी जुळले नाही. कृपया जिल्ह्याचे नाव सांगा (उदा: बेळगाव, धारवाड, म्हैसूर).",
    },
    "invalid_cost": {
        "english": "⚠️ I can only work with a project cost between ₹5,000 and ₹50,00,000.",
        "hindi": "⚠️ मैं केवल ₹5,000 से ₹50,00,000 तक की परियोजना लागत पर काम कर सकता हूँ।",
        "kannada": "⚠️ ನಾನು ₹5,000 ರಿಂದ ₹50,00,000 ವರೆಗಿನ ಯೋಜನಾ ವೆಚ್ಚಕ್ಕೆ ಮಾತ್ರ ಸಲಹೆ ನೀಡಬಲ್ಲೆ.",
        "telugu": "⚠️ నేను ₹5,000 నుండి ₹50,00,000 వరకు ఉన్న ప్రాజెక్ట్ ఖర్చుకు మాత్రమే సలహా ఇవ్వగలను.",
        "marathi": "⚠️ मी फक्त ₹5,000 ते ₹50,00,000 पर्यंतच्या प्रकल्प खर्चासाठी सल्ला देऊ शकतो.",
    },
}


def text_for(table: Dict[str, str], lang: str) -> str:
    return table.get(lang) or table["english"]
