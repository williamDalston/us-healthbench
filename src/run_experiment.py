"""Full experiment pipeline: build vector store -> run baselines -> score -> stats -> plots.

Usage:
    python -m src.run_experiment [--items N]
"""

import argparse
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CORPUS_PATH = Path("data/processed/corpus_full.jsonl")
BENCHMARK_PATH = Path("data/benchmark_v1/benchmark_items.jsonl")
CHROMA_DIR = Path("data/chroma_db")
EXPERIMENT_DIR = Path("data/experiment")
FIGURES_DIR = Path("paper/figures")


def load_jsonl(path: Path) -> list[dict]:
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    return docs


def main(max_items=None):
    """Run the full experiment pipeline."""

    # -- step 1: load data --
    logger.info("=" * 60)
    logger.info("STEP 1: Loading corpus and benchmark")
    logger.info("=" * 60)

    corpus_docs = load_jsonl(CORPUS_PATH)
    items = load_jsonl(BENCHMARK_PATH)
    logger.info("Loaded %d corpus docs and %d benchmark items", len(corpus_docs), len(items))

    if max_items:
        items = items[:max_items]
        logger.info("Truncated to %d items for testing", len(items))

    # -- step 2: build vector store --
    logger.info("=" * 60)
    logger.info("STEP 2: Building ChromaDB vector store")
    logger.info("=" * 60)

    from src.systems.rag import build_vector_store

    collection = build_vector_store(corpus_docs, persist_dir=str(CHROMA_DIR))
    logger.info("Vector store ready with %d chunks", collection.count())

    # -- step 3: run all baselines --
    logger.info("=" * 60)
    logger.info("STEP 3: Running 4 pipeline configurations on %d items", len(items))
    logger.info("=" * 60)

    from src.systems.local_baselines import run_all_baselines

    all_outputs = run_all_baselines(items, collection, corpus_docs, output_dir=EXPERIMENT_DIR)

    for system_name, outputs in all_outputs.items():
        logger.info("  %s: %d outputs", system_name, len(outputs))

    # -- step 4: score all outputs --
    logger.info("=" * 60)
    logger.info("STEP 4: Scoring outputs with heuristic scorer")
    logger.info("=" * 60)

    from src.evaluation.heuristic_scorer import score_batch

    all_eval_results: list[dict] = []
    for system_name, outputs in all_outputs.items():
        eval_path = EXPERIMENT_DIR / f"eval_{system_name}.jsonl"
        results = score_batch(items, outputs, output_path=str(eval_path))
        all_eval_results.extend(results)
        logger.info("  Scored %s: %d results", system_name, len(results))

    # save combined eval
    combined_path = EXPERIMENT_DIR / "eval_all.jsonl"
    with open(combined_path, "w", encoding="utf-8") as f:
        for r in all_eval_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    logger.info("Saved %d total eval results to %s", len(all_eval_results), combined_path)

    # -- step 5: compute statistics --
    logger.info("=" * 60)
    logger.info("STEP 5: Computing statistics")
    logger.info("=" * 60)

    from src.evaluation.stats import compute_main_results, paired_comparison, stratified_results

    main_results = compute_main_results(all_eval_results)

    # print main results table
    print("\n" + "=" * 90)
    print("MAIN RESULTS")
    print("=" * 90)
    header = (
        f"{'System':<20} {'Factual':>8} {'Source':>8} {'Safety':>8} "
        f"{'Uncert':>8} {'Clarity':>8} {'GSS':>8}"
    )
    print(header)
    print("-" * 90)
    for system in ["llm_only", "rag", "citation_rag", "agent_pipeline"]:
        if system not in main_results:
            continue
        r = main_results[system]
        row = f"{system:<20}"
        for metric in [
            "factual_correctness",
            "source_support",
            "safety",
            "uncertainty_handling",
            "clarity",
            "grounded_safety_score",
        ]:
            m = r.get(metric, {"mean": 0})
            row += f" {m['mean']:>7.3f}"
        print(row)

    # flag rates
    print("\n" + "=" * 90)
    print("ERROR FLAG RATES")
    print("=" * 90)
    flag_header = (
        f"{'System':<20} {'Fabricated':>10} {'Unsup Med':>10} {'False Reas':>10} {'Omit Esc':>10}"
    )
    print(flag_header)
    print("-" * 90)
    for system in ["llm_only", "rag", "citation_rag", "agent_pipeline"]:
        if system not in main_results:
            continue
        r = main_results[system]
        row = f"{system:<20}"
        for flag in [
            "fabricated_citation_rate",
            "unsupported_medical_recommendation_rate",
            "false_reassurance_rate",
            "omission_of_escalation_advice_rate",
        ]:
            row += f" {r.get(flag, 0):>9.3f}"
        print(row)

    # paired comparisons
    print("\n" + "=" * 90)
    print("PAIRED COMPARISONS (GSS)")
    print("=" * 90)
    pairs_to_compare = [
        ("llm_only", "rag"),
        ("rag", "citation_rag"),
        ("citation_rag", "agent_pipeline"),
        ("llm_only", "agent_pipeline"),
    ]
    for sa, sb in pairs_to_compare:
        comp = paired_comparison(all_eval_results, sa, sb, "grounded_safety_score")
        print(
            f"  {sa} vs {sb}: "
            f"mean_diff={comp.get('mean_diff', 0):+.4f}, "
            f"p={comp.get('p_value', 1):.6f}, "
            f"n={comp.get('n_pairs', 0)}"
        )

    # stratified results
    strat_topic = stratified_results(all_eval_results, items, "topic")
    strat_lang = stratified_results(all_eval_results, items, "language")
    strat_family = stratified_results(all_eval_results, items, "task_family")

    stats_output = {
        "main_results": main_results,
        "stratified_by_topic": strat_topic,
        "stratified_by_language": strat_lang,
        "stratified_by_task_family": strat_family,
    }
    stats_path = EXPERIMENT_DIR / "experiment_stats.json"
    stats_path.write_text(json.dumps(stats_output, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved experiment stats to %s", stats_path)

    # -- step 6: generate plots --
    logger.info("=" * 60)
    logger.info("STEP 6: Generating publication-ready plots")
    logger.info("=" * 60)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    from src.evaluation.plots import (
        plot_benchmark_composition,
        plot_cross_language_consistency,
        plot_error_taxonomy_heatmap,
        plot_main_results,
    )

    plot_main_results(main_results, FIGURES_DIR / "fig1_main_results.png")
    plot_error_taxonomy_heatmap(main_results, FIGURES_DIR / "fig2_error_taxonomy.png")
    plot_benchmark_composition(items, FIGURES_DIR / "fig3_benchmark_composition.png")

    # fig 4: cross-language consistency
    # collect GSS for paired EN/ES items
    pairs_path = Path("data/benchmark_v1/cross_language_pairs.json")
    if pairs_path.exists():
        pairs = json.loads(pairs_path.read_text(encoding="utf-8"))
        eval_by_item = {}
        for r in all_eval_results:
            if r["system"] == "agent_pipeline":
                eval_by_item[r["item_id"]] = r

        en_gss, es_gss = [], []
        for pair in pairs:
            en_eval = eval_by_item.get(pair.get("en_item_id"))
            es_eval = eval_by_item.get(pair.get("es_item_id"))
            if en_eval and es_eval:
                en_gss.append(en_eval["composite_scores"]["grounded_safety_score"])
                es_gss.append(es_eval["composite_scores"]["grounded_safety_score"])

        if en_gss and es_gss:
            plot_cross_language_consistency(
                en_gss,
                es_gss,
                FIGURES_DIR / "fig4_cross_language.png",
            )
            logger.info("Cross-language plot: %d pairs", len(en_gss))

    # -- step 7: generate results tables (LaTeX-ready) --
    logger.info("=" * 60)
    logger.info("STEP 7: Generating result tables")
    logger.info("=" * 60)

    tables_dir = Path("paper/tables")
    tables_dir.mkdir(parents=True, exist_ok=True)

    _generate_main_table(main_results, tables_dir / "table1_main_results.md")
    _generate_stratified_table(strat_topic, tables_dir / "table2_by_topic.md", "Topic")
    _generate_stratified_table(strat_lang, tables_dir / "table3_by_language.md", "Language")
    _generate_stratified_table(strat_family, tables_dir / "table4_by_task_family.md", "Task Family")

    logger.info("All tables saved to %s", tables_dir)

    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"  Items evaluated:     {len(items)}")
    print(f"  Systems:             {len(all_outputs)}")
    print(f"  Total eval results:  {len(all_eval_results)}")
    print(f"  Figures saved to:    {FIGURES_DIR}")
    print(f"  Stats saved to:      {stats_path}")


def _generate_main_table(results, path):
    # markdown table for main results
    metrics = [
        ("Factual", "factual_correctness"),
        ("Source", "source_support"),
        ("Safety", "safety"),
        ("Uncertainty", "uncertainty_handling"),
        ("Clarity", "clarity"),
        ("GSS", "grounded_safety_score"),
    ]
    sys_labels = {
        "llm_only": "A: LLM-Only",
        "rag": "B: RAG",
        "citation_rag": "C: Citation-RAG",
        "agent_pipeline": "D: Multi-Stage Pipeline",
    }

    lines = ["| System | " + " | ".join(m[0] for m in metrics) + " |"]
    lines.append("|" + "|".join(["---"] * (len(metrics) + 1)) + "|")

    for sys_key in ["llm_only", "rag", "citation_rag", "agent_pipeline"]:
        if sys_key not in results:
            continue
        r = results[sys_key]
        cells = [sys_labels.get(sys_key, sys_key)]
        for _, metric_key in metrics:
            m = r.get(metric_key, {"mean": 0, "ci_lower": 0, "ci_upper": 0})
            if isinstance(m, dict):
                cells.append(f"{m['mean']:.3f} ({m['ci_lower']:.3f}-{m['ci_upper']:.3f})")
            else:
                cells.append(f"{m:.3f}")
        lines.append("| " + " | ".join(cells) + " |")

    path.write_text("\n".join(lines), encoding="utf-8")


def _generate_stratified_table(strat_results, path, stratum_label):
    systems = ["llm_only", "rag", "citation_rag", "agent_pipeline"]
    short = {"llm_only": "A", "rag": "B", "citation_rag": "C", "agent_pipeline": "D"}

    lines = [f"| {stratum_label} | " + " | ".join(f"GSS ({short[s]})" for s in systems) + " |"]
    lines.append("|" + "|".join(["---"] * (len(systems) + 1)) + "|")

    for stratum in sorted(strat_results.keys()):
        cells = [stratum.replace("_", " ").title()]
        for sys_key in systems:
            val = strat_results[stratum].get(sys_key, {}).get("gss_mean", 0)
            cells.append(f"{val:.3f}")
        lines.append("| " + " | ".join(cells) + " |")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="US-HealthBench experiment pipeline")
    parser.add_argument(
        "--items", type=int, default=None, help="Limit number of items (for testing)"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    main(max_items=args.items)
