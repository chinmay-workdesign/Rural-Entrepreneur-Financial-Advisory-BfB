"""
Deterministic Benchmark Deviation Analysis Layer.
Compares user-proposed project costs against authoritative benchmarks (NABARD / Model Profiles).
Preserves user intent without silent overwrites, while flagging deviations for credit review.
"""
from typing import Dict, Any, Optional

DEFAULT_DEVIATION_THRESHOLD_PCT = 20.0

def analyze_benchmark_deviation(
    user_project_cost: float,
    trade: str,
    district: str = "Rural District",
    threshold_pct: float = DEFAULT_DEVIATION_THRESHOLD_PCT,
    real_data_only: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Compares user's proposed capital outlay against authoritative reference benchmark.
    Does NOT automatically reject the project. Produces an explicit deviation advisory.
    """
    from app.finance.repository import benchmark_repository

    benchmark = benchmark_repository.get_benchmark(trade, district=district, real_data_only=real_data_only)

    # If benchmark is unavailable (e.g., Tailoring/Kirana in real-data-only mode)
    if benchmark.get("status") == "DATA_NOT_AVAILABLE" or benchmark.get("verification_status") == "DATA_NOT_AVAILABLE":
        return {
            "has_benchmark": False,
            "status": "DATA_NOT_AVAILABLE",
            "user_project_cost": user_project_cost,
            "reference_cost": None,
            "absolute_difference": None,
            "percentage_difference": None,
            "is_significant_deviation": False,
            "threshold_pct": threshold_pct,
            "message": f"No authoritative reference benchmark available for '{trade}'. User outlay of ₹{user_project_cost:,.2f} evaluated on applicant's stated plan.",
            "source_id": None,
            "source_type": None,
            "verification_status": "DATA_NOT_AVAILABLE"
        }

    reference_cost = float(benchmark.get("total_cost") or benchmark.get("project_cost") or 0.0)
    if reference_cost <= 0:
        return {
            "has_benchmark": False,
            "user_project_cost": user_project_cost,
            "reference_cost": None,
            "is_significant_deviation": False,
            "message": "Reference cost is non-positive or undefined."
        }

    abs_diff = abs(user_project_cost - reference_cost)
    pct_diff = round((abs_diff / reference_cost) * 100.0, 2)
    is_significant = pct_diff > threshold_pct

    if user_project_cost > reference_cost:
        direction = "ABOVE_BENCHMARK"
        advisory = (
            f"User-proposed cost of ₹{user_project_cost:,.2f} is {pct_diff:.1f}% higher than "
            f"the reference benchmark (₹{reference_cost:,.2f}). "
            f"Field verification must review enhanced equipment capacity or higher scale justifications."
        )
    elif user_project_cost < reference_cost:
        direction = "BELOW_BENCHMARK"
        advisory = (
            f"User-proposed cost of ₹{user_project_cost:,.2f} is {pct_diff:.1f}% lower than "
            f"the reference benchmark (₹{reference_cost:,.2f}). "
            f"Applicant may be leveraging existing sheds, family machinery, or starting with a phased unit."
        )
    else:
        direction = "EQUAL"
        advisory = f"User-proposed cost matches the authoritative benchmark (₹{reference_cost:,.2f}) exactly."

    cost_note = None
    if benchmark.get("cost_nature") == "HISTORICAL_BENCHMARK_2020":
        cost_note = (
            f"Note: Reference cost of ₹{reference_cost:,.2f} is a historical 2020 pre-feasibility benchmark "
            f"(Source: Project SAMADHAN, p. {benchmark.get('source_page', 5)}). "
            f"Current market prices may justify higher outlay."
        )

    return {
        "has_benchmark": True,
        "status": "ANALYZED",
        "trade": trade,
        "user_project_cost": user_project_cost,
        "reference_cost": reference_cost,
        "absolute_difference": round(abs_diff, 2),
        "percentage_difference": pct_diff,
        "direction": direction,
        "is_significant_deviation": is_significant,
        "threshold_pct": threshold_pct,
        "source_organization": benchmark.get("source_organization"),
        "source_id": benchmark.get("source_id"),
        "source_page": benchmark.get("source_page"),
        "publication_year": benchmark.get("publication_year"),
        "source_type": benchmark.get("source_type"),
        "verification_status": benchmark.get("verification_status"),
        "advisory": advisory,
        "cost_nature_note": cost_note
    }
