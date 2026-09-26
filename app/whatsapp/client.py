import os
import base64
import logging
import requests
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger("whatsapp_client")

# Determine which provider to use based on configuration
def _use_evolution() -> bool:
    return bool(settings.EVOLUTION_API_URL and settings.EVOLUTION_INSTANCE_NAME)

def _evolution_headers() -> Dict[str, str]:
    return {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }

def _meta_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

def _evolution_base_url() -> str:
    base = settings.EVOLUTION_API_URL.rstrip('/')
    return f"{base}/message/sendText/{settings.EVOLUTION_INSTANCE_NAME}"

def _meta_base_url() -> str:
    return f"https://graph.facebook.com/v21.0/{settings.PHONE_NUMBER_ID}/messages"

def _current_base_url() -> str:
    return _evolution_base_url() if _use_evolution() else _meta_base_url()

def _current_headers() -> Dict[str, str]:
    return _evolution_headers() if _use_evolution() else _meta_headers()

def send_whatsapp_text(recipient_phone: str, text_body: str) -> Dict[str, Any]:
    """Send a text message via Evolution API if configured, otherwise fall back to Meta API.
    Mock mode is used when required credentials are missing for the selected provider.
    """
    # Mock handling
    if _use_evolution():
        if not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE_NAME:
            logger.info(f"[MOCK EVOLUTION WHATSAPP] To: {recipient_phone} | Message: {text_body}")
            return {"mock": True, "status": "sent", "to": recipient_phone, "body": text_body}
    else:
        if not settings.WHATSAPP_ACCESS_TOKEN or not settings.PHONE_NUMBER_ID:
            logger.info(f"[MOCK META WHATSAPP] To: {recipient_phone} | Message: {text_body}")
            return {"mock": True, "status": "sent", "to": recipient_phone, "body": text_body}

    url = _current_base_url()
    if _use_evolution():
        data = {
            "number": recipient_phone,
            "text": text_body
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {"preview_url": True, "body": text_body},
        }
    try:
        logger.debug(f"Sending WhatsApp text request to {url} with payload: {data}")
        response = requests.post(url, json=data, headers=_current_headers(), timeout=10)
        response.raise_for_status()
        logger.info(f"Sent WhatsApp text to {recipient_phone}, status: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        # No fallback: report Evolution send failure directly
        logger.error(f"Failed to send WhatsApp text to {recipient_phone}: {e}")
        return {"error": str(e), "success": False}

def send_whatsapp_buttons(
    recipient_phone: str,
    title: str,
    buttons: list,
    description: Optional[str] = None,
    footer: Optional[str] = None,
) -> Dict[str, Any]:
    """Send interactive reply buttons via Evolution API."""
    if _use_evolution():
        if not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE_NAME:
            logger.info(f"[MOCK EVOLUTION BUTTONS] To: {recipient_phone} | Buttons: {buttons}")
            return {"mock": True, "status": "sent", "to": recipient_phone}

        base = settings.EVOLUTION_API_URL.rstrip('/')
        url = f"{base}/message/sendButtons/{settings.EVOLUTION_INSTANCE_NAME}"

        # Format buttons for Evolution API v2 (Baileys)
        # Evolution accepts: [{"type": "reply", "displayText": "...", "id": "..."}, ...]
        formatted_buttons = []
        for btn in buttons:
            btn_id = btn.get("id") or btn.get("displayText") or "btn"
            btn_text = btn.get("displayText") or btn.get("title") or btn.get("text") or "Button"
            formatted_buttons.append({
                "type": "reply",
                "displayText": btn_text,
                "id": btn_id
            })

        data = {
            "number": recipient_phone,
            "title": title,
            "description": description or title,
            "footer": footer or "Rural Micro-Enterprise Advisor",
            "buttons": formatted_buttons
        }
        try:
            logger.debug(f"Sending WhatsApp buttons to {url}: {data}")
            response = requests.post(url, json=data, headers=_current_headers(), timeout=12)
            response.raise_for_status()
            logger.info(f"Sent WhatsApp buttons to {recipient_phone}, status: {response.status_code}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to send WhatsApp buttons to {recipient_phone}: {e}. Falling back to text.")
            return send_whatsapp_text(recipient_phone, f"{description or title}\n\n" + "\n".join([f"👉 {b['displayText']}" for b in formatted_buttons]))
    else:
        # Fallback to plain text
        return send_whatsapp_text(recipient_phone, f"{title}\n\n" + "\n".join([f"👉 {b.get('displayText', 'Option')}" for b in buttons]))

def send_whatsapp_list(
    recipient_phone: str,
    title: str,
    description: str,
    button_text: str,
    sections: list,
    footer: Optional[str] = None,
) -> Dict[str, Any]:
    """Send an interactive list message via Evolution API."""
    if _use_evolution():
        if not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE_NAME:
            logger.info(f"[MOCK EVOLUTION LIST] To: {recipient_phone} | Sections: {sections}")
            return {"mock": True, "status": "sent", "to": recipient_phone}

        base = settings.EVOLUTION_API_URL.rstrip('/')
        url = f"{base}/message/sendList/{settings.EVOLUTION_INSTANCE_NAME}"

        data = {
            "number": recipient_phone,
            "title": title,
            "description": description,
            "buttonText": button_text,
            "footerText": footer or "Rural Micro-Enterprise Advisor",
            "sections": sections
        }
        try:
            logger.debug(f"Sending WhatsApp list to {url}: {data}")
            response = requests.post(url, json=data, headers=_current_headers(), timeout=12)
            response.raise_for_status()
            logger.info(f"Sent WhatsApp list to {recipient_phone}, status: {response.status_code}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to send WhatsApp list to {recipient_phone}: {e}. Falling back to text.")
            text_lines = [f"*{title}*", description, ""]
            for sec in sections:
                for row in sec.get("rows", []):
                    text_lines.append(f"• *{row.get('title')}*: {row.get('description', '')}")
            return send_whatsapp_text(recipient_phone, "\n".join(text_lines))
def send_whatsapp_poll(
    recipient_phone: str,
    name: str,
    values: list,
    selectable_count: int = 1,
) -> Dict[str, Any]:
    """Send an interactive selectable poll message via Evolution API."""
    if _use_evolution():
        if not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE_NAME:
            logger.info(f"[MOCK EVOLUTION POLL] To: {recipient_phone} | Values: {values}")
            return {"mock": True, "status": "sent", "to": recipient_phone}

        base = settings.EVOLUTION_API_URL.rstrip('/')
        url = f"{base}/message/sendPoll/{settings.EVOLUTION_INSTANCE_NAME}"

        data = {
            "number": recipient_phone,
            "name": name,
            "selectableCount": selectable_count,
            "values": values
        }
        try:
            logger.debug(f"Sending WhatsApp poll to {url}: {data}")
            response = requests.post(url, json=data, headers=_current_headers(), timeout=12)
            response.raise_for_status()
            logger.info(f"Sent WhatsApp poll to {recipient_phone}, status: {response.status_code}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to send WhatsApp poll to {recipient_phone}: {e}. Falling back to text.")
            return send_whatsapp_text(recipient_phone, f"*{name}*\n\n" + "\n".join([f"• {v}" for v in values]))
    else:
        return send_whatsapp_text(recipient_phone, f"*{name}*\n\n" + "\n".join([f"• {v}" for v in values]))


def send_whatsapp_document(
    recipient_phone: str,
    document_url: str,
    filename: str,
    caption: str,
    document_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Send a document (e.g., DPR PDF) via Evolution API or Meta API."""
    if _use_evolution():
        if not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE_NAME:
            logger.info(
                f"[MOCK EVOLUTION WHATSAPP DOCUMENT] To: {recipient_phone} | URL: {document_url} | Filename: {filename} | Caption: {caption}"
            )
            return {"mock": True, "status": "sent", "to": recipient_phone, "document_url": document_url}
        
        base = settings.EVOLUTION_API_URL.rstrip('/')
        url = f"{base}/message/sendMedia/{settings.EVOLUTION_INSTANCE_NAME}"

        # If we have document bytes, convert to base64 for direct transmission
        if document_bytes:
            media_content = base64.b64encode(document_bytes).decode('utf-8')
        elif document_url and not document_url.startswith('/'):
            media_content = document_url
        else:
            # If local relative URL, try to read from disk if available
            local_path = os.path.join(os.getcwd(), document_url.lstrip('/'))
            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    media_content = base64.b64encode(f.read()).decode('utf-8')
            else:
                media_content = document_url

        data = {
            "number": recipient_phone,
            "mediatype": "document",
            "media": media_content,
            "fileName": filename,
            "caption": caption,
        }
    else:
        if not settings.WHATSAPP_ACCESS_TOKEN or not settings.PHONE_NUMBER_ID:
            logger.info(
                f"[MOCK META WHATSAPP DOCUMENT] To: {recipient_phone} | URL: {document_url} | Filename: {filename} | Caption: {caption}"
            )
            return {"mock": True, "status": "sent", "to": recipient_phone, "document_url": document_url}

        url = _meta_base_url()
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "document",
            "document": {"link": document_url, "filename": filename, "caption": caption},
        }

    try:
        response = requests.post(url, json=data, headers=_current_headers(), timeout=15)
        response.raise_for_status()
        logger.info(f"Sent WhatsApp document to {recipient_phone}: {filename}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send WhatsApp document to {recipient_phone}: {e}")
        return {"error": str(e), "success": False}

def send_whatsapp_voice(
    recipient_phone: str,
    voice_bytes: bytes,
    caption: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a voice note audio file via Evolution API."""
    if _use_evolution():
        if not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE_NAME:
            logger.info(f"[MOCK EVOLUTION WHATSAPP VOICE] To: {recipient_phone} | Bytes: {len(voice_bytes)}")
            return {"mock": True, "status": "sent", "to": recipient_phone}

        base = settings.EVOLUTION_API_URL.rstrip('/')
        url = f"{base}/message/sendWhatsAppAudio/{settings.EVOLUTION_INSTANCE_NAME}"
        audio_b64 = base64.b64encode(voice_bytes).decode('utf-8')
        data = {
            "number": recipient_phone,
            "audio": audio_b64,
        }
    else:
        logger.warning("Voice sending not configured for Meta provider directly.")
        return {"error": "Meta voice sending not configured", "success": False}

    try:
        response = requests.post(url, json=data, headers=_current_headers(), timeout=15)
        response.raise_for_status()
        logger.info(f"Sent WhatsApp voice note to {recipient_phone}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send WhatsApp voice note to {recipient_phone}: {e}")
        return {"error": str(e), "success": False}

def download_media_bytes(message_data: Any) -> Optional[bytes]:
    """Download binary media (e.g., audio) from Evolution API or Meta."""
    if _use_evolution():
        if not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE_NAME:
            logger.info("[MOCK EVOLUTION DOWNLOAD]")
            return b"MOCK_OGG_AUDIO_BYTES_FOR_TESTING"

        base = settings.EVOLUTION_API_URL.rstrip('/')
        url = f"{base}/chat/getBase64FromMediaMessage/{settings.EVOLUTION_INSTANCE_NAME}"

        # If message_data is the full data dict or message wrapper, construct message payload
        if isinstance(message_data, dict):
            payload = {
                "message": message_data,
                "convertToMp4": False,
            }
        else:
            # If string ID was passed, construct key wrapper
            payload = {
                "message": {
                    "key": {
                        "id": str(message_data)
                    }
                },
                "convertToMp4": False,
            }

        try:
            response = requests.post(url, json=payload, headers=_current_headers(), timeout=20)
            response.raise_for_status()
            res_json = response.json()
            b64_str = res_json.get("base64")
            if b64_str:
                return base64.b64decode(b64_str)
            logger.warning(f"No base64 in Evolution getBase64FromMediaMessage response: {res_json}")
            return None
        except requests.RequestException as e:
            logger.error(f"Failed to download media bytes from Evolution: {e}")
            return None
    else:
        if not settings.WHATSAPP_ACCESS_TOKEN:
            logger.info(f"[MOCK META DOWNLOAD] ID: {message_data}")
            return b"MOCK_OGG_AUDIO_BYTES_FOR_TESTING"

        media_url = f"https://graph.facebook.com/v21.0/{message_data}"
        try:
            res = requests.get(media_url, headers=_current_headers(), timeout=10)
            res.raise_for_status()
            download_url = res.json().get("url")
            if not download_url:
                return None
            media = requests.get(download_url, headers=_current_headers(), timeout=20)
            media.raise_for_status()
            return media.content
        except requests.RequestException as e:
            logger.error(f"Failed to download media bytes from Meta for {message_data}: {e}")
            return None

def fetch_media_url(media_id: str) -> Optional[str]:
    """Retrieve media URL (retained for backward compatibility)."""
    return f"{settings.EVOLUTION_API_URL.rstrip('/')}/chat/getBase64FromMediaMessage/{settings.EVOLUTION_INSTANCE_NAME}"
