"""
Comprehensive Integration Test Suite for Grounded Financial Engine and DPR Integration.
Validates:
1. Dairy uses NABARD data
2. Poultry uses NABARD data
3. Flour Mill uses model project profile
4. Flour Mill retains 2020 publication year
5. Flour Mill retains historical benchmark designation
6. Tailoring returns DATA_NOT_AVAILABLE
7. Kirana returns DATA_NOT_AVAILABLE
8. PMEGP uses only verified extracted rules
9. PMMY unverified values cannot enter authoritative calculations
10. Derived EMI has no fake source citation
11. DSCR is marked as derived
12. DPR contains provenance
13. User-entered project cost remains distinguishable from benchmark cost
14. Synthetic fallback is blocked under REAL_DATA_ONLY=True
"""
import io
import pytest
from pypdf import PdfReader
from app.finance.repository import (
    benchmark_repository,
    BenchmarkSourceType,
    VerificationStatus
)
from app.finance.calculator import calculate_financial_structure
from app.finance.multi_schemes import get_all_eligible_schemes
from app.finance.deviation import analyze_benchmark_deviation
from app.finance.credit_context import credit_context_service
from app.dpr.generator import generate_dpr_pdf

# 1. Dairy uses NABARD data
def test_dairy_uses_nabard_data():
    bench = benchmark_repository.get_benchmark("dairy cow", real_data_only=True)
    assert bench["verification_status"] == VerificationStatus.VERIFIED.value
    assert bench["source_type"] == BenchmarkSourceType.NABARD_UNIT_COST.value
    assert bench["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27"
    assert bench["source_page"] == 41
    assert bench["total_cost"] == 229000.0

# 2. Poultry uses NABARD data
def test_poultry_uses_nabard_data():
    bench = benchmark_repository.get_benchmark("poultry broiler", real_data_only=True)
    assert bench["verification_status"] == VerificationStatus.VERIFIED.value
    assert bench["source_type"] == BenchmarkSourceType.NABARD_UNIT_COST.value
    assert bench["source_id"] == "NABARD_KA_UC_BOOKLET_2026_27"
    assert bench["source_page"] == 50
    assert bench["total_cost"] == 456000.0

# 3. Flour Mill uses model project profile
def test_flour_mill_uses_model_project_profile():
    bench = benchmark_repository.get_benchmark("atta chakki flour mill", real_data_only=True)
    assert bench["verification_status"] == VerificationStatus.VERIFIED.value
    assert bench["source_type"] == BenchmarkSourceType.MODEL_PROJECT_PROFILE.value
    assert bench["source_id"] == "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE"
    assert bench["total_cost"] == 3293000.0

# 4. Flour Mill retains 2020 publication year
def test_flour_mill_retains_2020_publication_year():
    bench = benchmark_repository.get_benchmark("flour mill", real_data_only=True)
    assert bench["publication_year"] == 2020

# 5. Flour Mill retains historical benchmark designation
def test_flour_mill_retains_historical_benchmark_designation():
    bench = benchmark_repository.get_benchmark("flour mill", real_data_only=True)
    assert bench["cost_nature"] == "HISTORICAL_BENCHMARK_2020"

# 6. Tailoring returns DATA_NOT_AVAILABLE
def test_tailoring_returns_data_not_available():
    bench = benchmark_repository.get_benchmark("Tailoring Shop", real_data_only=True)
    assert bench["status"] == "DATA_NOT_AVAILABLE"
    assert bench["verification_status"] == VerificationStatus.DATA_NOT_AVAILABLE.value
    assert bench["is_synthetic"] is False

# 7. Kirana returns DATA_NOT_AVAILABLE
def test_kirana_returns_data_not_available():
    bench = benchmark_repository.get_benchmark("Kirana Store", real_data_only=True)
    assert bench["status"] == "DATA_NOT_AVAILABLE"
    assert bench["verification_status"] == VerificationStatus.DATA_NOT_AVAILABLE.value
    assert bench["is_synthetic"] is False

# 8. PMEGP uses only verified extracted rules
def test_pmegp_uses_only_verified_extracted_rules():
    profile = {"gender": "female", "social_category": "obc", "area_type": "rural", "age": 34}
    schemes = get_all_eligible_schemes(cost=200000.0, trade="Dairy", district="Belagavi", profile=profile)
    pmegp = schemes["pmegp"]
    assert pmegp["verification_status"] == "VERIFIED_OFFICIAL"
    assert pmegp["source_id"] == "PMEGP_REVISED_GUIDELINES_2023"
    assert pmegp["source_page"] == 4
    assert pmegp["eligible"] is True
    assert pmegp["subsidy_pct"] == 35.0
    assert pmegp["subsidy_amount"] == 70000.0
    assert pmegp["own_contribution_pct"] == 5
    assert pmegp["bank_loan_pct"] == 95.0
    assert pmegp["bank_loan"] == 190000.0


def test_pmegp_without_profile_shows_no_subsidy_figure():
    pmegp = get_all_eligible_schemes(cost=200000.0, trade="Dairy", district="Belagavi")["pmegp"]
    assert pmegp["eligible"] is None
    assert pmegp["subsidy_pct"] is None
    assert pmegp["subsidy_amount"] is None

# 9. PMMY unverified values cannot enter authoritative calculations
def test_pmmy_unverified_values_cannot_enter_authoritative_calculations():
    schemes = get_all_eligible_schemes(cost=200000.0, district="Belagavi")
    mudra = schemes["mudra"]
    assert mudra["verification_status"] == "NEEDS_SOURCE_VERIFICATION"
    assert mudra["source_type"] == "UNVERIFIED_POLICY_GUIDELINE"
    assert "awaiting formal Ministry circular" in mudra["provenance_note"]

# 10. Derived EMI has no fake source citation
def test_derived_emi_has_no_fake_source_citation():
    res = calculate_financial_structure(229000.0)
    evidence = res["evidence"]
    derived_records = {r["parameter"]: r for r in evidence["derived_records"]}
    emi_rec = derived_records["monthly_emi"]
    assert emi_rec["source_type"] == "DERIVED_MATHEMATICAL"
    assert emi_rec["source_id"] is None
    assert emi_rec["source_page"] is None
    assert "loan_amount" in emi_rec["derived_from"]
    assert "interest_rate" in emi_rec["derived_from"]

# 11. DSCR is marked as derived
def test_dscr_is_marked_as_derived():
    res = calculate_financial_structure(229000.0)
    prov_table = res["provenance_table"]
    derived_entries = [row for row in prov_table if row["type"] == "DERIVED_CALCULATION"]
    assert len(derived_entries) >= 3
    for entry in derived_entries:
        assert entry["page"] == "—"
        assert entry["source"] == "Derived by Deterministic Engine"

# 12. DPR contains provenance
def test_dpr_contains_provenance():
    proposal = {
        "id": "12345678-abcd-1234-abcd-1234567890ab",
        "business_trade": "Dairy Farming (2 Cows)",
        "scheme_tier": "TERM_LOAN",
        "project_cost": 229000.0,
        "sanctioned_loan": 206100.0,
        "beneficiary_margin": 22900.0,
        "monthly_emi": 3409.82,
        "projected_dscr": 1.72,
        "status": "DRAFT"
    }
    beneficiary = {
        "full_name": "Shivappa Naik",
        "whatsapp_number": "919988776655",
        "district": "Belagavi",
        "state": "Karnataka",
        "preferred_language": "kannada",
        "annual_family_income": 65000.0
    }
    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = " ".join(p.extract_text() for p in reader.pages)
    assert "Source & Data Provenance" in full_text
    assert "NABARD" in full_text

# 13. User-entered project cost remains distinguishable from benchmark cost
def test_user_entered_project_cost_remains_distinguishable():
    analysis = analyze_benchmark_deviation(
        user_project_cost=400000.0,
        trade="Dairy Farming",
        district="Belagavi"
    )
    assert analysis["user_project_cost"] == 400000.0
    assert analysis["reference_cost"] == 229000.0
    assert analysis["percentage_difference"] == 74.67
    assert analysis["direction"] == "ABOVE_BENCHMARK"
    assert analysis["is_significant_deviation"] is True
    assert "Field verification must review enhanced equipment capacity" in analysis["advisory"]

# 14. Synthetic fallback is blocked under REAL_DATA_ONLY=True
def test_synthetic_fallback_is_blocked_under_real_data_only():
    bench = benchmark_repository.get_benchmark("Handloom Weaving Unit", real_data_only=True)
    assert bench["status"] == "DATA_NOT_AVAILABLE"
    assert bench["verification_status"] == VerificationStatus.DATA_NOT_AVAILABLE.value
    assert bench["is_synthetic"] is False
    assert "capex" not in bench

# 15. Flour Mill DPR contains historical 2020 warning
def test_flour_mill_dpr_contains_historical_warning():
    proposal = {
        "id": "87654321-dcba-4321-dcba-0987654321fe",
        "business_trade": "Mini Flour Mill (Atta Chakki)",
        "scheme_tier": "TERM_LOAN",
        "project_cost": 3293000.0,
        "sanctioned_loan": 2963700.0,
        "beneficiary_margin": 329300.0,
        "monthly_emi": 49091.22,
        "projected_dscr": 1.68,
        "status": "DRAFT"
    }
    beneficiary = {
        "full_name": "Kallappa Gouda",
        "whatsapp_number": "919876500000",
        "district": "Belagavi",
        "state": "Karnataka",
        "preferred_language": "kannada",
        "annual_family_income": 95000.0
    }
    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = " ".join(p.extract_text() for p in reader.pages)
    assert "SAMADHAN" in full_text
    assert "2020" in full_text
    assert "historical" in full_text.lower()

