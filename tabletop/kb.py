"""Knowledge base: manifest merge, clause chunking, hash verification, BM25 retrieval.

The text layer (kb/text/<id>.txt) is what the gate checks quotes against. Raw files
(kb/raw/) are not committed; `fetch` re-downloads them and `verify` re-hashes them
against the pinned SHA-256.
"""

import hashlib
import json
import math
import re
import unicodedata
import urllib.request
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"

HEADING = re.compile(
    r"^(?:#{1,4}\s+\S"
    r"|(?:Article|Art\.|ARTICLE)\s*\(?\d+"
    r"|(?:Chapter|CHAPTER|Section|SECTION|Part|PART|Annex|ANNEX|Appendix|Recommendation|Clause)\s+[\dIVXLA-Z]"
    r"|§\s*\d"
    r"|\d{1,2}(?:\.\d{1,2}){1,4}\.?\s+\S"
    r"|\d{1,3}\.\s+[A-Z][a-z]"
    r")"
)
MIN_CHUNK = 160
MAX_CHUNK = 2400
TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)*")
STOP = set(
    "the of and to a in or any be by for is that as with on shall this an are which its from at it such not may other".split()
)


def norm(text: str) -> str:
    """Normalisation used for verbatim matching: NFKC, unify quotes/dashes, collapse whitespace, casefold."""
    t = unicodedata.normalize("NFKC", text or "")
    t = t.translate(
        str.maketrans(
            {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "­": ""}
        )
    )
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"(\w)- (\w)", r"\1\2", t)  # words hyphenated across a line break
    return t.casefold()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------- manifest ----------


def merge_manifest() -> list[dict]:
    sources = []
    for part in sorted((KB / "manifest.d").glob("*.json")):
        sources += json.loads(part.read_text())["sources"]
    ids = [s["id"] for s in sources]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate source ids: {sorted(dupes)}")
    return sorted(sources, key=lambda s: s["id"])


def load_manifest() -> dict[str, dict]:
    return {
        s["id"]: s for s in json.loads((KB / "manifest.json").read_text())["sources"]
    }


# ---------- chunking ----------


def split_clauses(text: str) -> list[tuple[str, int, int]]:
    """Split a text layer into (ref, start, end) spans at heading lines."""
    starts = [0]
    pos = 0
    for line in text.splitlines(keepends=True):
        if pos and HEADING.match(line.strip()):
            starts.append(pos)
        pos += len(line)
    spans = [
        (a, b) for a, b in zip(starts, starts[1:] + [len(text)]) if text[a:b].strip()
    ]

    merged = []  # fold heading-only or tiny spans into the following span
    carry = None
    for a, b in spans:
        a = carry if carry is not None else a
        if b - a < MIN_CHUNK and (a, b) != spans[-1]:
            carry = a
            continue
        carry = None
        merged.append((a, b))

    out = []
    for a, b in merged:
        ref = text[a:b].strip().splitlines()[0].strip().lstrip("#").strip()[:90]
        for i, (x, y) in enumerate(_windows(text, a, b)):
            out.append((ref if i == 0 else f"{ref} (cont. {i + 1})", x, y))
    return out


