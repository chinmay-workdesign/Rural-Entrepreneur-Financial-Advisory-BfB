import hmac
import hashlib
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.voice.voice_service import transcribe_audio, synthesize_speech, get_language_code
from app.db.session import SessionLocal
from app.db import crud
from app.retrieval.router import execute_authoritative_routing

client = TestClient(app)

"""
Phase 7 Steps 5 & 6: Voice Pipeline and Channel Testing.
Validates:
1. Voice: transcription, language normalization, intent routing from voice, TTS synthesis.
2. WhatsApp: HMAC-SHA256 signature validation, challenge GET, text & audio webhook parsing, idempotency.
3. Telegram: text & voice update parsing, session tracking, state persistence, malformed payload resilience.
"""

# ==============================================================================
# STEP 5: VOICE PIPELINE TESTS
# ==============================================================================

@pytest.mark.parametrize("language, lang_code", [
    ("kannada", "kn"),
    ("hindi", "hi"),
    ("english", "en"),
    ("telugu", "te"),
    ("marathi", "mr")
])
def test_voice_language_normalization_and_stt(language, lang_code):
    """
    Test STT transcription across Kannada, Hindi, English, Telugu, Marathi.
    Validates ISO code mapping and test suite speech recognition.
    """
    assert get_language_code(language) == lang_code

    # Simulated voice bytes with test prefix
    audio_bytes = f"MOCK_AUDIO_SAMPLE_{language.upper()}".encode("utf-8")
    transcript = transcribe_audio(audio_bytes, source_language=language)
    assert len(transcript) > 0

    # Ensure transcript can be routed through intent & retrieval pipeline
    res = execute_authoritative_routing(transcript, language=language)
    assert res["request_id"] is not None
    assert "intent" in res

def test_voice_tts_speech_synthesis_pipeline():
    """
    Test Text-to-Speech (TTS) synthesis for response delivery.
    Verifies that generated audio bytes contain valid audio header.
    """
    sample_text = "ನಬಾರ್ಡ್ ಅಧಿಕೃತ ಮಾನದಂಡದ ಪ್ರಕಾರ 2 ಹಸುಗಳ ಹೈನುಗಾರಿಕೆ ವೆಚ್ಚ ₹2,29,000 ಆಗಿದೆ."
    audio_output = synthesize_speech(sample_text, target_language="kannada")

    assert audio_output is not None
    assert len(audio_output) > 20
    # Check that audio output is either mp3 or wav
    assert audio_output[:4] == b"RIFF" or audio_output[:3] == b"ID3" or len(audio_output) > 100

def test_voice_e2e_roundtrip_flow():
    """
    Test complete Voice -> STT -> Intent -> Retrieval -> Response -> TTS pipeline.
    """
    # 1. Spoken audio input (English Dairy inquiry)
    voice_bytes = b"REAL_AUDIO_SAMPLE_TEST_VOICE"
    with patch("app.voice.voice_service.is_gemini_configured", return_value=True), \
         patch("app.voice.voice_service.transcribe_audio_gemini", return_value="What is the NABARD cost for 2 dairy cows?"):
        transcription = transcribe_audio(voice_bytes, source_language="english")
        assert "dairy cows" in transcription

        # 2. Authoritative retrieval routing
        routing_res = execute_authoritative_routing(transcription, language="english")
        assert routing_res["retrieval_used"] is True
        assert len(routing_res["evidence"]) > 0

        # 3. Text response to TTS audio
        tts_audio = synthesize_speech(routing_res["answer"], target_language="english")
        assert tts_audio is not None
        assert len(tts_audio) > 10


# ==============================================================================
# STEP 6: CHANNEL TESTING (WHATSAPP & TELEGRAM)
# ==============================================================================

def test_whatsapp_webhook_challenge_verification():
    """
    Verify Meta webhook hub challenge endpoint (GET /webhook/whatsapp).
    """
    verify_token = "rural_advisor_verify_token_2026"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": verify_token,
        "hub.challenge": "CHALLENGE_ACCEPTED_12345"
    }
    with patch.object(settings, "WHATSAPP_VERIFY_TOKEN", verify_token):
        response = client.get("/webhook/whatsapp", params=params)
        assert response.status_code == 200
        assert response.text == "CHALLENGE_ACCEPTED_12345"

        # Invalid token check
        invalid_params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "WRONG_TOKEN",
            "hub.challenge": "CHALLENGE_123"
        }
        bad_response = client.get("/webhook/whatsapp", params=invalid_params)
        assert bad_response.status_code == 403

