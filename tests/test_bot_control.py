"""
Starting / stopping the bots from the officer dashboard, and no queued replies.

1. A stopped WhatsApp bot ignores messages; after it is started again only new messages are answered
2. Messages sent before the bot came online, or delivered late (older than 2 minutes), are not answered
3. Telegram polling: start / stop from the dashboard runs and ends the polling thread; old updates are skipped
4. Only an administrator can start or stop the bots; officers see the status; anonymous users get 401
"""
import time
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import bot_control
from app.config import settings
from app.db import crud
from app.db.session import SessionLocal
from app.main import app
from tests.intake_helpers import login_officer


@pytest.fixture(autouse=True)
def bots_on_after_each_test():
    yield
    bot_control.stop_telegram()
    bot_control.start_whatsapp()


def _evolution(text: str, sent_at=None) -> dict:
    data = {"key": {"remoteJid": f"91{uuid.uuid4().int % 10**10:010d}@s.whatsapp.net", "fromMe": False,
                    "id": uuid.uuid4().hex.upper()},
            "message": {"conversation": text}}
    if sent_at is not None:
        data["messageTimestamp"] = int(sent_at)
    return {"event": "messages.upsert", "instance": "kirana-bot", "data": data}


def _admin_client() -> TestClient:
    client = TestClient(app)
    db = SessionLocal()
    try:
        crud.seed_default_users(db)
    finally:
        db.close()
    assert client.post("/auth/login", json={"email": "admin@sca.gov.in", "password": "Admin@123"}).status_code == 200
    return client


# 1. Stopped WhatsApp bot ignores messages; restarting does not answer them later
def test_stopped_whatsapp_bot_ignores_messages():
    client = TestClient(app)
    with patch("app.whatsapp.webhook_handler.process_user_query") as handle:
        bot_control.stop_whatsapp("test")
        assert client.post("/webhook/whatsapp", json=_evolution("hi while stopped", time.time())).status_code == 200
        sent_while_stopped = time.time() - 2
        time.sleep(1.1)  # the switch is stored with one-second precision
        bot_control.start_whatsapp("test")
        # Redelivered after the restart, but sent while the bot was stopped
        client.post("/webhook/whatsapp", json=_evolution("late copy", sent_while_stopped))
        client.post("/webhook/whatsapp", json=_evolution("new message", time.time()))
    assert [c.args[1] for c in handle.call_args_list] == ["new message"]


# 2. Late deliveries are dropped
def test_late_messages_are_not_answered():
    assert bot_control.accept_message("whatsapp", time.time())
    assert bot_control.accept_message("whatsapp", None)  # no timestamp: judged on the switch alone
    assert not bot_control.accept_message("whatsapp", time.time() - bot_control.STALE_AFTER_SECONDS - 30)
    assert not bot_control.accept_message("whatsapp", {"low": int(bot_control._PROCESS_STARTED) - 60})
    assert not bot_control.accept_message("telegram", time.time(), via_polling=True)  # polling not running


# 3. Telegram polling thread follows the dashboard switch
def test_telegram_start_stop_runs_and_ends_polling(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "123:TEST")
    seen = []

    def fake_poll():
        bot_control.note_telegram_polling_started()
        while not bot_control.telegram_should_stop():
            seen.append(bot_control.accept_message("telegram", time.time(), via_polling=True))
            time.sleep(0.02)

    with patch("scripts.run_telegram_polling.poll_telegram_updates", fake_poll):
        assert bot_control.start_telegram("test")
        time.sleep(0.2)
        assert bot_control.telegram_running() and bot_control.is_enabled("telegram")
        assert not bot_control.accept_message("telegram", time.time() - 3600, via_polling=True)
        bot_control.stop_telegram("test")
        time.sleep(0.2)
    assert not bot_control.telegram_running() and not bot_control.is_enabled("telegram")
    assert seen and all(seen)
    assert not bot_control.accept_message("telegram", time.time(), via_polling=True)


# 4. Permissions
def test_only_admin_can_control_bots():
    anon = TestClient(app)
    assert anon.get("/internal/bots").status_code == 401
    assert anon.post("/internal/bots/whatsapp/stop").status_code == 401

    officer = TestClient(app)
    login_officer(officer)
    body = officer.get("/internal/bots").json()
    assert body["can_control"] is False and body["whatsapp"]["running"] is True
    assert officer.post("/internal/bots/whatsapp/stop").status_code == 403
    assert bot_control.is_enabled("whatsapp")

    admin = _admin_client()
    assert admin.get("/internal/bots").json()["can_control"] is True
    res = admin.post("/internal/bots/whatsapp/stop")
    assert res.status_code == 200 and res.json()["whatsapp"]["running"] is False
    assert res.json()["whatsapp"]["changed_by"] == "admin@sca.gov.in"
    assert admin.post("/internal/bots/whatsapp/start").json()["whatsapp"]["running"] is True
    assert admin.post("/internal/bots/email/start").status_code == 404
