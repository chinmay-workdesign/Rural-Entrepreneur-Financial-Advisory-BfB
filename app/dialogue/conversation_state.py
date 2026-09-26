import re
import copy
import logging
from sqlalchemy.orm.attributes import flag_modified
from typing import Dict, Any, Optional
from app.db.session import SessionLocal
from app.db import crud
from app.whatsapp.client import (
    send_whatsapp_text,
    send_whatsapp_document,
    send_whatsapp_voice,
    send_whatsapp_buttons,
    download_media_bytes as download_whatsapp_media,
)
from app.telegram.client import (
    send_telegram_text,
    send_telegram_document,
    send_telegram_voice,
    download_telegram_file,
)
from app.voice.voice_service import transcribe_audio, synthesize_speech
from app.ai.extraction import extract_entrepreneur_details, generate_advisory_message
from app.dialogue import intake
from app.finance.benchmarks import get_trade_benchmark
from app.finance.calculator import calculate_financial_structure, validate_project_cost
from app.dpr.generator import generate_dpr_pdf
from app.storage import save_dpr_pdf, upload_dpr_pdf

logger = logging.getLogger("conversation_state")

GREETING_MSG_KN = "ನಮಸ್ಕಾರ! ಗ್ರಾಮೀಣ ಕಿರು-ಉದ್ಯಮ ಸಲಹಾ ಕೇಂದ್ರಕ್ಕೆ ಸ್ವಾಗತ. ನೀವು ಯಾವ ಉದ್ಯಮವನ್ನು (ಉದಾ. ಕಿರಾಣಿ ಅಂಗಡಿ, ಹೈನುಗಾರಿಕೆ, ಹೊಲಿಗೆ) ಕರ್ನಾಟಕದ ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ, ಮತ್ತು ಯೋಜನೆಯ ಒಟ್ಟು ವೆಚ್ಚ ಎಷ್ಟು? ನೀವು ಟೈಪ್ ಮಾಡಬಹುದು ಅಥವಾ ಧ್ವನಿ ಸಂದೇಶ ಕಳುಹಿಸಬಹುದು."
GREETING_MSG_HI = "नमस्ते! ग्रामीण सूक्ष्म उद्यम सलाहकार केंद्र में आपका स्वागत है। आप कौन सा व्यवसाय (जैसे किराना दुकान, डेयरी, सिलाई) कर्नाटक के किस जिले में शुरू करना चाहते हैं, और परियोजना की कुल लागत कितनी है? आप टाइप कर सकते हैं या वॉइस नोट भेज सकते हैं।"
GREETING_MSG_TE = "నమస్కారం! గ్రామీణ సూక్ష్మ-వ్యాపార సలహా కేంద్రానికి స్వాగతం. మీరు ఏ వ్యాపారాన్ని (ఉదా. కిరాణా దుకాణం, పాడి పరిశ్రమ/ఆవులు, కుట్టు పని, కోళ్ల పెంపకం) కర్ణాటకలోని ఏ జిల్లాలో ప్రారంభించాలనుకుంటున్నారు, ప్రాజెక్ట్ మొత్తం ఖర్చు ఎంత? మీరు టైప్ చేయవచ్చు లేదా వాయిస్ నోట్ పంపవచ్చు."
GREETING_MSG_MR = "नमस्कार! ग्रामीण सूक्ष्म-उद्योग सल्ला केंद्रात आपले स्वागत आहे. आपण कोणता व्यवसाय (उदा. किराणा दुकान, दुग्ध व्यवसाय/गाय, शिलाई काम, कुक्कुटपालन) कर्नाटकातील कोणत्या जिल्ह्यात सुरू करू इच्छिता, आणि प्रकल्पाचा एकूण खर्च किती आहे? आपण टाइप करू शकता किंवा व्हॉइस नोट पाठवू शकता."
GREETING_MSG_EN = "Namaste! Welcome to the Rural Micro-Enterprise AI Advisory. Which business (e.g. Kirana stall, Dairy cow, Tailoring) do you want to start, in which district of Karnataka, and what is the total project cost? You can type or send a voice note."

# Appended deterministically (never via LLM) when a trade has no official benchmark.
NO_BENCHMARK_NOTICE = {
    "english": (
        "⚠️ *Note*: There is no official government / NABARD cost benchmark for this business yet. "
        "The loan and EMI above are calculated from the budget you gave. A DSCR (repayment capacity) "
        "figure is not shown because there is no verified data to base it on. Please get your costs "
        "checked at your bank or DIC office."
    ),
    "hindi": (
        "⚠️ *ध्यान दें*: इस व्यवसाय के लिए अभी कोई आधिकारिक सरकारी / NABARD लागत मानक उपलब्ध नहीं है। "
        "ऊपर दिया गया ऋण और EMI आपके बताए गए बजट के आधार पर गणना किया गया है। सत्यापित आंकड़े न होने के "
        "कारण DSCR (ऋण चुकाने की क्षमता) नहीं दिखाया गया है। कृपया अपनी लागत बैंक या DIC कार्यालय से जांच करवाएं।"
    ),
    "kannada": (
        "⚠️ *ಗಮನಿಸಿ*: ಈ ವ್ಯವಹಾರಕ್ಕೆ ಇನ್ನೂ ಯಾವುದೇ ಅಧಿಕೃತ ಸರ್ಕಾರಿ / NABARD ವೆಚ್ಚದ ಮಾನದಂಡ ಲಭ್ಯವಿಲ್ಲ. "
        "ಮೇಲಿನ ಸಾಲ ಮತ್ತು EMI ಅನ್ನು ನೀವು ನೀಡಿದ ಬಜೆಟ್ ಆಧಾರದ ಮೇಲೆ ಲೆಕ್ಕ ಹಾಕಲಾಗಿದೆ. ಪರಿಶೀಲಿತ ಮಾಹಿತಿ ಇಲ್ಲದ "
        "ಕಾರಣ DSCR (ಸಾಲ ಮರುಪಾವತಿ ಸಾಮರ್ಥ್ಯ) ತೋರಿಸಲಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ವೆಚ್ಚವನ್ನು ಬ್ಯಾಂಕ್ ಅಥವಾ DIC ಕಚೇರಿಯಲ್ಲಿ ಪರಿಶೀಲಿಸಿಕೊಳ್ಳಿ."
    ),
    "telugu": (
        "⚠️ *గమనిక*: ఈ వ్యాపారానికి ఇంకా అధికారిక ప్రభుత్వ / NABARD వ్యయ ప్రమాణం అందుబాటులో లేదు. "
        "పైన ఉన్న రుణం మరియు EMI మీరు చెప్పిన బడ్జెట్ ఆధారంగా లెక్కించబడ్డాయి. ధృవీకరించిన సమాచారం లేనందున "
        "DSCR (రుణ చెల్లింపు సామర్థ్యం) చూపబడలేదు. దయచేసి మీ ఖర్చులను బ్యాంక్ లేదా DIC కార్యాలయంలో తనిఖీ చేయించుకోండి."
    ),
    "marathi": (
        "⚠️ *सूचना*: या व्यवसायासाठी अद्याप कोणताही अधिकृत सरकारी / NABARD खर्च मानक उपलब्ध नाही. "
        "वरील कर्ज आणि EMI तुम्ही सांगितलेल्या बजेटवरून मोजले आहेत. सत्यापित माहिती नसल्यामुळे DSCR "
        "(कर्ज फेडण्याची क्षमता) दाखवलेला नाही. कृपया तुमचा खर्च बँक किंवा DIC कार्यालयाकडून तपासून घ्या."
    ),
}

NO_BENCHMARK_LLM_CONTEXT = (
    "No official government / NABARD cost benchmark exists for this trade. "
    "Do not cite, estimate or invent any benchmark, unit cost or DSCR figure."
)


def _resolve_trade_benchmark(trade: str, district: str, cashflows: Dict[str, Any]) -> Dict[str, Any]:
    """
    Look up the trade benchmark and apply it to the cashflows.
    Without an official benchmark the DSCR is left out (None) rather than defaulted.
    """
    benchmark = get_trade_benchmark(trade, district)
    available = benchmark.get("status") != "DATA_NOT_AVAILABLE"
    if available:
        if benchmark.get("dscr"):
            cashflows["dscr"] = float(benchmark["dscr"])
        summary = benchmark.get("summary", f"Grounded in standard rural lending norms in {district}.")
    else:
        cashflows["dscr"] = None
        cashflows["is_bankable"] = None
        summary = NO_BENCHMARK_LLM_CONTEXT
    return {"available": available, "summary": summary}


LANGUAGE_PROMPT_MSG = (
    "🙏 *Welcome to Rural Micro-Enterprise AI Advisory* / *ಗ್ರಾಮೀಣ ಕಿರು-ಉದ್ಯಮ ಸಲಹಾ ಕೇಂದ್ರಕ್ಕೆ ಸ್ವಾಗತ*\n\n"
    "ದಯವಿಟ್ಟು ನೀವು ಮುಂದುವರಿಯಲು ಬಯಸುವ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ / Please select the language you want to proceed in:\n\n"
    "1️⃣ English\n"
    "2️⃣ हिंदी (Hindi)\n"
    "3️⃣ ಕನ್ನಡ (Kannada)\n"
    "4️⃣ తెలుగు (Telugu)\n"
    "5️⃣ मराठी (Marathi)\n\n"
    "👉 _Tap a button below or reply with 1, 2, 3, 4, 5 or your language name._"
)

LANGUAGE_KEYBOARD = {
    "keyboard": [
        [{"text": "1. English"}, {"text": "2. हिंदी (Hindi)"}],
        [{"text": "3. ಕನ್ನಡ (Kannada)"}],
        [{"text": "4. తెలుగు (Telugu)"}, {"text": "5. मराठी (Marathi)"}]
    ],
    "resize_keyboard": True,
    "one_time_keyboard": True
}

