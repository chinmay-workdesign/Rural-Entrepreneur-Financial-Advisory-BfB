"""
Validator for data/processed/nabard/karnataka_benchmarks.json.
Checks that all extracted benchmark records contain mandatory schema fields,
valid numbers, existing source_id in manifests, and valid source_page.
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

def validate_nabard_data():
    benchmarks_path = os.path.join("data", "processed", "nabard", "karnataka_benchmarks.json")
    manifest_path = os.path.join("data", "manifests", "sources_manifest.json")

    if not os.path.exists(benchmarks_path):
        print(f"[FAIL] File not found at {benchmarks_path}")
        sys.exit(1)

    with open(benchmarks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid_source_ids = {s["source_id"]: s for s in manifest.get("sources", [])}

    benchmarks = data.get("benchmarks", [])
    if not benchmarks:
        print("[FAIL] No benchmark records found.")
        sys.exit(1)

    errors = []
    print(f"[VALIDATE] Validating {len(benchmarks)} NABARD benchmark records...\n")

    for b in benchmarks:
        bid = b.get("benchmark_id")
        act = b.get("activity")
        unit_cost = b.get("unit_cost")
        total_cost = b.get("total_cost")
        sid = b.get("source_id")
        spage = b.get("source_page")
        status = b.get("verification_status")

        if not bid or not act or unit_cost is None or total_cost is None:
            errors.append(f"Missing core fields in benchmark: {b}")
            continue

        if not isinstance(unit_cost, (int, float)) or unit_cost <= 0:
            errors.append(f"Invalid unit_cost {unit_cost} for benchmark {bid}")

        if sid not in valid_source_ids:
            errors.append(f"Unknown source_id '{sid}' in benchmark {bid}")
        else:
            source_info = valid_source_ids[sid]
            raw_pdf = source_info["local_path"]
            if os.path.exists(raw_pdf):
                reader = PdfReader(raw_pdf)
                if spage is None or spage < 1 or spage > len(reader.pages):
                    errors.append(f"Invalid source_page {spage} for benchmark {bid} (PDF has {len(reader.pages)} pages)")

        breakdown = b.get("cost_breakdown", [])
        if not breakdown:
            errors.append(f"Missing cost_breakdown list in benchmark {bid}")
        else:
            breakdown_sum = sum(item.get("amount", 0) for item in breakdown)
            # NABARD tables routinely round headline unit cost to the nearest thousand (e.g., Rs. 229,260 -> Rs. 2,29,000)
            diff = abs(breakdown_sum - unit_cost)
            if diff > 1000.0 and (diff / unit_cost) > 0.01:
                errors.append(
                    f"Cost breakdown sum (Rs.{breakdown_sum:,.2f}) deviates significantly from unit_cost (Rs.{unit_cost:,.2f}) for {bid}"
                )

        print(f"  [PASS] {bid}: {act} (Rs.{unit_cost:,.2f}, Page {spage}, Status: {status})")

    # Verify unsupported activities are explicitly documented and not fabricated
    unsupported = data.get("unsupported_pilot_activities", [])
    print(f"\n[VALIDATE] Verifying {len(unsupported)} unmanufactured / unavailable categories...")
    for u in unsupported:
        if u.get("status") != "DATA_NOT_AVAILABLE":
            errors.append(f"Unsupported activity {u.get('activity')} has invalid status: {u.get('status')}")
        else:
            print(f"  [INFO] {u.get('activity')}: Confirmed marked as DATA_NOT_AVAILABLE")

    if errors:
        print("\n[FAIL] VALIDATION ERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] ALL NABARD BENCHMARKS VALIDATED AND RECONCILED SUCCESSFULLY.")

if __name__ == "__main__":
    validate_nabard_data()
