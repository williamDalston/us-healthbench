"""Regenerate all four figures from the frozen item file.

Fig 1 reproduces the benchmark's composition as the passing validation recorded
it; Figs 2-4 report the audit. All four are computed here so that no figure in
the paper depends on a pipeline that is no longer runnable. All figures here are computed by the same code path as
scripts/audit_data_quality.py, so captions and figures cannot drift apart.

Usage:  python -m scripts.make_audit_figures
"""

from __future__ import annotations

import collections
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from scripts.audit_data_quality import MOJIBAKE, item_texts, load  # noqa: E402

OUT = Path("paper/figures")
INK = "#1f2937"
ACCENT = "#b45309"
MUTED = "#9ca3af"
SHORT = {
    "respiratory_illness": "respiratory",
    "infectious_disease": "infectious dis.",
    "mental_health_substance": "mental health",
    "insurance_access": "insurance",
    "chronic_disease": "chronic dis.",
    "pregnancy_maternal": "pregnancy",
    "emergency_preparedness": "emergency prep.",
    "misinformation_rebuttal": "misinfo. rebuttal",
    "factual_retrieval": "factual retrieval",
    "consumer_action": "consumer action",
    "cross_language": "cross-language",
    "en": "English", "es": "Spanish",
}


def _finish(ax, title, ylabel=None):
    ax.set_title(title, fontsize=11, color=INK, pad=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=INK, labelsize=9)


def main() -> None:
    items = load()
    n = len(items)
    OUT.mkdir(parents=True, exist_ok=True)

    # --- shared computations (identical to the audit script) ---
    mojibake = [i for i in items if any(MOJIBAKE.search(t or "") for t in item_texts(i))]
    garbled = [i for i in items if i["question"].rstrip().endswith(":?") or "??" in i["question"]]
    byq = collections.defaultdict(list)
    for i in items:
        byq[i["question"].strip()].append(i)
    dupes = {q: v for q, v in byq.items() if len(v) > 1}
    conflicting = {
        q: v for q, v in dupes.items()
        if len({(i.get("reference_answer") or {}).get("answer_text", "") for i in v}) > 1
    }
    n_conf = sum(len(v) for v in conflicting.values())

    # --- Fig 1: composition as recorded ---
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.8))
    for ax, (title, counter, top) in zip(axes, [
        ("Topic", collections.Counter(i["topic"] for i in items), 6),
        ("Language", collections.Counter(i["language"] for i in items), 2),
        ("Task family", collections.Counter(i["task_family"] for i in items), 4),
    ]):
        pairs = counter.most_common(top)
        labels = [SHORT.get(k, k.replace("_", " ")) for k, _ in pairs]
        ax.barh(labels[::-1], [v for _, v in pairs][::-1], color=MUTED, height=0.6)
        ax.set_title(title, fontsize=9, color=INK)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(colors=INK, labelsize=6.5)
    fig.suptitle(f"Benchmark composition as recorded (n = {n:,})", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_composition_as_recorded.png", dpi=300)
    plt.close(fig)

    # --- Fig 2: defect rates by class ---
    labels = ["Template collision\n(conflicting golds)", "Encoding\ncorruption", "Malformed-join\nquestions"]
    vals = [100 * n_conf / n, 100 * len(mojibake) / n, 100 * len(garbled) / n]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    bars = ax.bar(labels, vals, color=[ACCENT, ACCENT, MUTED], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.1f}%", ha="center", fontsize=10, color=INK)
    ax.set_ylim(0, max(vals) * 1.25)
    _finish(ax, f"Defect rates in the frozen benchmark (n = {n:,}); all values are lower bounds", "% of items")
    fig.tight_layout(); fig.savefig(OUT / "fig2_defect_rates.png", dpi=300); plt.close(fig)

    # --- Fig 4: encoding corruption by language ---
    lang_tot = collections.Counter(i["language"] for i in items)
    lang_bad = collections.Counter(i["language"] for i in mojibake)
    order = ["es", "en"]
    names = {"es": "Spanish", "en": "English"}
    rates = [100 * lang_bad[l] / lang_tot[l] for l in order]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    bars = ax.barh([names[l] for l in order], rates, color=[ACCENT, MUTED], height=0.5)
    for b, l, r in zip(bars, order, rates):
        ax.text(r + 1.2, b.get_y() + b.get_height() / 2,
                f"{r:.1f}%  ({lang_bad[l]}/{lang_tot[l]})", va="center", fontsize=10, color=INK)
    agg = 100 * len(mojibake) / n
    ax.axvline(agg, color=INK, linestyle="--", linewidth=1)
    # annotate inside the axes, clear of the x tick labels
    ax.annotate(f"aggregate {agg:.1f}%", xy=(agg, 0.5), xytext=(agg + 4, 0.62),
                textcoords="data", fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
    ax.set_xlim(0, 100)
    ax.margins(y=0.28)
    _finish(ax, "Encoding corruption concentrates in the minority-language subset", None)
    ax.set_xlabel("% of items in that language", fontsize=9, color=INK)
    fig.tight_layout(); fig.savefig(OUT / "fig4_encoding_by_language.png", dpi=300); plt.close(fig)

    # --- Fig 3: template collision distribution ---
    sizes = collections.Counter(len(v) for v in byq.values())
    conf_sizes = collections.Counter(len(v) for v in conflicting.values())
    xs = sorted(sizes)
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.bar([str(x) for x in xs], [sizes[x] for x in xs], color=MUTED, width=0.6, label="question strings")
    ax.bar([str(x) for x in xs], [conf_sizes.get(x, 0) for x in xs], color=ACCENT, width=0.6,
           label="of which: differing gold answers")
    ax.set_yscale("log")
    ax.legend(frameon=False, fontsize=9)
    _finish(ax, f"{len(byq):,} distinct question strings across {n:,} items (max repetition: {max(xs)})",
            "count of question strings (log)")
    ax.set_xlabel("items sharing the same question string", fontsize=9, color=INK)
    fig.tight_layout(); fig.savefig(OUT / "fig3_template_collision.png", dpi=300); plt.close(fig)

    print(f"wrote fig1 (defects {vals[0]:.1f}/{vals[1]:.1f}/{vals[2]:.1f}%), "
          f"fig2 (es {rates[0]:.1f}%, en {rates[1]:.1f}%), fig3 (max repeat {max(xs)})")


if __name__ == "__main__":
    main()