# WhatsApp (Evolution API) buttons; a tap returns the id, e.g. "lang_3"
LANGUAGE_BUTTONS = [
    {"displayText": "1. English", "id": "lang_1"},
    {"displayText": "2. हिन्दी (Hindi)", "id": "lang_2"},
    {"displayText": "3. ಕನ್ನಡ (Kannada)", "id": "lang_3"},
    {"displayText": "4. తెలుగు (Telugu)", "id": "lang_4"},
    {"displayText": "5. मराठी (Marathi)", "id": "lang_5"},
]
_LANGUAGE_BUTTON_IDS = {"lang_1": "english", "lang_2": "hindi", "lang_3": "kannada", "lang_4": "telugu", "lang_5": "marathi"}

LANGUAGE_CHOICES = {
    "1": "english",
    "1.": "english",
    "1. english": "english",
    "english": "english",

    "2": "hindi",
    "2.": "hindi",
    "2. हिंदी": "hindi",
    "2. हिंदी (hindi)": "hindi",
    "hindi": "hindi",
    "हिंदी": "hindi",
    "हिन्दी": "hindi",

    "3": "kannada",
    "3.": "kannada",
    "3. ಕನ್ನಡ": "kannada",
    "3. ಕನ್ನಡ (kannada)": "kannada",
    "kannada": "kannada",
    "ಕನ್ನಡ": "kannada",

    "4": "telugu",
    "4.": "telugu",
    "4. తెలుగు": "telugu",
    "4. తెలుగు (telugu)": "telugu",
    "telugu": "telugu",
    "telgu": "telugu",
    "తెలుగు": "telugu",

    "5": "marathi",
    "5.": "marathi",
    "5. मराठी": "marathi",
    "5. मराठी (marathi)": "marathi",
    "marathi": "marathi",
    "मराठी": "marathi",
}

LANGUAGE_CONFIRMATIONS = {
    "english": "Language selected: *English* ✅\n\n" + GREETING_MSG_EN,
    "hindi": "भाषा चुनी गई: *हिंदी* ✅\n\n" + GREETING_MSG_HI,
    "kannada": "ಆಯ್ಕೆಮಾಡಲಾದ ಭಾಷೆ: *ಕನ್ನಡ* ✅\n\n" + GREETING_MSG_KN,
    "telugu": "ఎంచుకున్న భాష: *తెలుగు* ✅\n\n" + GREETING_MSG_TE,
    "marathi": "निवडलेली भाषा: *मराठी* ✅\n\n" + GREETING_MSG_MR,
}

_LANGUAGE_NAMES = {
    "english": "english", "hindi": "hindi", "हिंदी": "hindi", "हिन्दी": "hindi",
    "kannada": "kannada", "ಕನ್ನಡ": "kannada", "telugu": "telugu", "telgu": "telugu", "తెలుగు": "telugu",
    "marathi": "marathi", "मराठी": "marathi",
}
_LANGUAGE_REQUEST = re.compile(
    r"^(?:(?:in|change to|switch to|speak|reply in)\s+)?(?P<name>\S+)(?:\s+(?:language|please|bhasha|भाषा|ಭಾಷೆ|భాష))?$"
)


def _resolve_language_choice(text: str, allow_numeric: bool = True) -> Optional[str]:
    """
    Language picked by the user. While the menu is shown (allow_numeric) menu numbers, codes and names count.
    Afterwards only a menu button or a message that is just a language name ("Hindi", "in Kannada",
    "ಕನ್ನಡ") changes it, so answers such as "2 lakh", "Hi" or "Bengaluru" never switch the language.
    """
    t = text.strip().lower().rstrip(".!")
    # WhatsApp button ids and Telegram keyboard buttons, e.g. "2. हिंदी (Hindi)", work at any time
    if t in _LANGUAGE_BUTTON_IDS:
        return _LANGUAGE_BUTTON_IDS[t]
    button = re.match(r"^([1-5])\.\s+\S", t)
    if button and "(" in t or t == "1. english":
        return {"1": "english", "2": "hindi", "3": "kannada", "4": "telugu", "5": "marathi"}[button.group(1)]
    m = _LANGUAGE_REQUEST.match(t)
    if m and m.group("name") in _LANGUAGE_NAMES:
        return _LANGUAGE_NAMES[m.group("name")]
    if not allow_numeric:
        return None
    if t in LANGUAGE_CHOICES:
        return LANGUAGE_CHOICES[t]
    for num, lang in [("1", "english"), ("2", "hindi"), ("3", "kannada"), ("4", "telugu"), ("5", "marathi")]:
        if t == num or t.startswith(f"{num} ") or t.startswith(f"{num}.") or t.startswith(f"{num}-"):
            return lang
    if len(t.split()) <= 4:
        for lang, keys in (("telugu", ["telugu", "telgu", "తెలుగు"]), ("marathi", ["marathi", "मराठी"]),
                           ("kannada", ["kannada", "ಕನ್ನಡ"]), ("hindi", ["hindi", "हिंदी", "हिन्दी"]),
                           ("english", ["english"])):
            if any(k in t for k in keys):
                return lang
    return None

MARATHI_DISTINCT_WORDS = {
    "आहे", "आहेत", "नाही", "माझे", "माझी", "माझा", "मला", "मी", "करा", "करायचा",
    "करायचे", "करायची", "पाहिजे", "जिल्हा", "जिल्ह्यात", "भांडवल", "मध्ये", "शेती",
    "शेतकरी", "होय", "कसा", "कशी", "कसे", "झाले", "झाला", "झाली", "मिळेल", "लागेल",
    "किराणा", "करावे", "करावा", "दुग्ध", "कुक्कुटपालन", "गाय", "पाहा", "सांगा"
}

HINDI_DISTINCT_WORDS = {
    "है", "हैं", "नहीं", "मेरा", "मेरी", "मेरे", "मुझे", "मुझको", "मैं", "करना",
    "करनी", "करने", "चाहिए", "में", "हाँ", "नमस्ते", "होगा", "होगी", "सकता",
    "सकती", "सकते", "किराना", "पूंजी", "जिले", "किसान", "खेती", "बताएं", "दीजिए"
}

def detect_message_language(text: str) -> Optional[str]:
    """
    Detect language strictly from text or voice transcript using Unicode scripts and explicit keywords.
    Supported: 'kannada', 'hindi', 'telugu', 'tamil', 'marathi', 'english'.
    """
    if not text:
        return None

    clean = text.strip()
    lower = clean.lower()

    # 1. Explicit language command keywords
    if any(k in lower for k in ["in kannada", "kannada please", "kannadadalli", "kannada", "ಕನ್ನಡ"]):
        return "kannada"
    if any(k in lower for k in ["in hindi", "hindi please", "hindi mein", "hindi", "हिंदी", "हिन्दी"]):
        return "hindi"
    if any(k in lower for k in ["in telugu", "telugu please", "telugulo", "telgu please", "in telgu", "telugu", "telgu", "తెలుగు"]):
        return "telugu"
    if any(k in lower for k in ["in tamil", "tamil please", "tamil", "தமிழ்"]):
        return "tamil"
    if any(k in lower for k in ["in marathi", "marathi please", "marathit", "marathi", "मराठी"]):
        return "marathi"
    if any(k in lower for k in ["in english", "english please", "english"]):
        return "english"

    # 2. Unicode script frequency counting
    counts = {
        "kannada": 0,
        "devanagari": 0,    # Devanagari script (Hindi / Marathi)
        "telugu": 0,
        "tamil": 0,
    }
    has_marathi_char = False
    for char in clean:
        code = ord(char)
        if 0x0C80 <= code <= 0x0CFF:
            counts["kannada"] += 1
        elif 0x0900 <= code <= 0x097F:
            counts["devanagari"] += 1
            if char == "ळ" or code == 0x0933:
                has_marathi_char = True
        elif 0x0C00 <= code <= 0x0C7F:
            counts["telugu"] += 1
        elif 0x0B80 <= code <= 0x0BFF:
            counts["tamil"] += 1

    top_lang, top_count = max(counts.items(), key=lambda x: x[1])
    if top_count >= 2:
        if top_lang == "devanagari":
            if has_marathi_char:
                return "marathi"
            devanagari_words = set(re.findall(r'[\u0900-\u097F]+', clean))
            mr_score = sum(1 for w in devanagari_words if w in MARATHI_DISTINCT_WORDS)
            hi_score = sum(1 for w in devanagari_words if w in HINDI_DISTINCT_WORDS)
            if mr_score > hi_score:
                return "marathi"
            elif hi_score > mr_score:
                return "hindi"
            if mr_score > 0:
                return "marathi"
            return "hindi"
        return top_lang

    # 3. Detect English if text is predominantly Latin letters
    latin_count = sum(1 for c in clean if 'a' <= c.lower() <= 'z')
    if latin_count >= 5:
        return "english"

    return None

def send_channel_text(beneficiary, text: str, reply_markup: Optional[Dict[str, Any]] = None):
    """Dispatch outbound message to beneficiary's active channel (Telegram or WhatsApp)."""
    if getattr(beneficiary, "primary_channel", "") == "telegram" and beneficiary.telegram_chat_id:
        send_telegram_text(beneficiary.telegram_chat_id, text, reply_markup=reply_markup)
    else:
        send_whatsapp_text(beneficiary.whatsapp_number, text)

def send_channel_voice(beneficiary, voice_bytes: bytes, caption: Optional[str] = None):
    """Dispatch outbound voice note to beneficiary's active channel (Telegram or WhatsApp)."""
    if getattr(beneficiary, "primary_channel", "") == "telegram" and beneficiary.telegram_chat_id:
        send_telegram_voice(beneficiary.telegram_chat_id, voice_bytes, caption=caption)
    elif beneficiary.whatsapp_number:
        send_whatsapp_voice(beneficiary.whatsapp_number, voice_bytes, caption=caption)


