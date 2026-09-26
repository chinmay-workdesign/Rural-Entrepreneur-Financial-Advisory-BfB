"""
Validator for data/processed/non_farm/flour_mill_benchmark.json.
Validates model project profiles, provenance, cost breakdowns, and physical PDF page bounds.
"""
import os
import sys
import json
from pypdf import PdfReader

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def validate_non_farm_data():
    flour_path = os.path.join("data", "processed", "non_farm", "flour_mill_benchmark.json")
    manifest_path = os.path.join("data", "manifests", "sources_manifest.json")

    if not os.path.exists(flour_path):
        print(f"[FAIL] Flour Mill benchmark file not found at {flour_path}")
        sys.exit(1)

    with open(flour_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid_sources = {s["source_id"]: s for s in manifest.get("sources", [])}

    errors = []
    benchmarks = data.get("benchmarks", [])
    if not benchmarks:
        print("[FAIL] No benchmark records found in flour mill dataset.")
        sys.exit(1)

    print(f"[VALIDATE] Validating {len(benchmarks)} non-farm model project profiles...\n")

    for b in benchmarks:
        bid = b.get("benchmark_id")
        act = b.get("activity")
        pcost = b.get("project_cost")
        sid = b.get("source_id")
        spage = b.get("primary_source_page")
        status = b.get("verification_status")
        stype = b.get("benchmark_source_type")

        if not bid or not act or pcost is None or not sid:
            errors.append(f"Missing core fields in non-farm profile: {b}")
            continue

        if not isinstance(pcost, (int, float)) or pcost <= 0:
            errors.append(f"Invalid project_cost {pcost} in {bid}")

        if stype != "MODEL_PROJECT_PROFILE":
            errors.append(f"Invalid benchmark_source_type '{stype}' for {bid}, must be MODEL_PROJECT_PROFILE")

        if sid not in valid_sources:
            errors.append(f"Unknown source_id '{sid}' in {bid}")
        else:
            source_info = valid_sources[sid]
            raw_pdf = source_info["local_path"]
            if os.path.exists(raw_pdf):
                reader = PdfReader(raw_pdf)
                if spage is None or spage < 1 or spage > len(reader.pages):
                    errors.append(f"Invalid primary_source_page {spage} in {bid} (PDF has {len(reader.pages)} pages)")

        # Verify employment and capacity
        emp = b.get("employment", {})
        if emp.get("total_headcount") != 12:
            errors.append(f"Expected headcount 12, got {emp.get('total_headcount')}")

        cap = b.get("production_capacity", {})
        if cap.get("installed_capacity_annual_mt") != 2400.0:
            errors.append(f"Expected 2400 MT capacity, got {cap.get('installed_capacity_annual_mt')}")

        # Verify breakdown
        breakdown = b.get("cost_breakdown", [])
        if not breakdown:
            errors.append(f"Missing cost breakdown in {bid}")
        else:
            total_bd = sum(item.get("amount", 0) for item in breakdown)
            if abs(total_bd - pcost) > 1.0:
                errors.append(f"Breakdown sum (Rs.{total_bd:,.2f}) does not match project cost (Rs.{pcost:,.2f})")

        print(f"  [PASS] {bid}: {act} (Project Cost: Rs.{pcost:,.2f}, Page {spage}, Type: {stype}, Status: {status})")

    if errors:
        print("\n[FAIL] VALIDATION ERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] ALL NON-FARM MODEL PROFILES VALIDATED SUCCESSFULLY.")

if __name__ == "__main__":
    validate_non_farm_data()
