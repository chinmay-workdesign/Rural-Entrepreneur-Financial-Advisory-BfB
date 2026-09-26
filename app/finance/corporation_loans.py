"""
Concessional loan from the national finance corporation that serves the applicant's social category.

SC -> NSFDC, OBC -> NBCFDC, ST -> NSTFDC, Minority -> NMDFC (not verified), General -> none.
Every percentage, ceiling, rate and period is read from the verified rule files in
data/processed/schemes/ (saved official pages, see the source manifest). This module only does the
arithmetic: loan = share x cost within the ceiling, and a reducing-balance instalment.
All three corporations state quarterly instalments, so the instalment is computed per quarter.
"""
import os
import json
import math
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.finance.formatting import format_inr

_SCHEMES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "processed", "schemes",
)

AGENCY = {
    "sc": ("NSFDC", "National Scheduled Castes Finance and Development Corporation"),
    "obc": ("NBCFDC", "National Backward Classes Finance & Development Corporation"),
    "st": ("NSTFDC", "National Scheduled Tribes Finance and Development Corporation"),
    "minority": ("NMDFC", "National Minorities Development & Finance Corporation"),
}


@lru_cache(maxsize=None)
def _rules(filename: str) -> Dict[str, Dict[str, Any]]:
    with open(os.path.join(_SCHEMES_DIR, filename), "r", encoding="utf-8") as f:
        return {r["rule_id"]: r for r in json.load(f)["rules"]}


def quarterly_instalment(principal: float, annual_rate_pct: float, quarters: int) -> float:
    """Equal quarterly instalment on a reducing balance."""
    r = annual_rate_pct / 100.0 / 4.0
    if quarters <= 0:
        raise ValueError("Repayment period must be at least one quarter")
    if r == 0:
        return principal / quarters
    growth = math.pow(1 + r, quarters)
    return principal * r * growth / (growth - 1)


def _terms(scheme_code: str, scheme_name: str, agency: str, cost: float, loan: float, rate: float,
           tenure_months: int, moratorium_months: Optional[int], sources: List[Dict[str, Any]],
           notes: List[str]) -> Dict[str, Any]:
    morat = moratorium_months or 0
    repay_quarters = (tenure_months - morat) // 3
    q_inst = quarterly_instalment(loan, rate, repay_quarters)
    margin = cost - loan
    return {
        "eligible": True,
        "available": True,
        "scheme": scheme_code,
        "scheme_name": scheme_name,
        "agency": agency,
        "cost": round(cost, 2),
        "loan": round(loan, 2),
        "margin": round(margin, 2),
        "margin_pct": round(margin / cost * 100, 2),
        "loan_pct": round(loan / cost * 100, 2),
        "rate": rate,
        "tenure": tenure_months,
        "morat": moratorium_months,
        "repayment_months": tenure_months - morat,
        "repayment_quarters": repay_quarters,
        "instalment_frequency": "QUARTERLY",
        "quarterly_instalment": round(q_inst, 2),
        # Monthly figure kept for the proposal record and dashboard; the scheme itself is repaid quarterly
        "emi": round(q_inst / 3.0, 2),
        "sources": sources,
        "notes": notes,
    }


def _unavailable(category: Optional[str], reason_code: str, reasons: List[str], agency: Optional[str] = None,
                 sources: Optional[List[Dict[str, Any]]] = None, eligible: Optional[bool] = False) -> Dict[str, Any]:
    return {
        "eligible": eligible,
        "available": False,
        "scheme": "NONE",
        "scheme_name": None,
        "agency": agency,
        "category": category,
        "reason_code": reason_code,
        "reasons": reasons,
        "sources": sources or [],
        "loan": 0.0,
        "margin": None,
        "emi": 0.0,
    }