def send_channel_language_menu(beneficiary):
    """Language menu: reply keyboard on Telegram, tap-able buttons on WhatsApp (plain text if buttons fail)."""
    if getattr(beneficiary, "primary_channel", "") == "telegram" and beneficiary.telegram_chat_id:
        send_telegram_text(beneficiary.telegram_chat_id, LANGUAGE_PROMPT_MSG, reply_markup=LANGUAGE_KEYBOARD)
    else:
        send_whatsapp_buttons(
            recipient_phone=beneficiary.whatsapp_number,
            title="🌐 Select your language / ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ / भाषा चुनें",
            description=LANGUAGE_PROMPT_MSG,
            buttons=LANGUAGE_BUTTONS,
            footer="Rural Micro-Enterprise Advisor",
        )

def send_channel_document(beneficiary, document_url: str, filename: str, caption: str, document_bytes: Optional[bytes] = None):
    """Dispatch outbound document to beneficiary's active channel (Telegram or WhatsApp)."""
    if getattr(beneficiary, "primary_channel", "") == "telegram" and beneficiary.telegram_chat_id:
        doc_payload = document_bytes if (document_bytes and len(document_bytes) > 0) else document_url
        send_telegram_document(beneficiary.telegram_chat_id, doc_payload, filename=filename, caption=caption)
    else:
        send_whatsapp_document(
            recipient_phone=beneficiary.whatsapp_number,
            document_url=document_url,
            filename=filename,
            caption=caption,
            document_bytes=document_bytes
        )


# ==================== TELEGRAM HANDLERS ====================

def process_telegram_voice_query(chat_id: str, file_id: str, user_name: Optional[str] = None):
    """Pipeline for Telegram voice notes (.oga/.ogg): download -> Gemini STT -> language sync -> dialogue."""
    logger.info(f"Processing Telegram voice query from chat_id {chat_id}, file_id: {file_id}")
    audio_bytes = download_telegram_file(file_id)
    if not audio_bytes:
        send_telegram_text(chat_id, "Sorry, could not download voice note. Please try sending again.")
        return

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id, full_name=user_name)
        lang = beneficiary.preferred_language or "kannada"
    finally:
        db.close()

    transcription = transcribe_audio(audio_bytes, source_language=lang)
    logger.info(f"Telegram voice note transcribed: '{transcription}'")

    if not transcription or not transcription.strip():
        if lang == "kannada":
            err_msg = "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸಂದೇಶ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ ಅಥವಾ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಿ ಕಳುಹಿಸಿ."
        elif lang == "hindi":
            err_msg = "क्षमा करें, आपकी आवाज़ स्पष्ट रूप से सुनाई नहीं दी। कृपया फिर से बोलें या टेक्स्ट लिखकर भेजें।"
        elif lang == "telugu":
            err_msg = "క్షమించండి, మీ వాయిస్ సందేశం స్పష్టంగా వినిపించలేదు. దయచేసి మళ్లీ స్పష్టంగా మాట్లాడండి లేదా టెక్స్ట్ మెసేజ్ పంపండి."
        elif lang == "marathi":
            err_msg = "क्षमस्व, आपला आवाज स्पष्टपणे ऐकू आला नाही. कृपया पुन्हा स्पष्टपणे बोला किंवा संदेश टाईप करून पाठवा."
        else:
            err_msg = "Sorry, we could not hear your voice clearly. Please speak clearly again or reply with text."
        send_telegram_text(chat_id, err_msg)
        return

    # Synchronize language immediately from the spoken voice note transcript
    # The selected language is kept: a transcript (possibly romanised) never switches it
    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id, full_name=user_name)
        _handle_user_turn(db, beneficiary, transcription, from_voice=True)
    finally:
        db.close()

def process_telegram_query(chat_id: str, text: str, user_name: Optional[str] = None, from_voice: bool = False):
    """Process incoming text message from Telegram."""
    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_telegram_beneficiary(db, chat_id, full_name=user_name)
        _handle_user_turn(db, beneficiary, text, from_voice=from_voice)
    finally:
        db.close()

# ==================== WHATSAPP HANDLERS ====================

_VOICE_NOT_HEARD = {
    "kannada": "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸಂದೇಶ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ ಅಥವಾ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಿ ಕಳುಹಿಸಿ.",
    "hindi": "क्षमा करें, आपकी आवाज़ स्पष्ट रूप से सुनाई नहीं दी। कृपया फिर से बोलें या टेक्स्ट लिखकर भेजें।",
    "telugu": "క్షమించండి, మీ వాయిస్ సందేశం స్పష్టంగా వినిపించలేదు. దయచేసి మళ్లీ స్పష్టంగా మాట్లాడండి లేదా టెక్స్ట్ మెసేజ్ పంపండి.",
    "marathi": "क्षमस्व, आपला आवाज स्पष्टपणे ऐकू आला नाही. कृपया पुन्हा स्पष्टपणे बोला किंवा संदेश टाईप करून पाठवा.",
    "english": "Sorry, we could not hear your voice clearly. Please speak clearly again or reply with text.",
}


def process_voice_query(from_phone: str, media_data: Any):
    """
    WhatsApp voice notes: download -> Gemini STT -> dialogue. `media_data` is the Evolution message data
    (or a Meta media id). The selected language is kept, as on Telegram.
    """
    logger.info(f"Processing WhatsApp voice query from {from_phone}")
    audio_bytes = download_whatsapp_media(media_data)
    if not audio_bytes:
        send_whatsapp_text(from_phone, "Sorry, we could not retrieve your voice note. Please send your message again.")
        return

    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, from_phone)
        lang = beneficiary.preferred_language or "kannada"
    finally:
        db.close()

    transcription = transcribe_audio(audio_bytes, source_language=lang)
    logger.info(f"WhatsApp voice note transcribed: '{transcription}'")
    if not transcription or not transcription.strip():
        send_whatsapp_text(from_phone, _VOICE_NOT_HEARD.get(lang, _VOICE_NOT_HEARD["english"]))
        return

    process_user_query(from_phone, transcription, from_voice=True)


def process_user_query(from_phone: str, user_text: str, from_voice: bool = False):
    """Process incoming text message (or voice transcript) from WhatsApp."""
    db = SessionLocal()
    try:
        beneficiary = crud.get_or_create_beneficiary(db, from_phone)
        _handle_user_turn(db, beneficiary, user_text, from_voice=from_voice)
    finally:
        db.close()

# ==================== CORE STATE MACHINE ====================

def _send_voice_audio_reply(beneficiary, text: str, lang: str, max_lines: Optional[int] = 3):
    """Synthesize speech and send as voice note to the user if channel supports voice."""
    try:
        lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("━")]
        spoken_text = " ".join(lines[:max_lines] if max_lines else lines) if lines else text[:250]
        clean_text = spoken_text.replace("*", "").replace("#", "").replace("-", " ")
        audio_bytes = synthesize_speech(clean_text, target_language=lang)
        if audio_bytes:
            send_channel_voice(beneficiary, audio_bytes)
    except Exception as e:
        logger.warning(f"Failed to send voice audio reply: {e}")

