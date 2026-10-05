"""Metrics computed from audit logs only. Every number in the README and report comes from here.

Answer keys (tabletop/data/keys/*.json) were written and hashed before the first live run;
each run's run_start event records the key hash it was scored against.
"""

import json
from collections import Counter
from pathlib import Path
from statistics import mean

from tabletop import audit
from tabletop.audit import load, verify
from tabletop.engine import DATA, load_json
from tabletop.kb import chunks, load_manifest

ROOT = Path(__file__).resolve().parent.parent


def _cited_text(claim: dict, field: str = "evidence") -> str:
    ch = chunks()
    return " ".join(
        ch[e["chunk_id"]]["text"].lower()
        for e in claim.get(field) or []
        if e.get("chunk_id") in ch
    )


def _cited_docs(claim: dict, field: str) -> set[str]:
    ch = chunks()
    return {
        ch[e["chunk_id"]]["doc_id"]
        for e in claim.get(field) or []
        if e.get("chunk_id") in ch
    }


def match_action(k: dict, rec: dict) -> bool:
    c = rec["claim"]
    return (
        rec["agent"] == k["agent"]
        and c.get("type") == "action"
        and c.get("verb") in k["verbs"]
        and all(c.get("params", {}).get(p) in v for p, v in k.get("params", {}).items())
    )


def match_obligation(k: dict, rec: dict) -> bool:
    c = rec["claim"]
    return (
        rec["agent"] in k["agents"]
        and c.get("type") == "obligation"
        and any(p.lower() in _cited_text(c) for p in k["phrases"])
    )


def match_gap(k: dict, rec: dict) -> bool:
    c = rec["claim"]
    if c.get("type") != "gap" or c.get("gap_type") not in k["types"]:
        return False
    return bool(_cited_docs(c, "global_examples") & set(k["global_docs"])) or any(
        p.lower() in _cited_text(c) for p in k["uae_phrases"]
    )


def claims_of(events: list[dict]) -> list[dict]:
    return [
        {
            "agent": e["data"]["agent"],
            "claim": e["data"]["claim"],
            "accepted": e["data"]["accepted"],
            "reasons": e["data"]["reasons"],
            "seq": e["seq"],
        }
        for e in events
        if e["type"] in ("claim", "baseline_claim")
    ]


def recall(items: list[dict], recs: list[dict], matcher) -> tuple[int, int, list[str]]:
    hit = [k["id"] for k in items if any(matcher(k, r) for r in recs)]
    return len(hit), len(items), hit


