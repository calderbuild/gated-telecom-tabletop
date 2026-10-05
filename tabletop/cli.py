"""Command line: the real interface. Every reported number comes from one of these commands."""

import argparse
import json
import sys
from pathlib import Path

from tabletop import audit, kb
from tabletop.agents import mock_responder
from tabletop.engine import (
    DATA,
    Run,
    baseline,
    load_json,
    load_mandates,
    load_rules,
    load_scenario,
)
from tabletop.gate import quote_ok
from tabletop.llm import DEFAULT_MODEL, DeepSeek, Mock, Replay, load_env

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ["S1", "S3", "S2"]


def provider_for(args, scenario):
    if args.provider == "mock":
        return Mock(mock_responder(scenario, load_mandates()))
    load_env(ROOT / ".env")
    return DeepSeek(args.model)


def cmd_kb(args):
    if args.action == "build":
        n, c = kb.build()
        print(f"built kb/manifest.json ({n} sources) and kb/chunks.jsonl ({c} chunks)")
    elif args.action == "verify":
        problems = kb.verify()
        print("\n".join(problems) or "all sources: text present, raw hashes match")
        return 1 if any("mismatch" in p or "missing text" in p for p in problems) else 0
    elif args.action == "fetch":
        print("\n".join(kb.fetch()) or "nothing to fetch")
    elif args.action == "search":
        for c in kb.Index().search(args.query, 8):
            print(f"{c['score']:7.2f} {c['chunk_id']:32} {c['ref'][:60]}")
    return 0


def cmd_check_data(args):
    """Every quote that backs a mandate verb or a rule must be verbatim in the KB text layer."""
    texts = {}
    bad = 0

    def ok(doc_id, quote):
        if doc_id not in texts:
            texts[doc_id] = (kb.KB / "text" / f"{doc_id}.txt").read_text()
        return quote_ok(quote, texts[doc_id])

    manifest = kb.load_manifest()
    for inst, m in load_mandates().items():
        for verb, spec in m["verbs"].items():
            for b in spec.get("basis", []):
                if b["doc_id"] not in manifest or not ok(b["doc_id"], b["quote"]):
                    print(
                        f"mandate {inst}.{verb}: basis quote not found in {b['doc_id']}"
                    )
                    bad += 1
    for rid, r in load_rules().items():
        if r["doc_id"] not in manifest or not ok(r["doc_id"], r["quote"]):
            print(f"rule {rid}: quote not found in {r['doc_id']}")
            bad += 1
    for sid in SCENARIOS:
        key = load_json(DATA / "keys" / f"{sid}.json")
        for g in key["gaps"]:
            missing = [d for d in g["global_docs"] if d not in manifest]
            if missing:
                print(f"key {sid}.{g['id']}: unknown docs {missing}")
                bad += 1
    print(f"{bad} problems")
    return 1 if bad else 0


def cmd_run(args):
    scenario = load_scenario(args.scenario)
    out = (
        Path(args.out)
        if args.out
        else ROOT / "runs" / "scratch" / f"{args.scenario}-{args.provider}.jsonl"
    )
    path = Run(scenario, provider_for(args, scenario), out).run()
    print(path, audit.verify(path)[1])
    return 0


def cmd_replay(args):
    """Re-execute a recorded run with its recorded model responses and compare every gate verdict."""
    src = Path(args.log)
    events = audit.load(src)
    sid = events[0]["data"]["scenario"]
    out = ROOT / "runs" / "scratch" / f"replay-{src.stem}.jsonl"
    Run(load_scenario(sid), Replay(events), out).run()
    pick = lambda evs: [
        (e["data"]["agent"], e["data"]["accepted"], e["data"]["reasons"])
        for e in evs
        if e["type"] == "claim"
    ]
    a, b = pick(events), pick(audit.load(out))
    same = a == b
    print(
        f"replayed {src.name}: {len(b)} claims, verdicts {'identical' if same else 'DIFFER'} to the recording"
    )
    return 0 if same else 1