def _handle_user_turn(db, beneficiary, user_text: str, from_voice: bool = False):
    """Shared state machine for both Telegram and WhatsApp channels."""
    text_clean = user_text.strip()
    state = beneficiary.conversation_state or "LANGUAGE_SELECTION"
    # Work on a copy: in-place edits to the stored JSON are invisible to SQLAlchemy and would not be saved
    context = copy.deepcopy(beneficiary.conversation_context or {})

    channel_name = "Telegram" if getattr(beneficiary, "primary_channel", "") == "telegram" else "WhatsApp"
    logger.info(f"[{channel_name}] Beneficiary {beneficiary.id[:8]} (state: {state}): '{text_clean}'")

    # 1. Reset / Restart / Language selection commands
    start_or_lang_cmds = [
        "/START", "START", "RESET", "RESTART", "CLEAR", "NEW",
        "LANGUAGE", "LANG", "CHANGE LANGUAGE", "SELECT LANGUAGE",
        "ಭಾಷೆ", "भाषा", "భాష", "MENU"
    ]
    if text_clean.upper() in start_or_lang_cmds:
        beneficiary.conversation_state = "LANGUAGE_SELECTION"
        # A new conversation starts empty: nothing from an earlier conversation is reused
        beneficiary.conversation_context = {}
        db.commit()
        send_channel_language_menu(beneficiary)
        return

    # 2. Check if user selected or typed a language choice (e.g. 1-5, 'telugu', 'telgu', 'marathi', etc.)
    chosen_lang = _resolve_language_choice(text_clean, allow_numeric=(state == "LANGUAGE_SELECTION"))
    if chosen_lang:
        beneficiary.preferred_language = chosen_lang
        beneficiary.conversation_state = "COLLECTING"
        db.commit()
        confirmation = LANGUAGE_CONFIRMATIONS.get(chosen_lang, LANGUAGE_CONFIRMATIONS["english"])
        send_channel_text(beneficiary, confirmation)
        if from_voice:
            _send_voice_audio_reply(beneficiary, confirmation, chosen_lang)
        return

    # 3. Once the user has chosen a language it stays fixed; only the menu or naming a language changes it
    # (handled above). Detection from the message is used only while no language has been chosen yet.
    detected_lang = detect_message_language(text_clean) if state == "LANGUAGE_SELECTION" else None
    if detected_lang:
        beneficiary.preferred_language = detected_lang
        db.commit()

    # 4. Handle initial LANGUAGE_SELECTION state
    if state == "LANGUAGE_SELECTION":
        # Native greetings directly map to language selection
        if any(k in text_clean for k in ["నమస్కారం", "నమస్తే"]):
            beneficiary.preferred_language = "telugu"
            beneficiary.conversation_state = "COLLECTING"
            db.commit()
            send_channel_text(beneficiary, GREETING_MSG_TE)
            if from_voice:
                _send_voice_audio_reply(beneficiary, GREETING_MSG_TE, "telugu")
            return
        elif "ನಮಸ್ಕಾರ" in text_clean:
            beneficiary.preferred_language = "kannada"
            beneficiary.conversation_state = "COLLECTING"
            db.commit()
            send_channel_text(beneficiary, GREETING_MSG_KN)
            if from_voice:
                _send_voice_audio_reply(beneficiary, GREETING_MSG_KN, "kannada")
            return
        elif "नमस्ते" in text_clean:
            beneficiary.preferred_language = "hindi"
            beneficiary.conversation_state = "COLLECTING"
            db.commit()
            send_channel_text(beneficiary, GREETING_MSG_HI)
            if from_voice:
                _send_voice_audio_reply(beneficiary, GREETING_MSG_HI, "hindi")
            return
        elif "नमस्कार" in text_clean:
            chosen = "marathi" if beneficiary.preferred_language == "marathi" else "hindi"
            beneficiary.preferred_language = chosen
            beneficiary.conversation_state = "COLLECTING"
            db.commit()
            g_msg = GREETING_MSG_MR if chosen == "marathi" else GREETING_MSG_HI
            send_channel_text(beneficiary, g_msg)
            if from_voice:
                _send_voice_audio_reply(beneficiary, g_msg, chosen)
            return

        # If user entered an actual business query or sentence where language was detected:
        if detected_lang:
            beneficiary.conversation_state = "COLLECTING"
            db.commit()
            _handle_intake_turn(db, beneficiary, text_clean, context, from_voice=from_voice)
            return

        # Otherwise re-send language selection prompt
        send_channel_language_menu(beneficiary)
        return

    lang = beneficiary.preferred_language or "kannada"

    # 5. Greetings when already in an active dialogue state
    if text_clean.upper() in ["HI", "HELLO", "ನಮಸ್ಕಾರ", "नमस्ते", "నమస్కారం", "నమస్తే", "नमस्कार"]:
        beneficiary.conversation_state = "COLLECTING"
        beneficiary.conversation_context = {}
        db.commit()
        if lang == "kannada":
            greeting = GREETING_MSG_KN
        elif lang == "hindi":
            greeting = GREETING_MSG_HI
        elif lang == "telugu":
            greeting = GREETING_MSG_TE
        elif lang == "marathi":
            greeting = GREETING_MSG_MR
        else:
            greeting = GREETING_MSG_EN
        send_channel_text(beneficiary, greeting)
        if from_voice:
            _send_voice_audio_reply(beneficiary, greeting, lang)
        return

    # Check for DPR generation trigger
    if "GENERATE DPR" in text_clean.upper() or "DPR" in text_clean.upper():
        # A DPR is produced only from details the applicant has stated and confirmed
        if not context.get("profile_confirmed") or not context.get("financial_structure"):
            _prompt_intake(db, beneficiary, context, lang, from_voice)
            return

        # Send the 2-minute waiting notification requested by the user
        if lang == "kannada":
            wait_msg = "⏳ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿಯನ್ನು (DPR PDF) ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು 2 ನಿಮಿಷ ಕಾಯಿರಿ, ಪೂರ್ಣ ವರದಿಯು ಇಲ್ಲಿಯೇ ನೇರವಾಗಿ ತಲುಪಲಿದೆ..."
        elif lang == "hindi":
            wait_msg = "⏳ आपकी बैंक-तैयार विस्तृत परियोजना रिपोर्ट (DPR PDF) तैयार की जा रही है। कृपया 2 मिनट प्रतीक्षा करें, पूरी रिपोर्ट यहीं प्राप्त होगी..."
        elif lang == "telugu":
            wait_msg = "⏳ మీ బ్యాంక్ ప్రాజెక్ట్ నివేదిక (DPR PDF) సిద్ధం చేయబడుతోంది. దయచేసి 2 నిమిషాలు వేచి ఉండండి, పూర్తి నివేదిక ఇక్కడే మీకు అందుతుంది..."
        elif lang == "marathi":
            wait_msg = "⏳ आपला बँक-तयार सविस्तर प्रकल्प अहवाल (DPR PDF) तयार केला जात आहे. कृपया २ मिनिटे प्रतीक्षा करा, संपूर्ण अहवाल थेट येथे पाठवला जाईल..."
        else:
            wait_msg = "⏳ Generating your bank-ready Detailed Project Report (DPR PDF). Please wait for 2 minutes while we compile your financial statements and cash flow projections..."
        send_channel_text(beneficiary, wait_msg)

        _handle_dpr_generation(db, beneficiary, context)
        return

    lower_text = text_clean.lower()

    # 1. Voice capability inquiry (e.g. "Do you accept voice input", "can I speak", "voice note")
    voice_keywords = [
        "voice", "voice input", "voice note", "audio", "mic", "microphone",
        "ಧ್ವನಿ", "ಆಡಿಯೋ", "ಮಾತನಾಡು", "बोल", "ऑडिओ", "आवाज", "बोला",
        "వాయిస్", "ఆడియో", "మాట్లాడు"
    ]
    if any(k in lower_text for k in voice_keywords) and len(text_clean.split()) < 10:
        if lang == "kannada":
            msg = (
                "ಹೌದು, ಖಂಡಿತವಾಗಿ! 🎙️ ನೀವು ಕನ್ನಡ, ಹಿಂದಿ, ತೆಲುಗು, ಮರಾಠಿ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಧ್ವನಿ ಸಂದೇಶ (Voice Note) ಕಳುಹಿಸಬಹುದು.\n\n"
                "ಟೆಲಿಗ್ರಾಮ್‌ನಲ್ಲಿರುವ ಮೈಕ್ರೋಫೋನ್ ಐಕಾನ್ ಒತ್ತಿ ಹಿಡಿದು ನಿಮ್ಮ ವ್ಯಾಪಾರದ ಕಲ್ಪನೆ, ನಿಮ್ಮ ಜಿಲ್ಲೆ ಮತ್ತು ಅಂದಾಜು ಬಂಡವಾಳವನ್ನು ಮಾತನಾಡಿ ಕಳುಹಿಸಿ!"
            )
        elif lang == "hindi":
            msg = (
                "हाँ, बिल्कुल! 🎙️ आप हिंदी, मराठी, तेलुगु, कन्नड़ या अंग्रेजी में वॉइस नोट भेज सकते हैं।\n\n"
                "टेलीग्राम पर माइक बटन दबाकर अपने व्यापार का विचार, जिला और बजट बोलकर भेजें!"
            )
        elif lang == "telugu":
            msg = (
                "అవును, ఖచ్చితంగా! 🎙️ మీరు తెలుగు, కన్నడ, హిందీ, మరాఠీ లేదా ఇంగ్లీషులో వాయిస్ నోట్ (Voice Note) పంపవచ్చు.\n\n"
                "టెలిగ్రామ్‌లోని మైక్రోఫోన్ బటన్ నొక్కి పట్టుకుని మీ వ్యాపార ఆలోచన, మీ జిల్లా మరియు అవసరమైన పెట్టుబడిని మాట్లాడి పంపండి!"
            )
        elif lang == "marathi":
            msg = (
                "होय, नक्कीच! 🎙️ आपण मराठी, हिंदी, तेलुगु, कन्नड किंवा इंग्रजीमध्ये व्हॉइस नोट (Voice Note) पाठवू शकता.\n\n"
                "टेलिग्रामवरील मायक्रोफोन बटण दाबून धरून आपल्या व्यवसायाची कल्पना, जिल्हा आणि अपेक्षित भांडवल बोलून पाठवा!"
            )
        else:
            msg = (
                "Yes, absolutely! 🎙️ You can send voice notes in English, Kannada (ಕನ್ನಡ), Hindi (हिंदी), Telugu (తెలుగు), Marathi (मराठी), or your regional language.\n\n"
                "Simply hold down the microphone button in Telegram, describe your business idea, your district, and your required capital, and I will structure your government financing options!"
            )
        send_channel_text(beneficiary, msg)
        if from_voice:
            _send_voice_audio_reply(beneficiary, msg, lang)
        return

    # 2. General help inquiry (e.g. "what can you do", "help", "who are you")
    if any(k in lower_text for k in ["what can you do", "help", "who are you", "ಏನು ಮಾಡಬಹುದು", "ಸಹಾಯ", "मदद", "मदत", "సహాయం", "ఏం చేయగలరు"]) and len(text_clean.split()) < 7:
        if lang == "kannada":
            msg = (
                "ನಾನು ನಿಮ್ಮ ಎಐ ಗ್ರಾಮೀಣ ಉದ್ಯಮ ಸಲಹೆಗಾರ. 🙏\n\n"
                "ನಾನು ಸ್ಥಳೀಯ ವ್ಯಾಪಾರಿಗಳು ಮತ್ತು ಗ್ರಾಮೀಣ ಉದ್ಯಮಿಗಳಿಗೆ ಸರ್ಕಾರಿ ರಿಯಾಯಿತಿ ಸಾಲಗಳು (MFS/TLS 6.5%-8%), "
                "PMEGP 35% ಸಬ್ಸಿಡಿ ಮತ್ತು ಮುದ್ರಾ ಸಾಲಗಳನ್ನು ಲೆಕ್ಕಾಚಾರ ಮಾಡಿ ಬ್ಯಾಂಕ್-ಸಿದ್ಧ ಯೋಜನಾ ವರದಿ (DPR) ತಯಾರಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.\n\n"
                "ನೀವು ಯಾವ ವ್ಯಾಪಾರವನ್ನು, ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ, ಎಷ್ಟು ಬಂಡವಾಳದೊಂದಿಗೆ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ ಎಂದು ತಿಳಿಸಿ!"
            )
        elif lang == "hindi":
            msg = (
                "मैं आपका एआई ग्रामीण उद्यम सलाहकार हूँ। 🙏\n\n"
                "मैं स्थानीय व्यापारियों और उद्यमियों के लिए सरकारी रियायती ऋण (MFS/TLS 6.5%-8%), "
                "PMEGP 35% सब्सिडी और मुद्रा ऋण की गणना करके बैंक-तैयार प्रोजेक्ट रिपोर्ट (DPR) बनाने में मदद करता हूँ।\n\n"
                "बताएं कि आप कौन सा व्यवसाय, किस जिले में, कितनी पूंजी के साथ शुरू करना चाहते हैं!"
            )
        elif lang == "telugu":
            msg = (
                "నేను మీ AI గ్రామీణ వ్యాపార సలహాదారుని. 🙏\n\n"
                "నేను స్థానిక వ్యాపారులు మరియు గ్రామీణ పారిశ్రామికవేత్తలకు ప్రభుత్వ రాయితీ రుణాలు (MFS/TLS 6.5%-8%), "
                "PMEGP 35% సబ్సిడీ మరియు ముద్రా రుణాలను లెక్కించి బ్యాంక్-సిద్ధ ప్రాజెక్ట్ నివేదిక (DPR) తయారు చేయడానికి సహాయం చేస్తాను.\n\n"
                "మీరు ఏ వ్యాపారాన్ని, ఏ జిల్లాలో, ఎంత పెట్టుబడితో ప్రారంభించాలనుకుంటున్నారో తెలియజేయండి!"
            )
        elif lang == "marathi":
            msg = (
                "मी आपला एआय ग्रामीण उद्योग सल्लागार आहे. 🙏\n\n"
                "मी स्थानिक व्यापारी आणि ग्रामीण उद्योजकांसाठी सरकारी सवलतीचे कर्ज (MFS/TLS 6.5%-8%), "
                "PMEGP 35% सबसिडी आणि मुद्रा कर्ज यांचे नियोजन करून बँक-तयार प्रकल्प अहवाल (DPR) तयार करण्यास मदत करतो.\n\n"
                "आपण कोणता व्यवसाय, कोणत्या जिल्ह्यात आणि किती भांडवलासह सुरू करू इच्छिता ते सांगा!"
            )
        else:
            msg = (
                "I am your AI Rural Enterprise Advisor. 🙏\n\n"
                "I help rural entrepreneurs and hyper-local business owners structure bank-ready loan proposals, "
                "calculate eligibility for government concessional schemes (MFS/TLS at 6.5%-8%), "
                "claim PMEGP capital subsidies (up to 35%), and generate official Detailed Project Reports (DPR).\n\n"
                "Tell me which business trade you want to start, your district, and your required budget to get started!"
            )
        send_channel_text(beneficiary, msg)
        if from_voice:
            _send_voice_audio_reply(beneficiary, msg, lang)
        return

    # 3. Conversational follow-ups when advisory has already been generated or submitted
    if state in ["CONFIRM_DPR", "SUBMITTED"]:
        extracted = extract_entrepreneur_details(text_clean)
        new_trade = extracted.get("trade")
        curr_trade = context.get("trade", "")
        # If user proposes a different trade, reset old context so it doesn't hallucinate previous venture details
        is_new_venture = bool(new_trade and new_trade.lower() != curr_trade.lower())
        has_new_cost = bool(extracted.get("project_cost") and extracted.get("project_cost") != context.get("project_cost"))

        if is_new_venture or has_new_cost:
            if is_new_venture:
                # A different business starts a fresh application: every detail is asked again
                context = {}
            beneficiary.conversation_state = "COLLECTING"
            _handle_intake_turn(db, beneficiary, text_clean, context, from_voice=from_voice)
            return

        trade = context.get("trade", "your enterprise")
        district = context.get("district", "your district")
        cost = context.get("project_cost")
        cost_str = f"with outlay ₹{cost:,.2f}" if cost else ""

        follow_up_prompt = (
            f"You are a helpful Rural Enterprise Lending Advisor. The entrepreneur has received advisory for their "
            f"{trade} in {district} {cost_str}. "
            f"Answer their message concisely, politely, and strictly in {lang} language. "
            f"At the end, remind them: 'Reply GENERATE DPR whenever you are ready to download your official bank report PDF.'"
        )
        try:
            from app.ai.llm_client import call_llm_chat
            answer = call_llm_chat(
                messages=[
                    {"role": "system", "content": follow_up_prompt},
                    {"role": "user", "content": text_clean}
                ],
                temperature=0.3
            )
            if answer and answer.strip():
                send_channel_text(beneficiary, answer.strip())
                if from_voice:
                    _send_voice_audio_reply(beneficiary, answer.strip(), lang)
                return
        except Exception as e:
            logger.warning(f"Follow-up answer failed: {e}")

        # Fallback reminder if LLM unavailable
        if lang == "kannada":
            fallback_ans = f"ನಿಮ್ಮ {trade} ಯೋಜನೆಯ ಅಧಿಕೃತ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿಯನ್ನು (PDF) ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು 'GENERATE DPR' ಎಂದು ಉತ್ತರಿಸಿ."
        elif lang == "hindi":
            fallback_ans = f"अपने {trade} उद्यम की आधिकारिक बैंक रिपोर्ट डाउनलोड करने के लिए 'GENERATE DPR' लिखकर भेजें।"
        elif lang == "telugu":
            fallback_ans = f"మీ {trade} ప్రాజెక్ట్ అధికారిక బ్యాంక్ నివేదికను (PDF) డౌన్‌లోడ్ చేయడానికి 'GENERATE DPR' అని రిప్లై ఇవ్వండి."
        elif lang == "marathi":
            fallback_ans = f"आपल्या {trade} प्रकल्पाचा अधिकृत बँक अहवाल (PDF) डाउनलोड करण्यासाठी 'GENERATE DPR' लिहून पाठवा."
        else:
            fallback_ans = f"Reply 'GENERATE DPR' whenever you are ready to download your official bank report PDF for your {trade}."
        send_channel_text(beneficiary, fallback_ans)
        if from_voice:
            _send_voice_audio_reply(beneficiary, fallback_ans, lang)
        return

    # 4. While collecting details, treat the message as an answer first
    if state == "CONFIRM_PROFILE":
        _handle_profile_confirmation(db, beneficiary, text_clean, context, from_voice=from_voice)
        return
    # Statements such as "dairy in Belagavi, cost 2 lakh" are details, not factual questions; only a message
    # that looks like a question (with no question pending) goes straight to the factual router.
    if state in ("COLLECTING", "GREETING") and (context.get("pending_field") or not _looks_like_question(text_clean)):
        if _handle_intake_turn(db, beneficiary, text_clean, context, from_voice=from_voice, allow_passthrough=True):
            return

    # 5. Phase 5: Local Authoritative RAG Intent Routing
    # Check for Factual, Mixed, or Data-Unavailable inquiries before proposal accumulation
    from app.retrieval.router import classify_query_intent, execute_authoritative_routing, QueryIntent
    rag_intent, _ = classify_query_intent(text_clean)
    if rag_intent in [QueryIntent.FACTUAL, QueryIntent.MIXED, QueryIntent.DATA_UNAVAILABLE]:
        routing_res = execute_authoritative_routing(text_clean, language=lang)
        send_channel_text(beneficiary, routing_res["answer"])
        if from_voice:
            _send_voice_audio_reply(beneficiary, routing_res["answer"], lang)
        return

    # Handle conversation stages
    if state in ["GREETING", "COLLECTING", "ADVISING", "CONFIRM_DPR"]:
        _handle_intake_turn(db, beneficiary, text_clean, context, from_voice=from_voice)

