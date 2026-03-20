"""Visualization -- main results charts, heatmaps, consistency plots."""

import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

logger = logging.getLogger(__name__)

# Publication-ready style defaults
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)

SYSTEM_LABELS = {
    "llm_only": "LLM-Only",
    "rag": "RAG",
    "citation_rag": "Citation-RAG",
    "agent_pipeline": "Multi-Stage Pipeline",
}

SYSTEM_COLORS = {
    "llm_only": "#4C78A8",
    "rag": "#F58518",
    "citation_rag": "#E45756",
    "agent_pipeline": "#72B7B2",
}

METRIC_LABELS = {
    "factual_correctness": "Factual\nCorrectness",
    "source_support": "Source\nSupport",
    "safety": "Safety",
    "uncertainty_handling": "Uncertainty\nHandling",
    "clarity": "Clarity",
    "grounded_safety_score": "Grounded\nSafety Score",
}


def plot_main_results(
    results: dict,
    output_path,
    title: str = "System Performance Across Metrics",
) -> None:
    """Grouped bar chart of system performance across metrics."""
    metrics = [
        "factual_correctness",
        "source_support",
        "safety",
        "uncertainty_handling",
        "clarity",
        "grounded_safety_score",
    ]
    systems = [s for s in SYSTEM_LABELS if s in results]

    x = np.arange(len(metrics))
    width = 0.18
    fig, ax = plt.subplots(figsize=(14, 6))

    for i, system in enumerate(systems):
        means = []
        err_lo = []
        err_hi = []
        for m in metrics:
            r = results[system].get(m, {"mean": 0, "ci_lower": 0, "ci_upper": 0})
            mean = r["mean"]
            means.append(mean)
            err_lo.append(mean - r["ci_lower"])
            err_hi.append(r["ci_upper"] - mean)

        offset = (i - len(systems) / 2 + 0.5) * width
        ax.bar(
            x + offset,
            means,
            width,
            label=SYSTEM_LABELS[system],
            color=SYSTEM_COLORS[system],
            yerr=[err_lo, err_hi],
            capsize=3,
            error_kw={"linewidth": 0.8},
        )

    ax.set_xlabel("Metric")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels([METRIC_LABELS.get(m, m) for m in metrics])
    ax.legend(loc="upper left", framealpha=0.9)
    ax.set_ylim(0, 2.2)
    ax.axhline(y=2.0, color="gray", linestyle="--", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info("Saved main results plot to %s", output_path)


def plot_error_taxonomy_heatmap(
    flag_rates: dict,
    output_path,
    title: str = "Error Taxonomy by System",
) -> None:
    """Heatmap of binary flag rates across systems."""
    flags = [
        "fabricated_citation_rate",
        "unsupported_medical_recommendation_rate",
        "false_reassurance_rate",
        "omission_of_escalation_advice_rate",
    ]
    flag_labels = [
        "Fabricated\nCitation",
        "Unsupported\nMedical Rec.",
        "False\nReassurance",
        "Omitted\nEscalation",
    ]

    systems = [s for s in SYSTEM_LABELS if s in flag_rates]
    data = []
    for system in systems:
        row = [flag_rates[system].get(f, 0.0) for f in flags]
        data.append(row)

    data_arr = np.array(data)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(
        data_arr,
        annot=True,
        fmt=".2f",
        xticklabels=flag_labels,
        yticklabels=[SYSTEM_LABELS[s] for s in systems],
        cmap="YlOrRd",
        vmin=0,
        vmax=0.5,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title(title)

    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info("Saved error taxonomy heatmap to %s", output_path)


def plot_cross_language_consistency(
    en_gss,
    es_gss,
    output_path,
    title: str = "English vs. Spanish Grounded Safety Score",
) -> None:
    # Scatter comparing EN and ES GSS for cross-language pairs
    fig, ax = plt.subplots(figsize=(7, 7))

    ax.scatter(en_gss, es_gss, alpha=0.6, s=30, color="#4C78A8", edgecolors="white", linewidth=0.3)

    # diagonal = perfect consistency
    lims = [0, 1.05]
    ax.plot(lims, lims, "--", color="gray", alpha=0.5, linewidth=1)

    ax.set_xlabel("English GSS")
    ax.set_ylabel("Spanish GSS")
    ax.set_title(title)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_aspect("equal")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info("Saved cross-language consistency plot to %s", output_path)


def plot_benchmark_composition(
    items,
    output_path,
    title: str = "Benchmark Composition",
) -> None:
    """Multi-panel figure: benchmark composition by topic, language, task family."""
    from collections import Counter

    topics = Counter(item.get("topic", "unknown") for item in items)
    languages = Counter(item.get("language", "unknown") for item in items)
    families = Counter(item.get("task_family", "unknown") for item in items)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Topics
    ax = axes[0]
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    ax.barh(
        [t[0].replace("_", " ").title() for t in sorted_topics],
        [t[1] for t in sorted_topics],
        color="#4C78A8",
    )
    ax.set_xlabel("Count")
    ax.set_title("By Topic")
    ax.invert_yaxis()

    # Languages
    ax = axes[1]
    lang_labels = {"en": "English", "es": "Spanish"}
    ax.bar(
        [lang_labels.get(k, k) for k in languages],
        list(languages.values()),
        color=["#4C78A8", "#F58518"],
    )
    ax.set_xlabel("Language")
    ax.set_ylabel("Count")
    ax.set_title("By Language")

    # Task families
    ax = axes[2]
    family_labels = {
        "factual_retrieval": "Factual\nRetrieval",
        "consumer_action": "Consumer\nAction",
        "misinformation_rebuttal": "Misinfo.\nRebuttal",
        "cross_language": "Cross-\nLanguage",
    }
    sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)
    ax.bar(
        [family_labels.get(f[0], f[0]) for f in sorted_families],
        [f[1] for f in sorted_families],
        color="#72B7B2",
    )
    ax.set_xlabel("Task Family")
    ax.set_ylabel("Count")
    ax.set_title("By Task Family")

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info("Saved benchmark composition figure to %s", output_path)
