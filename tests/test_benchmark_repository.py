"""
Test suite for Authoritative Benchmark Repository and Real-Data Migration.
Validates:
1. NABARD dairy retrieval
2. NABARD poultry retrieval
3. Flour Mill retrieval
4. Flour Mill provenance
5. Source page preservation
6. Source hash existence
7. Tailoring returns DATA_NOT_AVAILABLE in REAL_DATA_ONLY mode
8. Kirana returns DATA_NOT_AVAILABLE in REAL_DATA_ONLY mode
9. No silent synthetic fallback
10. Unverified PMMY data cannot be treated as authoritative
11. Repository records always preserve provenance
12. Financial calculations remain deterministic
"""
import os
import json
import pytest
from app.finance.repository import (
    BenchmarkRepository,
    BenchmarkSourceType,
    VerificationStatus,
    benchmark_repository
)
from app.finance.benchmarks import get_trade_benchmark
from app.finance.calculator import calculate_financial_structure

@pytest.fixture
def repo():
    return benchmark_repository

@pytest.fixture
def manifest():
    manifest_path = os.path.join("data", "manifests", "sources_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 1. NABARD dairy retrieval
def test_nabard_dairy_retrieval(repo):
    bench = repo.get_benchmark("Small Dairy Unit (2 Crossbred Cows)")
    assert bench["verification_status"] == VerificationStatus.VERIFIED.value
    assert bench["source_type"] == BenchmarkSourceType.NABARD_UNIT_COST.value
    assert bench["total_cost"] == 229000.0
    assert bench["source_page"] == 41
    assert "Karnataka" in bench["summary"]

# 2. NABARD poultry retrieval
def test_nabard_poultry_retrieval(repo):
    bench = repo.get_benchmark("Poultry Broiler Farm")
    assert bench["verification_status"] == VerificationStatus.VERIFIED.value
    assert bench["source_type"] == BenchmarkSourceType.NABARD_UNIT_COST.value
    assert bench["total_cost"] == 456000.0
    assert bench["source_page"] == 50

# 3. Flour Mill retrieval
def test_flour_mill_retrieval(repo):
    bench = repo.get_benchmark("Mini Flour Mill (Atta Chakki)")
    assert bench["verification_status"] == VerificationStatus.VERIFIED.value
    assert bench["source_type"] == BenchmarkSourceType.MODEL_PROJECT_PROFILE.value
    assert bench["total_cost"] == 3293000.0
    assert bench["source_page"] == 5

# 4. Flour Mill provenance
def test_flour_mill_provenance(repo):
    bench = repo.get_benchmark("Mini Flour Mill")
    assert bench["publication_year"] == 2020
    assert "SAMADHAN" in bench["source_organization"]
    assert bench["source_id"] == "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE"
    assert bench["employment"]["total_headcount"] == 12
    assert bench["production_capacity"]["installed_capacity_annual_mt"] == 2400.0
    assert bench["cost_nature"] == "HISTORICAL_BENCHMARK_2020"

# 5. Source page preservation
def test_source_page_preservation(repo):
    for activity in ["dairy cow", "poultry broiler", "flour mill"]:
        bench = repo.get_benchmark(activity, real_data_only=True)
        assert bench.get("source_page") is not None
        assert isinstance(bench["source_page"], int)
        assert bench["source_page"] >= 1

# 6. Source hash existence
def test_source_hash_existence(repo, manifest):
    sources = {s["source_id"]: s for s in manifest["sources"]}
    for activity in ["dairy", "poultry", "flour mill"]:
        bench = repo.get_benchmark(activity, real_data_only=True)
        sid = bench["source_id"]
        assert sid in sources
        sha256 = sources[sid]["sha256"]
        assert len(sha256) == 64

# 7. Tailoring returns DATA_NOT_AVAILABLE in REAL_DATA_ONLY mode
def test_tailoring_real_data_only_mode(repo):
    bench = repo.get_benchmark("Tailoring Shop", real_data_only=True)
    assert bench["status"] == "DATA_NOT_AVAILABLE"
    assert bench["verification_status"] == VerificationStatus.DATA_NOT_AVAILABLE.value
    assert bench["is_synthetic"] is False
    assert bench.get("future_scope") is True
    assert "capex" not in bench

# 8. Kirana returns DATA_NOT_AVAILABLE in REAL_DATA_ONLY mode
def test_kirana_real_data_only_mode(repo):
    bench = repo.get_benchmark("Kirana Store", real_data_only=True)
    assert bench["status"] == "DATA_NOT_AVAILABLE"
    assert bench["verification_status"] == VerificationStatus.DATA_NOT_AVAILABLE.value
    assert bench["is_synthetic"] is False
    assert bench.get("future_scope") is True
    assert "capex" not in bench

# 9. No silent synthetic fallback
def test_no_silent_synthetic_fallback(repo):
    # When real_data_only is False, fallback must be explicitly flagged
    bench = repo.get_benchmark("Tailoring Shop", real_data_only=False)
    assert bench["source_type"] == BenchmarkSourceType.SYNTHETIC_BASELINE.value
    assert bench["verification_status"] == VerificationStatus.SYNTHETIC.value
    assert bench["is_synthetic"] is True
    assert "TEMPORARY_SYNTHETIC_FALLBACK" in bench.get("warning", "")
    assert bench["source_id"] == "SYNTHETIC_IN_MEMORY"

# 10. Unverified PMMY data cannot be treated as authoritative
def test_unverified_pmmy_cannot_be_authoritative(manifest):
    pmmy_source = next((s for s in manifest["sources"] if "PMMY" in s["source_id"]), None)
    assert pmmy_source is not None
    assert pmmy_source["verification_status"] == "NEEDS_SOURCE_VERIFICATION"
    assert pmmy_source["verification_status"] != "VERIFIED_OFFICIAL"

# 11. Repository records always preserve provenance
def test_repository_records_always_preserve_provenance(repo):
    for activity in ["dairy", "poultry broiler", "atta mill"]:
        bench = repo.get_benchmark(activity, real_data_only=True)
        assert "source_id" in bench and bench["source_id"] is not None
        assert "source_organization" in bench and bench["source_organization"] is not None
        assert "source_type" in bench and bench["source_type"] in [
            BenchmarkSourceType.NABARD_UNIT_COST.value,
            BenchmarkSourceType.MODEL_PROJECT_PROFILE.value
        ]
        assert bench["verification_status"] == VerificationStatus.VERIFIED.value

# 12. Financial calculations remain deterministic
def test_financial_calculations_remain_deterministic():
    # Test identical input produces identical output across 10 iterations
    calc_1 = calculate_financial_structure(project_cost=229000.0)
    for _ in range(10):
        calc_n = calculate_financial_structure(project_cost=229000.0)
        assert calc_1 == calc_n
    # Assert exact calculated values
    assert calc_1["cost"] == 229000.0
    assert calc_1["scheme"] == "TERM_LOAN"
    assert calc_1["loan"] == 0.90 * 229000.0
    assert calc_1["margin"] == 229000.0 - calc_1["loan"]
    assert calc_1["emi"] > 0

# 13. New allied activities retrieval in REAL_DATA_ONLY mode
def test_new_allied_benchmarks_retrieval(repo):
    activities = [
        ("sheep", 111000.0, 56),
        ("goat", 113000.0, 60),
        ("piggery", 164000.0, 64),
        ("fisheries", 829000.0, 68),
        ("beekeeping", 62800.0, 30),
        ("sericulture", 225000.0, 34),
    ]
    for act, exp_cost, exp_page in activities:
        bench = repo.get_benchmark(act, real_data_only=True)
        assert bench["verification_status"] == VerificationStatus.VERIFIED.value
        assert bench["source_type"] == BenchmarkSourceType.NABARD_UNIT_COST.value
        assert bench["benchmark_status"] == "CURRENT_BENCHMARK"
        assert bench["total_cost"] == exp_cost
        assert bench["source_page"] == exp_page
        assert bench["is_synthetic"] is False

# 14. Multilingual activity query routing
def test_multilingual_activity_queries(repo):
    # Kannada: ಕುರಿ (sheep), ಮೀನುಗಾರಿಕೆ (fisheries), ರೇಷ್ಮೆ (sericulture)
    assert repo.get_benchmark("ಕುರಿ ಸಾಕಾಣಿಕೆ", real_data_only=True)["total_cost"] == 111000.0
    assert repo.get_benchmark("ಮೀನುಗಾರಿಕೆ", real_data_only=True)["total_cost"] == 829000.0
    assert repo.get_benchmark("ರೇಷ್ಮೆ ಕೃಷಿ", real_data_only=True)["total_cost"] == 225000.0
    # Hindi: बकरी (goat), मधुमक्खी (beekeeping)
    assert repo.get_benchmark("बकरी पालन", real_data_only=True)["total_cost"] == 113000.0
    assert repo.get_benchmark("मधुमक्खी पालन", real_data_only=True)["total_cost"] == 62800.0

# 15. Historical vs Current Benchmark Governance
def test_historical_vs_current_governance(repo):
    dairy = repo.get_benchmark("dairy", real_data_only=True)
    assert dairy["benchmark_status"] == "CURRENT_BENCHMARK"
    assert dairy["publication_year"] == 2026
    assert "historical_warning" not in dairy

    flour = repo.get_benchmark("flour mill", real_data_only=True)
    assert flour["benchmark_status"] == "HISTORICAL_BENCHMARK"
    assert flour["publication_year"] == 2020
    assert "historical_warning" in flour
    assert "2020" in flour["historical_warning"]



