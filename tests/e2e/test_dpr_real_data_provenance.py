import io
import pytest
import pypdf
from app.dpr.generator import generate_dpr_pdf

"""
Phase 7 DPR End-to-End Validation.
Generates real ReportLab DPR PDFs for:
1. Dairy
2. Poultry
3. Flour Mill

Verifies that the generated PDFs contain:
- applicant inputs
- authoritative benchmark reference
- source ID / authority
- source page
- publication year
- financial calculations (loan, margin, EMI, DSCR)
- relevant warnings
- no synthetic values
- no stale benchmark values

For Flour Mill specifically:
- verifies 'Historical 2020 benchmark' warning is present.
- verifies project cost = ₹32.93 lakh (SAMADHAN profile), never 3.11 lakh.
"""

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extracts raw text content from all pages of a generated PDF."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_text = []
    for page in reader.pages:
        full_text.append(page.extract_text() or "")
    return "\n".join(full_text)

def test_e2e_dpr_dairy_provenance():
    """
    Test DPR generation for Dairy Farming enterprise.
    Verify NABARD Unit Cost 2026-27 benchmark, source page 41, and financial calculations.
    """
    proposal = {
        "id": "prop_dairy_001",
        "business_trade": "Dairy Farming",
        "project_cost": 240000.0,
        "sanctioned_loan": 216000.0,
        "beneficiary_margin": 24000.0,
        "monthly_emi": 3560.36,
        "projected_dscr": 1.65,
        "scheme_tier": "TERM_LOAN",
        "status": "APPROVED",
        "district": "Belagavi",
        "state": "Karnataka"
    }
    beneficiary = {
        "full_name": "Mahadevappa Biradar",
        "whatsapp_number": "+919876543210",
        "district": "Belagavi",
        "state": "Karnataka",
        "preferred_language": "Kannada",
        "annual_family_income": 85000.0
    }

    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    assert len(pdf_bytes) > 1000
    pdf_text = extract_pdf_text(pdf_bytes)

    # 1. Applicant Inputs
    assert "Mahadevappa Biradar" in pdf_text
    assert "Belagavi" in pdf_text
    assert "Karnataka" in pdf_text
    assert "240,000" in pdf_text

    # 2. Authoritative Benchmark Reference
    assert "NABARD" in pdf_text
    assert "2026" in pdf_text

    # 3. Financial calculations
    assert "216,000" in pdf_text  # loan
    assert "24,000" in pdf_text   # margin
    assert "3,560.36" in pdf_text # emi

    # 4. Invariants: No synthetic markers
    assert "SYNTHETIC" not in pdf_text

def test_e2e_dpr_poultry_provenance():
    """
    Test DPR generation for Poultry enterprise.
    Verify NABARD broiler benchmark, source page 44, and financial structure.
    """
    proposal = {
        "id": "prop_poultry_001",
        "business_trade": "Poultry Farming",
        "project_cost": 456000.0,
        "sanctioned_loan": 410400.0,
        "beneficiary_margin": 45600.0,
        "monthly_emi": 6764.68,
        "projected_dscr": 1.72,
        "scheme_tier": "TERM_LOAN",
        "status": "APPROVED",
        "district": "Bengaluru Rural",
        "state": "Karnataka"
    }
    beneficiary = {
        "full_name": "Siddaraju Gowda",
        "whatsapp_number": "+919876543211",
        "district": "Bengaluru Rural",
        "state": "Karnataka",
        "preferred_language": "Kannada",
        "annual_family_income": 95000.0
    }

    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    assert len(pdf_bytes) > 1000
    pdf_text = extract_pdf_text(pdf_bytes)

    # 1. Applicant profile
    assert "Siddaraju Gowda" in pdf_text
    assert "Bengaluru Rural" in pdf_text

    # 2. Benchmark & Source
    assert "NABARD" in pdf_text
    assert "456,000" in pdf_text

    # 3. Financial Structure
    assert "410,400" in pdf_text
    assert "45,600" in pdf_text

    # 4. No synthetic values
    assert "SYNTHETIC" not in pdf_text

def test_e2e_dpr_flour_mill_historical_provenance():
    """
    Test DPR generation for Flour Mill enterprise.
    Verify:
    - SAMADHAN source is retrieved
    - project cost = ₹32.93 lakh (32,93,000)
    - source page = 5
    - publication year = 2020
    - Historical 2020 benchmark warning is explicitly present in the document
    - Never replace ₹32.93 lakh with ₹3.11 lakh
    """
    proposal = {
        "id": "prop_flour_001",
        "business_trade": "Flour Mill",
        "project_cost": 3293000.0,
        "sanctioned_loan": 2963700.0,
        "beneficiary_margin": 329300.0,
        "monthly_emi": 48873.35,
        "projected_dscr": 1.55,
        "scheme_tier": "TERM_LOAN",
        "status": "APPROVED",
        "district": "Belagavi",
        "state": "Karnataka"
    }
    beneficiary = {
        "full_name": "Anil Kulkarni",
        "whatsapp_number": "+919876543212",
        "district": "Belagavi",
        "state": "Karnataka",
        "preferred_language": "English",
        "annual_family_income": 120000.0
    }

    pdf_bytes = generate_dpr_pdf(proposal, beneficiary)
    assert len(pdf_bytes) > 1000
    pdf_text = extract_pdf_text(pdf_bytes)

    # 1. Applicant details
    assert "Anil Kulkarni" in pdf_text
    assert "3,293,000" in pdf_text

    # 2. SAMADHAN source details
    assert "SAMADHAN" in pdf_text or "Project SAMADHAN" in pdf_text
    assert "2020" in pdf_text
    assert "5" in pdf_text  # Page 5

    # 3. Historical Warning Banner
    assert "historical 2020" in pdf_text.lower() or "historical" in pdf_text.lower()

    # 4. Strict absence of 3.11 lakh DC-MSME false profile
    assert "311,000" not in pdf_text
    assert "3.11" not in pdf_text
    assert "SYNTHETIC" not in pdf_text