def _generate_clarification_question(missing: list, trade: Optional[str], district: Optional[str], lang: str) -> str:
    """Generate friendly, personalized clarification prompt for missing parameters in preferred language."""
    if "trade" in missing and "district" in missing and "project_cost" in missing:
        if lang == "kannada":
            return (
                "ನಮಸ್ಕಾರ! ಗ್ರಾಮೀಣ ಕಿರು-ಉದ್ಯಮ ಮತ್ತು ಸ್ಥಳೀಯ ವ್ಯಾಪಾರ ಸಲಹಾ ಸೇವೆಗೆ ಸ್ವಾಗತ. 🙏\n\n"
                "ನಿಮ್ಮ ಯೋಜನೆಗೆ ಲಭ್ಯವಿರುವ ಸರ್ಕಾರಿ ಸಾಲ (MFS/TLS), ಮುದ್ರಾ ಸಾಲ ಹಾಗೂ 35% ವರೆಗಿನ PMEGP ಸಬ್ಸಿಡಿ ವಿವರಗಳನ್ನು ತಿಳಿಸಲು, ದಯವಿಟ್ಟು ಈ 3 ವಿವರಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳಿ:\n\n"
                "1. 🏪 *ನೀವು ಯಾವ ವ್ಯಾಪಾರ/ಉದ್ಯಮ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ?* (ಉದಾ: ಕಿರಾಣಿ ಅಂಗಡಿ, ಹೈನುಗಾರಿಕೆ/ಹಸು, ಟೈಲರಿಂಗ್, ಕೋಳಿ ಸಾಕಾಣಿಕೆ, ಹಿಟ್ಟಿನ ಗಿರಣಿ)\n"
                "2. 📍 *ನಿಮ್ಮ ಜಿಲ್ಲೆ ಯಾವುದು?* (ಉದಾ: ಬೆಳಗಾವಿ, ಮೈಸೂರು, ಧಾರವಾಡ, ಮಂಡ್ಯ)\n"
                "3. 💰 *ನಿಮ್ಮ ಅಂದಾಜು ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚ (ಬಜೆಟ್) ಎಷ್ಟು?* (ಉದಾ: ₹50,000, ₹1,20,000, ₹3,00,000)\n\n"
                "ದಯವಿಟ್ಟು ಉತ್ತರಿಸಿ, ನಾವು ನಿಮಗೆ ಸಂಪೂರ್ಣ ಸಾಲದ ವಿವರಗಳನ್ನು ನೀಡುತ್ತೇವೆ."
            )
        elif lang == "hindi":
            return (
                "नमस्ते! ग्रामीण सूक्ष्म उद्यम वित्तीय सलाहकार में आपका स्वागत है। 🙏\n\n"
                "आपके व्यवसाय के लिए सबसे उपयुक्त सरकारी योजनाएं, रियायती ऋण और 35% तक सब्सिडी जानने के लिए कृपया यह विवरण बताएं:\n\n"
                "1. 🏪 *आप कौन सा व्यवसाय/उद्योग शुरू करना चाहते हैं?* (उदा: किराना दुकान, डेयरी/गाय पालन, सिलाई, मुर्गी पालन)\n"
                "2. 📍 *आपका जिला कौन सा है?* (उदा: बेलगावी, मैसूरु, धारवाड़)\n"
                "3. 💰 *आपकी अनुमानित कुल परियोजना लागत (बजट) कितनी है?* (उदा: ₹50,000, ₹1,20,000, ₹3,00,000)"
            )
        elif lang == "telugu":
            return (
                "నమస్కారం! గ్రామీణ సూక్ష్మ-వ్యాపార సలహా కేంద్రానికి స్వాగతం. 🙏\n\n"
                "మీ ప్రాజెక్ట్‌కు అందుబాటులో ఉన్న ప్రభుత్వ రాయితీ రుణాలు (MFS/TLS), ముద్రా రుణాలు మరియు 35% వరకు PMEGP సబ్సిడీ వివరాలను తెలుసుకోవడానికి, దయచేసి ఈ 3 వివరాలను తెలియజేయండి:\n\n"
                "1. 🏪 *మీరు ఏ వ్యాపారం/పరిశ్రమను ప్రారంభించాలనుకుంటున్నారు?* (ఉదా: కిరాణా దుకాణం, పాడి పరిశ్రమ/ఆవులు, టైలరింగ్, కోళ్ల పెంపకం, పిండి మిల్లు)\n"
                "2. 📍 *మీ జిల్లా ఏది?* (ఉదా: గుంటూరు, విజయవాడ, వరంగల్, కర్నూలు, విశాఖపట్నం)\n"
                "3. 💰 *మీ అంచనా ప్రాజెక్ట్ ఖర్చు (బడ్జెట్) ఎంత?* (ఉదా: ₹50,000, ₹1,20,000, ₹3,00,000)\n\n"
                "దయచేసి సమాధానం ఇవ్వండి, మేము మీకు పూర్తి రుణ మరియు సబ్సిడీ వివరాలను అందిస్తాము."
            )
        elif lang == "marathi":
            return (
                "नमस्कार! ग्रामीण सूक्ष्म-उद्योग आणि स्थानिक व्यवसाय सल्ला केंद्रात आपले स्वागत आहे. 🙏\n\n"
                "आपल्या व्यवसायासाठी उपलब्ध सरकारी सवलतीचे कर्ज (MFS/TLS), मुद्रा कर्ज आणि ३५% पर्यंत PMEGP सबसिडीचे तपशील जाणून घेण्यासाठी, कृपया हे ३ तपशील सांगा:\n\n"
                "1. 🏪 *आपण कोणता व्यवसाय/उद्योग सुरू करू इच्छिता?* (उदा: किराणा दुकान, दुग्ध व्यवसाय/गाय, शिलाई काम, कुक्कुटपालन, पिठाची गिरणी)\n"
                "2. 📍 *आपला जिल्हा कोणता आहे?* (उदा: पुणे, नागपूर, नाशिक, कोल्हापूर, सोलापूर)\n"
                "3. 💰 *आपला अंदाजे एकूण प्रकल्प खर्च (भांडवल) किती आहे?* (उदा: ₹50,000, ₹1,20,000, ₹3,00,000)\n\n"
                "कृपया उत्तर द्या, आम्ही आपल्याला संपूर्ण कर्ज व सबसिडीचे तपशील देऊ."
            )
        else:
            return (
                "Namaste! Welcome to the Rural Micro-Enterprise & Hyper-Local Business Advisory. 🙏\n\n"
                "To identify the best government concessional loans (MFS/TLS), MUDRA bank credit, and PMEGP capital subsidies (up to 35%) for you, please share:\n\n"
                "1. 🏪 *What business/trade do you want to start?* (e.g., Kirana store, Dairy cow unit, Tailoring, Poultry farm, Flour mill)\n"
                "2. 📍 *Which district are you located in?* (e.g., Belagavi, Mysuru, Dharwad)\n"
                "3. 💰 *What is your estimated total project cost or required budget?* (e.g., ₹50,000, ₹1,20,000, ₹3,00,000)\n\n"
                "Please share your details to receive your personalized financing plan!"
            )

    questions = []
    if "trade" in missing:
        if lang == "kannada":
            questions.append("🏪 *ನೀವು ಪ್ರಾರಂಭಿಸಲು ಬಯಸುವ ನಿರ್ದಿಷ್ಟ ವ್ಯಾಪಾರ ಅಥವಾ ಉದ್ಯಮ ಯಾವುದು?* (ಉದಾ: ಕಿರಾಣಿ ಅಂಗಡಿ, ಹೈನುಗಾರಿಕೆ, ಟೈಲರಿಂಗ್, ಬೇಕರಿ)")
        elif lang == "hindi":
            questions.append("🏪 *आप कौन सा व्यवसाय शुरू करना चाहते हैं?* (उदा: किराना दुकान, डेयरी, सिलाई, बेकरी)")
        elif lang == "telugu":
            questions.append("🏪 *మీరు ప్రారంభించాలనుకుంటున్న నిర్దిష్ట వ్యాపారం ఏది?* (ఉదా: కిరాణా దుకాణం, పాడి పరిశ్రమ, టైలరింగ్, బేకరీ)")
        elif lang == "marathi":
            questions.append("🏪 *आपण कोणता विशिष्ट व्यवसाय सुरू करू इच्छिता?* (उदा: किराणा दुकान, दुग्ध व्यवसाय, शिलाई, बेकरी)")
        else:
            questions.append("🏪 *Which specific business trade would you like to start?* (e.g., Kirana store, Dairy farming, Tailoring, Poultry)")

    if "district" in missing:
        trade_label = trade if trade else ("ನಿಮ್ಮ ಉದ್ಯಮ" if lang == "kannada" else ("మీ వ్యాపారం" if lang == "telugu" else ("आपला व्यवसाय" if lang == "marathi" else "your venture")))
        if lang == "kannada":
            questions.append(f"📍 *{trade_label}ವನ್ನು ನೀವು ಯಾವ ಜಿಲ್ಲೆಯಲ್ಲಿ ಪ್ರಾರಂಭಿಸಲು ಯೋಜಿಸುತ್ತಿದ್ದೀರಿ?* (ಉದಾ: ಬೆಳಗಾವಿ, ಮೈಸೂರು, ಧಾರವಾಡ)")
        elif lang == "hindi":
            questions.append(f"📍 *{trade_label} आप किस जिले में शुरू करने की योजना बना रहे हैं?*")
        elif lang == "telugu":
            questions.append(f"📍 *{trade_label}ను మీరు ఏ జిల్లాలో ప్రారంభించాలని యోచిస్తున్నారు?* (ఉదా: గుంటూరు, విశాఖపట్నం, వరంగల్)")
        elif lang == "marathi":
            questions.append(f"📍 *{trade_label} आपण कोणत्या जिल्ह्यात सुरू करण्याचा विचार करत आहात?* (उदा: पुणे, नाशिक, कोल्हापूर)")
        else:
            questions.append(f"📍 *Which district will your {trade_label} be located in?* (e.g., Belagavi, Mysuru, Dharwad)")

    if "project_cost" in missing:
        if lang == "kannada":
            prefix = f"{district} ಜಿಲ್ಲೆಯಲ್ಲಿ ನಿಮ್ಮ {trade}" if (district and trade) else "ನಿಮ್ಮ ಉದ್ಯಮ"
            questions.append(f"💰 *{prefix}ಕ್ಕಾಗಿ ನಿಮ್ಮ ಅಂದಾಜು ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚ ಅಥವಾ ಅಗತ್ಯವಿರುವ ಬಂಡವಾಳ ಎಷ್ಟು?* (ಉದಾ: ₹80,000, ₹1,20,000, ₹3,00,000)")
        elif lang == "hindi":
            prefix = f"{district} में आपके {trade}" if (district and trade) else "आपके व्यवसाय"
            questions.append(f"💰 *{prefix} के लिए आपकी अनुमानित कुल परियोजना लागत (बजट) कितनी है?* (उदा: ₹80,000, ₹1,20,000, ₹3,00,000)")
        elif lang == "telugu":
            prefix = f"{district} లో మీ {trade}" if (district and trade) else "మీ వ్యాపారం"
            questions.append(f"💰 *{prefix} కోసం మీ అంచనా మొత్తం ప్రాజెక్ట్ ఖర్చు లేదా అవసరమైన పెట్టుబడి ఎంత?* (ఉదా: ₹80,000, ₹1,20,000, ₹3,00,000)")
        elif lang == "marathi":
            prefix = f"{district} मध्ये आपल्या {trade}" if (district and trade) else "आपल्या व्यवसाया"
            questions.append(f"💰 *{prefix}साठी आपला अंदाजे एकूण प्रकल्प खर्च किंवा आवश्यक भांडवल किती आहे?* (उदा: ₹80,000, ₹1,20,000, ₹3,00,000)")
        else:
            prefix = f"your {trade} in {district}" if (district and trade) else "your business"
            questions.append(f"💰 *What is your estimated total project cost or required capital for {prefix}?* (e.g., ₹80,000, ₹1,20,000, ₹3,00,000)")

    if lang == "kannada":
        return "ದಯವಿಟ್ಟು ಈ ಕೆಳಗಿನ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ, ನಾವು ನಿಮಗೆ ನಿಖರವಾದ ಸರ್ಕಾರಿ ಸಾಲ ಮತ್ತು ಸಬ್ಸಿಡಿ ವಿವರಗಳನ್ನು ನೀಡುತ್ತೇವೆ:\n\n" + "\n\n".join(questions)
    elif lang == "hindi":
        return "कृपया निम्नलिखित विवरण बताएं ताकि हम आपको सटीक सरकारी ऋण और सब्सिडी विवरण प्रदान कर सकें:\n\n" + "\n\n".join(questions)
    elif lang == "telugu":
        return "దయచేసి కింది వివరాలను తెలియజేయండి, మేము మీకు ఖచ్చితమైన ప్రభుత్వ రుణ మరియు సబ్సిడీ వివరాలను అందిస్తాము:\n\n" + "\n\n".join(questions)
    elif lang == "marathi":
        return "कृपया खालील तपशील सांगा जेणेकरून आम्ही आपल्याला अचूक सरकारी कर्ज आणि सबसिडीचे तपशील देऊ शकू:\n\n" + "\n\n".join(questions)
    else:
        return "Please share the following details so we can structure your exact government loan and subsidy options:\n\n" + "\n\n".join(questions)

