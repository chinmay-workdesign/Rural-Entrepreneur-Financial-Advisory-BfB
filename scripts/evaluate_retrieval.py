"""
Evaluation and Latency Benchmark Script for Local Authoritative Knowledge Retrieval (FastEmbed + Qdrant).
Evaluates Precision@1, Precision@3, Recall@5, source correctness, and page correctness
across a 16-query ground truth evaluation dataset.
"""
import os
import sys
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.retrieval.service import retrieve_evidence

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 16 Ground Truth Evaluation Queries
EVALUATION_DATASET = [
    {
        "id": "Q1",
        "query": "2 cow dairy unit cost in Karnataka",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 41,
        "expected_topic": "Dairy Farming",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q2",
        "query": "Jersey cow model unit cost",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 41,
        "expected_topic": "Dairy Farming",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q3",
        "query": "cost of cattle shed for 2 crossbred cows",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 41,
        "expected_topic": "Dairy Farming",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q4",
        "query": "2000 broiler poultry integration unit cost",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 50,
        "expected_topic": "Poultry Farming",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q5",
        "query": "commercial 5000 broiler poultry farm project cost",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 49,
        "expected_topic": "Poultry Farming",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q6",
        "query": "mini flour mill total project cost 2020",
        "expected_source": "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE",
        "expected_page": 5,
        "expected_topic": "Mini Flour Mill",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q7",
        "query": "flour mill plant and machinery equipment cost",
        "expected_source": "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE",
        "expected_page": 6,
        "expected_topic": "Mini Flour Mill",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q8",
        "query": "flour mill manpower requirement and employee salaries",
        "expected_source": "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE",
        "expected_page": 4,
        "expected_topic": "Mini Flour Mill",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q9",
        "query": "PMEGP rural special category margin money subsidy",
        "expected_source": "PMEGP_REVISED_GUIDELINES_2023",
        "expected_page": 4,
        "expected_topic": "PMEGP",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q10",
        "query": "PMEGP manufacturing maximum project cost ceiling",
        "expected_source": "PMEGP_REVISED_GUIDELINES_2023",
        "expected_page": 4,
        "expected_topic": "PMEGP",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q11",
        "query": "PMEGP minimum age and education qualification criteria",
        "expected_source": "PMEGP_REVISED_GUIDELINES_2023",
        "expected_page": 5,
        "expected_topic": "PMEGP",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q12",
        "query": "PMEGP loan repayment tenure years",
        "expected_source": "PMEGP_REVISED_GUIDELINES_2023",
        "expected_page": 5,
        "expected_topic": "PMEGP",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q13",
        "query": "rural incidence of indebtedness in Karnataka AIDIS",
        "expected_source": "AIDIS_NSS_77_REPORT_588",
        "expected_page": 92,
        "expected_topic": "AIDIS",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q14",
        "query": "informal non-institutional moneylender interest rates in rural Karnataka",
        "expected_source": "AIDIS_NSS_77_REPORT_588",
        "expected_page": 97,
        "expected_topic": "AIDIS",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q15",
        "query": "RBI priority sector lending targets for agriculture and micro enterprises",
        "expected_source": "RBI_PSL_MASTER_DIRECTIONS_2025",
        "expected_page": 10,
        "expected_topic": "RBI_PSL",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q16",
        "query": "PMMY MUDRA refinance eligibility for partner banks",
        "expected_source": "PMMY_PARTNER_ELIGIBILITY",
        "expected_page": 1,
        "expected_topic": "PMMY",
        "expected_status": "NEEDS_SOURCE_VERIFICATION"
    },
    {
        "id": "Q17",
        "query": "sheep rearing unit cost in Karnataka Bannur breed 10 plus 1",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 56,
        "expected_topic": "Sheep Rearing",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q18",
        "query": "goat rearing 10 does 1 buck improved breed unit cost",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 60,
        "expected_topic": "Goat Rearing",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q19",
        "query": "piggery 3 sows 1 boar fattening unit project cost",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 64,
        "expected_topic": "Piggery Farming",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q20",
        "query": "freshwater fish culture composite carp 1 hectare unit cost",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 68,
        "expected_topic": "Fisheries and Aquaculture",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q21",
        "query": "beekeeping apiary 10 colony unit cost and honey extractor",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 30,
        "expected_topic": "Beekeeping / Apiary",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q22",
        "query": "sericulture mulberry garden establishment cost per hectare",
        "expected_source": "NABARD_KA_UC_BOOKLET_2026_27",
        "expected_page": 34,
        "expected_topic": "Sericulture",
        "expected_status": "VERIFIED_OFFICIAL"
    },
    {
        "id": "Q23",
        "query": "All-India rural incidence of indebtedness and average amount of debt AIDIS",
        "expected_source": "AIDIS_NSS_77_REPORT_588",
        "expected_page": 92,
        "expected_topic": "AIDIS",
        "expected_status": "VERIFIED_OFFICIAL"
    }
]

