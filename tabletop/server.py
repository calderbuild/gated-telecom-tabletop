"""Demo server. Read-only: it serves recorded runs, the KB chunks they cite, and eval results.
The page replays a run event by event; the chain is re-verified on every load."""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from tabletop import audit
from tabletop.engine import load_rules, load_scenario
from tabletop.kb import chunks, load_manifest

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
app = FastAPI(title="Telecom incident tabletop")


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/runs")
def runs():
    out = []
    for p in sorted(RUNS.glob("S*/*.jsonl")):
        out.append(
            {"scenario": p.parent.name, "name": p.stem, "chain_ok": audit.verify(p)[0]}
        )
    return out


@app.get("/api/runs/{scenario}/{name}")
def run(scenario: str, name: str):
    path = (RUNS / scenario / f"{name}.jsonl").resolve()
    if path.parent.parent != RUNS.resolve() or not path.exists():
        raise HTTPException(404, "no such run")
    ok, msg = audit.verify(path)
    return {
        "chain_ok": ok,
        "chain": msg,
        "scenario": load_scenario(scenario),
        "rules": load_rules(),
        "events": audit.load(path),
    }


@app.get("/api/chunk/{chunk_id:path}")
def chunk(chunk_id: str):
    c = chunks().get(chunk_id)
    if c is None:
        raise HTTPException(404, "no such chunk")
    return {**c, "source": load_manifest()[c["doc_id"]]}


@app.get("/api/eval")
def evaluation():
    path = ROOT / "eval" / "results.json"
    return json.loads(path.read_text()) if path.exists() else {}
