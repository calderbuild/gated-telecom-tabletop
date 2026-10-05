"""Institution agents: prompt construction, mandate-scoped retrieval, and the mock fixture.

The model sees only its own inbox, its mandate and the KB excerpts retrieved for it.
It returns one JSON object of claims; the gate decides which of them count.
"""

import json

SYSTEM = """You are {name} in a telecom incident tabletop exercise. UAE instance of this role: {uae_instance}.
The operator in this exercise is a fictional mobile operator called OpCo. Injects are synthetic.
You know only what is in your INBOX. Other institutions hold information you do not have.

Return exactly one JSON object:
{{"situation": "<two sentences: what you know and what you do not>",
  "claims": [<claim>, ...]}}

Claim types (field "type"):
- "action": you take one of YOUR MANDATE verbs. Fields: verb, params (object, as listed), inject_refs, rationale, evidence.
- "obligation": a duty that applies to you now. Fields: statement, inject_refs, rationale, evidence, deadline_hours (number, ONLY if the quoted text itself states an hour or day figure for that duty; otherwise null).
- "gap": a policy, strategy or standards gap this incident exposes. Fields: gap_type (no_rule | no_deadline | no_owner | overlap | conflict), statement, inject_refs, rationale, evidence (UAE text that shows the gap, or the closest UAE text), global_examples (quotes from global sources showing how others handle it).
- "share": pass an item from your inbox to other institutions. Fields: to (list of institution ids), inject_refs, statement.
- "insufficient_evidence": the excerpts do not answer a question you were asked. Fields: statement (what is missing), inject_refs, evidence (closest excerpt, may be empty).

Each rationale is an object {{"observation": ..., "rule": ..., "inference": ...}}.
Each evidence or global_examples item is {{"chunk_id": "<id from KNOWLEDGE>", "quote": "<exact characters copied from that excerpt, 20-300 characters>"}}.

Rules. A deterministic gate checks every claim; rejected claims are logged and do not count.
- Quote only from the KNOWLEDGE excerpts shown in this message or earlier turns, copied character for character. Never quote from memory.
- Use only verbs in YOUR MANDATE. If something needs a verb you do not have, ask the institution that has it (share or notify) instead.
- inject_refs may only contain ids from your INBOX.
- Do not invent numbers, deadlines or laws. If the excerpts do not answer it, say insufficient_evidence or record a gap.
- Institution ids: {institutions}.
"""

USER = """STAGE {stage}

INBOX (newest last; * = new since your last turn)
{inbox}

YOUR MANDATE (verbs you may use)
{mandate}

{feedback}KNOWLEDGE (retrieved for you; cite by chunk_id)
{knowledge}
"""


def render_inbox(items: list[dict], seen: set[str]) -> str:
    return "\n".join(
        f"{'*' if m['id'] not in seen else ' '} [{m['id']}] from {m['from']} ({m['label']}): {m['text']}"
        for m in items
    )


def render_mandate(mandate: dict) -> str:
    lines = []
    for verb, spec in mandate["verbs"].items():
        params = json.dumps(spec.get("params", {}), ensure_ascii=False)
        lines.append(f"- {verb} {params}: {spec['description']}")
    return "\n".join(lines)


def render_feedback(rejected: list[dict]) -> str:
    if not rejected:
        return ""
    lines = [
        f"- {r['claim'].get('type')} {r['claim'].get('verb') or (r['claim'].get('statement') or '')[:60]!r}: {', '.join(r['reasons'])}"
        for r in rejected
    ]
    return (
        "GATE FEEDBACK (your claims rejected last turn)\n" + "\n".join(lines) + "\n\n"
    )


def render_knowledge(chunks: list[dict], manifest: dict) -> str:
    out = []
    for c in chunks:
        s = manifest[c["doc_id"]]
        out.append(
            f"[{c['chunk_id']}] {s['title']} | {c['ref']} | {s['layer']} | {s['status']}\n{c['text']}"
        )
    return "\n\n".join(out)


def retrieve(
    indexes: dict, mandate: dict, query: str, k_local: int = 6, k_global: int = 6
) -> list[dict]:
    """Mandate-scoped retrieval: the institution's own UAE layers plus the shared global layers."""
    local = indexes[tuple(mandate["layers"])].search(query, k_local)
    glob = indexes["global"].search(query, k_global)
    seen, out = set(), []
    for c in local + glob:
        if c["chunk_id"] not in seen:
            seen.add(c["chunk_id"])
            out.append(c)
    return out