def run_evaluation():
    print("[EVAL] Running Authoritative Knowledge Retrieval Evaluation Suite...\n")
    latencies = []
    p_at_1_hits = 0
    p_at_3_hits = 0
    recall_at_5_hits = 0
    source_correct_hits = 0
    page_correct_hits = 0
    status_correct_hits = 0

    results = []

    for item in EVALUATION_DATASET:
        qid = item["id"]
        q = item["query"]
        exp_src = item["expected_source"]
        exp_pg = item["expected_page"]
        exp_status = item["expected_status"]

        t0 = time.perf_counter()
        retrieved = retrieve_evidence(q, top_k=5, require_verified=False)
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0
        latencies.append(latency_ms)

        top1 = retrieved[0] if retrieved else None
        top3_sources = [r.source_id for r in retrieved[:3]]
        top5_sources = [r.source_id for r in retrieved[:5]]

        hit_p1 = (top1.source_id == exp_src) if top1 else False
        hit_p3 = exp_src in top3_sources
        hit_r5 = exp_src in top5_sources

        # Page match within top 3
        page_hit = any(r.source_id == exp_src and r.source_page == exp_pg for r in retrieved[:3])
        status_hit = (top1.verification_status == exp_status) if top1 else False

        if hit_p1: p_at_1_hits += 1
        if hit_p3: p_at_3_hits += 1
        if hit_r5: recall_at_5_hits += 1
        if hit_p1: source_correct_hits += 1
        if page_hit: page_correct_hits += 1
        if status_hit: status_correct_hits += 1

        top1_desc = f"{top1.source_id} (p.{top1.source_page}, score={top1.relevance_score:.3f})" if top1 else "NONE"
        results.append({
            "id": qid,
            "query": q,
            "latency_ms": round(latency_ms, 2),
            "top1": top1_desc,
            "p1_match": hit_p1,
            "page_match": page_hit,
            "status_match": status_hit
        })

        print(f"  {qid}: '{q[:35]}...' -> {top1_desc} [{latency_ms:.1f}ms]")

    total = len(EVALUATION_DATASET)
    precision_1 = (p_at_1_hits / total) * 100.0
    precision_3 = (p_at_3_hits / total) * 100.0
    recall_5 = (recall_at_5_hits / total) * 100.0
    page_accuracy = (page_correct_hits / total) * 100.0
    status_accuracy = (status_correct_hits / total) * 100.0
    avg_latency = sum(latencies) / len(latencies)

    print("\n" + "=" * 60)
    print("RETRIEVAL EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Queries Evaluated:    {total}")
    print(f"Precision@1:                {precision_1:.1f}% ({p_at_1_hits}/{total})")
    print(f"Precision@3:                {precision_3:.1f}% ({p_at_3_hits}/{total})")
    print(f"Recall@5:                   {recall_5:.1f}% ({recall_at_5_hits}/{total})")
    print(f"Page Correctness (Top-3):   {page_accuracy:.1f}% ({page_correct_hits}/{total})")
    print(f"Status Correctness (Top-1): {status_accuracy:.1f}% ({status_correct_hits}/{total})")
    print(f"Average Retrieval Latency:  {avg_latency:.2f} ms")
    print(f"Max Retrieval Latency:      {max(latencies):.2f} ms")
    print(f"Min Retrieval Latency:      {min(latencies):.2f} ms")
    print("=" * 60)

    # Save output report
    eval_report = {
        "metrics": {
            "total_queries": total,
            "precision_at_1_pct": precision_1,
            "precision_at_3_pct": precision_3,
            "recall_at_5_pct": recall_5,
            "page_accuracy_pct": page_accuracy,
            "status_accuracy_pct": status_accuracy,
            "avg_latency_ms": round(avg_latency, 2),
            "max_latency_ms": round(max(latencies), 2),
            "min_latency_ms": round(min(latencies), 2),
        },
        "query_results": results
    }
    with open(os.path.join("docs", "retrieval_evaluation_data.json"), "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    return eval_report

if __name__ == "__main__":
    run_evaluation()