def score_run(path: Path, key: dict) -> dict:
    events = load(path)
    ok, chain = verify(path)
    cl = claims_of(events)
    acc = [c for c in cl if c["accepted"]]
    reasons = Counter(r.split(":")[0] for c in cl for r in c["reasons"])
    with_ev = [
        c for c in cl if c["claim"].get("type") in ("action", "obligation", "gap")
    ]
    cite_bad = [
        c
        for c in with_ev
        if any(
            r.split(":")[0]
            in ("NOT_VERBATIM", "NOT_RETRIEVED", "SHORT_QUOTE", "NO_EVIDENCE")
            for r in c["reasons"]
        )
    ]
    actions = [c for c in cl if c["claim"].get("type") == "action"]
    # an accepted action the twin refused (e.g. rolling back a change never applied) did nothing
    twin_failed = {
        e["data"]["claim_seq"]
        for e in events
        if e["type"] == "state_change" and e["data"]["change"]["error"]
    }
    effective = [c for c in acc if c["seq"] not in twin_failed]
    gaps_acc = [c for c in acc if c["claim"].get("type") == "gap"]
    mech = [
        e["data"]
        for e in events
        if e["type"] == "gap_detected" and not e["data"]["origin"].startswith("agent:")
    ]
    end = next(e["data"] for e in events if e["type"] == "run_end")
    ab = key.get("abstention")
    abstained = None
    if ab:
        abstained = any(
            c["agent"] == ab["agent"]
            and c["claim"].get("type") in ("insufficient_evidence", "gap")
            and ab["inject"] in (c["claim"].get("inject_refs") or [])
            for c in acc
        )
    mech_hits = [
        k["id"]
        for k in key["gaps"]
        if any(g.get("duty") == k.get("duty") and k.get("duty") for g in mech)
    ]
    agent_gap_hits = recall(key["gaps"], acc, match_gap)
    return {
        "log": str(path.relative_to(ROOT)),
        "chain_ok": ok,
        "chain": chain,
        "model_calls": sum(e["type"] == "model_call" for e in events),
        "parse_errors": sum(e["type"] == "parse_error" for e in events),
        "claims": len(cl),
        "accepted": len(acc),
        "rejected": len(cl) - len(acc),
        "reject_reasons": dict(reasons),
        "citation_validity": round(1 - len(cite_bad) / len(with_ev), 4)
        if with_ev
        else None,
        "mandate_attempts": sum(
            any(r.startswith("MANDATE") for r in c["reasons"]) for c in actions
        ),
        "actions_proposed": len(actions),
        "inject_boundary_attempts": sum(
            any(r.startswith("INJECT") for r in c["reasons"]) for c in cl
        ),
        "action_recall": recall(key["actions"], effective, match_action)[:2],
        "actions_failed_in_twin": len(twin_failed),
        "obligation_recall": recall(key["obligations"], acc, match_obligation)[:2],
        "gap_recall_agent": agent_gap_hits[:2],
        "gap_recall_any": (
            len(set(agent_gap_hits[2]) | set(mech_hits)),
            len(key["gaps"]),
        ),
        "gaps_accepted": len(gaps_acc),
        "gaps_with_verified_global_example": sum(
            bool(c["claim"].get("global_examples")) for c in gaps_acc
        ),
        "mechanical_gaps": len(mech),
        "abstention_correct": abstained,
        "loop_restored": end["check"]["holds"],
        "final_metrics": end["metrics"],
        "tokens": sum(
            e["data"].get("usage", {}).get("total_tokens", 0)
            for e in events
            if e["type"] == "model_call"
        ),
    }


def score_baseline(path: Path, key: dict) -> dict:
    events = load(path)
    cl = claims_of(events)
    acc = [c for c in cl if c["accepted"]]
    reasons = Counter(r.split(":")[0] for c in cl for r in c["reasons"])
    return {
        "log": str(path.relative_to(ROOT)),
        "chain_ok": verify(path)[0],
        "claims": len(cl),
        "would_be_rejected": len(cl) - len(acc),
        "reject_reasons": dict(reasons),
        "gap_recall_ungated": recall(key["gaps"], cl, match_gap)[:2],
        "gap_recall_gated": recall(key["gaps"], acc, match_gap)[:2],
        "action_recall_ungated": recall(key["actions"], cl, match_action)[:2],
    }


def frac(pair) -> float:
    return pair[0] / pair[1] if pair[1] else 0.0


def check_logs(scenarios: list[str]) -> list[str]:
    """Every scored log must verify: an incomplete or tampered run would skew the numbers."""
    bad = []
    for sid in scenarios:
        for p in sorted((ROOT / "runs" / sid).glob("*.jsonl")):
            ok, msg = audit.verify(p)
            if not ok:
                bad.append(f"{p.relative_to(ROOT)}: {msg}")
    return bad