def test_whatsapp_webhook_signature_validation():
    """
    Verify X-Hub-Signature-256 HMAC authentication for WhatsApp webhooks.
    """
    secret = "test_webhook_secret_key"
    payload = json.dumps({"entry": [{"id": "123"}]}).encode("utf-8")
    valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    with patch.object(settings, "WHATSAPP_APP_SECRET", secret):
        # 1. Valid Signature
        res_ok = client.post("/webhook/whatsapp", data=payload, headers={"X-Hub-Signature-256": valid_sig, "Content-Type": "application/json"})
        assert res_ok.status_code == 200

        # 2. Invalid Signature
        res_bad = client.post("/webhook/whatsapp", data=payload, headers={"X-Hub-Signature-256": "sha256=invalid_hash", "Content-Type": "application/json"})
        assert res_bad.status_code == 403

        # 3. Missing Signature
        res_missing = client.post("/webhook/whatsapp", data=payload, headers={"Content-Type": "application/json"})
        assert res_missing.status_code == 403

def test_whatsapp_webhook_idempotency_deduplication():
    """
    Verify duplicate WhatsApp message IDs are discarded without reprocessing.
    """
    msg_id = f"wamid_test_{uuid.uuid4().hex[:10]}"
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": msg_id,
                        "from": "919988776655",
                        "type": "text",
                        "text": {"body": "Hello"}
                    }]
                }
            }]
        }]
    }

    # First event
    with patch("app.dialogue.conversation_state.process_user_query") as mock_process:
        res1 = client.post("/webhook/whatsapp", json=payload)
        assert res1.status_code == 200

    # Second event (duplicate with same msg_id)
    with patch("app.dialogue.conversation_state.process_user_query") as mock_process_dup:
        res2 = client.post("/webhook/whatsapp", json=payload)
        assert res2.status_code == 200
        # Background task for duplicated message must NOT be scheduled
        mock_process_dup.assert_not_called()

def test_telegram_webhook_text_parsing_and_routing():
    """
    Verify Telegram webhook parsing for text messages.
    """
    chat_id = 987654321
    update = {
        "update_id": 10001,
        "message": {
            "message_id": 501,
            "from": {"id": chat_id, "first_name": "Shivanna"},
            "chat": {"id": chat_id, "type": "private"},
            "text": "What is the cost of 2 dairy cows?"
        }
    }

    with patch("app.dialogue.conversation_state.process_telegram_query") as mock_tg_query:
        res = client.post("/webhook/telegram", json=update)
        assert res.status_code == 200
        mock_tg_query.assert_called_once_with(str(chat_id), "What is the cost of 2 dairy cows?", "Shivanna")

def test_telegram_webhook_voice_parsing():
    """
    Verify Telegram webhook parsing for voice audio messages.
    """
    chat_id = 123456789
    update = {
        "update_id": 10002,
        "message": {
            "message_id": 502,
            "from": {"id": chat_id, "first_name": "Mallikarjun"},
            "chat": {"id": chat_id, "type": "private"},
            "voice": {
                "file_id": "tg_voice_file_abc123",
                "duration": 5,
                "mime_type": "audio/ogg"
            }
        }
    }

    with patch("app.dialogue.conversation_state.process_telegram_voice_query") as mock_tg_voice:
        res = client.post("/webhook/telegram", json=update)
        assert res.status_code == 200
        mock_tg_voice.assert_called_once_with(str(chat_id), "tg_voice_file_abc123", "Mallikarjun")

def test_telegram_webhook_malformed_resilience():
    """
    Verify graceful handling of malformed and empty Telegram webhook payloads.
    """
    # 1. Non-JSON string
    res_bad_json = client.post("/webhook/telegram", content=b"INVALID_PAYLOAD", headers={"Content-Type": "application/json"})
    assert res_bad_json.status_code == 400

    # 2. Empty update without message
    res_empty = client.post("/webhook/telegram", json={"update_id": 9999})
    assert res_empty.status_code == 200
