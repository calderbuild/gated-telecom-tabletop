"""The report's tables are hand-laid-out, so this rebuilds every row from eval/results.json
and fails if docs/report.md no longer says the same thing."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDER = ["S1", "S3", "S2"]  # column order used in the report


def cell(m: dict) -> str:
    lo, hi = f"{m['min']:.2f}", f"{m['max']:.2f}"
    return f"{m['mean']:.2f}" + ("" if lo == hi else f" ({lo}-{hi})")


def row(label: str, values: list[str]) -> str:
    return f"| {label} | " + " | ".join(values) + " |"


def test_report_tables_match_eval_results():
    res = json.loads((ROOT / "eval" / "results.json").read_text())["scenarios"]
    s = [res[k]["summary"] for k in ORDER]
    report = (ROOT / "docs" / "report.md").read_text()
    expected = [
        row(
            "Claims / rejected by gate", [f"{x['claims']} / {x['rejected']}" for x in s]
        ),
        row("Citation validity", [cell(x["citation_validity"]) for x in s]),
        row("Action recall", [cell(x["action_recall"]) for x in s]),
        row("Obligation recall", [cell(x["obligation_recall"]) for x in s]),
        row("Gap recall, agents", [cell(x["gap_recall_agent"]) for x in s]),
        row("Correct abstention", [x["abstention_correct"] for x in s]),
        row("Twin restored", [x["loop_restored"] for x in s]),
        row("Chains verified", [x["chains_ok"] for x in s]),
        row(
            "Claims the gate would reject", [x["baseline_would_be_rejected"] for x in s]
        ),
        row(
            "Gap recall, raw / gate-accepted only",
            [
                f"{x['baseline_gap_recall_ungated']:.2f} / {x['baseline_gap_recall_gated']:.2f}"
                for x in s
            ],
        ),
    ]
    missing = [r for r in expected if r not in report]
    assert not missing, (
        "report.md is out of date with eval/results.json:\n" + "\n".join(missing)
    )

    rej = [int(n) / int(d) for n, d in (x["baseline_would_be_rejected"].split("/") for x in s)]
    raw = [x["baseline_gap_recall_ungated"] for x in s]
    assert f"{min(rej):.0%}-{max(rej):.0%}".replace("%-", "-") in report
    assert f"{min(raw):.0%}-{max(raw):.0%}".replace("%-", "-") in report
