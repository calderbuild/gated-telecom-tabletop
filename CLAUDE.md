# Gated multi-institution telecom tabletop (ITU AI for Good Lab Hackathon UAE 2026)

Solo entry by Calder (Luo Lin, BISTU undergrad). Submission is due 2026-11-10 (internal cutoff 20:00 Beijing): a technical report of at most 5 pages, a public GitHub repo, and the knowledge base. Final is in Dubai on 2026-12-08. The goal is 1st prize.

Read before working:
- docs/CONTEXT.md: decisions, architecture, glossary. It is the source of truth for scope.
- ../requirements.md: verified official rules, timeline and checklist.
- ../research/*.md: winners study, rules and judges, KB sources, architecture options, scenario validation.

## Hard rules for this repo
- Deterministic code decides; the LLM only retrieves, proposes and explains. No claim counts unless it passes the gates (verbatim quote match, mandate allow-list, inject provenance).
- Never claim a raw chain of thought. Claude 5.x thinking is hidden or summarized, so traces are the agent's structured rationale plus the audit log. Say exactly that in the report.
- Every number in the report or the demo comes from a CLI run whose output is committed. No hand-typed metrics.
- The demo replays a recorded, hash-verified run by default; live mode is optional.
- Knowledge base: official sources only, each pinned by SHA-256 with a URL and section reference. Mark anything unverified as unverified. Never fabricate a clause.
- No API keys in the repo. Read keys from env, and keep .env out of git.
- Calendar overlaps with other events are not a risk item.
- Public GitHub repo creation, pushes to a remote, and anything sent to the organizers need Calder's OK first.
