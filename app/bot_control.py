"""
Start / stop the Telegram and WhatsApp bots from the officer dashboard.

A bot only answers messages sent while it was online. Anything sent while it was stopped (or while the app
or the WhatsApp gateway was down) is dropped instead of being answered later:
- Telegram: polling runs only while the bot is on; on restart, updates older than the restart are skipped.
- WhatsApp: the webhook ignores messages while the bot is off, and messages timestamped before it came
  online, or older than STALE_AFTER_SECONDS (redelivered after an outage), are ignored.
"""
import logging
import threading
import time
from datetime import timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import BotControl
from app.db.session import engine

logger = logging.getLogger("bot_control")

CHANNELS = ("telegram", "whatsapp")
STALE_AFTER_SECONDS = 120

_PROCESS_STARTED = time.time()
_lock = threading.Lock()
_telegram_thread: Optional[threading.Thread] = None
_telegram_stop = threading.Event()
_telegram_online_since: Optional[float] = None


# ---------- stored switch ----------
def _row(db: Session, channel: str) -> BotControl:
    row = db.get(BotControl, channel)
    if row is None:
        row = BotControl(channel=channel, enabled=True)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def is_enabled(channel: str) -> bool:
    with Session(engine) as db:
        return bool(_row(db, channel).enabled)


def _set_enabled(channel: str, enabled: bool, changed_by: Optional[str]) -> None:
    with Session(engine) as db:
        row = _row(db, channel)
        row.enabled = enabled
        row.changed_by = changed_by
        db.commit()


def _enabled_at(channel: str) -> Optional[float]:
    with Session(engine) as db:
        row = _row(db, channel)
        if not row.enabled or row.changed_at is None:
            return None
        ts = row.changed_at
        if ts.tzinfo is None:  # SQLite returns naive UTC
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.timestamp()


# ---------- message freshness ----------
def _as_epoch(value: Any) -> Optional[float]:
    """Telegram `date` / WhatsApp `messageTimestamp`: int, numeric string, or {"low": ...} from Baileys."""
    if isinstance(value, dict):
        value = value.get("low")
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _switch_online_since(channel: str) -> Optional[float]:
    """Webhook channels: online since the later of app start and the last time the bot was switched on."""
    if not is_enabled(channel):
        return None
    return max(_PROCESS_STARTED, _enabled_at(channel) or 0)


def accept_message(channel: str, sent_at: Any, via_polling: bool = False) -> bool:
    """True when the bot is on and the message was sent while it was online (so it should be answered)."""
    since = _telegram_online_since if via_polling else _switch_online_since(channel)
    if since is None:
        logger.info(f"{channel} bot is stopped: message ignored")
        return False
    sent = _as_epoch(sent_at)
    if sent is None:
        return True
    if sent < since - 1:
        logger.info(f"{channel}: message sent while the bot was offline ignored")
        return False
    if time.time() - sent > STALE_AFTER_SECONDS:
        logger.info(f"{channel}: message older than {STALE_AFTER_SECONDS}s (delayed delivery) ignored")
        return False
    return True


# ---------- Telegram polling thread ----------
def telegram_running() -> bool:
    return _telegram_thread is not None and _telegram_thread.is_alive() and not _telegram_stop.is_set()


def note_telegram_polling_started() -> None:
    """Polling run as a standalone script (not started from the app): it is online from now."""
    global _telegram_online_since
    with _lock:
        if _telegram_online_since is None and not _telegram_stop.is_set():
            _telegram_online_since = time.time()


def telegram_should_stop() -> bool:
    """Called by the polling loop; exits only if no restart was requested in the meantime."""
    global _telegram_thread
    with _lock:
        if _telegram_stop.is_set():
            _telegram_thread = None
            return True
        return False


def start_telegram(changed_by: Optional[str] = None) -> bool:
    """Start Telegram polling (and remember it is on). Returns False when no bot token is configured."""
    global _telegram_thread, _telegram_online_since
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    if changed_by is not None:
        _set_enabled("telegram", True, changed_by)
    with _lock:
        _telegram_online_since = time.time()
        _telegram_stop.clear()
        if _telegram_thread is None or not _telegram_thread.is_alive():
            from scripts.run_telegram_polling import poll_telegram_updates
            _telegram_thread = threading.Thread(target=poll_telegram_updates, name="telegram-polling", daemon=True)
            _telegram_thread.start()
    logger.info("Telegram bot started")
    return True


def stop_telegram(changed_by: Optional[str] = None) -> None:
    global _telegram_online_since
    if changed_by is not None:
        _set_enabled("telegram", False, changed_by)
    with _lock:
        _telegram_stop.set()
        _telegram_online_since = None
    logger.info("Telegram bot stopped")


# ---------- WhatsApp ----------
def start_whatsapp(changed_by: Optional[str] = None) -> None:
    _set_enabled("whatsapp", True, changed_by)
    logger.info("WhatsApp bot started")


def stop_whatsapp(changed_by: Optional[str] = None) -> None:
    _set_enabled("whatsapp", False, changed_by)
    logger.info("WhatsApp bot stopped")


def _whatsapp_link_state() -> Optional[str]:
    """'open' when the WhatsApp number is linked in Evolution API; None if unknown / not configured."""
    if not (settings.EVOLUTION_API_URL and settings.EVOLUTION_INSTANCE_NAME):
        return None
    try:
        import requests
        res = requests.get(
            f"{settings.EVOLUTION_API_URL.rstrip('/')}/instance/connectionState/{settings.EVOLUTION_INSTANCE_NAME}",
            headers={"apikey": settings.EVOLUTION_API_KEY}, timeout=3)
        return res.json().get("instance", {}).get("state") if res.ok else None
    except Exception:
        return None


def status() -> Dict[str, Any]:
    with Session(engine) as db:
        rows = {c: _row(db, c) for c in CHANNELS}
        info = {c: {"changed_at": rows[c].changed_at.isoformat() if rows[c].changed_at else None,
                    "changed_by": rows[c].changed_by} for c in CHANNELS}
    return {
        "telegram": {**info["telegram"], "running": telegram_running(),
                     "configured": bool(settings.TELEGRAM_BOT_TOKEN)},
        "whatsapp": {**info["whatsapp"], "running": is_enabled("whatsapp"),
                     "configured": bool(settings.EVOLUTION_API_URL or settings.WHATSAPP_ACCESS_TOKEN),
                     "link_state": _whatsapp_link_state()},
    }