def _save_context(db, beneficiary, context: Dict[str, Any]):
    beneficiary.conversation_context = copy.deepcopy(context)
    flag_modified(beneficiary, "conversation_context")
    db.commit()


def _send(beneficiary, text: str, lang: str, from_voice: bool, speak_all: bool = False):
    send_channel_text(beneficiary, text)
    if from_voice:
        _send_voice_audio_reply(beneficiary, text, lang, max_lines=None if speak_all else 3)


def _looks_like_question(text: str) -> bool:
    lower = text.lower()
    return "?" in text or any(w in lower for w in (
        "what", "how", "which", "why", "ಏನು", "ಹೇಗೆ", "ಯಾವ", "ಏಕೆ", "क्या", "कैसे", "कौन", "क्यों",
        "ఏమి", "ఎలా", "ఏ ", "ఎందుకు", "काय", "कसे", "कोणत", "का ",
    ))


def _prompt_intake(db, beneficiary, context: Dict[str, Any], lang: str, from_voice: bool, prefix: str = ""):
    """Ask the next group of missing details, or show the summary for confirmation once everything is collected."""
    nxt = intake.next_prompt(context, lang)
    context["awaiting_field_choice"] = False
    if nxt:
        msg, fields = nxt
        context["pending_fields"] = fields
        context["pending_field"] = fields[0]
        beneficiary.conversation_state = "COLLECTING"
    else:
        context["pending_fields"] = []
        context["pending_field"] = None
        beneficiary.conversation_state = "CONFIRM_PROFILE"
        msg = intake.summary(context, lang)
    speak_all = True  # voice users must hear every question and every detail they confirm
    _save_context(db, beneficiary, context)
    _send(beneficiary, f"{prefix}\n\n{msg}" if prefix else msg, lang, from_voice, speak_all=speak_all)


