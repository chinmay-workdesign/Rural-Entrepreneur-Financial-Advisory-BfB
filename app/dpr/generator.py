import os
from app.finance.formatting import format_inr
import io
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("dpr_generator")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)

NOT_PROVIDED = "Not provided"
GENDER_LABELS = {"male": "Man", "female": "Woman", "transgender": "Transgender"}
CATEGORY_LABELS = {"general": "General", "sc": "SC", "st": "ST", "obc": "OBC", "minority": "Minority"}
AREA_LABELS = {"rural": "Rural (Gram Panchayat)", "urban": "Urban (Municipality)"}


def _pmegp_summary(pmegp):
    """(benefit text, norm text) for the PMEGP rows, from the computed result only."""
    if pmegp.get("eligible") is False:
        return "Not eligible: " + " ".join(pmegp.get("ineligible_reasons") or []), "Not eligible"
    if pmegp.get("eligible") and pmegp.get("subsidy_pct") is not None:
        amount = format_inr(pmegp["subsidy_amount"]) if pmegp.get("subsidy_amount") is not None else "amount to be confirmed by DIC"
        basis = f"{pmegp['category_basis'].capitalize()} category, {pmegp['area_type']}"
        return (
            f"{pmegp['subsidy_pct']:g}% subsidy ({amount}); own contribution {pmegp['own_contribution_pct']:g}% "
            f"({format_inr(pmegp['own_contribution'])}); bank loan {pmegp['bank_loan_pct']:g}%",
            f"{pmegp['subsidy_pct']:g}% ({basis})",
        )
    return "Not computed: applicant category / location not provided", "Not computed"


