"""
Scheme figures follow the applicant's category and the verified official rules.

1. SC -> NSFDC (micro finance up to Rs 1.40 lakh unit cost, term loan above), 90% loan, 6.5% / 8%
2. OBC -> NBCFDC individual loan, 85% loan, 7% up to Rs 1.25 lakh loan, 8% above
3. ST -> NSTFDC term loan slabs; ST women with small loans -> AMSY at 4%; income limit flagged as conflicting
4. Income above the corporation's limit -> not eligible; minority -> not verified; general -> no corporation loan
5. MUDRA shows only the notified loan categories (Tarun Plus condition included), never a rate or loan share
6. Advisory text cites its sources and contains no DSCR or invented MUDRA rate
7. Every rule file points at a source registered in the manifest
"""
import json
import os

from app.ai.advisory_text import build_advisory
from app.finance.corporation_loans import compute_corporation_loan, quarterly_instalment
from app.finance.multi_schemes import compute_mudra, get_all_eligible_schemes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _loan(category, cost, **profile):
    return compute_corporation_loan(cost, {"social_category": category, "annual_family_income": 150000.0, **profile})


# 1. SC -> NSFDC
def test_sc_gets_nsfdc_terms():
    mfs = _loan("sc", 120000.0)
    assert (mfs["scheme"], mfs["loan"], mfs["rate"], mfs["morat"], mfs["repayment_quarters"]) == ("NSFDC_MICRO_FINANCE", 108000.0, 6.5, 3, 11)
    tl = _loan("sc", 5000000.0)
    assert (tl["scheme"], tl["loan"], tl["rate"], tl["repayment_quarters"]) == ("NSFDC_TERM_LOAN", 4500000.0, 8.0, 26)
    assert tl["income_limit"] == 500000.0


# 2. OBC -> NBCFDC
def test_obc_gets_nbcfdc_terms():
    small = _loan("obc", 120000.0)
    assert (small["scheme"], small["loan"], small["loan_pct"], small["rate"], small["repayment_quarters"]) == \
        ("NBCFDC_INDIVIDUAL", 102000.0, 85.0, 7.0, 15)
    large = _loan("obc", 5000000.0)
    assert (large["loan"], large["rate"], large["repayment_quarters"]) == (2500000.0, 8.0, 27)


# 3. ST -> NSTFDC
def test_st_gets_nstfdc_terms_and_income_conflict_flag():
    tl = _loan("st", 800000.0, gender="male")
    assert (tl["scheme"], tl["loan"], tl["rate"]) == ("NSTFDC_TERM_LOAN", 720000.0, 8.0)
    assert tl["income_limit_conflict"] is True
    amsy = _loan("st", 100000.0, gender="female")
    assert (amsy["scheme"], amsy["rate"]) == ("NSTFDC_AMSY", 4.0)


# 4. Ineligible or unverified cases produce no loan figure
def test_no_loan_figures_when_not_eligible_or_not_verified():
    rich = _loan("sc", 200000.0, annual_family_income=600000.0)
    assert (rich["available"], rich["reason_code"], rich["loan"]) == (False, "income_above_limit", 0.0)
    minority = _loan("minority", 200000.0)
    assert (minority["available"], minority["reason_code"]) == (False, "not_verified")
    general = _loan("general", 200000.0)
    assert (general["available"], general["reason_code"]) == (False, "no_corporation_for_category")


# 5. MUDRA
def test_mudra_categories_only():
    assert compute_mudra(40000.0)["possible_tiers"] == ["Shishu"]
    big = compute_mudra(1500000.0)
    assert big["possible_tiers"][-1] == "Tarun Plus" and big["tarun_plus_condition"] is True
    assert big["interest_rate"] is None and big["margin_money"] is None


# 6. Advisory text
def test_advisory_cites_sources_and_invents_nothing():
    profile = {"social_category": "obc", "gender": "female", "area_type": "rural", "age": 30, "annual_family_income": 150000.0}
    schemes = get_all_eligible_schemes(200000.0, "Dairy Farming", "Belagavi", "Karnataka", 20000.0, profile)
    text = build_advisory("Dairy Farming", "Belagavi", 200000.0, 20000.0, schemes, "english")
    assert "NBCFDC Individual Loan Scheme" in text and "Pattern of Finance" in text
    assert "₹1,70,000" in text and "8% per year" in text
    assert "PMEGP" in text and "35% = ₹70,000" in text
    assert "decided by the bank" in text
    assert "DSCR" not in text and "85% loan" not in text


def test_quarterly_instalment_matches_annuity():
    q = quarterly_instalment(180000.0, 8.0, 26)
    r = 0.02
    assert abs(q - 180000.0 * r * (1 + r) ** 26 / ((1 + r) ** 26 - 1)) < 0.01


# 7. Rule files reference registered sources
def test_rule_files_cite_registered_sources():
    manifest = json.load(open(os.path.join(ROOT, "data", "manifests", "sources_manifest.json"), encoding="utf-8"))
    registered = {s["source_id"] for s in manifest["sources"]}
    for name in ("nsfdc_rules.json", "nbcfdc_rules.json", "nstfdc_rules.json", "pmmy_pib_2024_rules.json"):
        data = json.load(open(os.path.join(ROOT, "data", "processed", "schemes", name), encoding="utf-8"))
        assert data["source_id"] in registered
        for rule in data["rules"]:
            assert rule["source_id"] in registered, (name, rule["rule_id"])
