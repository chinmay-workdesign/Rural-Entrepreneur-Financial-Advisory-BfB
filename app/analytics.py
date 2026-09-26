"""
Statistics for the admin analytics page. Every number is counted from the database (people who messaged the
bot, their applications, DPRs and officer decisions); nothing is estimated. Values an applicant did not give
are counted as "Not stated".

Note: /start wipes a person's answers, so the funnel counts people who reached a stage in their current
conversation or who have an application on file (an application means they passed every earlier stage).
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db import crud
from app.db.models import Beneficiary, EnterpriseProposal

IST = timezone(timedelta(hours=5, minutes=30))
NOT_STATED = "Not stated"
TREND_DAYS = 30

# How far each conversation state is into the flow
_STAGE_OF_STATE = {"GREETING": 0, "LANGUAGE_SELECTION": 0, "COLLECTING": 1, "CONFIRM_PROFILE": 2,
                   "CONFIRM_DPR": 3, "SUBMITTED": 4}
_STATE_LABEL = {"GREETING": "Choosing a language", "LANGUAGE_SELECTION": "Choosing a language",
                "COLLECTING": "Answering questions", "CONFIRM_PROFILE": "Confirming their details",
                "CONFIRM_DPR": "Seen advice, DPR not requested", "SUBMITTED": "Finished (DPR sent)"}
_STATUS_LABEL = {"DRAFT": "Awaiting review", "REVISIT": "Sent back", "SANCTIONED": "Sanctioned",
                 "REJECTED": "Rejected"}
_GENDER = {"male": "Men", "female": "Women", "transgender": "Transgender"}
_CATEGORY = {"general": "General", "sc": "SC", "st": "ST", "obc": "OBC", "minority": "Minority"}
_AREA = {"rural": "Village", "urban": "Town / city"}


def _district(name: Optional[str]) -> str:
    return name.strip().title() if name and name.strip() else NOT_STATED


def _ist_day(ts: Optional[datetime]) -> Optional[str]:
    if ts is None:
        return None
    if ts.tzinfo is None:  # SQLite returns naive UTC
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(IST).date().isoformat()


def _age_band(age: Any) -> str:
    try:
        a = int(age)
    except (TypeError, ValueError):
        return NOT_STATED
    for hi, label in ((25, "18–25"), (35, "26–35"), (45, "36–45"), (60, "46–60")):
        if a <= hi:
            return label
    return "Over 60"


def _counts(counter: Counter, order: Optional[List[str]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """[{label, count}] with 'Not stated' last; fixed `order` first when given."""
    items = [(k, v) for k, v in counter.items() if v]
    if order:
        items.sort(key=lambda kv: (kv[0] == NOT_STATED, order.index(kv[0]) if kv[0] in order else len(order), -kv[1]))
    else:
        items.sort(key=lambda kv: (kv[0] == NOT_STATED, -kv[1], kv[0]))
    if limit and len(items) > limit:
        rest = sum(v for _, v in items[limit:])
        items = items[:limit] + [("Others", rest)]
    return [{"label": k, "count": v} for k, v in items]


def _pct(part: int, whole: int) -> Optional[float]:
    return round(100 * part / whole, 1) if whole else None


def _ist(ts: Optional[datetime]) -> Optional[datetime]:
    """India time without tzinfo (Excel cells cannot hold time zones)."""
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(IST).replace(tzinfo=None)


def _wa_number(b: Optional[Beneficiary]) -> Optional[str]:
    """Telegram users carry an internal "tg_<chat id>" placeholder in whatsapp_number; that is not a phone number."""
    n = b.whatsapp_number if b else None
    return None if not n or n.startswith("tg_") else n


def application_rows(db: Session, district: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every application (optionally one district), newest first, exactly as stated / decided."""
    selected = _district(district) if district else None
    rows = []
    for p in db.query(EnterpriseProposal).order_by(EnterpriseProposal.created_at.desc()).all():
        snap = crud.get_proposal_snapshot(db, p.id)
        b = p.beneficiary
        d = _district(snap.get("district") or (b.district if b else None))
        if selected and d != selected:
            continue
        pr = snap.get("profile") or {}
        agency = (snap.get("financial_structure") or {}).get("agency")
        last = sorted(p.verifications, key=lambda v: v.verified_at or datetime.min)[-1] if p.verifications else None
        rows.append({
            "Reference": "DPR-" + str(p.id)[:8].upper(),
            "Received (IST)": _ist(p.created_at),
            "Applicant name": pr.get("full_name") or (b.full_name if b else None),
            "Channel": "WhatsApp" if b and b.primary_channel == "whatsapp" else "Telegram",
            "WhatsApp number": _wa_number(b),
            "Telegram chat id": b.telegram_chat_id if b else None,
            "Language": (snap.get("language") or (b.preferred_language if b else None) or "").title() or None,
            "District": d,
            "Business": p.business_trade,
            "Project cost (Rs.)": float(p.project_cost or 0),
            "Loan requested (Rs.)": float(p.sanctioned_loan or 0),
            "Own contribution (Rs.)": float(p.beneficiary_margin or 0),
            "Scheme": p.scheme_tier.replace("_", " ").title() if p.scheme_tier and p.scheme_tier != "NONE" else "None",
            "Corporation": agency,
            "Gender": _GENDER.get(str(pr.get("gender") or "").lower()),
            "Age": pr.get("age"),
            "Social category": _CATEGORY.get(str(pr.get("social_category") or "").lower()),
            "Area": _AREA.get(str(pr.get("area_type") or "").lower()),
            "Annual family income (Rs.)": pr.get("annual_family_income"),
            "Status": _STATUS_LABEL.get(p.status, p.status),
            "DPR generated": "Yes" if p.dpr_pdf_url else "No",
            "Field verified": "Yes" if p.verifications else "No",
            "Last officer recommendation": last.recommendation if last else None,
            "Last officer action (IST)": _ist(last.verified_at) if last else None,
        })
    return rows