def _handle_intake_turn(db, beneficiary, text: str, context: Dict[str, Any], from_voice: bool = False,
                        allow_passthrough: bool = False) -> bool:
    """
    One intake step. Returns False (without replying) only when allow_passthrough is set and the message
    answered nothing but looks like a general question, so the caller can route it elsewhere.
    """
    lang = beneficiary.preferred_language or "english"
    pending = context.get("pending_fields") or ([context["pending_field"]] if context.get("pending_field") else [])
    # Before any question is pending, the greeting has asked for the business, district and total cost
    asked = pending or list(intake.GROUPS[0][1])
    answers = intake.extract_answers(text, pending)
    had_volunteered = dict(context.get("volunteered") or {})
    updated, issue = intake.apply_answers(context, answers, asked=asked)
    if answers.get("confirmation") == "yes":
        updated += intake.accept_volunteered(context, asked)
    if not updated and context.get("volunteered") != had_volunteered:
        updated = ["volunteered"]  # something was mentioned for a later question: carry on asking
    logger.info(f"Intake answers: updated={updated} issue={issue}")

    if updated:
        # Any change means the applicant must confirm again before advice is recalculated
        context["profile_confirmed"] = False
        for stale in ("financial_structure", "cashflows", "multi_schemes", "nabard_benchmark"):
            context.pop(stale, None)

    if issue:
        if issue[0] in ("out_of_coverage", "district_unrecognised"):
            context.pop("district", None)
            context.pop("state", None)
        _prompt_intake(db, beneficiary, context, lang, from_voice, prefix=intake.issue_message(issue, lang))
        return True

    if not updated:
        if allow_passthrough and _looks_like_question(text):
            return False
        prefix = intake.text_for(intake.MESSAGES["not_understood"], lang) if pending else ""
        _prompt_intake(db, beneficiary, context, lang, from_voice, prefix=prefix)
        return True

    _prompt_intake(db, beneficiary, context, lang, from_voice)
    return True


def _handle_profile_confirmation(db, beneficiary, text: str, context: Dict[str, Any], from_voice: bool = False):
    """CONFIRM_PROFILE: 'yes' runs the advisory; corrections update the details and show the summary again."""
    lang = beneficiary.preferred_language or "english"

    if context.get("awaiting_field_choice"):
        field = intake.match_field_name(text)
        if field:
            intake.set_value(context, field, None)
            context["profile_confirmed"] = False
            _prompt_intake(db, beneficiary, context, lang, from_voice)
            return

    answers = intake.extract_answers(text, None)
    updated, issue = intake.apply_answers(context, answers)
    if updated or issue:
        context["profile_confirmed"] = False
        if issue and issue[0] in ("out_of_coverage", "district_unrecognised"):
            context.pop("district", None)
            context.pop("state", None)
        _prompt_intake(db, beneficiary, context, lang, from_voice,
                       prefix=intake.issue_message(issue, lang) if issue else "")
        return

    if answers.get("confirmation") == "yes" and intake.next_missing(context) is None:
        context["profile_confirmed"] = True
        context["pending_field"] = None
        context["pending_fields"] = []
        context["awaiting_field_choice"] = False
        _run_advisory(db, beneficiary, context, from_voice=from_voice)
        return

    if answers.get("confirmation") == "no":
        context["awaiting_field_choice"] = True
        _save_context(db, beneficiary, context)
        _send(beneficiary, intake.text_for(intake.MESSAGES["which_field"], lang), lang, from_voice)
        return

    field = intake.match_field_name(text)
    if field:
        intake.set_value(context, field, None)
        context["profile_confirmed"] = False
        _prompt_intake(db, beneficiary, context, lang, from_voice)
        return

    _prompt_intake(db, beneficiary, context, lang, from_voice,
                   prefix=intake.text_for(intake.MESSAGES["not_understood"], lang))


def _run_advisory(db, beneficiary, context: Dict[str, Any], from_voice: bool = False):
    """Advisory from the confirmed applicant details only. Nothing here is assumed."""
    lang = beneficiary.preferred_language or "english"
    trade = context["trade"]
    district = context["district"]
    state = context["state"]
    project_cost = float(context["project_cost"])
    available_capital = context.get("available_capital")
    profile = intake.profile_for_records(context)

    beneficiary.full_name = profile.get("full_name")
    beneficiary.annual_family_income = profile.get("annual_family_income")

    # 1. Schemes for this applicant, from verified rules only (NEVER LLM):
    #    corporation loan for the stated category, PMEGP for category/area, MUDRA loan categories
    from app.finance.multi_schemes import get_all_eligible_schemes
    multi_schemes = get_all_eligible_schemes(
        cost=project_cost,
        trade=trade,
        district=district,
        state=state,
        available_capital=available_capital,
        profile=profile
    )
    fin_result = multi_schemes["primary_sca"]

    # 2. NABARD unit cost for reference. No DSCR or cash-flow projection is produced: no official source
    #    gives revenue or operating costs for these trades, so any such figure would be invented.
    benchmark = get_trade_benchmark(trade, district)
    benchmark_available = benchmark.get("status") != "DATA_NOT_AVAILABLE"

    context.update({
        "trade": trade,
        "district": district,
        "state": state,
        "project_cost": project_cost,
        "financial_structure": fin_result,
        "cashflows": {},
        "nabard_benchmark": benchmark.get("summary") if benchmark_available else NO_BENCHMARK_LLM_CONTEXT,
        "benchmark_available": benchmark_available,
        "multi_schemes": multi_schemes
    })

    beneficiary.district = district
    beneficiary.state = state
    beneficiary.preferred_language = lang
    beneficiary.conversation_state = "CONFIRM_DPR"
    _save_context(db, beneficiary, context)

    # Record or update an active DRAFT proposal for real-time admin visibility
    proposal_fields = {
        "business_trade": trade,
        "scheme_tier": fin_result["scheme"],
        "project_cost": project_cost,
        "sanctioned_loan": fin_result.get("loan") or 0.0,
        "beneficiary_margin": fin_result.get("margin") or 0.0,
        "monthly_emi": fin_result.get("emi") or 0.0,
        "projected_dscr": None,
    }
    from app.db.models import EnterpriseProposal
    existing_p = (
        db.query(EnterpriseProposal)
        .filter(EnterpriseProposal.beneficiary_id == beneficiary.id)
        .order_by(EnterpriseProposal.created_at.desc())
        .first()
    )
    if existing_p and existing_p.status == "DRAFT":
        for key, value in proposal_fields.items():
            setattr(existing_p, key, value)
        db.commit()
        proposal = existing_p
    else:
        proposal = crud.create_proposal(db, {"beneficiary_id": beneficiary.id, "status": "DRAFT", "dpr_pdf_url": None, **proposal_fields})

    # Keep the confirmed details and scheme results with the application for the officer dashboard
    from datetime import datetime, timezone
    crud.save_proposal_snapshot(db, proposal.id, {
        "profile": profile,
        "available_capital": available_capital,
        "trade": trade,
        "district": district,
        "state": state,
        "language": lang,
        "channel": getattr(beneficiary, "primary_channel", None),
        "financial_structure": fin_result,
        "pmegp": multi_schemes.get("pmegp"),
        "mudra": multi_schemes.get("mudra"),
        "benchmark_available": benchmark_available,
        "details_confirmed_at": datetime.now(timezone.utc).isoformat(),
    })

    # 3. Advisory text assembled from the verified results in the user's language
    advisory = generate_advisory_message(
        financial_data={"cost": project_cost},
        trade=trade,
        district=district,
        language=lang,
        state=state,
        available_capital=available_capital,
        multi_schemes=multi_schemes,
        benchmark=benchmark if benchmark_available else None,
    )
    if not benchmark_available:
        advisory = f"{advisory}\n\n{NO_BENCHMARK_NOTICE.get(lang, NO_BENCHMARK_NOTICE['english'])}"

    _send(beneficiary, advisory, lang, from_voice)