def cmd_baseline(args):
    scenario = load_scenario(args.scenario)
    out = (
        Path(args.out)
        if args.out
        else ROOT / "runs" / "scratch" / f"{args.scenario}-baseline.jsonl"
    )
    path = baseline(scenario, provider_for(args, scenario), out)
    print(path, audit.verify(path)[1])
    return 0


def cmd_verify_log(args):
    ok, msg = audit.verify(Path(args.log))
    print(("OK " if ok else "BROKEN ") + msg)
    return 0 if ok else 1


def cmd_eval(args):
    from tabletop.evals import evaluate, markdown

    res = evaluate(SCENARIOS)
    (ROOT / "eval").mkdir(exist_ok=True)
    (ROOT / "eval" / "results.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False) + "\n"
    )
    md = markdown(res)
    (ROOT / "eval" / "results.md").write_text(md)
    readme = ROOT / "README.md"
    head, _, rest = readme.read_text().partition("<!-- eval:start -->\n")
    _, _, tail = rest.partition("<!-- eval:end -->")
    table = md.split("\n", 2)[2]  # drop the results.md title
    readme.write_text(f"{head}<!-- eval:start -->\n{table}<!-- eval:end -->{tail}")
    print(md)
    return 0


def cmd_selftest(args):
    """No network, no key: mock provider through every scenario; gate, twin and chain must behave."""
    failures = []
    for sid in SCENARIOS:
        scenario = load_scenario(sid)
        out = ROOT / "runs" / "scratch" / f"selftest-{sid}.jsonl"
        Run(
            scenario,
            Mock(mock_responder(scenario, load_mandates())),
            out,
        ).run()
        events = audit.load(out)
        ok, msg = audit.verify(out)
        reasons = {
            r.split(":")[0]
            for e in events
            if e["type"] == "claim"
            for r in e["data"]["reasons"]
        }
        end = next(e["data"] for e in events if e["type"] == "run_end")
        broke = any(
            e["type"] == "invariants" and not e["data"]["check"]["holds"]
            for e in events
        )
        checks = {
            "chain intact": ok,
            "fabricated quote rejected": "NOT_VERBATIM" in reasons,
            "out-of-mandate verb rejected": "MANDATE" in reasons,
            "unreleased inject rejected": "INJECT" in reasons,
            "fault broke an invariant": broke,
            "closed loop restored": end["check"]["holds"],
        }
        for name, passed in checks.items():
            print(f"{sid} {'PASS' if passed else 'FAIL'} {name}")
            if not passed:
                failures.append(f"{sid}: {name}")
    print("selftest " + ("passed" if not failures else f"FAILED: {failures}"))
    return 1 if failures else 0


def cmd_serve(args):
    import uvicorn

    uvicorn.run("tabletop.server:app", host=args.host, port=args.port)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m tabletop", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kb", help="build, verify, fetch or search the knowledge base")
    k.add_argument("action", choices=["build", "verify", "fetch", "search"])
    k.add_argument("query", nargs="?", default="")
    sub.add_parser(
        "check-data", help="verify every mandate/rule quote is verbatim in the KB"
    )
    for name in ("run", "baseline"):
        r = sub.add_parser(name, help=f"{name} one scenario")
        r.add_argument("scenario", choices=SCENARIOS)
        r.add_argument("--provider", choices=["deepseek", "mock"], default="deepseek")
        r.add_argument("--model", default=DEFAULT_MODEL)
        r.add_argument("--out")
    rp = sub.add_parser(
        "replay", help="re-execute a recorded run and compare gate verdicts"
    )
    rp.add_argument("log")
    v = sub.add_parser("verify-log", help="recompute an audit log's hash chain")
    v.add_argument("log")
    sub.add_parser("eval", help="compute metrics from runs/ into eval/")
    sub.add_parser("selftest", help="offline end-to-end check with the mock provider")
    s = sub.add_parser("serve", help="demo page (replays recorded runs)")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)
    handlers = {
        "kb": cmd_kb,
        "check-data": cmd_check_data,
        "run": cmd_run,
        "baseline": cmd_baseline,
        "replay": cmd_replay,
        "verify-log": cmd_verify_log,
        "eval": cmd_eval,
        "selftest": cmd_selftest,
        "serve": cmd_serve,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