def _income_check(income: Optional[float], limit: float, agency: str, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if income is not None and income > limit:
        return _unavailable(None, "income_above_limit",
                            [f"{agency} requires annual family income up to {format_inr(limit)}."], agency, [source])
    return None


def _src(rule: Dict[str, Any]) -> Dict[str, Any]:
    return {"source_id": rule["source_id"], "section": rule.get("section"), "rule_id": rule["rule_id"]}


def _nsfdc(cost: float, income: Optional[float]) -> Dict[str, Any]:
    r = _rules("nsfdc_rules.json")
    blocked = _income_check(income, r["NSFDC_MAX_FAMILY_INCOME"]["value"], "NSFDC", _src(r["NSFDC_MAX_FAMILY_INCOME"]))
    if blocked:
        return blocked
    if cost <= r["NSFDC_MFS_MAX_UNIT_COST"]["value"]:
        loan = min(cost * r["NSFDC_MFS_LOAN_PCT"]["value"] / 100.0, r["NSFDC_MFS_MAX_LOAN"]["value"])
        rep = r["NSFDC_MFS_REPAYMENT"]
        keys = ("NSFDC_MFS_MAX_UNIT_COST", "NSFDC_MFS_LOAN_PCT", "NSFDC_MFS_MAX_LOAN", "NSFDC_MFS_INTEREST", "NSFDC_MFS_REPAYMENT")
        return _terms("NSFDC_MICRO_FINANCE", "NSFDC Micro Finance Scheme", "NSFDC", cost, loan,
                      r["NSFDC_MFS_INTEREST"]["value"], rep["value"], rep["moratorium_months"],
                      [_src(r[k]) for k in keys] + [_src(r["NSFDC_MAX_FAMILY_INCOME"])], [])
    if cost <= r["NSFDC_TL_MAX_UNIT_COST"]["value"]:
        loan = min(cost * r["NSFDC_TL_LOAN_PCT"]["value"] / 100.0, r["NSFDC_TL_MAX_LOAN"]["value"])
        rep = r["NSFDC_TL_REPAYMENT"]
        keys = ("NSFDC_TL_MAX_UNIT_COST", "NSFDC_TL_LOAN_PCT", "NSFDC_TL_MAX_LOAN", "NSFDC_TL_INTEREST", "NSFDC_TL_REPAYMENT")
        return _terms("NSFDC_TERM_LOAN", "NSFDC Term Loan", "NSFDC", cost, loan,
                      r["NSFDC_TL_INTEREST"]["value"], rep["value"], rep["moratorium_months"],
                      [_src(r[k]) for k in keys] + [_src(r["NSFDC_MAX_FAMILY_INCOME"])],
                      ["Moratorium is 12 months for plantation and construction activities."])
    return _unavailable(None, "cost_above_ceiling", ["NSFDC term loans are for units costing up to ₹50 lakh."], "NSFDC")


def _nbcfdc(cost: float, income: Optional[float]) -> Dict[str, Any]:
    r = _rules("nbcfdc_rules.json")
    blocked = _income_check(income, r["NBCFDC_MAX_FAMILY_INCOME"]["value"], "NBCFDC", _src(r["NBCFDC_MAX_FAMILY_INCOME"]))
    if blocked:
        return blocked
    loan = min(cost * r["NBCFDC_IND_LOAN_PCT"]["value"] / 100.0, r["NBCFDC_IND_MAX_LOAN"]["value"])
    slab1 = loan <= r["NBCFDC_IND_SLAB1_UPTO"]["value"]
    rate_rule = r["NBCFDC_IND_SLAB1_INTEREST" if slab1 else "NBCFDC_IND_SLAB2_INTEREST"]
    rep = r["NBCFDC_IND_SLAB1_REPAYMENT" if slab1 else "NBCFDC_IND_SLAB2_REPAYMENT"]
    sources = [_src(r[k]) for k in ("NBCFDC_IND_LOAN_PCT", "NBCFDC_IND_MAX_LOAN", "NBCFDC_MAX_FAMILY_INCOME")] + [_src(rate_rule), _src(rep)]
    return _terms("NBCFDC_INDIVIDUAL", "NBCFDC Individual Loan Scheme", "NBCFDC", cost, loan,
                  rate_rule["value"], rep["value"], rep["moratorium_months"], sources,
                  ["The 15% balance is the channel partner's or your share.",
                   "1% yearly rebate for timely repayment, shared between the channel partner and you."])


def _nstfdc(cost: float, income: Optional[float], gender: Optional[str]) -> Dict[str, Any]:
    r = _rules("nstfdc_rules.json")
    if cost > r["NSTFDC_TL_MAX_UNIT_COST"]["value"]:
        return _unavailable(None, "cost_above_ceiling", ["NSTFDC term loans are for units costing up to ₹50 lakh."], "NSTFDC")
    loan = cost * r["NSTFDC_TL_LOAN_PCT"]["value"] / 100.0
    income_rule = r["NSTFDC_MAX_FAMILY_INCOME"]
    notes = ["NSTFDC's own site gives two income limits (₹3 lakh, or ₹98,000 rural / ₹1,20,000 urban); "
             "the SCA will confirm which applies."]
    if gender == "female" and loan <= r["NSTFDC_AMSY_INTEREST"]["applies_to_max_loan"]:
        rep = r["NSTFDC_TL_REPAYMENT"]
        result = _terms("NSTFDC_AMSY", "NSTFDC Adivasi Mahila Sashaktikaran Yojana (AMSY)", "NSTFDC", cost, loan,
                        r["NSTFDC_AMSY_INTEREST"]["value"], rep["value"], None,
                        [_src(r["NSTFDC_AMSY_MAX_LOAN"]), _src(r["NSTFDC_AMSY_INTEREST"]), _src(rep), _src(income_rule)],
                        notes + ["No own contribution is insisted upon under AMSY.",
                                 "Instalment assumes no moratorium; the site does not state its length."])
    else:
        rate = next(s["pct"] for s in r["NSTFDC_TL_INTEREST_SLABS"]["value"] if s["max_loan"] is None or loan <= s["max_loan"])
        promoter = next(s["pct"] for s in r["NSTFDC_TL_PROMOTER_CONTRIBUTION"]["value"] if s["max_cost"] is None or cost <= s["max_cost"])
        rep = r["NSTFDC_TL_REPAYMENT"]
        result = _terms("NSTFDC_TERM_LOAN", "NSTFDC Term Loan", "NSTFDC", cost, loan, rate, rep["value"], None,
                        [_src(r[k]) for k in ("NSTFDC_TL_MAX_UNIT_COST", "NSTFDC_TL_LOAN_PCT", "NSTFDC_TL_INTEREST_SLABS",
                                              "NSTFDC_TL_PROMOTER_CONTRIBUTION", "NSTFDC_TL_REPAYMENT")] + [_src(income_rule)],
                        notes + [f"Minimum promoter contribution for this project size: {promoter:g}% of project cost.",
                                 "Instalment assumes no moratorium; the site does not state its length."])
    result["income_limit_conflict"] = True
    return result


def compute_corporation_loan(cost: float, profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Loan from the corporation matching the applicant's stated category, or the reason there is none."""
    profile = profile or {}
    category = profile.get("social_category")
    income = profile.get("annual_family_income")
    if category == "sc":
        result = _nsfdc(cost, income)
    elif category == "obc":
        result = _nbcfdc(cost, income)
    elif category == "st":
        result = _nstfdc(cost, income, profile.get("gender"))
    elif category == "minority":
        result = _unavailable("minority", "not_verified",
                              ["NMDFC terms could not be verified from an official source yet."], "NMDFC", eligible=None)
    elif category == "general":
        result = _unavailable("general", "no_corporation_for_category",
                              ["The national finance corporations lend only to SC, ST, Backward Classes and Minorities."])
    else:
        result = _unavailable(category, "category_missing", ["Social category not provided."], eligible=None)
    result["category"] = category
    limit_rule = {"sc": ("nsfdc_rules.json", "NSFDC_MAX_FAMILY_INCOME"), "obc": ("nbcfdc_rules.json", "NBCFDC_MAX_FAMILY_INCOME"),
                  "st": ("nstfdc_rules.json", "NSTFDC_MAX_FAMILY_INCOME")}.get(category)
    result["income_limit"] = _rules(limit_rule[0])[limit_rule[1]]["value"] if limit_rule else None
    if category in AGENCY:
        result["agency_full_name"] = AGENCY[category][1]
    return result