def _windows(text: str, a: int, b: int):
    """Cut an oversized span at paragraph (or line) boundaries."""
    while b - a > MAX_CHUNK:
        cut = text.rfind("\n\n", a + MAX_CHUNK // 2, a + MAX_CHUNK)
        if cut == -1:
            cut = text.rfind("\n", a + MAX_CHUNK // 2, a + MAX_CHUNK)
        if cut == -1:
            cut = a + MAX_CHUNK
        yield a, cut
        a = cut
    yield a, b


def build() -> tuple[int, int]:
    sources = merge_manifest()
    (KB / "manifest.json").write_text(
        json.dumps({"sources": sources}, indent=2, ensure_ascii=False) + "\n"
    )
    n = 0
    with (KB / "chunks.jsonl").open("w") as f:
        for s in sources:
            text = (KB / "text" / f"{s['id']}.txt").read_text()
            for i, (ref, a, b) in enumerate(split_clauses(text)):
                rec = {
                    "chunk_id": f"{s['id']}#{i:04d}",
                    "doc_id": s["id"],
                    "ref": ref,
                    "start": a,
                    "end": b,
                    "text": text[a:b].strip(),
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    chunks.cache_clear()
    return len(sources), n


@lru_cache(maxsize=1)
def chunks() -> dict[str, dict]:
    path = KB / "chunks.jsonl"
    # split on "\n" only: str.splitlines would also break on U+2028 inside JSON strings
    rows = [json.loads(line) for line in path.read_text().split("\n") if line]
    return {c["chunk_id"]: c for c in rows}


# ---------- hashes ----------


def verify() -> list[str]:
    """Return problems; empty list means every source has text and every raw file present matches its pin."""
    problems = []
    for s in merge_manifest():
        if not (KB / "text" / f"{s['id']}.txt").exists():
            problems.append(f"{s['id']}: missing text layer")
        raw = KB / "raw" / s["raw"]
        if not raw.exists():
            problems.append(f"{s['id']}: raw file not present (run `kb fetch`)")
        elif sha256_file(raw) != s["sha256"]:
            problems.append(
                f"{s['id']}: sha256 mismatch (source changed upstream or file corrupted)"
            )
    return problems


def fetch(only_missing: bool = True) -> list[str]:
    report = []
    (KB / "raw").mkdir(exist_ok=True)
    for s in merge_manifest():
        dest = KB / "raw" / s["raw"]
        if only_missing and dest.exists():
            continue
        url = s.get("fetch_url") or s["url"]
        part = dest.with_name(dest.name + ".part")
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (tabletop kb fetch)"}
            )
            part.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        except Exception as e:  # report and continue: one blocked host must not stop the rest
            report.append(f"{s['id']}: FAILED fetch: {e}")
            continue
        if sha256_file(part) == s["sha256"]:
            part.replace(dest)
            report.append(f"{s['id']}: ok")
        else:  # never let a block page or a changed upstream replace the pinned file
            report.append(
                f"{s['id']}: FAILED hash differs, kept as {part.name} (upstream changed or a block page; reader-proxy output is not byte-stable)"
            )
    return report


# ---------- retrieval ----------


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


class Index:
    """Plain BM25 over the chunks, optionally restricted to some source layers."""

    def __init__(
        self, layers: set[str] | None = None, k1: float = 1.5, b: float = 0.75
    ):
        manifest = load_manifest()
        self.docs = [
            c
            for c in chunks().values()
            if manifest[c["doc_id"]]["status"] != "HISTORICAL"
            and (layers is None or manifest[c["doc_id"]]["layer"] in layers)
        ]
        self.tf = [Counter(tokens(c["ref"] + " " + c["text"])) for c in self.docs]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = sum(self.len) / max(len(self.len), 1)
        df = Counter(t for tf in self.tf for t in tf)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.k1, self.b = k1, b

    def search(self, query: str, k: int = 8) -> list[dict]:
        q = set(tokens(query))
        scored = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for t in q & tf.keys():
                f = tf[t]
                s += (
                    self.idf[t]
                    * f
                    * (self.k1 + 1)
                    / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
                )
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return [dict(self.docs[i], score=round(s, 3)) for s, i in scored[:k]]


# ---------- export for the ITU reference toolkit ----------

def export_toolkit(out: Path) -> int:
    """Write the KB as InputDocs/<category>/<id>.md plus Inputs.md, the layout the ITU reference
    toolkit (CrashingGuru/ITUAIReadiness, simulation/server/knowledge/ingest.py) ingests into ChromaDB.
    Each file starts with its provenance so the status survives the toolkit's own re-chunking."""
    rows = []
    for s in load_manifest().values():
        cat = "UAE_Telecom_Policy" if s["layer"].startswith("uae") else "Global_Telecom_Policy"
        dest = out / "InputDocs" / cat / f"{s['id']}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        head = "\n".join(
            f"{k}: {s[k]}" for k in ("title", "issuer", "date", "url", "sha256", "status", "layer") if k in s
        )
        dest.write_text(f"# {s['title']}\n\n{head}\n\n---\n\n{(KB / 'text' / f'{s['id']}.txt').read_text()}")
        rows.append(f"| `{cat}/{dest.name}` | {s['status']} | {s['issuer']} | {s['title']} |")
    (out / "InputDocs" / "Inputs.md").write_text(
        "# Input Documents Manifest\n\nGenerated by `python -m tabletop kb export`. Only VERIFIED sources can back an accepted claim in the tabletop gate.\n\n"
        "| File | Status | Issuer | Title |\n|---|---|---|---|\n" + "\n".join(sorted(rows)) + "\n"
    )
    return len(rows)