def _render_reportlab_pdf(proposal: Dict[str, Any], beneficiary: Dict[str, Any], date_str: str) -> bytes:
    """Professional 2-page bank-ready Detailed Project Report (DPR) PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus import Paragraph as _RLParagraph

    def Paragraph(text, style):
        # The built-in PDF fonts have no rupee glyph (it renders as a box), so amounts are printed as "Rs."
        return _RLParagraph(str(text).replace("₹", "Rs. "), style)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=26,
        bottomMargin=26
    )
    styles = getSampleStyleSheet()
    story = []

    # Typography Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=13,
        textColor=colors.HexColor("#1a365d"),
        alignment=1,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=9.5,
        textColor=colors.HexColor("#2b6cb0"),
        alignment=1,
        spaceAfter=8
    )
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=9.5,
        textColor=colors.HexColor("#2c5282"),
        spaceBefore=6,
        spaceAfter=4
    )
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=7.5, leading=9.5)
    bold_cell_style = ParagraphStyle('BoldCell', parent=styles['Normal'], fontSize=7.5, leading=9.5, fontName='Helvetica-Bold')
    white_header_style = ParagraphStyle('WhiteHeader', parent=styles['Normal'], fontSize=7.5, leading=9.5, fontName='Helvetica-Bold', textColor=colors.white)

    # PAGE 1 HEADER
    story.append(Paragraph("STATE CHANNELIZING AGENCY (SCA) &bull; GOVT OF KARNATAKA", title_style))
    story.append(Paragraph("DETAILED PROJECT REPORT (DPR) FOR BANK CONCURRENCE & LENDING", subtitle_style))

    # Meta bar
    prop_id = str(proposal.get("id", "PROPOSAL"))[:8].upper()
    trade_name = str(proposal["business_trade"])
    district_name = str(beneficiary.get("district") or proposal.get("district") or NOT_PROVIDED)
    state_name = str(beneficiary.get("state") or proposal.get("state") or NOT_PROVIDED)
    meta_text = (
        f"<b>DPR Ref:</b> DPR-{prop_id} &nbsp;|&nbsp; "
        f"<b>Date:</b> {date_str} &nbsp;|&nbsp; "
        f"<b>Trade:</b> {trade_name} &nbsp;|&nbsp; "
        f"<b>Location:</b> {district_name}, {state_name}"
    )
    story.append(Paragraph(meta_text, cell_style))
    story.append(Spacer(1, 5))

    # 1. Beneficiary Profile
    story.append(Paragraph("1. Entrepreneur & Promoter Profile", heading2_style))
    # Applicant details exactly as stated and confirmed by the applicant; never defaulted
    profile = beneficiary.get("profile") or {}

    def _stated(field, fmt=str):
        value = profile.get(field, beneficiary.get(field))
        return fmt(value) if value is not None else NOT_PROVIDED

    gender_age = f"{_stated('gender', lambda v: GENDER_LABELS.get(v, v))} / {_stated('age')}"
    beneficiary_table_data = [
        [
            Paragraph("<b>Applicant Name:</b>", cell_style),
            Paragraph(_stated("full_name"), bold_cell_style),
            Paragraph("<b>Contact No:</b>", cell_style),
            Paragraph(str(beneficiary.get("whatsapp_number") or NOT_PROVIDED), cell_style)
        ],
        [
            Paragraph("<b>Enterprise Location:</b>", cell_style),
            Paragraph(f"{district_name}, {state_name}", cell_style),
            Paragraph("<b>Language:</b>", cell_style),
            Paragraph(str(beneficiary.get("preferred_language") or NOT_PROVIDED).capitalize(), cell_style)
        ],
        [
            Paragraph("<b>Gender / Age:</b>", cell_style),
            Paragraph(gender_age, cell_style),
            Paragraph("<b>Social Category:</b>", cell_style),
            Paragraph(_stated("social_category", lambda v: CATEGORY_LABELS.get(v, v)), cell_style)
        ],
        [
            Paragraph("<b>Location Type:</b>", cell_style),
            Paragraph(_stated("area_type", lambda v: AREA_LABELS.get(v, v)), cell_style),
            Paragraph("<b>Annual Family Income:</b>", cell_style),
            Paragraph(_stated("annual_family_income", format_inr), cell_style)
        ],
        [
            Paragraph("<b>Own Money to Invest:</b>", cell_style),
            Paragraph(_stated("available_capital", format_inr), cell_style),
            Paragraph("<b>Appraisal Status:</b>", cell_style),
            Paragraph(f"<b>{proposal.get('status', 'DRAFT')} (Ready for Bank/SCA)</b>", cell_style)
        ]
    ]
    b_table = Table(beneficiary_table_data, colWidths=[120, 145, 110, 160])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(b_table)
    story.append(Paragraph(
        "<i>Applicant details are as stated and confirmed by the applicant in the conversation (User Input); "
        "to be verified by the SCA field officer.</i>", cell_style))
    story.append(Spacer(1, 4))

    # 2-6 use only: the applicant's stated cost, the NABARD booklet, and verified scheme rules.
    cost = float(proposal["project_cost"])
    fin = proposal.get("financial_structure") or {}
    schemes = proposal.get("multi_schemes") or {}
    pmegp = schemes.get("pmegp") or {}
    mudra = schemes.get("mudra") or {}

    from app.finance.repository import benchmark_repository
    bench = benchmark_repository.get_benchmark(trade_name, district=district_name)
    has_official_benchmark = bench.get("status") != "DATA_NOT_AVAILABLE"
    is_nabard = bench.get("source_id") == "NABARD_KA_UC_BOOKLET_2026_27"
    if has_official_benchmark and is_nabard:
        ref_label = f"NABARD reference unit cost: {bench.get('sub_activity') or bench.get('activity')}"
        ref_source = f"NABARD Karnataka Unit Cost Booklet 2026-27, page {bench.get('source_page')}"
    elif has_official_benchmark:
        ref_label = f"Reference project cost: {bench.get('sub_activity') or bench.get('activity')}"
        ref_source = (f"{bench.get('source_organization')} model project profile ({bench.get('publication_year')}), "
                      f"page {bench.get('source_page')}; not a government unit cost")

    def _table(rows, widths, header=True):
        t = Table(rows, colWidths=widths)
        style = [('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                 ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
        if header:
            style.append(('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b6cb0")))
        t.setStyle(TableStyle(style))
        return t

    def _h(text):
        return Paragraph(f"<b>{text}</b>", white_header_style)

    # 2. Project cost
    story.append(Paragraph(f"2. Project Cost ({trade_name})", heading2_style))
    cost_rows = [[_h("Item"), _h("Amount"), _h("Basis")],
                 [Paragraph("Total project cost", cell_style), Paragraph(f"<b>{format_inr(cost)}</b>", bold_cell_style),
                  Paragraph("Stated and confirmed by the applicant (User Input)", cell_style)]]
    if has_official_benchmark:
        cost_rows.append([Paragraph(ref_label, cell_style), Paragraph(format_inr(bench["total_cost"]), bold_cell_style),
                          Paragraph(ref_source, cell_style)])
    else:
        cost_rows.append([Paragraph("NABARD reference unit cost", cell_style), Paragraph("Not available", bold_cell_style),
                          Paragraph("No official unit cost exists for this activity", cell_style)])
    story.append(_table(cost_rows, [190, 90, 255]))
    if has_official_benchmark and bench.get("historical_warning"):
        story.append(Paragraph(f"<b>Historical reference:</b> {bench['historical_warning']}", cell_style))
    story.append(Paragraph("<i>Itemised costs of machinery, animals, shed and stock are to be attached from supplier "
                           "quotations; this report does not estimate them.</i>", cell_style))
    story.append(Spacer(1, 4))

    # 3. Concessional corporation loan for the applicant's category
    story.append(Paragraph("3. Concessional Loan for the Applicant's Category", heading2_style))
    if fin.get("available"):
        morat = f", after a {fin['morat']}-month moratorium" if fin.get("morat") else " (moratorium not stated by the corporation; none assumed)"
        loan_rows = [[_h("Term"), _h("Value")],
                     [Paragraph("Scheme", cell_style), Paragraph(f"<b>{fin['scheme_name']}</b> ({fin.get('agency_full_name') or fin['agency']})", cell_style)],
                     [Paragraph("Loan", cell_style), Paragraph(f"<b>{format_inr(fin['loan'])}</b> ({fin['loan_pct']:g}% of project cost)", cell_style)],
                     [Paragraph("Balance (applicant / channelising agency)", cell_style), Paragraph(f"{format_inr(fin['margin'])} ({fin['margin_pct']:g}%)", cell_style)],
                     [Paragraph("Interest to beneficiary", cell_style), Paragraph(f"{fin['rate']:g}% per year", cell_style)],
                     [Paragraph("Repayment", cell_style), Paragraph(
                         f"{fin['repayment_quarters']} quarterly instalments of <b>{format_inr(fin['quarterly_instalment'])}</b> "
                         f"(about {format_inr(fin['quarterly_instalment'] / 3)} a month, reducing balance){morat}", cell_style)]]
        if fin.get("income_limit"):
            limit_text = format_inr(fin["income_limit"])
            if fin.get("income_limit_conflict"):
                limit_text += " (the corporation's site also states ₹98,000 rural / ₹1,20,000 urban; SCA to confirm)"
            loan_rows.append([Paragraph("Income limit (annual family)", cell_style), Paragraph(limit_text, cell_style)])
        story.append(_table(loan_rows, [190, 345]))
        for note in fin.get("notes") or []:
            story.append(Paragraph(f"&bull; {note}", cell_style))
    else:
        story.append(Paragraph(" ".join(fin.get("reasons") or ["No concessional corporation loan applies."]), cell_style))
    story.append(Spacer(1, 4))

    # 4. Repayment capacity
    story.append(Paragraph("4. Repayment Capacity (DSCR) and Cash Flow", heading2_style))
    story.append(Paragraph(
        "<b>Not computed.</b> No official source gives the expected income and operating costs for this activity, so "
        "a DSCR or 5-year cash flow here would be invented. They should be prepared from the applicant's expected monthly "
        "sales and expenses and checked by the lending bank.", cell_style))
    story.append(Spacer(1, 4))

    # 5. Other schemes
    story.append(Paragraph("5. Other Government Schemes", heading2_style))
    pmegp_benefit, pmegp_norm = _pmegp_summary(pmegp)
    tiers = ", ".join(mudra.get("possible_tiers") or []) or "—"
    scheme_rows = [[_h("Scheme"), _h("What it offers this applicant"), _h("Where to apply")],
                   [Paragraph("<b>PMEGP (KVIC / DIC)</b>", bold_cell_style), Paragraph(pmegp_benefit, cell_style),
                    Paragraph("Online at www.kviconline.gov.in", cell_style)],
                   [Paragraph("<b>MUDRA (PMMY)</b>", bold_cell_style),
                    Paragraph(f"Collateral-free bank loan (CGFMU guarantee). Category for a loan up to the project cost: {tiers}. "
                              "Interest rate and own contribution are decided by the bank.", cell_style),
                    Paragraph("Any bank branch or the Udyamimitra portal", cell_style)]]
    story.append(_table(scheme_rows, [110, 290, 135]))
    story.append(Spacer(1, 6))

    # 6. Source & Data Provenance
    story.append(Paragraph("6. Source & Data Provenance", heading2_style))
    prov_rows = [[_h("Parameter"), _h("Value"), _h("Source"), _h("Type")]]
    prov_rows.append([Paragraph("Project cost", cell_style), Paragraph(format_inr(cost), bold_cell_style),
                      Paragraph("Applicant, confirmed in conversation", cell_style), Paragraph("User Input", cell_style)])
    if has_official_benchmark:
        prov_rows.append([Paragraph("Reference project cost", cell_style), Paragraph(format_inr(bench["total_cost"]), bold_cell_style),
                          Paragraph(ref_source, cell_style),
                          Paragraph("Official Benchmark" if is_nabard else "Historical Model Profile", cell_style)])
    if fin.get("available"):
        corp_source = {"NSFDC": "nsfdc.nic.in scheme & eligibility pages (updated 23.09.2026)",
                       "NBCFDC": "NBCFDC Pattern of Finance (w.e.f. 01.04.2025)",
                       "NSTFDC": "nstfdc.tribal.gov.in Term Loan / AMSY pages (undated)"}.get(fin["agency"], fin["agency"])
        prov_rows.append([Paragraph("Loan share, ceiling, interest, repayment", cell_style),
                          Paragraph(f"{fin['loan_pct']:g}%, {fin['rate']:g}%", bold_cell_style),
                          Paragraph(corp_source, cell_style), Paragraph("Scheme Rule", cell_style)])
        prov_rows.append([Paragraph("Quarterly instalment", cell_style), Paragraph(format_inr(fin["quarterly_instalment"]), bold_cell_style),
                          Paragraph("Reducing-balance annuity on the rule values above", cell_style), Paragraph("Derived Math", cell_style)])
    prov_rows.append([Paragraph("PMEGP subsidy", cell_style), Paragraph(pmegp_norm, bold_cell_style),
                      Paragraph("PMEGP Revised Guidelines (Ministry of MSME), para 3.2 & 8.1", cell_style), Paragraph("Scheme Rule", cell_style)])
    prov_rows.append([Paragraph("MUDRA loan categories", cell_style), Paragraph(tiers, bold_cell_style),
                      Paragraph("PIB, Ministry of Finance, 29.10.2024", cell_style), Paragraph("Scheme Rule", cell_style)])
    prov_rows.append([Paragraph("DSCR / cash flow", cell_style), Paragraph("Not computed", bold_cell_style),
                      Paragraph("No official source for income and operating costs", cell_style), Paragraph("DATA_NOT_AVAILABLE", cell_style)])
    prov_table = Table(prov_rows, colWidths=[140, 95, 215, 85])
    prov_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(prov_table)
    story.append(Spacer(1, 3))

    story.append(Spacer(1, 3))

    # 8. Field Verification & Signatures Box
    story.append(Paragraph("7. SCA Field Verification & Bank Concurrence", heading2_style))
    verif_text = (
        "<b>Field Officer Verification ID:</b> _________________________ &nbsp;&nbsp;&nbsp;&nbsp; "
        "<b>GPS Geotag:</b> Lat: ____________, Long: ____________ (&plusmn;5m)<br/>"
        "<b>Margin Money Verified In-Hand:</b> [ &nbsp; ] YES &nbsp;&nbsp;&nbsp; [ &nbsp; ] NO &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
        "<b>Sanction Recommendation:</b> [ &nbsp; ] RECOMMENDED FOR SANCTION &nbsp;&nbsp; [ &nbsp; ] REVISE"
    )
    v_table = Table([[Paragraph(verif_text, cell_style)]], colWidths=[535])
    v_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#4a5568")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(v_table)
    story.append(Spacer(1, 16))

    # Signatures
    sig_data = [
        [
            Paragraph("___________________________________<br/><b>Beneficiary Signature / Thumb Impression</b>", cell_style),
            Paragraph("___________________________________<br/><b>Authorized SCA Sanctioning Officer</b>", cell_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[265, 270])
    sig_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(sig_table)

    doc.build(story)
    return buffer.getvalue()

def generate_dpr_pdf(
    proposal_data: Dict[str, Any],
    beneficiary_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> bytes:
    """
    Build bank-ready Detailed Project Report (DPR) PDF.
    Attempts WeasyPrint first; if native dependencies are missing, uses ReportLab.
    """
    from datetime import timezone
    date_str = datetime.now(timezone.utc).strftime("%d-%b-%Y")

    pdf_bytes = None

    # Attempt WeasyPrint if available
    try:
        import weasyprint
        template = _jinja_env.get_template("dpr_template.html")
        rendered_html = template.render(
            proposal=proposal_data,
            beneficiary=beneficiary_data,
            date_str=date_str
        )
        pdf_bytes = weasyprint.HTML(string=rendered_html).write_pdf()
        logger.info(f"Rendered DPR PDF via WeasyPrint ({len(pdf_bytes)} bytes)")
    except Exception as e:
        logger.warning(f"WeasyPrint rendering unavailable or failed ({e}). Compiling via ReportLab fallback.")
        pdf_bytes = _render_reportlab_pdf(proposal_data, beneficiary_data, date_str)
        logger.info(f"Rendered DPR PDF via ReportLab ({len(pdf_bytes)} bytes)")

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"Saved DPR PDF to: {output_path}")

    return pdf_bytes
