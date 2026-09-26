"""
WhatsApp through Evolution API, alongside Telegram.

1. Evolution webhook: text, button replies and voice notes reach the conversation engine
2. Evolution webhook ignores the bot's own messages, group chats and duplicate deliveries
3. A WhatsApp applicant gets the language menu as buttons, and a button tap sets the language
4. A full WhatsApp conversation reaches advice and a DPR, independently of a Telegram conversation
5. WhatsApp voice notes keep the chosen language and are answered as voice (from_voice)
"""
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.db import crud
from app.db.session import SessionLocal
from app.dialogue import conversation_state as cs
from app.main import app
from tests.intake_helpers import complete_intake

client = TestClient(app)


def _phone() -> str:
    return f"91{uuid.uuid4().int % 10**10:010d}"


def _evolution(phone: str, message: dict, msg_id: str = None, from_me: bool = False, group: bool = False) -> dict:
    jid = f"{phone}@g.us" if group else f"{phone}@s.whatsapp.net"
    return {"event": "messages.upsert", "instance": "kirana-bot",
            "data": {"key": {"remoteJid": jid, "fromMe": from_me, "id": msg_id or uuid.uuid4().hex.upper()},
                     "message": message}}


# 1. Messages reach the engine
def test_evolution_text_button_and_voice_are_routed():
    phone = _phone()
    with patch("app.whatsapp.webhook_handler.process_user_query") as text, \
         patch("app.whatsapp.webhook_handler.process_voice_query") as voice:
        assert client.post("/webhook/whatsapp", json=_evolution(phone, {"conversation": "dairy in Belagavi"})).status_code == 200
        client.post("/webhook/whatsapp", json=_evolution(phone, {"extendedTextMessage": {"text": "2 lakh"}}))
        client.post("/webhook/whatsapp", json=_evolution(phone, {"buttonsResponseMessage": {"selectedButtonId": "lang_3"}}))
        client.post("/webhook/whatsapp", json=_evolution(phone, {"audioMessage": {"mimetype": "audio/ogg; codecs=opus"}}))
    assert [c.args for c in text.call_args_list] == [(phone, "dairy in Belagavi"), (phone, "2 lakh"), (phone, "lang_3")]
    assert voice.call_count == 1 and voice.call_args.args[0] == phone


# 2. Own messages, groups and duplicates are ignored
def test_evolution_ignores_own_group_and_duplicate_messages():
    phone = _phone()
    with patch("app.whatsapp.webhook_handler.process_user_query") as text:
        client.post("/webhook/whatsapp", json=_evolution(phone, {"conversation": "echo"}, from_me=True))
        client.post("/webhook/whatsapp", json=_evolution(phone, {"conversation": "group"}, group=True))
        dup = _evolution(phone, {"conversation": "once"}, msg_id="DUPLICATE-ID-" + uuid.uuid4().hex)
        client.post("/webhook/whatsapp", json=dup)
        client.post("/webhook/whatsapp", json=dup)
    assert [c.args for c in text.call_args_list] == [(phone, "once")]


# 3. Language menu as buttons; a tap sets the language
def test_whatsapp_language_menu_buttons_and_tap():
    phone = _phone()
    with patch("app.dialogue.conversation_state.send_whatsapp_buttons") as buttons, \
         patch("app.dialogue.conversation_state.send_whatsapp_text"):
        cs.process_user_query(phone, "Hi")
        assert buttons.called and [b["id"] for b in buttons.call_args.kwargs["buttons"]][:2] == ["lang_1", "lang_2"]
        cs.process_user_query(phone, "lang_3")
    db = SessionLocal()
    try:
        b = crud.get_or_create_beneficiary(db, phone)
        assert (b.preferred_language, b.conversation_state, b.primary_channel) == ("kannada", "COLLECTING", "whatsapp")
    finally:
        db.close()


# 4. Full WhatsApp conversation, independent of Telegram
def test_whatsapp_and_telegram_conversations_run_side_by_side():
    phone, chat = _phone(), f"tg_{uuid.uuid4().hex[:10]}"
    with patch("app.dialogue.conversation_state.send_whatsapp_text") as wa_text, \
         patch("app.dialogue.conversation_state.send_whatsapp_buttons"), \
         patch("app.dialogue.conversation_state.send_whatsapp_document") as wa_doc, \
         patch("app.dialogue.conversation_state.send_telegram_text") as tg_text, \
         patch("app.dialogue.conversation_state.send_telegram_document") as tg_doc:
        cs.process_user_query(phone, "Hi")
        cs.process_user_query(phone, "lang_1")
        cs.process_telegram_query(chat, "/start")
        cs.process_telegram_query(chat, "3. ಕನ್ನಡ (Kannada)")

        cs.process_user_query(phone, "dairy in Belagavi, project cost 2 lakh")
        complete_intake(lambda t: cs.process_user_query(phone, t), lambda db: crud.get_or_create_beneficiary(db, phone))
        cs.process_telegram_query(chat, "ಬೆಳಗಾವಿಯಲ್ಲಿ ಹೈನುಗಾರಿಕೆ, ಒಟ್ಟು ವೆಚ್ಚ 2 ಲಕ್ಷ")
        complete_intake(lambda t: cs.process_telegram_query(chat, t), lambda db: crud.get_or_create_telegram_beneficiary(db, chat))

        assert any("GENERATE DPR" in c.args[1] for c in wa_text.call_args_list)
        cs.process_user_query(phone, "GENERATE DPR")
        cs.process_telegram_query(chat, "GENERATE DPR")

    assert wa_doc.called and wa_doc.call_args.kwargs["recipient_phone"] == phone
    assert wa_doc.call_args.kwargs["document_bytes"]  # PDF sent directly, not only a local link
    assert tg_doc.called and tg_doc.call_args.args[0] == chat
    # Telegram replies stayed in Kannada, WhatsApp replies in English
    assert any("ಸಾಲ" in c.args[1] for c in tg_text.call_args_list)
    assert not any("ಸಾಲ" in c.args[1] for c in wa_text.call_args_list)
    db = SessionLocal()
    try:
        wa = crud.get_or_create_beneficiary(db, phone)
        tg = crud.get_or_create_telegram_beneficiary(db, chat)
        assert wa.id != tg.id and wa.conversation_state == tg.conversation_state == "SUBMITTED"
    finally:
        db.close()


# 5. Voice notes on WhatsApp
def test_whatsapp_voice_note_keeps_language_and_is_answered_as_voice():
    phone = _phone()
    db = SessionLocal()
    try:
        b = crud.get_or_create_beneficiary(db, phone, default_lang="marathi")
    finally:
        db.close()
    with patch("app.dialogue.conversation_state.download_whatsapp_media", return_value=b"OggS-audio"), \
         patch("app.dialogue.conversation_state.transcribe_audio", return_value="maza vay 28 ahe") as stt, \
         patch("app.dialogue.conversation_state.process_user_query") as handle:
        cs.process_voice_query(phone, {"key": {"id": "ABC"}, "message": {"audioMessage": {}}})
    assert stt.call_args.kwargs["source_language"] == "marathi"
    assert handle.call_args.args == (phone, "maza vay 28 ahe") and handle.call_args.kwargs["from_voice"] is True
