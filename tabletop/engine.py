"""The Y.3172 MLFO role: releases injects in stages, steps agents, gates claims, applies
approved actions to the twin and logs every step to the hash-chained audit log."""

import json
import subprocess
from pathlib import Path

from tabletop import agents, coordinator, gate
from tabletop.audit import AuditLog, sha256
from tabletop.kb import KB, Index, chunks, load_manifest
from tabletop.llm import parse_json
from tabletop.twin import Twin, check

DATA = Path(__file__).resolve().parent / "data"
MAX_ROUNDS_PER_STAGE = 3
GLOBAL_LAYERS = ("global-standard", "global-law", "global-precedent", "global-guidance")


def load_json(path: Path):
    return json.loads(Path(path).read_text())


def load_scenario(sid: str) -> dict:
    return load_json(DATA / "scenarios" / f"{sid}.json")


def load_mandates() -> dict:
    return load_json(DATA / "mandates.json")["institutions"]


def load_rules() -> dict:
    return {r["id"]: r for r in load_json(DATA / "rules.json")["rules"]}


def file_sha(path: Path) -> str:
    return sha256(Path(path).read_bytes())


def git_head() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=KB.parent,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


class Run:
    def __init__(self, scenario: dict, provider, log_path: Path):
        self.s = scenario
        self.provider = provider
        self.log = AuditLog(log_path)
        self.mandates = {
            i: m for i, m in load_mandates().items() if i in scenario["institutions"]
        }
        self.rules = load_rules()
        self.manifest = load_manifest()
        self.chunks = chunks()
        self.indexes = {"global": Index(set(GLOBAL_LAYERS))}
        for m in self.mandates.values():
            self.indexes.setdefault(tuple(m["layers"]), Index(set(m["layers"])))
        self.twin = Twin()
        self.inbox = {i: [] for i in self.mandates}
        self.seen = {i: set() for i in self.mandates}
        self.retrieved = {i: set() for i in self.mandates}
        self.rejected_last = {i: [] for i in self.mandates}
        self.steps = {i: 0 for i in self.mandates}
        self.accepted = []
        self.inject_t = {}
        self.msg_n = 0
        self.t = 0

    # ---------- helpers ----------

    def deliver(self, to: str, mid: str, sender: str, label: str, text: str):
        self.inbox[to].append(
            {"id": mid, "from": sender, "label": label, "text": text, "t": self.t}
        )

    def new_message_id(self, kind: str) -> str:
        self.msg_n += 1
        return f"{self.s['id']}-{kind}{self.msg_n:02d}"

    def invariants(self, where: str):
        m = self.twin.metrics()
        self.log.append(
            "invariants",
            where=where,
            t=self.t,
            metrics=m,
            check=check(m, self.s["invariants"]),
        )

    # ---------- run ----------

    def start(self):
        keys = DATA / "keys" / f"{self.s['id']}.json"
        self.log.append(
            "run_start",
            scenario=self.s["id"],
            title=self.s["title"],
            provider=self.provider.name,
            model=getattr(self.provider, "model", None),
            git_head=git_head(),
            hashes={
                "kb_manifest": file_sha(KB / "manifest.json"),
                "kb_chunks": file_sha(KB / "chunks.jsonl"),
                "scenario": file_sha(DATA / "scenarios" / f"{self.s['id']}.json"),
                "answer_key": file_sha(keys) if keys.exists() else None,
                "mandates": file_sha(DATA / "mandates.json"),
                "rules": file_sha(DATA / "rules.json"),
                "prompt_template": sha256(
                    {"system": agents.SYSTEM, "user": agents.USER}
                ),
            },
            hitl_policy=coordinator.HITL_POLICY,
        )
        for ev in self.s.get("twin_setup", []):
            self.twin.act(ev["verb"], ev["params"])
        self.invariants("setup")

    def release(self, inj: dict):
        self.inject_t[inj["id"]] = inj["t"]
        for to in inj["to"]:
            self.deliver(to, inj["id"], "exercise control", inj["label"], inj["text"])
        self.log.append("inject_released", t=self.t, inject=inj)
        if inj.get("twin_event"):
            ev = inj["twin_event"]
            change = self.twin.act(ev["verb"], ev["params"])
            self.log.append(
                "twin_event",
                t=self.t,
                inject=inj["id"],
                verb=ev["verb"],
                params=ev["params"],
                change=change,
            )

    def step(self, agent: str, stage: str):
        m = self.mandates[agent]
        new = [x for x in self.inbox[agent] if x["id"] not in self.seen[agent]]
        query = f"{m['name']} {m['retrieval_hint']} " + " ".join(x["text"] for x in new)
        retrieved = agents.retrieve(self.indexes, m, query)
        self.retrieved[agent] |= {c["chunk_id"] for c in retrieved}
        self.log.append(
            "retrieval",
            agent=agent,
            t=self.t,
            query=query[:2000],
            results=[
                {"chunk_id": c["chunk_id"], "score": c["score"]} for c in retrieved
            ],
        )

        system = agents.SYSTEM.format(
            name=m["name"],
            uae_instance=m["uae_instance"],
            institutions=", ".join(self.mandates),
        )
        user = agents.USER.format(
            stage=stage,
            inbox=agents.render_inbox(self.inbox[agent], self.seen[agent]),
            mandate=agents.render_mandate(m),
            feedback=agents.render_feedback(self.rejected_last[agent]),
            knowledge=agents.render_knowledge(retrieved, self.manifest),
        )
        self.seen[agent] |= {x["id"] for x in new}
        self.steps[agent] += 1
        tag = f"{self.s['id']}:{agent}:{self.steps[agent]}"
        resp = self.provider.complete(system, user, tag)
        self.log.append(
            "model_call",
            tag=tag,
            agent=agent,
            t=self.t,
            request_sha256=sha256({"system": system, "user": user}),
            **resp,
        )

        obj, err = parse_json(resp["text"])
        if err:
            self.log.append("parse_error", agent=agent, tag=tag, error=err)
            self.rejected_last[agent] = []
            return
        self.rejected_last[agent] = []
        ctx = {
            "agent": agent,
            "mandate": m,
            "institutions": list(self.mandates),
            "retrieved": self.retrieved[agent],
            "visible": {x["id"] for x in self.inbox[agent]},
            "chunks": self.chunks,
            "manifest": self.manifest,
            "rules": list(self.rules.values()),
        }
        for claim in (
            obj.get("claims", []) if isinstance(obj.get("claims"), list) else []
        ):
            if not isinstance(claim, dict):
                continue
            reasons = gate.check(claim, ctx)
            ev = self.log.append(
                "claim",
                agent=agent,
                tag=tag,
                t=self.t,
                claim=claim,
                accepted=not reasons,
                reasons=reasons,
            )
            if reasons:
                self.rejected_last[agent].append({"claim": claim, "reasons": reasons})
                continue
            record = {"agent": agent, "t": self.t, "seq": ev["seq"], "claim": claim}
            self.accepted.append(record)
            self.effect(record)

    def effect(self, rec: dict):
        """Carry out an accepted claim: route shares, deliver notifications, apply twin verbs."""
        agent, c = rec["agent"], rec["claim"]
        if c["type"] == "share":
            for to in c["to"]:
                for ref in c["inject_refs"]:
                    if any(x["id"] == ref for x in self.inbox[to]):
                        continue
                    orig = next(x for x in self.inbox[agent] if x["id"] == ref)
                    self.deliver(
                        to, ref, f"{agent} (shared)", orig["label"], orig["text"]
                    )
            self.log.append(
                "message_routed",
                from_=agent,
                to=c["to"],
                refs=c["inject_refs"],
                claim_seq=rec["seq"],
            )
            return
        if c["type"] != "action":
            return
        verb, params = c["verb"], c.get("params", {})
        if verb in coordinator.HIGH_IMPACT:
            self.log.append(
                "hitl_decision",
                agent=agent,
                verb=verb,
                params=params,
                decision="approved",
                policy=coordinator.HITL_POLICY,
                claim_seq=rec["seq"],
            )
        if verb in Twin.VERBS:
            change = self.twin.act(verb, params)
            conflict = coordinator.objective_conflict(change, self.s["invariants"])
            self.log.append(
                "state_change",
                agent=agent,
                t=self.t,
                verb=verb,
                params=params,
                change=change,
                invariants_after=check(change["after"], self.s["invariants"]),
                conflict=conflict,
                claim_seq=rec["seq"],
            )
            result = (
                "failed: " + change["error"]
                if change["error"]
                else "done. Twin metrics now: "
                + json.dumps(
                    {
                        k: v
                        for k, v in change["after"].items()
                        if change["before"][k] != v
                    }
                    or "no change"
                )
            )
            self.deliver(
                agent,
                self.new_message_id("FB"),
                "network telemetry",
                "feedback",
                f"{verb} {json.dumps(params)} {result}",
            )
        elif verb == "notify" and params.get("to") in self.mandates:
            mid = self.new_message_id("MSG")
            self.deliver(
                params["to"],
                mid,
                agent,
                "notification",
                str(params.get("content", ""))[:1500],
            )
            self.log.append(
                "message_routed",
                from_=agent,
                to=[params["to"]],
                refs=[mid],
                claim_seq=rec["seq"],
            )
        else:
            self.log.append(
                "communication",
                agent=agent,
                verb=verb,
                params=params,
                claim_seq=rec["seq"],
            )

    def stage_loop(self, stage: str):
        for _ in range(MAX_ROUNDS_PER_STAGE):
            due = [
                a
                for a in self.mandates
                if any(x["id"] not in self.seen[a] for x in self.inbox[a])
            ]
            if not due:
                return
            for a in due:
                self.step(a, stage)

    def finish(self):
        self.t += 1
        end = self.s["debrief"]
        for a in self.mandates:
            self.deliver(a, f"{self.s['id']}-END", "exercise control", "debrief", end)
        self.stage_loop("debrief")
        actions = [r for r in self.accepted if r["claim"]["type"] == "action"]
        obligations = [r for r in self.accepted if r["claim"]["type"] == "obligation"]
        for g in coordinator.duty_gaps(self.s, actions, obligations, self.chunks):
            self.log.append("gap_detected", **g)
        for c in coordinator.clock_checks(self.s, self.rules, actions, self.inject_t):
            self.log.append("clock_check", **{k: v for k, v in c.items() if k != "gap"})
            if c["gap"]:
                self.log.append("gap_detected", **c["gap"])
        for r in self.accepted:
            if r["claim"]["type"] == "gap":
                self.log.append(
                    "gap_detected",
                    origin=f"agent:{r['agent']}",
                    gap_type=r["claim"].get("gap_type"),
                    description=r["claim"].get("statement"),
                    claim_seq=r["seq"],
                )
        m = self.twin.metrics()
        self.log.append(
            "run_end",
            metrics=m,
            check=check(m, self.s["invariants"]),
            accepted=len(self.accepted),
            steps=self.steps,
        )

    def run(self):
        self.start()
        for t in sorted({i["t"] for i in self.s["injects"]}):
            self.t = t
            batch = [i for i in self.s["injects"] if i["t"] == t]
            for inj in batch:
                self.release(inj)
            self.invariants(f"after release t={t}")
            self.stage_loop(batch[0]["label"])
            self.invariants(f"after agents t={t}")
        self.finish()
        return self.log.path


