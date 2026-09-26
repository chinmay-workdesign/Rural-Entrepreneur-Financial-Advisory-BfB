"""Answers the intake questions in tests, the way a user would, until the details are confirmed."""
from typing import Callable, Dict, Optional

from app.db.session import SessionLocal

DEFAULT_ANSWERS: Dict[str, str] = {
    "trade": "dairy",
    "district": "Belagavi",
    "project_cost": "2 lakh",
    "full_name": "Ramesh Kumar",
    "gender": "man",
    "age": "35",
    "social_category": "SC",
    "area_type": "village",
    "annual_family_income": "1.5 lakh",
    "available_capital": "20000",
    "special_status": "no",
    "education_8th_pass": "yes",
}


def complete_intake(send: Callable[[str], None], load_beneficiary: Callable, answers: Optional[Dict[str, str]] = None,
                    confirm: bool = True, max_turns: int = 20) -> None:
    """Replies to each pending question, then says 'yes' to the summary (unless confirm is False)."""
    answers = {**DEFAULT_ANSWERS, **(answers or {})}
    for _ in range(max_turns):
        db = SessionLocal()
        try:
            beneficiary = load_beneficiary(db)
            state = beneficiary.conversation_state
            pending = (beneficiary.conversation_context or {}).get("pending_field")
        finally:
            db.close()
        if state == "CONFIRM_PROFILE":
            if confirm:
                send("yes")
            return
        if state != "COLLECTING" or not pending:
            return
        send(answers[pending])
    raise AssertionError("Intake did not finish")


def login_officer(client) -> None:
    """Logs the test client in as the seeded Belagavi field officer (the session cookie is kept by the client)."""
    from app.db import crud
    db = SessionLocal()
    try:
        crud.seed_default_users(db)
    finally:
        db.close()
    res = client.post("/auth/login", json={"email": "officer.belagavi@sca.gov.in", "password": "Officer@123"})
    assert res.status_code == 200, res.text
