from typing import Dict, Any, List, Optional
from app.finance.calculator import calculate_financial_structure
from app.finance.pmegp import compute_pmegp

def get_sector_specific_scheme(trade: str, cost: float, district: str) -> Optional[Dict[str, Any]]:
    """Determine sectoral/trade-specific government scheme based on business type."""
    trade_lower = trade.lower()

    if any(w in trade_lower for w in ["dairy", "cow", "buffalo", "milk", "cattle", "livestock"]):
        return {
            "name": "Kishan Credit Card (KCC) Animal Husbandry & AHIDF",
            "type": "Sectoral Livestock Working Capital & Infrastructure",
            "loan_amount": min(cost * 0.90, 200000.0),
            "interest_rate": "4.0% effective (7% base with 3% prompt repayment subvention)",
            "margin_money": "Nil up to ₹1.60 Lakhs, 10% above",
            "highlights": "Subsidized working capital for cattle feed, veterinary care, and insurance; 3% interest subvention under AHIDF.",
            "how_to_redeem": [
                "Fill out the simplified 1-page KCC Animal Husbandry application at your nearest Bank branch or PACS (Primary Agricultural Cooperative Society) in " + district + ".",
                "Provide Aadhaar, Land records (or proof of cattle shed), and ear-tag / veterinary certificate of cattle.",
                "Disbursement within 14 days directly into savings account with RuPay KCC card."
            ]
        }
    elif any(w in trade_lower for w in ["poultry", "chicken", "broiler", "layer", "egg"]):
        return {
            "name": "Poultry Venture Capital Fund (NABARD PVCF / AHIDF)",
            "type": "Poultry Infrastructure & Breeding Subsidy",
            "loan_amount": cost * 0.75,
            "interest_rate": "8.0% - 10.0% p.a.",
            "margin_money": "10% to 25% depending on scale",
            "highlights": "25% capital subsidy (33.33% for SC/ST and hilly areas) back-ended through NABARD.",
            "how_to_redeem": [
                "Submit project proposal with the bank-ready DPR generated here to any commercial bank or regional rural bank.",
                "Bank sanctions loan and sends subsidy claim to NABARD Regional Office.",
                "Subsidy is credited into a Subsidy Reserve Fund account with zero interest charged on that portion."
            ]
        }
    elif any(w in trade_lower for w in ["tailor", "tailoring", "garment", "weaving", "handloom", "embroidery", "textile"]):
        return {
            "name": "PM Vishwakarma Scheme / Weaver MUDRA",
            "type": "Artisan & Traditional Trade Support",
            "loan_amount": min(cost * 0.95, 100000.0 if cost <= 100000 else 200000.0),
            "interest_rate": "5.0% fixed concessional",
            "margin_money": "5% own contribution",
            "highlights": "Collateral-free credit (₹1 Lakh in Phase 1, ₹2 Lakhs in Phase 2) + ₹15,000 modern toolkit incentive grant + 5 days skill training with ₹500/day stipend.",
            "how_to_redeem": [
                "Visit your nearest Common Service Centre (CSC) in " + district + " or apply at pmvishwakarma.gov.in.",
                "Complete biometric Aadhaar authentication with Gram Panchayat / Urban Local Body verification.",
                "Attend basic training and receive loan disbursement with 5% fixed interest."
            ]
        }
    elif any(w in trade_lower for w in ["kirana", "shop", "grocery", "retail", "store", "stall", "vendor"]):
        return {
            "name": "PM SVANidhi / Stand-Up Micro-Credit",
            "type": "Micro-Retail & Vendor Working Capital",
            "loan_amount": min(cost, 50000.0),
            "interest_rate": "7.0% interest subsidy on prompt digital repayments",
            "margin_money": "Zero margin required",
            "highlights": "Collateral-free graduated working capital: ₹10,000 (1st tranche), ₹20,000 (2nd tranche), ₹50,000 (3rd tranche). Cashback up to ₹1,200/yr on digital transactions.",
            "how_to_redeem": [
                "Apply online on pmsvanidhi.mohua.gov.in or through any nationalized bank branch in " + district + ".",
                "Submit Aadhaar, Bank Passbook, and Letter of Recommendation (LOR) or Trade Certificate from local Municipality/Panchayat.",
                "Disbursement directly to your bank account with QR code for digital cashback."
            ]
        }
    elif any(w in trade_lower for w in ["flour", "oil", "spice", "food", "bakery", "pickle", "processing"]):
        return {
            "name": "PM Formalisation of Micro Food Processing Enterprises (PM-FME)",
            "type": "Food Processing Credit-Linked Capital Subsidy",
            "loan_amount": cost * 0.65,
            "interest_rate": "8.5% - 9.5% p.a.",
            "margin_money": "10% beneficiary contribution",
            "highlights": "35% credit-linked capital subsidy (maximum ₹10 Lakhs) for machinery, packaging, and unit modernization.",
            "how_to_redeem": [
                "Apply online at pmfme.mofpi.gov.in with your Detailed Project Report (DPR).",
                "Assistance provided by District Resource Person (DRP) at District Industries Centre (DIC) in " + district + ".",
                "Bank sanctions loan and subsidy is disbursed directly to your loan account."
            ]
        }
    return None