def _handle_dpr_generation(db, beneficiary, context: Dict[str, Any]):
    """Compile Detailed Project Report PDF, upload to Cloudflare R2, and deliver link."""
    fin = context["financial_structure"]
    cashflows = context.get("cashflows", {})
    trade = context["trade"]
    lang = beneficiary.preferred_language or "kannada"

    # Find existing DRAFT proposal or create a new row
    from app.db.models import EnterpriseProposal
    proposal = (
        db.query(EnterpriseProposal)
        .filter(EnterpriseProposal.beneficiary_id == beneficiary.id)
        .order_by(EnterpriseProposal.created_at.desc())
        .first()
    )
    proposal_fields = {
        "business_trade": trade,
        "scheme_tier": fin["scheme"],
        "project_cost": float(context["project_cost"]),
        "sanctioned_loan": fin.get("loan") or 0.0,
        "beneficiary_margin": fin.get("margin") or 0.0,
        "monthly_emi": fin.get("emi") or 0.0,
        "projected_dscr": None,
    }
    if proposal and proposal.status == "DRAFT":
        for key, value in proposal_fields.items():
            setattr(proposal, key, value)
        db.commit()
    else:
        proposal = crud.create_proposal(db, {"beneficiary_id": beneficiary.id, "status": "DRAFT", "dpr_pdf_url": None, **proposal_fields})

    contact_id = beneficiary.telegram_chat_id if getattr(beneficiary, "primary_channel", "") == "telegram" else beneficiary.whatsapp_number

    # Applicant details exactly as stated and confirmed in the conversation (never defaulted)
    profile = intake.profile_for_records(context)
    beneficiary_dict = {
        "id": beneficiary.id,
        "full_name": profile.get("full_name"),
        "whatsapp_number": contact_id,
        "district": context.get("district"),
        "state": context.get("state"),
        "preferred_language": beneficiary.preferred_language,
        "annual_family_income": profile.get("annual_family_income"),
        "profile": profile,
    }

    proposal_dict = {
        "id": proposal.id,
        "business_trade": proposal.business_trade,
        "scheme_tier": proposal.scheme_tier,
        "project_cost": float(proposal.project_cost),
        "sanctioned_loan": float(proposal.sanctioned_loan),
        "beneficiary_margin": float(proposal.beneficiary_margin),
        "monthly_emi": float(proposal.monthly_emi),
        "projected_dscr": float(proposal.projected_dscr) if proposal.projected_dscr is not None else None,
        "status": proposal.status,
        "multi_schemes": context.get("multi_schemes") or {},
        "financial_structure": fin,
        "cashflows": context.get("cashflows") or {},
        "nabard_benchmark": context.get("nabard_benchmark") or "",
        "district": context.get("district"),
        "state": context.get("state"),
    }

    # Generate PDF
    pdf_filename = f"DPR_{trade.replace(' ', '_')}_{str(proposal.id)[:8]}.pdf"
    pdf_bytes = generate_dpr_pdf(proposal_dict, beneficiary_dict)

    # Upload to Cloudflare R2 / local fallback
    public_url = upload_dpr_pdf(pdf_bytes, pdf_filename)
    proposal.dpr_pdf_url = public_url
    from datetime import datetime, timezone
    crud.save_proposal_snapshot(db, proposal.id, {"dpr_generated_at": datetime.now(timezone.utc).isoformat()})
    beneficiary.conversation_state = "SUBMITTED"
    db.commit()

    channel_name = "Telegram" if getattr(beneficiary, "primary_channel", "") == "telegram" else "WhatsApp"

    # Multilingual caption and delivery confirmation
    if lang == "kannada":
        caption = f"📄 ನಿಮ್ಮ {trade} ಉದ್ಯಮದ ಬ್ಯಾಂಕ್ ಯೋಜನಾ ವರದಿ (DPR). ಉಲ್ಲೇಖ: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 ಅಭಿನಂದನೆಗಳು! ನಿಮ್ಮ ವಿವರವಾದ ಯೋಜನಾ ವರದಿ (DPR PDF) ಸಿದ್ಧವಾಗಿದ್ದು, ಮೇಲೆ ಕಳುಹಿಸಲಾಗಿದೆ!\n\n"
            f"📋 *ಉಲ್ಲೇಖ ಸಂಖ್ಯೆ (Ref ID)*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *ಸ್ಥಿತಿ*: ಪರಿಶೀಲನೆಗಾಗಿ ರಾಜ್ಯ ವಾಹಕ ಏಜೆನ್ಸಿ (SCA) ಗೆ ಸಲ್ಲಿಸಲಾಗಿದೆ.\n\n"
            f"ನಿಗಮದ ಅಧಿಕಾರಿಗಳು ನಿಮ್ಮ ಸ್ಥಳ ಮತ್ತು ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿದ ನಂತರ, ನಿಮ್ಮ ಸಾಲ ಮಂಜೂರಾತಿ ಅಧಿಸೂಚನೆಯು ನೇರವಾಗಿ ಇಲ್ಲಿಯೇ {channel_name} ನಲ್ಲಿ ತಲುಪಲಿದೆ."
        )
    elif lang == "hindi":
        caption = f"📄 आपके {trade} व्यवसाय की बैंक रिपोर्ट (DPR). संदर्भ: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 बधाई! आपकी विस्तृत परियोजना रिपोर्ट (DPR PDF) तैयार होकर ऊपर भेजी जा चुकी है!\n\n"
            f"📋 *संदर्भ संख्या (Ref ID)*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *स्थिति*: सत्यापन हेतु राज्य एजेंसी को प्रेषित।\n\n"
            f"सत्यापन के पश्चात आपकी ऋण स्वीकृति की सूचना सीधे यहीं {channel_name} पर प्राप्त होगी।"
        )
    elif lang == "telugu":
        caption = f"📄 మీ {trade} వ్యాపారానికి బ్యాంక్ ప్రాజెక్ట్ నివేదిక (DPR). రిఫరెన్స్: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 అభినందనలు! మీ సమగ్ర ప్రాజెక్ట్ నివేదిక (DPR PDF) సిద్ధమైంది, పైన పంపబడింది!\n\n"
            f"📋 *రిఫరెన్స్ నంబర్ (Ref ID)*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *స్థితి*: క్షేత్రస్థాయి జియో-ధృవీకరణ కోసం రాష్ట్ర ఏజెన్సీ (SCA)కి సమర్పించబడింది.\n\n"
            f"అధికారులు పరిశీలించిన తర్వాత మీ రుణ మంజూరు నోటిఫికేషన్ నేరుగా ఇక్కడే {channel_name} లో అందుతుంది."
        )
    elif lang == "marathi":
        caption = f"📄 आपल्या {trade} व्यवसायाचा बँक प्रकल्प अहवाल (DPR). संदर्भ: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 अभिनंदन! आपला सविस्तर प्रकल्प अहवाल (DPR PDF) तयार झाला असून वर पाठवला आहे!\n\n"
            f"📋 *संदर्भ क्रमांक (Ref ID)*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *स्थिती*: प्रत्यक्ष पडताळणीसाठी राज्य एजन्सीकडे (SCA) सादर केला आहे.\n\n"
            f"पडताळणी पूर्ण झाल्यावर आपल्या कर्ज मंजुरीची सूचना थेट येथेच {channel_name} वर मिळेल."
        )
    else:
        caption = f"📄 Detailed Project Report (DPR) for your {trade}. Ref: DPR-{str(proposal.id)[:8].upper()}"
        confirmation_msg = (
            f"🎉 Your Detailed Project Report (DPR) has been generated and sent above!\n\n"
            f"📋 *Reference ID*: DPR-{str(proposal.id)[:8].upper()}\n"
            f"🏛️ *Status*: Submitted to State Channelizing Agency (SCA) for field geo-verification.\n\n"
            f"An SCA field officer will visit to verify your margin money and location, after which your sanction notification will arrive right here on {channel_name}."
        )

    # Deliver document directly with raw PDF bytes for zero-tunnel Telegram delivery
    send_channel_document(
        beneficiary,
        document_url=public_url,
        filename=pdf_filename,
        caption=caption,
        document_bytes=pdf_bytes
    )

    send_channel_text(beneficiary, confirmation_msg)

