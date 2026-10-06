"""Draw the report figures. Fig. 2 reads eval/results.json only, so its numbers come from `python -m tabletop eval`."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).parent
OUT = HERE / "fig"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})


def box(ax, x, y, w, h, text, node, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2 + 0.12, text, ha="center", va="center", fontsize=7.5)
    ax.text(x + w / 2, y + 0.1, node, ha="center", va="bottom", fontsize=6.5, color="#555", style="italic")


def arrow(ax, x1, y1, x2, y2, label="", color="#333"):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", color=color, lw=0.9))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.08, label, ha="center", fontsize=6.5, color=color)


def architecture():
    fig, ax = plt.subplots(figsize=(7.09, 2.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4); ax.axis("off")
    box(ax, 0.1, 2.4, 1.8, 1.2, "Scenario injects\n+ KB (61 sources)", "SRC", "#eef3f8")
    box(ax, 2.3, 2.4, 1.9, 1.2, "Institution inboxes\n(one agent each)", "C", "#eef3f8")
    box(ax, 4.6, 2.4, 1.7, 1.2, "Mandate-scoped\nclause retrieval", "PP", "#eef3f8")
    box(ax, 6.7, 2.4, 1.7, 1.2, "LLM proposes\nJSON claims", "M", "#fff4e0")
    box(ax, 8.8, 2.4, 1.6, 1.2, "Deterministic\ngate", "P", "#e6f2e6")
    box(ax, 8.6, 0.3, 2.0, 1.2, "Coordinator + HITL\nduty matrix, clocks", "D", "#e6f2e6")
    box(ax, 5.9, 0.3, 2.2, 1.2, "Digital twin\ninvariants", "ML sandbox (Y.3090)", "#e6f2e6")
    box(ax, 2.6, 0.3, 2.8, 1.2, "Hash-chained audit log\ngap matrix, replay page", "SINK", "#f3eef8")
    for x1, x2 in [(1.9, 2.3), (4.2, 4.6), (6.3, 6.7), (8.4, 8.8)]:
        arrow(ax, x1, 3.0, x2, 3.0)
    arrow(ax, 9.6, 2.4, 9.6, 1.5)
    ax.text(9.7, 1.9, "accepted", fontsize=6.5)
    arrow(ax, 10.4, 3.0, 11.6, 3.0, "", "#b8322a")
    ax.text(11.0, 3.15, "rejected:\nlogged, fed back,\nnever repaired", ha="left", fontsize=6.5, color="#b8322a")
    arrow(ax, 8.6, 0.9, 8.1, 0.9)
    arrow(ax, 5.9, 0.9, 5.4, 0.9)
    ax.text(0.3, 0.6, "MLFO:\nengine.py\n(stage loop)", ha="left", fontsize=6.5, color="#555")
    fig.tight_layout()
    fig.savefig(OUT / "fig1-architecture.png", dpi=300)


def frac(pair):
    return pair[0] / pair[1]


def mean_of(vals):
    return sum(vals) / len(vals), vals


def results():
    """Bars match the tables in the report (pooled rejection rate, mean recall); whiskers span the 3 runs."""
    r = json.loads((HERE.parent / "eval" / "results.json").read_text())["scenarios"]
    sids = list(r)
    series = {
        "rej": (
            [(sum(x["rejected"] for x in r[s]["runs"]) / sum(x["claims"] for x in r[s]["runs"]), [x["rejected"] / x["claims"] for x in r[s]["runs"]]) for s in sids],
            [(sum(x["would_be_rejected"] for x in r[s]["baselines"]) / sum(x["claims"] for x in r[s]["baselines"]), [x["would_be_rejected"] / x["claims"] for x in r[s]["baselines"]]) for s in sids],
        ),
        "gap": (
            [mean_of([frac(x["gap_recall_agent"]) for x in r[s]["runs"]]) for s in sids],
            [mean_of([frac(x["gap_recall_ungated"]) for x in r[s]["baselines"]]) for s in sids],
        ),
    }
    fig, axes = plt.subplots(1, 2, figsize=(7.09, 2.2))
    titles = {"rej": "Share of claims the gate rejects", "gap": "Gap recall against the frozen keys"}
    for ax, key, tag in [(axes[0], "rej", "a"), (axes[1], "gap", "b")]:
        for off, data, colour, label in [(-0.18, series[key][0], "#2a7a37", "Gated agents"), (0.18, series[key][1], "#b0560c", "Ungated baseline, same model")]:
            xs = [i + off for i in range(len(sids))]
            vals = [v for v, _ in data]
            lo = [v - min(runs) for v, runs in data]
            hi = [max(runs) - v for v, runs in data]
            ax.bar(xs, vals, 0.34, color=colour, label=label, yerr=[lo, hi], capsize=2, error_kw={"lw": 0.7, "ecolor": "#222"})
            for x, v, h in zip(xs, vals, hi):
                ax.text(x, v + h + 0.03, f"{v:.2f}", ha="center", fontsize=6.5)
        ax.set_xticks(range(len(sids)), sids)
        ax.set_ylim(0, 1.15)
        ax.set_title(titles[key], fontsize=8)
        ax.text(-0.14, 1.04, tag, transform=ax.transAxes, fontsize=10, fontweight="bold")
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=6.5, frameon=False, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.0))
    fig.text(0.99, 0.01, "3 runs per bar; whiskers: min-max across runs", ha="right", fontsize=6, color="#555")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT / "fig2-results.png", dpi=300)


architecture()
results()