# ---------- mock fixture (tests and selftest only; never used for reported numbers) ----------


def mock_responder(scenario: dict, mandates: dict):
    """Build a deterministic responder. Per call it emits:
    - one obligation quoting the first retrieved chunk,
    - the scenario's mock_actions due for this agent,
    - on each agent's first call, three claims the gate must reject
      (fabricated quote, verb outside the mandate, an inject the agent never received).
    """
    first_call = set()

    def respond(tag: str, user: str) -> str:
        agent = tag.split(":")[1]
        inbox_ids = [
            line.split("]")[0].split("[")[1]
            for line in _section(user, "INBOX").splitlines()
            if "[" in line
        ]
        chunk_ids = [
            line[1 : line.index("]")]
            for line in _section(user, "KNOWLEDGE").splitlines()
            if line.startswith("[")
        ]
        texts = _chunk_texts(user)
        claims = []
        if chunk_ids and inbox_ids:
            q = " ".join(texts[chunk_ids[0]].split())[:120]
            claims.append(
                {
                    "type": "obligation",
                    "statement": "mock obligation",
                    "inject_refs": inbox_ids[-1:],
                    "rationale": {
                        "observation": "mock",
                        "rule": "mock",
                        "inference": "mock",
                    },
                    "evidence": [{"chunk_id": chunk_ids[0], "quote": q}],
                    "deadline_hours": None,
                }
            )
        for a in scenario.get("mock_actions", []):
            if (
                a["agent"] == agent
                and a["after"] in inbox_ids
                and (agent, a["verb"], a["after"]) not in first_call
            ):
                first_call.add((agent, a["verb"], a["after"]))
                ev = (
                    [
                        {
                            "chunk_id": chunk_ids[0],
                            "quote": " ".join(texts[chunk_ids[0]].split())[:120],
                        }
                    ]
                    if chunk_ids
                    else []
                )
                claims.append(
                    {
                        "type": "action",
                        "verb": a["verb"],
                        "params": a.get("params", {}),
                        "inject_refs": [a["after"]],
                        "rationale": {
                            "observation": "mock",
                            "rule": "mock",
                            "inference": "mock",
                        },
                        "evidence": ev,
                    }
                )
        if agent not in first_call and chunk_ids and inbox_ids:
            first_call.add(agent)
            outside = next(
                v
                for m in mandates.values()
                for v in m["verbs"]
                if v not in mandates[agent]["verbs"]
            )
            ev = [
                {
                    "chunk_id": chunk_ids[0],
                    "quote": " ".join(texts[chunk_ids[0]].split())[:120],
                }
            ]
            claims += [
                {
                    "type": "obligation",
                    "statement": "fabricated",
                    "inject_refs": inbox_ids[-1:],
                    "rationale": {},
                    "evidence": [
                        {
                            "chunk_id": chunk_ids[0],
                            "quote": "the licensee shall notify within 2 hours of any outage",
                        }
                    ],
                },
                {
                    "type": "action",
                    "verb": outside,
                    "params": {},
                    "inject_refs": inbox_ids[-1:],
                    "rationale": {},
                    "evidence": ev,
                },
                {
                    "type": "obligation",
                    "statement": "unreleased",
                    "inject_refs": ["NOT-RELEASED"],
                    "rationale": {},
                    "evidence": ev,
                },
            ]
        return json.dumps({"situation": "mock", "claims": claims})

    return respond


def _section(user: str, name: str) -> str:
    start = user.index(name)
    rest = user[start:].split("\n", 1)[1]
    for nxt in ("\nYOUR MANDATE", "\nGATE FEEDBACK", "\nKNOWLEDGE", "\nSTAGE"):
        if nxt in rest and not nxt.strip().startswith(name):
            rest = rest.split(nxt, 1)[0]
    return rest


def _chunk_texts(user: str) -> dict:
    body = user.split("KNOWLEDGE (retrieved for you; cite by chunk_id)\n", 1)[1]
    out = {}
    for block in body.split("\n\n["):
        block = block if block.startswith("[") else "[" + block
        cid = block[1 : block.index("]")]
        out[cid] = block.split("\n", 1)[1] if "\n" in block else ""
    return out
