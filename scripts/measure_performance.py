import time
import statistics
import json
import os

from app.finance.calculator import calculate_financial_structure
from app.dpr.generator import generate_dpr_pdf
from app.retrieval.router import execute_authoritative_routing
from app.retrieval.service import retrieval_service

def measure_all():
    print("=== PHASE 7 PERFORMANCE BENCHMARKING ===")

    # 1. Cold Start Latency
    t0 = time.perf_counter()
    _ = retrieval_service.embedding_model
    cold_start_embed_ms = (time.perf_counter() - t0) * 1000.0

    # 2. Retrieval Latency
    queries = [
        "What is the NABARD unit cost for 2 dairy cows in Karnataka?",
        "What is the official project cost for a flour mill in Project SAMADHAN?",
        "What share of rural household debt was institutional in AIDIS 2019?",
        "What are the PMEGP subsidy rates for rural micro enterprises?",
        "What are the RBI Priority Sector Lending guidelines for agriculture?"
    ]
    retrieval_latencies = []
    for q in queries:
        for _ in range(2):
            t_start = time.perf_counter()
            _ = retrieval_service.retrieve_evidence(query=q, top_k=3, require_verified=True)
            retrieval_latencies.append((time.perf_counter() - t_start) * 1000.0)

    avg_retrieval_ms = statistics.mean(retrieval_latencies)
    p95_retrieval_ms = statistics.quantiles(retrieval_latencies, n=20)[18] if len(retrieval_latencies) >= 20 else max(retrieval_latencies)

    # 3. Financial Calculation Latency
    costs = [50000.0, 100000.0, 150000.0, 200000.0, 500000.0, 1200000.0, 3293000.0]
    fin_latencies = []
    for _ in range(100):
        for c in costs:
            t_start = time.perf_counter()
            _ = calculate_financial_structure(c)
            fin_latencies.append((time.perf_counter() - t_start) * 1000.0)

    avg_fin_ms = statistics.mean(fin_latencies)
    max_fin_ms = max(fin_latencies)

    # 4. DPR Generation Latency
    proposal = {
        "id": "prop_bench_001",
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
        "full_name": "Ramesh Patil",
        "whatsapp_number": "+919876543210",
        "district": "Belagavi",
        "state": "Karnataka",
        "preferred_language": "Kannada",
        "annual_family_income": 85000.0
    }
    dpr_latencies = []
    for _ in range(5):
        t_start = time.perf_counter()
        _ = generate_dpr_pdf(proposal, beneficiary)
        dpr_latencies.append((time.perf_counter() - t_start) * 1000.0)

    avg_dpr_ms = statistics.mean(dpr_latencies)

    # 5. Deterministic End-to-End Latency (Intent + Retrieval + Financial Engine + Citation Formatting)
    e2e_latencies = []
    for q in ["How much does 2 cows cost?", "Flour mill project profile cost", "Calculate EMI for 200000"]:
        t_start = time.perf_counter()
        _ = execute_authoritative_routing(q, language="english")
        e2e_latencies.append((time.perf_counter() - t_start) * 1000.0)

    avg_e2e_ms = statistics.mean(e2e_latencies)

    results = {
        "cold_start_embed_ms": round(cold_start_embed_ms, 2),
        "avg_retrieval_latency_ms": round(avg_retrieval_ms, 2),
        "p95_retrieval_latency_ms": round(p95_retrieval_ms, 2),
        "avg_financial_calc_latency_ms": round(avg_fin_ms, 4),
        "max_financial_calc_latency_ms": round(max_fin_ms, 4),
        "avg_dpr_generation_latency_ms": round(avg_dpr_ms, 2),
        "avg_e2e_deterministic_latency_ms": round(avg_e2e_ms, 2),
    }

    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    measure_all()
