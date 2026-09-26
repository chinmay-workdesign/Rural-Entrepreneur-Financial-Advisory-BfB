"""
The advisor asks for every detail instead of assuming it.

1. Advice and DPR only after every detail is stated and confirmed; nothing is defaulted
2. Districts outside Karnataka are refused (the official cost data covers Karnataka only)
3. Answers such as '2 lakh' are never read as a language menu choice
4. A correction at the summary updates the value and shows the summary again
5. PMEGP rate follows the stated category/area; kirana is not eligible under PMEGP
6. Ex-serviceman / disability is asked only of general-category men
7. Spoken-style answers in regional languages are understood
"""
import uuid
from unittest.mock import patch

from app.db import crud
from app.db.session import SessionLocal
from app.dialogue import intake
from app.dialogue.conversation_state import process_telegram_query
from app.finance.pmegp import compute_pmegp
from tests.intake_helpers import complete_intake


def _chat() -> str:
    return f"tg_{uuid.uuid4().hex[:10]}"


def _say(chat_id: str, text: str) -> list:
    with patch("app.dialogue.conversation_state.send_channel_text") as sent:
        process_telegram_query(chat_id, text)
    return [c.args[1] for c in sent.call_args_list]


def _load(chat_id: str):
    db = SessionLocal()
    try:
        b = crud.get_or_create_telegram_beneficiary(db, chat_id)
        return b.conversation_state, dict(b.conversation_context or {})
    finally:
        db.close()


def _start_english(chat_id: str):
    _say(chat_id, "/start")
    _say(chat_id, "1. English")


# 1. No advice, no DPR and no defaults until every detail is stated and confirmed
def test_advice_and_dpr_wait_for_confirmed_details():
    chat_id = _chat()
    _start_english(chat_id)
    _say(chat_id, "I want to start a dairy in Belagavi, project cost 2 lakh")

    state, ctx = _load(chat_id)
    assert state == "COLLECTING"
    assert ctx["pending_field"] == "full_name"
    assert "financial_structure" not in ctx
    assert (ctx.get("profile") or {}).get("annual_family_income") is None

    with patch("app.dialogue.conversation_state.generate_dpr_pdf") as pdf:
        _say(chat_id, "GENERATE DPR")
    pdf.assert_not_called()

    complete_intake(lambda t: _say(chat_id, t), lambda db: crud.get_or_create_telegram_beneficiary(db, chat_id),
                    answers={"annual_family_income": "90000"}, confirm=False)
    state, ctx = _load(chat_id)
    assert state == "CONFIRM_PROFILE"
    assert "financial_structure" not in ctx

    messages = _say(chat_id, "yes")
    state, ctx = _load(chat_id)
    assert state == "CONFIRM_DPR"
    assert ctx["profile"]["annual_family_income"] == 90000.0
    assert any("PMEGP" in m for m in messages)


# 2. Outside Karnataka is refused, not silently advised with Karnataka data
def test_district_outside_karnataka_is_refused():
    chat_id = _chat()
    _start_english(chat_id)
    messages = _say(chat_id, "I want to start a dairy unit in Kolhapur")
    state, ctx = _load(chat_id)
    assert any("only advise for businesses in *Karnataka*" in m for m in messages)
    assert ctx.get("district") is None
    assert ctx["pending_field"] == "district"


# 3. '2 lakh' mid-conversation is an amount, not the Hindi menu option
def test_amount_answer_is_not_a_language_choice():
    chat_id = _chat()
    _start_english(chat_id)
    _say(chat_id, "dairy in Mysuru")
    _say(chat_id, "2 lakh")
    db = SessionLocal()
    try:
        b = crud.get_or_create_telegram_beneficiary(db, chat_id)
        assert b.preferred_language == "english"
        assert b.conversation_context["project_cost"] == 200000.0
    finally:
        db.close()


# 4. Correction at the summary
def test_correction_updates_value_and_asks_again():
    chat_id = _chat()
    _start_english(chat_id)
    _say(chat_id, "dairy in Mysuru, project cost 2 lakh")
    complete_intake(lambda t: _say(chat_id, t), lambda db: crud.get_or_create_telegram_beneficiary(db, chat_id),
                    confirm=False)
    messages = _say(chat_id, "age 41")
    state, ctx = _load(chat_id)
    assert state == "CONFIRM_PROFILE"
    assert ctx["profile"]["age"] == 41
    assert any("Age: 41" in m for m in messages)


# 5. PMEGP follows the stated profile and the guideline's activity rules
def test_pmegp_rate_depends_on_stated_profile():
    woman_rural = compute_pmegp(200000.0, "Dairy", {"gender": "female", "social_category": "general", "area_type": "rural", "age": 30})
    man_general_urban = compute_pmegp(200000.0, "Flour mill", {
        "gender": "male", "social_category": "general", "special_status": False, "area_type": "urban", "age": 30})
    kirana = compute_pmegp(120000.0, "Kirana Store", {"gender": "female", "social_category": "sc", "area_type": "rural", "age": 30})
    goat = compute_pmegp(113000.0, "Goat rearing", {"gender": "female", "social_category": "sc", "area_type": "rural", "age": 30})

    assert (woman_rural["subsidy_pct"], woman_rural["own_contribution_pct"]) == (35.0, 5.0)
    assert (man_general_urban["subsidy_pct"], man_general_urban["own_contribution_pct"]) == (15.0, 10.0)
    assert kirana["eligible"] is False and "trading" in kirana["ineligible_codes"]
    assert goat["eligible"] is False and "animal_husbandry" in goat["ineligible_codes"]
    assert kirana["subsidy_amount"] is None


# 6. Special-status question only where it can change the rate
def test_special_status_asked_only_for_general_category_men():
    ctx = {"profile": {"gender": "male", "social_category": "general"}}
    assert "special_status" in intake.required_fields(ctx)
    ctx = {"profile": {"gender": "female", "social_category": "general"}}
    assert "special_status" not in intake.required_fields(ctx)


# 7. Regional-language and spoken-style answers
def test_regional_language_answers_are_understood():
    assert intake.extract_answers("ಎರಡು ಲಕ್ಷ", "project_cost")["project_cost"] == 200000.0
    assert intake.extract_answers("मेरी उम्र 42 साल है", "age")["age"] == 42
    assert intake.extract_answers("ಮಹಿಳೆ", "gender")["gender"] == "female"
    assert intake.extract_answers("अनुसूचित जनजाति", "social_category")["social_category"] == "st"
    assert intake.extract_answers("గ్రామం", "area_type")["area_type"] == "rural"
    assert intake.extract_answers("होय", "education_8th_pass")["education_8th_pass"] is True