def evaluate(scenarios: list[str]) -> dict:
    bad = check_logs(scenarios)
    if bad:
        raise SystemExit("cannot evaluate, these logs do not verify:\n" + "\n".join(bad))
    out = {"scenarios": {}, "kb": kb_stats()}
    for sid in scenarios:
        key = load_json(DATA / "keys" / f"{sid}.json")
        runs = [
            score_run(p, key) for p in sorted((ROOT / "runs" / sid).glob("run*.jsonl"))
        ]
        base = [
            score_baseline(p, key)
            for p in sorted((ROOT / "runs" / sid).glob("baseline*.jsonl"))
        ]
        summary = {}
        if runs:
            for name in ("citation_validity",):
                vals = [r[name] for r in runs if r[name] is not None]
                summary[name] = (
                    {"mean": round(mean(vals), 4), "min": min(vals), "max": max(vals)}
                    if vals
                    else None
                )
            for name in (
                "action_recall",
                "obligation_recall",
                "gap_recall_agent",
                "gap_recall_any",
            ):
                vals = [frac(r[name]) for r in runs]
                summary[name] = {
                    "mean": round(mean(vals), 4),
                    "min": round(min(vals), 4),
                    "max": round(max(vals), 4),
                }
            summary["loop_restored"] = (
                f"{sum(r['loop_restored'] for r in runs)}/{len(runs)}"
            )
            summary["abstention_correct"] = (
                f"{sum(bool(r['abstention_correct']) for r in runs)}/{len(runs)}"
            )
            summary["claims"] = sum(r["claims"] for r in runs)
            summary["rejected"] = sum(r["rejected"] for r in runs)
            summary["mandate_attempts_blocked"] = sum(
                r["mandate_attempts"] for r in runs
            )
            summary["inject_boundary_attempts_blocked"] = sum(
                r["inject_boundary_attempts"] for r in runs
            )
            summary["chains_ok"] = f"{sum(r['chain_ok'] for r in runs)}/{len(runs)}"
        if base:
            summary["baseline_would_be_rejected"] = (
                f"{sum(b['would_be_rejected'] for b in base)}/{sum(b['claims'] for b in base)}"
            )
            summary["baseline_gap_recall_ungated"] = round(
                mean(frac(b["gap_recall_ungated"]) for b in base), 4
            )
            summary["baseline_gap_recall_gated"] = round(
                mean(frac(b["gap_recall_gated"]) for b in base), 4
            )
        out["scenarios"][sid] = {"summary": summary, "runs": runs, "baselines": base}
    return out


def kb_stats() -> dict:
    m = load_manifest()
    by = lambda f: dict(Counter(s[f] for s in m.values()))
    return {
        "sources": len(m),
        "chunks": len(chunks()),
        "by_status": by("status"),
        "by_layer": by("layer"),
    }


def markdown(res: dict) -> str:
    kb = res["kb"]
    lines = [
        f"# Evaluation results",
        "",
        "Generated by `python -m tabletop eval` from the committed audit logs in runs/. Do not edit by hand.",
        "",
        f"KB: {kb['sources']} sources, {kb['chunks']} chunks; status {kb['by_status']}.",
        "",
        "| Scenario | Runs (chain ok) | Claims | Rejected by gate | Citation validity (mean, min-max) | Action recall | Obligation recall | Gap recall, agents | Gap recall, agents + rules | Abstention | Loop restored | Ungated baseline: claims the gate would reject | Baseline gap recall ungated / gated |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for sid, s in res["scenarios"].items():
        x = s["summary"]
        if not x:
            continue
        r = lambda k: f"{x[k]['mean']:.2f} ({x[k]['min']:.2f}-{x[k]['max']:.2f})"
        lines.append(
            f"| {sid} | {x['chains_ok']} | {x['claims']} | {x['rejected']} | {r('citation_validity') if x['citation_validity'] else 'n/a'} | {r('action_recall')} | {r('obligation_recall')} | {r('gap_recall_agent')} | {r('gap_recall_any')} | {x['abstention_correct']} | {x['loop_restored']} | {x.get('baseline_would_be_rejected', 'n/a')} | {x.get('baseline_gap_recall_ungated', 'n/a')} / {x.get('baseline_gap_recall_gated', 'n/a')} |"
        )
    lines += [
        "",
        "Recall is measured against answer keys I wrote before the first live run (hash in each run_start event). It is relative to those keys, not to all possible gaps. Injects are synthetic.",
    ]
    return "\n".join(lines) + "\n"
