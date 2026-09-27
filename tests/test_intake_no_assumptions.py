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


# 8. The selected language never changes by itself (typed or spoken answers)
def _lang(chat_id: str) -> str:
    db = SessionLocal()
    try:
        return crud.get_or_create_telegram_beneficiary(db, chat_id).preferred_language
    finally:
        db.close()


def test_selected_language_is_kept_for_latin_script_answers():
    chat_id = _chat()
    _say(chat_id, "/start")
    _say(chat_id, "5. मराठी (Marathi)")
    for text in ("maza vay 28 ahe", "Bengaluru", "Hi", "OBC", "2 lakh", "My name is Pranav Chougule"):
        messages = _say(chat_id, text)
        assert _lang(chat_id) == "marathi", text
        assert all("Sorry, I didn't catch that" not in m for m in messages)


def test_voice_transcript_does_not_switch_language():
    from app.dialogue.conversation_state import process_telegram_voice_query
    chat_id = _chat()
    _say(chat_id, "/start")
    _say(chat_id, "3. ಕನ್ನಡ (Kannada)")
    with patch("app.dialogue.conversation_state.download_telegram_file", return_value=b"OggS-audio"), \
         patch("app.dialogue.conversation_state.transcribe_audio", return_value="maza vay 28 ahe"), \
         patch("app.dialogue.conversation_state.send_channel_text"):
        process_telegram_voice_query(chat_id, "file-1")
    assert _lang(chat_id) == "kannada"


def test_explicit_language_request_still_switches():
    chat_id = _chat()
    _start_english(chat_id)
    _say(chat_id, "Hindi please")
    assert _lang(chat_id) == "hindi"


# 9. Nothing from an earlier conversation is reused
def test_new_conversation_asks_every_question_again():
    chat_id = _chat()
    _start_english(chat_id)
    _say(chat_id, "dairy in Mysuru, project cost 2 lakh")
    complete_intake(lambda t: _say(chat_id, t), lambda db: crud.get_or_create_telegram_beneficiary(db, chat_id),
                    answers={"gender": "man", "age": "28", "social_category": "general"})

    for restart in ("/start", "Hi", "RESET"):
        _say(chat_id, restart)
        _say(chat_id, "1. English")
        state, ctx = _load(chat_id)
        assert ctx.get("profile") in (None, {}), restart
        assert ctx.get("trade") is None and ctx.get("project_cost") is None
        _say(chat_id, "poultry in Hassan, project cost 3 lakh")
        asked = []
        for _ in range(12):
            state, ctx = _load(chat_id)
            if state != "COLLECTING":
                break
            asked.append(ctx["pending_field"])
            _say(chat_id, {"full_name": "Ravi", "gender": "woman", "age": "40", "social_category": "SC",
                           "area_type": "village", "annual_family_income": "1 lakh", "available_capital": "0"}[ctx["pending_field"]])
        assert asked == ["full_name", "age", "gender", "social_category", "area_type", "annual_family_income",
                         "available_capital"], (restart, asked)


# 10. Related questions are asked together; partial answers keep what was said and ask only for the rest
def test_grouped_questions_and_partial_answers():
    chat_id = _chat()
    _start_english(chat_id)
    _say(chat_id, "dairy in Belagavi, project cost 2 lakh")
    state, ctx = _load(chat_id)
    assert ctx["pending_fields"] == ["full_name", "age", "gender", "social_category"]

    messages = _say(chat_id, "Lakshmi, 34")
    state, ctx = _load(chat_id)
    assert (ctx["profile"]["full_name"], ctx["profile"]["age"]) == ("Lakshmi", 34)
    assert ctx["pending_fields"] == ["gender", "social_category"]
    assert any("Please also tell me" in m for m in messages)

    _say(chat_id, "woman, SC")
    state, ctx = _load(chat_id)
    assert ctx["pending_fields"] == ["area_type", "annual_family_income", "available_capital"]

    _say(chat_id, "village, income 1.5 lakh, own money 20 thousand")
    state, ctx = _load(chat_id)
    assert state == "CONFIRM_PROFILE"
    assert (ctx["profile"]["area_type"], ctx["profile"]["annual_family_income"], ctx["available_capital"]) == ("rural", 150000.0, 20000.0)


def test_ambiguous_grouped_amounts_are_asked_again_not_guessed():
    answers = intake.extract_answers("village, 1.5 lakh", ["area_type", "annual_family_income", "available_capital"])
    assert answers["area_type"] == "rural"
    assert answers["annual_family_income"] is None and answers["available_capital"] is None


def test_extra_group_only_when_rules_need_it():
    ctx = {"trade": "Flour Mill", "project_cost": 600000.0, "district": "Dharwad",
           "profile": {"full_name": "R", "age": 45, "gender": "male", "social_category": "general",
                       "area_type": "urban", "annual_family_income": 300000.0}, "available_capital": 60000.0}
    group, needed, missing = intake.next_group(ctx)
    assert group == "extra" and missing == ["special_status"]  # manufacturing: 8th pass only above Rs 10 lakh
    ctx["profile"]["gender"] = "female"
    assert intake.next_group(ctx) is None


# 11. Every question is asked: details mentioned early are held back until their own question is asked
def test_early_mentions_are_asked_again_not_skipped():
    chat_id = _chat()
    _start_english(chat_id)
    # Own money and name mentioned in the opening message, before their questions
    _say(chat_id, "dairy in Mysuru, project cost 3 lakh, my own money 50000")
    state, ctx = _load(chat_id)
    assert ctx.get("available_capital") is None
    assert ctx["volunteered"]["available_capital"] == 50000.0

    _say(chat_id, "Ravi, 40, man, SC")
    messages = []
    state, ctx = _load(chat_id)
    assert "available_capital" in ctx["pending_fields"]  # own money is still asked
    messages = _say(chat_id, "village, income 2 lakh")
    assert any("own money" in m.lower() and "₹50,000" in m for m in messages)  # the question shows what was mentioned
    state, ctx = _load(chat_id)
    assert ctx["pending_fields"] == ["available_capital"]

    _say(chat_id, "yes")
    state, ctx = _load(chat_id)
    assert ctx["available_capital"] == 50000.0
    assert state == "CONFIRM_PROFILE"


def test_yes_is_never_read_as_a_name():
    from app.dialogue.intake_parsing import parse_name
    assert parse_name("हाँ") is None and parse_name("yes") is None and parse_name("ಹೌದು") is None
