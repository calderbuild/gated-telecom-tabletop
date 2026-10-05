# Context

Updated 2026-10-05. Decisions were made by Calder through grilling on 2026-10-05; the evidence is in ../research/.

## What the judges score (official UAE page, ../research/web/uae.md:673-690)
1. Knowledge base quality: completeness, accuracy, structure, policy retrieval.
2. Agent capability: relevance and accuracy in simulated error scenarios, adherence to laws, mandates and coordination mechanisms; plus policy, strategy and standards gap identification, where the accuracy of global policy examples is critical.
3. Auditability: logs, chain-of-thought tracing, source attribution.
4. Alignment with ITU standards: the Y.3172 pipeline and the AI Readiness Framework.

FAQ facts:
- Prototype accuracy is NOT an evaluation criterion (uae.md:790).
- Evaluation scenarios should reflect both technical and policy roles and expose policy gaps.
- The report must cover: an introduction to the agentic solution, the use case, its requirements, and the Y.3172 mapping.
- The demo video must show the setup, the main functions, the expected outcome per scenario, and the real outcome.

## Decisions
| # | Decision | Why |
|---|---|---|
| D1 | Domain: telecommunications | ITU's home domain; the UAE kick-off is co-run with TDRA; it fits Calder's Communication Engineering major |
| D2 | New project | No existing project fits |
| D3 | Models: hosted Claude | Winners used hosted frontier models |
| D4 | Architecture C+: gated multi-institution tabletop plus an emulated network for closed loop | Covers all four agent roles in the brief; keeps the winners' gate pattern; past telecom build-a-thon podiums acted on emulated networks |
| D5 | Generic institution roles, with mandates sourced from UAE documents; gaps mapped to global examples | The page asks for domain-level gaps and global examples, not country-specific recommendations |
| D6 | KB base: the organizer's UAE dataset (CrashingGuru/Sandbox_Training Dataset/UAE/PolicyData) plus about 29 verified core sources, each verified at clause level and SHA-256 pinned | Visible KB-quality edge, since some organizer files are stubs |
| D7 | Scenarios: three (final set is in ../research/scenario-validation.md); S5 (traffic management vs open internet) dropped as sensitive | Reliable, valuable, closed loop where possible |
| D8 | Evaluation, light version: answer key frozen before the first run; automatic metrics (citation validity, mandate violations, information-boundary violations, gap recall), 3 runs per scenario, compared with an ungated baseline; small or no human labelling | Accuracy is not graded; gap identification and auditability are |
| D9 | Demo: FastAPI plus a static page; staged injects, agent messages, the audit chain and the gap matrix; replay mode by default; CLI produces every number | Robust for the Dubai final |
| D10 | Ask the expected KB format at the first Saturday mentoring session | Format is not specified on the page |

## Architecture (C+)
- **Institution agents**, each with its own mandate (an allow-list of actions and claim types, sourced from documents) and its own private inbox: operator NOC, telecom regulator, data-protection authority, cybersecurity authority, emergency services.
- **Inject engine**: releases scenario events in stages; each agent sees only its own injects, so information is incomplete and uneven.
- **Gates** (the Y.3172 Policy node):
  - every claim must quote a KB span verbatim;
  - the claimed action must be in the agent's mandate;
  - the facts the agent cites must come from injects it actually received.
  Rejected claims are logged, not dropped.
- **Emulated network**: a small topology with emergency-call routing and service state. Approved actions change it, and verification checks the outcome (e.g. emergency routing restored after rollback). The emulation level is set in scenario-validation.md.
- **Coordinator**: builds a matrix of who owns which obligation from the gated claims, then flags gaps (no owner), overlaps (two owners) and conflicts. Each gap is mapped to a global precedent with a citation.
- **Audit log**: hash-chained, per-event entries (inject, prompt hash, structured rationale, gate results, state diffs).

## Glossary
- **Inject**: a staged scenario event delivered to one or more agents.
- **Mandate**: the set of actions and claim types an institution may make, sourced from KB documents.
- **Gate**: a deterministic check a claim must pass to count.
- **Gap**: an obligation in a scenario with no owner, two conflicting owners, or no rule at all, relative to global frameworks.

## Key dates
10-10..11-07: Saturday mentoring. 10-21: kick-off and registration close. 11-10: submission. 11-18: shortlist (demo video if shortlisted). 12-08: Dubai final.
