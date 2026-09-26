import os
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import engine, Base, get_db, init_db
from app.db import crud, models
from app.whatsapp.webhook_handler import router as whatsapp_router
from app.whatsapp.client import send_whatsapp_text, send_whatsapp_document
from app.auth.routes import router as auth_router, get_current_user, get_optional_current_user, COOKIE_NAME
from app.auth.security import decode_access_token

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rural_advisor_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    init_db()
    try:
        with Session(engine) as db:
            crud.seed_default_users(db)
            logger.info("Default SCA demo user accounts verified/seeded.")
    except Exception as e:
        logger.warning(f"Could not seed default users: {e}")

    # Explicit startup check for authoritative Qdrant collection (built only at startup when missing/empty, never on user request)
    try:
        from app.retrieval.service import retrieval_service
        if retrieval_service.verify_collection_ready(auto_build_if_empty=settings.QDRANT_AUTO_INGEST):
            logger.info("Authoritative Qdrant knowledge collection verified ready.")
        else:
            logger.warning("Authoritative Qdrant collection missing or empty. Execute 'py -m app.retrieval.ingest' to initialize.")
    except Exception as e:
        logger.warning(f"Could not verify Qdrant collection during startup: {e}")

    # If configured for unified cloud deployment, run Telegram bot polling in background thread
    should_run_bot = (
        bool(settings.TELEGRAM_BOT_TOKEN)
        and not os.environ.get("PYTEST_CURRENT_TEST")
        and os.environ.get("RUN_TELEGRAM_POLLING", "true").lower() == "true"
    )
    if should_run_bot:
        from app import bot_control
        if bot_control.is_enabled("telegram"):
            logger.info("Starting integrated Telegram long-polling daemon thread...")
            bot_control.start_telegram()
        else:
            logger.info("Telegram bot is switched off in the officer dashboard; not polling.")
    yield
    logger.info("Shutting down Rural Advisor API...")

app = FastAPI(
    title="Rural Micro-Enterprise AI Advisory & Structuring API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure local static directory for DPRs exists and mount it
static_dir = os.path.join(os.getcwd(), "static", "dprs")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static/dprs", StaticFiles(directory=static_dir), name="static_dprs")

# Include Routers
from app.telegram.webhook_handler import router as telegram_router

app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(telegram_router)

# Request schemas for internal SCA dashboard
class VerificationRequest(BaseModel):
    field_officer_id: str
    geo_latitude: Optional[float] = None
    geo_longitude: Optional[float] = None
    margin_money_verified: bool = True
    recommendation: str = "APPROVE"  # APPROVE, REJECT, REVISIT
    remarks: Optional[str] = None

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Rural Micro-Enterprise AI Advisory",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

def _session_user(request: Request, db: Session) -> Optional[models.User]:
    """
    The signed-in officer, or None. The account must still exist and be active: a cookie that is merely
    well-signed (e.g. from before the database was reset) must not count, or /login and /admin redirect
    to each other forever.
    """
    token = request.cookies.get(COOKIE_NAME)
    payload = decode_access_token(token) if token else None
    if not payload or "sub" not in payload:
        return None
    user = crud.get_user_by_id(db, payload["sub"])
    return user if user and user.is_active else None


def _without_stale_cookie(response, request: Request):
    if request.cookies.get(COOKIE_NAME):
        response.delete_cookie(key=COOKIE_NAME, path="/", httponly=True, samesite="lax")
    return response


@app.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request, db: Session = Depends(get_db)):
    """Serves the secure Officer Authentication & Registration page."""
    if _session_user(request, db):
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

    login_template = os.path.join(os.path.dirname(__file__), "templates", "login.html")
    if os.path.exists(login_template):
        with open(login_template, "r", encoding="utf-8") as f:
            return _without_stale_cookie(HTMLResponse(content=f.read()), request)
    return HTMLResponse(content="<h2>SCA Portal login template loading...</h2>")

