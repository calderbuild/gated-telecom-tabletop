"""The Y.3172 policy (P) node: deterministic checks every agent claim must pass to count.

A claim that fails is rejected and logged with its reasons; it is never repaired.

Checks (reason codes):
  SCHEMA        claim shape is wrong (unknown type, missing field)
  NO_EVIDENCE   an action/obligation/gap carries no evidence
  NOT_RETRIEVED evidence cites a chunk this agent was never shown
  NOT_VERBATIM  quote is not a verbatim span of the cited chunk (after whitespace/quote normalisation)
  SHORT_QUOTE   quote under 20 characters, too short to prove anything
  NOT_VERIFIED  obligation or global example rests on a source whose status is not VERIFIED
  NOT_GLOBAL    a gap's global example does not come from a global-* source
  MANDATE       action verb is not in this institution's mandate
  INJECT        claim cites an inject or message this agent has not received
  DEADLINE      deadline_hours does not match the rule table for the cited source
  ROUTE         share target is unknown or is the agent itself
"""

from tabletop.kb import norm

CLAIM_TYPES = {"action", "obligation", "gap", "share", "insufficient_evidence"}
GAP_TYPES = {"no_rule", "no_deadline", "no_owner", "overlap", "conflict"}
MIN_QUOTE = 20


def quote_ok(quote: str, text: str) -> bool:
    q = norm(quote)
    return len(q) >= MIN_QUOTE and q in norm(text)


def _evidence(items, ctx, need_verified, need_global=False):
    reasons = []
    for ev in items:
        cid, quote = ev.get("chunk_id"), ev.get("quote", "")
        chunk = ctx["chunks"].get(cid)
        if chunk is None or cid not in ctx["retrieved"]:
            reasons.append(f"NOT_RETRIEVED:{cid}")
            continue
        if len(norm(quote)) < MIN_QUOTE:
            reasons.append(f"SHORT_QUOTE:{cid}")
        elif norm(quote) not in norm(chunk["text"]):
            reasons.append(f"NOT_VERBATIM:{cid}")
        src = ctx["manifest"][chunk["doc_id"]]
        if need_verified and src["status"] != "VERIFIED":
            reasons.append(f"NOT_VERIFIED:{chunk['doc_id']}={src['status']}")
        if need_global and not src["layer"].startswith("global"):
            reasons.append(f"NOT_GLOBAL:{chunk['doc_id']}")
    return reasons


def check(claim: dict, ctx: dict) -> list[str]:
    """Return the list of failure reasons; empty means accepted.

    ctx: agent (id), mandate (that agent's mandate record), institutions (all ids),
    retrieved (chunk ids shown to this agent so far), visible (inject/message ids it has
    received), chunks, manifest, rules.
    """
    t = claim.get("type")
    if t not in CLAIM_TYPES:
        return [f"SCHEMA:type={t}"]
    reasons = []
    refs = claim.get("inject_refs") or []
    unseen = [r for r in refs if r not in ctx["visible"]]
    reasons += [f"INJECT:{r}" for r in unseen]

    if t in ("action", "obligation", "share", "insufficient_evidence") and not refs:
        reasons.append("SCHEMA:inject_refs empty")

    if t == "share":
        to = claim.get("to") or []
        bad = [x for x in to if x not in ctx["institutions"] or x == ctx["agent"]]
        if not to or bad:
            reasons.append(f"ROUTE:{bad or 'empty'}")
        return reasons

    if t == "insufficient_evidence":
        return reasons + _evidence(
            claim.get("evidence") or [], ctx, need_verified=False
        )

    evidence = claim.get("evidence") or []
    if not evidence:
        reasons.append("NO_EVIDENCE")

    if t == "action":
        verb = claim.get("verb")
        if verb not in ctx["mandate"]["verbs"]:
            reasons.append(f"MANDATE:{verb}")
        if not isinstance(claim.get("params", {}), dict):
            reasons.append("SCHEMA:params")
        reasons += _evidence(evidence, ctx, need_verified=False)

    elif t == "obligation":
        reasons += _evidence(evidence, ctx, need_verified=True)
        hours = claim.get("deadline_hours")
        if hours is not None:
            docs = {
                ctx["chunks"][e["chunk_id"]]["doc_id"]
                for e in evidence
                if e.get("chunk_id") in ctx["chunks"]
            }
            if not any(
                r["doc_id"] in docs and r["hours"] == hours for r in ctx["rules"]
            ):
                reasons.append(
                    f"DEADLINE:{hours}h not in rule table for {sorted(docs)}"
                )

    elif t == "gap":
        if claim.get("gap_type") not in GAP_TYPES:
            reasons.append(f"SCHEMA:gap_type={claim.get('gap_type')}")
        reasons += _evidence(evidence, ctx, need_verified=False)
        examples = claim.get("global_examples") or []
        reasons += _evidence(examples, ctx, need_verified=True, need_global=True)
    return reasons