BASELINE_SYSTEM = """You are a single incident-response adviser with full visibility of every event in a telecom incident.
The operator is a fictional mobile operator called OpCo. Institutions: {institutions}.
For each institution, say what it should do, which duties apply, and which policy gaps the incident exposes.

Return exactly one JSON object: {{"claims": [<claim>, ...]}}. Every claim has a field "agent" (the institution id it belongs to)
and otherwise follows this shape:
- action: verb (from that institution's verbs), params, inject_refs, rationale, evidence
- obligation: statement, inject_refs, rationale, evidence, deadline_hours (number or null)
- gap: gap_type (no_rule | no_deadline | no_owner | overlap | conflict), statement, inject_refs, rationale, evidence, global_examples
- insufficient_evidence: statement, inject_refs, evidence
evidence and global_examples items are {{"chunk_id": ..., "quote": ...}} from the KNOWLEDGE excerpts.
"""


def baseline(scenario: dict, provider, log_path: Path) -> Path:
    """Ungated comparison: one call, every inject visible, whole-KB retrieval. Its claims are then
    scored by the same gate under each institution's real mandate and information boundary."""
    log = AuditLog(log_path)
    mandates = {i: m for i, m in load_mandates().items() if i in scenario["institutions"]}
    manifest, ch = load_manifest(), chunks()
    injects = scenario["injects"]
    query = " ".join(i["text"] for i in injects)
    retrieved = Index(None).search(query, 20)
    log.append("run_start", scenario=scenario["id"], mode="baseline", provider=provider.name,
               model=getattr(provider, "model", None), git_head=git_head(),
               hashes={"kb_chunks": file_sha(KB / "chunks.jsonl"), "scenario": file_sha(DATA / "scenarios" / f"{scenario['id']}.json")})
    log.append("retrieval", agent="baseline", query=query[:2000], results=[{"chunk_id": c["chunk_id"], "score": c["score"]} for c in retrieved])
    system = BASELINE_SYSTEM.format(institutions=", ".join(mandates))
    verbs = "\n".join(f"{i}: {', '.join(m['verbs'])}" for i, m in mandates.items())
    events = "\n".join(f"[{i['id']}] ({i['label']}, seen by {', '.join(i['to'])}): {i['text']}" for i in injects)
    user = f"EVENTS\n{events}\n\nVERBS PER INSTITUTION\n{verbs}\n\nKNOWLEDGE\n{agents.render_knowledge(retrieved, manifest)}\n"
    tag = f"{scenario['id']}:baseline:1"
    resp = provider.complete(system, user, tag)
    log.append("model_call", tag=tag, agent="baseline", request_sha256=sha256({"system": system, "user": user}), **resp)
    obj, err = parse_json(resp["text"])
    if err:
        log.append("parse_error", agent="baseline", tag=tag, error=err)
        return log.path
    ids = {c["chunk_id"] for c in retrieved}
    for claim in obj.get("claims", []):
        if not isinstance(claim, dict):
            continue
        agent = claim.get("agent")
        if agent not in mandates:
            reasons = [f"SCHEMA:agent={agent}"]
        else:
            ctx = {"agent": agent, "mandate": mandates[agent], "institutions": list(mandates), "retrieved": ids,
                   "visible": {i["id"] for i in injects if agent in i["to"]}, "chunks": ch, "manifest": manifest,
                   "rules": list(load_rules().values())}
            reasons = gate.check(claim, ctx)
        log.append("baseline_claim", agent=agent, claim=claim, accepted=not reasons, reasons=reasons)
    log.append("run_end", metrics={}, check={"holds": None}, accepted=None, steps={})
    return log.path