@app.get("/", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
def get_admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Serves the central SCA Field Officer & Admin Loan Appraisal Portal (Session Guarded)."""
    if not _session_user(request, db):
        return _without_stale_cookie(RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND), request)

    template_path = os.path.join(os.path.dirname(__file__), "templates", "admin.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="""
    <html><body style="font-family: sans-serif; padding: 40px; text-align: center;">
      <h2>🌾 Rural Enterprise AI Advisory Portal</h2>
      <p>Admin template loading. View API at <a href="/health">/health</a> or <a href="/internal/proposals">/internal/proposals</a>.</p>
    </body></html>
    """)


def _reference_cost(trade: str, district: Optional[str], cost: float) -> Dict[str, Any]:
    """Official unit cost for the activity (NABARD) or a labelled historical profile, and the variance."""
    from app.finance.repository import benchmark_repository
    bench = benchmark_repository.get_benchmark(trade, district=district or "")
    if bench.get("status") == "DATA_NOT_AVAILABLE" or not bench.get("total_cost"):
        return {"available": False}
    ref = float(bench["total_cost"])
    is_nabard = bench.get("source_id") == "NABARD_KA_UC_BOOKLET_2026_27"
    return {
        "available": True,
        "is_official_unit_cost": is_nabard,
        "unit": bench.get("sub_activity") or bench.get("activity"),
        "reference_cost": ref,
        "source": ("NABARD Karnataka Unit Cost Booklet 2026-27" if is_nabard
                   else f"{bench.get('source_organization')} model project profile ({bench.get('publication_year')})"),
        "source_page": bench.get("source_page"),
        "historical_warning": bench.get("historical_warning"),
    }


@app.get("/admin/analytics", response_class=HTMLResponse)
def get_analytics_page(request: Request, db: Session = Depends(get_db)):
    """Statistics page for administrators: contacts, DPRs, decisions, overall and per district."""
    user = _session_user(request, db)
    if not user:
        return _without_stale_cookie(RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND), request)
    if user.role != "ADMIN":
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    with open(os.path.join(os.path.dirname(__file__), "templates", "analytics.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/internal/analytics")
def get_analytics(
    district: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Counts behind the analytics page, for all districts or one (`?district=Belagavi`). Admins only."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Analytics are available to administrators only.")
    from app import analytics
    return analytics.compute(db, district=district)


@app.get("/internal/analytics/export")
def export_analytics(
    district: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Excel workbook of the analytics (all districts or one) with the full applications and contacts lists."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Analytics are available to administrators only.")
    import re
    from datetime import datetime
    from fastapi.responses import Response as RawResponse
    from app.analytics import IST
    from app.analytics_export import build_workbook
    scope = re.sub(r"[^A-Za-z0-9]+", "-", district.strip()).strip("-").lower() if district and district.strip() else "all-districts"
    return RawResponse(
        content=build_workbook(db, district=district),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="advisor-analytics-{scope}-{datetime.now(IST).date().isoformat()}.xlsx"'},
    )


@app.get("/internal/bots")
def bot_status(current_user: models.User = Depends(get_current_user)):
    """Whether the Telegram and WhatsApp bots are running (shown to every officer)."""
    from app import bot_control
    return {**bot_control.status(), "can_control": current_user.role == "ADMIN"}


@app.post("/internal/bots/{channel}/{action}")
def control_bot(channel: str, action: str, current_user: models.User = Depends(get_current_user)):
    """Start or stop a bot. Admins only. A stopped bot ignores messages; they are not answered later."""
    from app import bot_control
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an administrator can start or stop the bots.")
    if channel not in bot_control.CHANNELS or action not in ("start", "stop"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown bot or action.")
    who = current_user.email
    if channel == "telegram":
        if action == "start":
            if not bot_control.start_telegram(changed_by=who):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TELEGRAM_BOT_TOKEN is not configured.")
        else:
            bot_control.stop_telegram(changed_by=who)
    else:
        (bot_control.start_whatsapp if action == "start" else bot_control.stop_whatsapp)(changed_by=who)
    return bot_control.status()


@app.get("/internal/proposals")
def list_proposals(
    status: Optional[str] = None,
    district: Optional[str] = None,
    scheme: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),  # officers only: contains applicants' personal data
):
    """
    Applications for the SCA officer dashboard. Every value comes from the applicant's confirmed answers,
    the verified scheme rules or officer actions; nothing is defaulted. Missing values are null.
    """
    proposals = crud.get_proposals(db, status=status, district=district, scheme=scheme)
    results = []
    for p in proposals:
        b = p.beneficiary
        snap = crud.get_proposal_snapshot(db, p.id)
        if not snap and b and isinstance(b.conversation_context, dict):
            # Applications made before snapshots existed: use the conversation only if it is about the same business
            ctx = b.conversation_context
            if ctx.get("trade") == p.business_trade:
                ms = ctx.get("multi_schemes") or {}
                snap = {"profile": ctx.get("profile"), "available_capital": ctx.get("available_capital"),
                        "financial_structure": ctx.get("financial_structure"), "pmegp": ms.get("pmegp"),
                        "mudra": ms.get("mudra")}

        # Normalize DPR PDF URL to relative path so it seamlessly opens in any browser/domain
        pdf_url = p.dpr_pdf_url
        if pdf_url and "/static/dprs/" in pdf_url:
            pdf_url = f"/static/dprs/{pdf_url.split('/static/dprs/')[-1]}"

        profile = snap.get("profile") or {}
        district_name = snap.get("district") or (b.district if b else None)
        cost = float(p.project_cost)
        results.append({
            "id": p.id,
            "beneficiary_id": p.beneficiary_id,
            # Shown exactly as stated by the applicant; missing values stay empty rather than defaulted
            "beneficiary_name": profile.get("full_name") or (b.full_name if b else None),
            "whatsapp_number": b.whatsapp_number if b else "",
            "telegram_chat_id": b.telegram_chat_id if b else "",
            "primary_channel": (b.primary_channel if b else None) or "telegram",
            "preferred_language": snap.get("language") or (b.preferred_language if b else None),
            "district": district_name,
            "state": snap.get("state") or (b.state if b else None),
            "applicant_profile": profile or None,
            "available_capital": snap.get("available_capital"),
            "annual_family_income": profile.get("annual_family_income") or (float(b.annual_family_income) if (b and b.annual_family_income) else None),
            "business_trade": p.business_trade,
            "scheme_tier": p.scheme_tier,
            "project_cost": cost,
            "sanctioned_loan": float(p.sanctioned_loan),
            "beneficiary_margin": float(p.beneficiary_margin),
            "monthly_emi": float(p.monthly_emi),
            "projected_dscr": float(p.projected_dscr) if p.projected_dscr is not None else None,
            "status": p.status,
            "dpr_pdf_url": pdf_url,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "details_confirmed_at": snap.get("details_confirmed_at"),
            "dpr_generated_at": snap.get("dpr_generated_at"),
            "corporation_loan": snap.get("financial_structure"),
            "pmegp": snap.get("pmegp"),
            "mudra": snap.get("mudra"),
            "reference_cost": _reference_cost(p.business_trade, district_name, cost),
            "verifications": [
                {
                    "field_officer_id": v.field_officer_id,
                    "geo_latitude": float(v.geo_latitude) if v.geo_latitude is not None else None,
                    "geo_longitude": float(v.geo_longitude) if v.geo_longitude is not None else None,
                    "margin_money_verified": bool(v.margin_money_verified),
                    "recommendation": v.recommendation,
                    "verified_at": v.verified_at.isoformat() if v.verified_at else None,
                }
                for v in sorted(p.verifications, key=lambda v: v.verified_at or 0)
            ],
            "officer_log": snap.get("officer_log") or [],
        })
    return results

@app.post("/internal/sanction/{proposal_id}")
def sanction_proposal(
    proposal_id: str,
    payload: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # only a logged-in officer can decide
):
    """
    SCA Field Officer approval endpoint:
    1. Log geo-verification and margin money status
    2. Transition status to SANCTIONED
    3. Trigger automated WhatsApp sanction notification to beneficiary
    """
    proposal = crud.get_proposal_by_id(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    officer_id = payload.field_officer_id
    if current_user and (not officer_id or officer_id == "OFFICER-DEFAULT"):
        officer_id = f"{current_user.full_name} ({current_user.badge_number or current_user.email})"

    # Record field verification
    verification_data = {
        "proposal_id": proposal.id,
        "field_officer_id": officer_id,
        "geo_latitude": payload.geo_latitude,
        "geo_longitude": payload.geo_longitude,
        "margin_money_verified": payload.margin_money_verified,
        "recommendation": payload.recommendation
    }

    crud.record_field_verification(db, verification_data)

    # Keep the officer's remarks with the application (the verification table has no remarks column)
    from datetime import datetime, timezone
    log = list(crud.get_proposal_snapshot(db, proposal.id).get("officer_log") or [])
    log.append({"officer": officer_id, "recommendation": payload.recommendation, "remarks": payload.remarks,
                "margin_money_verified": payload.margin_money_verified, "at": datetime.now(timezone.utc).isoformat()})
    crud.save_proposal_snapshot(db, proposal.id, {"officer_log": log})

    if payload.recommendation == "APPROVE":
        crud.update_proposal_status(db, proposal_id, "SANCTIONED")
        beneficiary = proposal.beneficiary

        # Automated Multi-Channel Sanction Dispatch (Telegram or WhatsApp)
        from app.dialogue.conversation_state import send_channel_text, send_channel_document

        sanction_msg = (
            f"🎉 *CONGRATULATIONS! LOAN SANCTION NOTIFICATION* 🎉\n\n"
            f"Dear {beneficiary.full_name or 'Entrepreneur'},\n"
            f"Your enterprise proposal for *{proposal.business_trade}* has been officially *SANCTIONED* by the State Channelizing Agency!\n\n"
            f"📋 *Sanction Summary*:\n"
            f"• Reference ID: DPR-{str(proposal.id)[:8].upper()}\n"
            f"• Scheme: {proposal.scheme_tier}\n"
            f"• Sanctioned Agency Loan: ₹{float(proposal.sanctioned_loan):,.2f}\n"
            f"• Verified Margin Money: ₹{float(proposal.beneficiary_margin):,.2f}\n"
            f"• Monthly EMI: ₹{float(proposal.monthly_emi):,.2f}\n\n"
            f"📍 Verified by Field Officer: {payload.field_officer_id}\n\n"
            f"Please visit your local SCA district office or nodal branch with your original Aadhaar and bank passbook for disbursement release."
        )

        send_channel_text(beneficiary, sanction_msg)

        if proposal.dpr_pdf_url:
            send_channel_document(
                beneficiary=beneficiary,
                document_url=proposal.dpr_pdf_url,
                filename=f"Sanction_Letter_{str(proposal.id)[:8]}.pdf",
                caption="Official Sanctioned DPR Letter"
            )

        return {"status": "success", "proposal_id": proposal_id, "new_status": "SANCTIONED"}

    elif payload.recommendation == "REJECT":
        crud.update_proposal_status(db, proposal_id, "REJECTED")
        beneficiary = proposal.beneficiary
        rejection_msg = (
            f"Notification from State Channelizing Agency:\n"
            f"Your proposal for {proposal.business_trade} could not be approved at this stage.\n"
            f"Reason / Remarks: {payload.remarks or 'Field verification requirements unmet.'}\n"
            f"You may submit a revised proposal or visit the district office for guidance."
        )
        from app.dialogue.conversation_state import send_channel_text
        send_channel_text(beneficiary, rejection_msg)
        return {"status": "success", "proposal_id": proposal_id, "new_status": "REJECTED"}

    else:
        crud.update_proposal_status(db, proposal_id, "REVISIT")
        return {"status": "success", "proposal_id": proposal_id, "new_status": "REVISIT"}
