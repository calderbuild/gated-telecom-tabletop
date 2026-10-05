# Knowledge base

Official sources only. Each source is pinned by SHA-256 of the file as downloaded, with its URL and fetch date.

## Layout
- `manifest.d/*.json`: source records, one file per curation batch. `python -m tabletop kb build` merges them into `manifest.json`.
- `raw/` (not committed): the downloaded originals. `python -m tabletop kb fetch` re-downloads them; `kb verify` re-hashes.
- `text/<id>.txt`: the extracted English text layer the gate checks quotes against. Committed, so the gate works from a clean clone.
- `chunks.jsonl`: clause-level chunks built from `text/`.

## Source record
```json
{
  "id": "UAE-LIC-2-2026",
  "title": "Public Telecommunications Licence No. 2/2026 (e&)",
  "issuer": "TDRA",
  "date": "2026-08-06",
  "url": "https://...",
  "fetch_url": "https://r.jina.ai/https://...",
  "raw": "UAE-LIC-2-2026.pdf",
  "sha256": "<hex of raw file>",
  "fetched": "2026-10-05",
  "layer": "uae-telecom",
  "status": "VERIFIED",
  "binding": true,
  "notes": "Bilingual EN/AR; text layer keeps English only."
}
```
- `layer`: `uae-telecom` | `uae-data` | `uae-cyber` | `uae-ai` | `uae-continuity` | `global-standard` | `global-law` | `global-precedent` | `global-guidance`
- `status`: `VERIFIED` (primary text read and pinned) | `SECONDARY` (press or law-firm summary only) | `HISTORICAL` (superseded) | `UNVERIFIED` (summary page only; primary text not obtained). The gate accepts only `VERIFIED` sources as evidence for obligations and global examples.
- `fetch_url` is set only when the text came through a reader proxy (Jina) because the official host blocks scripts; `url` is always the official address.

## Text layer
Plain UTF-8. Keep article and clause headings on their own lines (`Article 9`, `12.9.2`, `§ 4.9`, `Annex III`) so the chunker can split on them. Arabic columns in bilingual PDFs are dropped. No paraphrase, no edits beyond whitespace and removing page headers/footers.
