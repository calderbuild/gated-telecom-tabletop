from tabletop import evals
from tabletop.audit import AuditLog

KEY = {
    "actions": [
        {"id": "A-ROLL", "agent": "NOC", "verbs": ["rollback_change"]},
        {"id": "A-NOTIFY", "agent": "NOC", "verbs": ["notify"], "params": {"to": ["REG"]}},
    ],
    "obligations": [{"id": "O1", "agents": ["NOC"], "phrases": ["unplanned interruption"]}],
    "gaps": [
        {"id": "G-GLOBAL", "types": ["no_deadline"], "uae_phrases": [], "global_docs": ["CA-CRTC-2025-225"]},
        {"id": "G-UAE", "types": ["no_rule"], "uae_phrases": ["as soon as possible as to the reason"], "global_docs": []},
        {"id": "G-MISS", "types": ["conflict"], "uae_phrases": [], "global_docs": []},
    ],
    "abstention": {"inject": "I9", "agent": "REG"},
}
LIC = [{"chunk_id": "UAE-LIC-2-2026#0086", "quote": "q"}]
CRTC = [{"chunk_id": "CA-CRTC-2025-225#0000", "quote": "q"}]


def claim(log, agent, accepted, reasons=(), **c):
    return log.append("claim", agent=agent, claim=c, accepted=accepted, reasons=list(reasons))["seq"]


def test_score_run_counts_only_what_the_log_supports(tmp_path, monkeypatch):
    monkeypatch.setattr(evals, "ROOT", tmp_path)
    path = tmp_path / "run.jsonl"
    log = AuditLog(path)
    log.append("run_start", scenario="T")
    roll = claim(log, "NOC", True, type="action", verb="rollback_change", evidence=LIC)
    log.append("state_change", claim_seq=roll, change={"error": "no applied change X"})
    claim(log, "NOC", True, type="action", verb="notify", params={"to": "REG"}, evidence=LIC)
    claim(log, "REG", True, type="action", verb="notify", params={"to": "REG"}, evidence=LIC)  # wrong agent
    claim(log, "NOC", True, type="obligation", evidence=LIC)
    claim(log, "NOC", True, type="gap", gap_type="no_deadline", evidence=LIC, global_examples=CRTC)
    claim(log, "DPA", True, type="gap", gap_type="no_rule", evidence=LIC)
    claim(log, "NOC", False, ["NOT_VERBATIM:x"], type="gap", gap_type="conflict", evidence=LIC)
    claim(log, "REG", True, type="insufficient_evidence", inject_refs=["I9"])
    log.append("run_end", check={"holds": False}, metrics={})
    r = evals.score_run(path, KEY)
    assert r["chain_ok"]
    assert r["action_recall"] == (1, 2)  # rollback failed in the twin, so only the notify counts
    assert r["actions_failed_in_twin"] == 1
    assert r["obligation_recall"] == (1, 1)
    assert r["gap_recall_agent"] == (2, 3)  # G-MISS only appears in a rejected claim
    assert r["citation_validity"] == round(1 - 1 / 7, 4)
    assert r["abstention_correct"] is True
    assert r["loop_restored"] is False


def test_evaluate_refuses_a_log_without_run_end(tmp_path, monkeypatch):
    monkeypatch.setattr(evals, "ROOT", tmp_path)
    (tmp_path / "runs" / "S1").mkdir(parents=True)
    log = AuditLog(tmp_path / "runs" / "S1" / "run1.jsonl")
    log.append("run_start", scenario="S1")
    assert "run1.jsonl" in evals.check_logs(["S1"])[0]


def test_audit_log_never_truncates_an_existing_file(tmp_path):
    path = tmp_path / "run.jsonl"
    AuditLog(path).append("run_end")
    before = path.read_text()
    try:
        AuditLog(path)
        raise AssertionError("opened an existing log")
    except FileExistsError:
        pass
    assert path.read_text() == before
