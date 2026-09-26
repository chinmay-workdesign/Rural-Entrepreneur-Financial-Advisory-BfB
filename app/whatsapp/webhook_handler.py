import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, Response, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.db import crud
from app import bot_control
from app.dialogue.conversation_state import process_user_query, process_voice_query

logger = logging.getLogger("whatsapp_webhook")

router = APIRouter()

def verify_signature(payload: bytes, signature_header: str) -> bool:
    """Validate X-Hub-Signature-256 HMAC against WHATSAPP_APP_SECRET."""
    if not settings.WHATSAPP_APP_SECRET:
        # In local dev / test if app secret not configured, bypass
        return True
    if not signature_header:
        return False
    parts = signature_header.split("sha256=")
    if len(parts) != 2:
        return False
    expected_hash = parts[1]
    computed_hash = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_hash, computed_hash)

@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """Meta webhook subscription verification endpoint."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.info(f"Webhook verification request: mode={mode}, token_match={token == settings.WHATSAPP_VERIFY_TOKEN}")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return Response(content="Verification failed", status_code=403)

@router.post("/webhook/whatsapp")
async def handle_whatsapp_message(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Handle inbound WhatsApp messages from Evolution API and Meta Webhook.
    Supports:
    1. Evolution API (data.key.remoteJid, data.message, etc.)
    2. Meta Cloud API (entry[].changes[].value.messages[])
    """
    body_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # Security check: Validate signature if secret provided
    if settings.WHATSAPP_APP_SECRET and not verify_signature(body_bytes, signature or ""):
        logger.warning("Rejected webhook: Invalid X-Hub-Signature-256")
        return Response(content="Invalid signature", status_code=403)

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to decode JSON payload: {e}")
        return Response(content="Invalid JSON", status_code=400)

    # 1. Check if Meta Cloud API format
    if "entry" in payload:
        try:
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        msg_id = msg.get("id")
                        from_phone = msg.get("from")
                        msg_type = msg.get("type")

                        if msg_id:
                            if crud.is_webhook_processed(db, msg_id):
                                logger.info(f"Duplicate webhook message {msg_id} ignored.")
                                continue
                            crud.record_webhook_event(db, msg_id, from_phone, msg_type)

                        # Bot stopped, or message sent while it was offline: not answered, not queued
                        if not bot_control.accept_message("whatsapp", msg.get("timestamp")):
                            continue

                        if msg_type == "text":
                            body = msg.get("text", {}).get("body", "").strip()
                            background_tasks.add_task(process_user_query, from_phone, body)
                        elif msg_type == "audio":
                            media_id = msg.get("audio", {}).get("id")
                            background_tasks.add_task(process_voice_query, from_phone, media_id)
                        elif msg_type == "interactive":
                            int_msg = msg.get("interactive", {})
                            btn_reply = int_msg.get("button_reply", {}).get("id") or int_msg.get("button_reply", {}).get("title")
                            list_reply = int_msg.get("list_reply", {}).get("id") or int_msg.get("list_reply", {}).get("title")
                            body = btn_reply or list_reply or ""
                            background_tasks.add_task(process_user_query, from_phone, str(body).strip())
            return Response(content="EVENT_RECEIVED", status_code=200)
        except Exception as e:
            logger.error(f"Error parsing Meta WhatsApp payload: {e}", exc_info=True)
            return Response(content="EVENT_RECEIVED", status_code=200)

    # 2. Handle Evolution API format
    data = payload.get("data", {})
    key = data.get("key", {})
    msg_id = key.get("id")
    remote_jid = key.get("remoteJid")
    if not remote_jid:
        logger.warning("Missing remoteJid or valid structure in payload")
        return Response(content="Missing remoteJid", status_code=400)

    # Ignore messages sent by the bot itself
    if key.get("fromMe"):
        logger.info(f"Ignoring outbound message {msg_id} from {remote_jid}")
        return Response(content="EVENT_RECEIVED", status_code=200)

    # Ignore group chats
    if remote_jid.endswith("@g.us"):
        logger.info(f"Ignoring group message {msg_id} from {remote_jid}")
        return Response(content="EVENT_RECEIVED", status_code=200)

    # Private chat phone number (strip domain)
    recipient_phone = remote_jid.split("@", 1)[0]

    # Idempotency
    if msg_id:
        if crud.is_webhook_processed(db, msg_id):
            logger.info(f"Duplicate webhook message {msg_id} ignored.")
            return Response(content="EVENT_RECEIVED", status_code=200)
        crud.record_webhook_event(db, msg_id, recipient_phone, "evolution")

    # Bot stopped, or message sent while it was offline (Evolution redelivers after an outage): not answered
    if not bot_control.accept_message("whatsapp", data.get("messageTimestamp")):
        return Response(content="EVENT_RECEIVED", status_code=200)

    message = data.get("message", {})
    # Log raw message for debugging
    logger.debug(f"Raw Evolution message payload: {message}")
    # Determine message content based on Evolution payload structure
    if "conversation" in message:
        body = message["conversation"].strip()
        background_tasks.add_task(process_user_query, recipient_phone, body)
    elif "extendedTextMessage" in message:
        ext_msg = message.get("extendedTextMessage", {})
        if isinstance(ext_msg, dict):
            body = ext_msg.get("text", "").strip()
        else:
            body = str(ext_msg).strip()
        background_tasks.add_task(process_user_query, recipient_phone, body)
    elif "buttonsResponseMessage" in message:
        btn_resp = message.get("buttonsResponseMessage", {})
        body = btn_resp.get("selectedButtonId") or btn_resp.get("selectedDisplayText") or ""
        background_tasks.add_task(process_user_query, recipient_phone, str(body).strip())
    elif "templateButtonReplyMessage" in message:
        btn_resp = message.get("templateButtonReplyMessage", {})
        body = btn_resp.get("selectedId") or btn_resp.get("selectedDisplayText") or ""
        background_tasks.add_task(process_user_query, recipient_phone, str(body).strip())
    elif "listResponseMessage" in message:
        list_resp = message.get("listResponseMessage", {})
        single_select = list_resp.get("singleSelectReply", {})
        body = single_select.get("selectedRowId") or list_resp.get("title") or ""
        background_tasks.add_task(process_user_query, recipient_phone, str(body).strip())
    elif "interactiveResponseMessage" in message:
        int_resp = message.get("interactiveResponseMessage", {})
        body = ""
        params = int_resp.get("nativeFlowResponseMessage", {}).get("paramsJson")
        if params:
            try:
                import json
                parsed = json.loads(params)
                body = parsed.get("id") or str(parsed)
            except Exception:
                body = str(params)
        background_tasks.add_task(process_user_query, recipient_phone, str(body).strip())
    elif "pollUpdateMessage" in message or "pollCreationMessage" in message:
        poll_msg = message.get("pollUpdateMessage", message.get("pollCreationMessage", {}))
        votes = poll_msg.get("votes", [])
        body = ""
        if votes and isinstance(votes, list):
            body = votes[0].get("optionName", "")
        if not body:
            body = poll_msg.get("name", "")
        background_tasks.add_task(process_user_query, recipient_phone, str(body).strip())
    elif "audioMessage" in message:
        # Pass the full message data structure for Evolution getBase64FromMediaMessage
        background_tasks.add_task(process_voice_query, recipient_phone, data if data else msg_id)
    else:
        logger.info(f"Unhandled Evolution message structure: {message}")

    return Response(content="EVENT_RECEIVED", status_code=200)