def get_all_eligible_schemes(
    cost: float,
    trade: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    available_capital: Optional[float] = None,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compile a complete multi-scheme package for an entrepreneur based on project cost and trade.
    Returns:
      - primary_sca: NBCFDC / NMDFC / State Channelising Agency scheme (MFS or TLS)
      - mudra: Pradhan Mantri MUDRA Yojana (Shishu / Kishore / Tarun)
      - pmegp: Prime Minister's Employment Generation Programme, computed from the applicant profile
      - sectoral: Sector/Trade specific scheme if applicable
    """
    # 1. Primary SCA Scheme (MFS or TLS)
    primary_calc = calculate_financial_structure(cost)

    # 2. PMMY Scheme Tier
    if cost <= 50000:
        mudra_tier = "Shishu"
        mudra_loan = cost
        mudra_margin = 0.0
        mudra_margin_pct = 0
        mudra_rate = "8.5% - 9.5%"
    elif cost <= 500000:
        mudra_tier = "Kishore"
        mudra_loan = cost * 0.85
        mudra_margin = cost * 0.15
        mudra_margin_pct = 15
        mudra_rate = "9.5% - 10.5%"
    else:
        mudra_tier = "Tarun"
        mudra_loan = min(cost * 0.85, 1000000.0)
        mudra_margin = cost - mudra_loan
        mudra_margin_pct = int(round((mudra_margin / cost) * 100))
        mudra_rate = "10.0% - 11.5%"

    mudra_scheme = {
        "name": f"Pradhan Mantri MUDRA Yojana (PMMY) - {mudra_tier}",
        "tier": mudra_tier,
        "type": "Zero-Collateral Commercial Bank Loan",
        "loan_amount": mudra_loan,
        "margin_money": mudra_margin,
        "margin_pct": mudra_margin_pct,
        "interest_rate": f"{mudra_rate} p.a.",
        "tenure": "36 to 60 months",
        "source_id": "PMMY_PARTNER_ELIGIBILITY",
        "source_organization": "Micro Units Development & Refinance Agency (MUDRA)",
        "source_page": None,
        "verification_status": "NEEDS_SOURCE_VERIFICATION",
        "source_type": "UNVERIFIED_POLICY_GUIDELINE",
        "provenance_note": "Borrower loan tiers (Shishu/Kishore/Tarun) reflect standard banking practice; awaiting formal Ministry circular in repository.",
        "highlights": "No collateral or third-party guarantor required. Covered under CGFMU government credit guarantee. Includes MUDRA RuPay Card.",
        "how_to_redeem": [
            "Apply online through the government JanSamarth Portal (www.jansamarth.in) or UdyamiMitra Portal (www.udyamimitra.in).",
            "Alternatively, walk into any Public Sector Bank (SBI, Canara Bank, BoB), Regional Rural Bank (Karnataka Gramin Bank), or local Bank branch in " + (district or "your district") + ".",
            "Submit your KYC (Aadhaar, PAN), Bank Passbook copy, Udyam Registration (free online), and the DPR generated here.",
            "Loan is sanctioned and credited into your account with MUDRA RuPay card."
        ]
    }

    # 3. PMEGP (KVIC/KVIB/DIC): rates depend on the applicant's stated category and area (verified guideline rules)
    pmegp_scheme = compute_pmegp(cost, trade, profile)

    # 4. Sectoral Scheme (if matching)
    sectoral_scheme = get_sector_specific_scheme(trade or "", cost, district or "your district")

    return {
        "cost": cost,
        "trade": trade,
        "district": district,
        "state": state,
        "available_capital": available_capital,
        "primary_sca": primary_calc,
        "mudra": mudra_scheme,
        "pmegp": pmegp_scheme,
        "sectoral": sectoral_scheme
    }
