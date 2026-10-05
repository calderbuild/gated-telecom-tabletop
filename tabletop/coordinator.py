"""The Y.3172 distributor (D) node: routes accepted claims and derives gaps mechanically.

Three deterministic gap sources, each logged with its origin:
  duty-matrix  a scenario duty no institution took up (no_owner), or an exclusive duty
               two institutions took up (overlap)
  rule-table   a notification clock where the UAE rule states no deadline (no_deadline),
               compared with the global rules that do, and whether OpCo met them
  twin         an accepted action that restored one invariant while breaking another
               (conflict of objectives)
Gaps proposed by agents are a fourth source; they count only after passing the gate.
"""

from tabletop.twin import check

HIGH_IMPACT = {
    "rollback_change",
    "wilt_sites",
    "rollback_model",
    "set_threshold",
    "disable_tool",
    "restore_scope",
    "export_minimised",
}
HITL_POLICY = (
    "scripted facilitator: approve a high-impact action only after the gate accepted it"
)


def duty_owners(
    duty: dict, actions: list[dict], obligations: list[dict], chunks: dict
) -> list[str]:
    owners = set()
    for a in actions:
        m = duty.get("action")
        if (
            m
            and a["claim"]["verb"] in m["verbs"]
            and all(
                a["claim"].get("params", {}).get(k) in v
                for k, v in m.get("params", {}).items()
            )
        ):
            owners.add(a["agent"])
    for o in obligations:
        m = duty.get("obligation")
        cited = " ".join(
            chunks[e["chunk_id"]]["text"].lower()
            for e in o["claim"]["evidence"]
            if e["chunk_id"] in chunks
        )
        if m and any(p.lower() in cited for p in m["phrases"]):
            owners.add(o["agent"])
    return sorted(owners)


def duty_gaps(scenario: dict, actions, obligations, chunks) -> list[dict]:
    gaps = []
    for d in scenario.get("duties", []):
        owners = duty_owners(d, actions, obligations, chunks)
        row = {
            "duty": d["id"],
            "description": d["description"],
            "owners": owners,
            "expected_owner": d.get("expected_owner"),
        }
        if not owners:
            gaps.append({"origin": "duty-matrix", "gap_type": "no_owner", **row})
        elif d.get("exclusive") and len(owners) > 1:
            gaps.append({"origin": "duty-matrix", "gap_type": "overlap", **row})
    return gaps


def clock_checks(
    scenario: dict, rules: dict, actions: list[dict], inject_t: dict
) -> list[dict]:
    """Elapsed exercise minutes from the fault inject to the matching notify, against each rule's clock."""
    out = []
    for c in scenario.get("clock_checks", []):
        done = [
            a
            for a in actions
            if a["agent"] == c["from"]
            and a["claim"]["verb"] == "notify"
            and a["claim"].get("params", {}).get("to") == c["to"]
        ]
        elapsed = (done[0]["t"] - inject_t[c["fault_inject"]]) if done else None
        rows = []
        for rid in [c["uae_rule"]] + c["global_rules"]:
            r = rules[rid]
            met = (
                None
                if r["hours"] is None or elapsed is None
                else elapsed <= r["hours"] * 60
            )
            rows.append(
                {
                    "rule": rid,
                    "jurisdiction": r["jurisdiction"],
                    "hours": r["hours"],
                    "met": met,
                }
            )
        gap = None
        if rules[c["uae_rule"]]["hours"] is None:
            gap = {
                "origin": "rule-table",
                "gap_type": "no_deadline",
                "duty": c["id"],
                "description": c["description"],
                "uae_rule": c["uae_rule"],
                "global_rules": [
                    r for r in c["global_rules"] if rules[r]["hours"] is not None
                ],
            }
        out.append(
            {"check": c["id"], "notified_after_min": elapsed, "rules": rows, "gap": gap}
        )
    return out


def objective_conflict(change: dict, invariants: list[dict]) -> list:
    """[fixed, broke] invariant names when an action fixed some and broke others, else []."""

    before, after = (
        check(change["before"], invariants)["results"],
        check(change["after"], invariants)["results"],
    )
    fixed = [k for k in before if not before[k] and after[k]]
    broke = [k for k in before if before[k] and not after[k]]
    return [fixed, broke] if fixed and broke else []