def contact_rows(db: Session, district: Optional[str] = None) -> List[Dict[str, Any]]:
    """Everyone who contacted the bot (optionally one district), newest first."""
    selected = _district(district) if district else None
    rows = []
    for b in db.query(Beneficiary).order_by(Beneficiary.created_at.desc()).all():
        d = _district(b.district)
        if selected and d != selected:
            continue
        rows.append({
            "First contact (IST)": _ist(b.created_at),
            "Channel": "WhatsApp" if b.primary_channel == "whatsapp" else "Telegram",
            "WhatsApp number": _wa_number(b),
            "Telegram chat id": b.telegram_chat_id,
            "Name": b.full_name,
            "Language": b.preferred_language.title() if b.preferred_language else None,
            "District": d,
            "Where they are now": _STATE_LABEL.get(b.conversation_state or "GREETING", "Choosing a language"),
            "Applications": len(b.proposals),
            "DPRs generated": sum(1 for p in b.proposals if p.dpr_pdf_url),
        })
    return rows


def compute(db: Session, district: Optional[str] = None) -> Dict[str, Any]:
    people = db.query(Beneficiary).all()
    proposals = db.query(EnterpriseProposal).all()

    # One row per application with the details the applicant confirmed
    apps = []
    for p in proposals:
        snap = crud.get_proposal_snapshot(db, p.id)
        b = p.beneficiary
        apps.append({
            "p": p,
            "district": _district(snap.get("district") or (b.district if b else None)),
            "profile": snap.get("profile") or {},
            "agency": (snap.get("financial_structure") or {}).get("agency"),
            "has_dpr": bool(p.dpr_pdf_url),
        })

    # District table (always over everything, so the admin can pick one)
    by_district: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"contacts": 0, "applications": 0, "dprs": 0,
                                                                 "people_with_dpr": set(), "awaiting": 0,
                                                                 "sanctioned": 0, "rejected": 0,
                                                                 "project_cost": 0.0})
    for b in people:
        by_district[_district(b.district)]["contacts"] += 1
    for a in apps:
        row, p = by_district[a["district"]], a["p"]
        row["applications"] += 1
        row["project_cost"] += float(p.project_cost or 0)
        if a["has_dpr"]:
            row["dprs"] += 1
            row["people_with_dpr"].add(p.beneficiary_id)
        row["awaiting"] += p.status == "DRAFT"
        row["sanctioned"] += p.status == "SANCTIONED"
        row["rejected"] += p.status == "REJECTED"
    districts = []
    for name, r in by_district.items():
        with_dpr = len(r.pop("people_with_dpr"))
        districts.append({"district": name, **r, "people_with_dpr": with_dpr,
                          "conversion_pct": _pct(min(with_dpr, r["contacts"]), r["contacts"])})
    districts.sort(key=lambda r: (r["district"] == NOT_STATED, -r["contacts"], r["district"]))

    # Filter to one district
    selected = _district(district) if district else None
    if selected:
        people = [b for b in people if _district(b.district) == selected]
        apps = [a for a in apps if a["district"] == selected]

    applicants = {a["p"].beneficiary_id for a in apps}
    dpr_people = {a["p"].beneficiary_id for a in apps if a["has_dpr"]}
    decided_people = {a["p"].beneficiary_id for a in apps if a["p"].status in ("SANCTIONED", "REJECTED")}
    sanctioned_people = {a["p"].beneficiary_id for a in apps if a["p"].status == "SANCTIONED"}
    # A person with an application (possibly filed under this district while their last chat was elsewhere) counts
    # as having passed every conversation stage
    stage = {b.id: 4 if b.id in applicants else _STAGE_OF_STATE.get(b.conversation_state or "GREETING", 0)
             for b in people}
    contacts = len(people)
    reached = lambda n: sum(1 for s in stage.values() if s >= n)
    funnel = [
        {"label": "Contacted the bot", "count": contacts},
        {"label": "Chose a language", "count": reached(1)},
        {"label": "Answered every question", "count": reached(2)},
        {"label": "Confirmed details and got advice", "count": reached(3)},
        {"label": "Generated a DPR", "count": len(dpr_people & set(stage))},
        {"label": "Officer decision made", "count": len(decided_people & set(stage))},
        {"label": "Sanctioned", "count": len(sanctioned_people & set(stage))},
    ]

    # Daily trend (India time)
    today = datetime.now(IST).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(TREND_DAYS - 1, -1, -1)]
    new_contacts = Counter(_ist_day(b.created_at) for b in people)
    new_dprs = Counter(_ist_day(a["p"].created_at) for a in apps if a["has_dpr"])
    trend = [{"day": d, "contacts": new_contacts.get(d, 0), "dprs": new_dprs.get(d, 0)} for d in days]

    ps = [a["p"] for a in apps]
    cost = [float(p.project_cost or 0) for p in ps]
    loan = [float(p.sanctioned_loan or 0) for p in ps]
    sanctioned_loans = [float(p.sanctioned_loan or 0) for p in ps if p.status == "SANCTIONED"]
    profiles = [a["profile"] for a in apps]

    return {
        "district": selected,
        "generated_at": datetime.now(IST).isoformat(timespec="seconds"),
        "summary": {
            "contacts": contacts,
            "contacts_telegram": sum(1 for b in people if (b.primary_channel or "telegram") == "telegram"),
            "contacts_whatsapp": sum(1 for b in people if b.primary_channel == "whatsapp"),
            "people_with_dpr": len(dpr_people),
            "dprs_generated": sum(1 for a in apps if a["has_dpr"]),
            "applications": len(apps),
            "conversion_pct": _pct(len(dpr_people & set(stage)), contacts),
            "awaiting": sum(p.status == "DRAFT" for p in ps),
            "sent_back": sum(p.status == "REVISIT" for p in ps),
            "sanctioned": sum(p.status == "SANCTIONED" for p in ps),
            "rejected": sum(p.status == "REJECTED" for p in ps),
            "field_verified": sum(1 for p in ps if p.verifications),
            "total_project_cost": sum(cost),
            "avg_project_cost": (sum(cost) / len(cost)) if cost else None,
            "total_loan_requested": sum(loan),
            "total_own_contribution": sum(float(p.beneficiary_margin or 0) for p in ps),
            "total_loan_sanctioned": sum(sanctioned_loans),
        },
        "funnel": funnel,
        "current_stage": _counts(Counter(_STATE_LABEL.get(b.conversation_state or "GREETING", "Choosing a language")
                                         for b in people), order=list(dict.fromkeys(_STATE_LABEL.values()))),
        "trend": trend,
        "channels": _counts(Counter("WhatsApp" if b.primary_channel == "whatsapp" else "Telegram" for b in people)),
        "languages": _counts(Counter((b.preferred_language or NOT_STATED).title() if b.preferred_language
                                     else NOT_STATED for b in people)),
        "status": _counts(Counter(_STATUS_LABEL.get(p.status, p.status) for p in ps),
                          order=list(_STATUS_LABEL.values())),
        "businesses": _counts(Counter((p.business_trade or NOT_STATED).strip().capitalize() for p in ps), limit=8),
        "schemes": _counts(Counter(a["agency"] or ("No corporation loan" if a["p"].scheme_tier == "NONE"
                                                   else a["p"].scheme_tier.replace("_", " ").title())
                                   for a in apps)),
        "gender": _counts(Counter(_GENDER.get(str(pr.get("gender") or "").lower(), NOT_STATED) for pr in profiles)),
        "social_category": _counts(Counter(_CATEGORY.get(str(pr.get("social_category") or "").lower(), NOT_STATED)
                                           for pr in profiles), order=list(_CATEGORY.values())),
        "area": _counts(Counter(_AREA.get(str(pr.get("area_type") or "").lower(), NOT_STATED) for pr in profiles)),
        "age": _counts(Counter(_age_band(pr.get("age")) for pr in profiles),
                       order=["18–25", "26–35", "36–45", "46–60", "Over 60"]),
        "districts": districts,
    }
