# AI for Good Sandbox Hackathon - CalderBuild - Gated Multi-Institution Telecom Tabletop

Team leader: Luo Lin (Calder), Beijing Information Science and Technology University
Team members: none (solo entry). Contact details: [fill in before submission]
Github link: [fill in after the public repo is created]

DRAFT for my own review. Every number in this report comes from `python -m tabletop eval` and is pasted from `eval/results.md`; none is typed by hand. Layout follows the official submission template.

## 1. Introduction

When a telecom incident spreads beyond one company, the operator, the regulator, the data authority, the cyber council and emergency services each hold part of the picture and part of the duty. Tabletop exercises are how these institutions rehearse that. They are expensive to run, and the policy gaps they expose are usually written up from memory afterwards.

I built an AI tabletop in which each institution is an agent that sees only its own share of a staged incident. An agent can propose actions, obligations, gaps and messages to other institutions, but nothing it says counts until a deterministic gate accepts it. To pass, a claim must quote a verified source word for word from a passage that agent was actually shown, use a verb inside that institution's legal mandate, cite only injects it received, and give a deadline only if the rule table holds one. Accepted actions change a digital twin of the network, and invariants check whether the incident is actually fixed. At the debrief a coordinator derives the policy gaps and sets each against global examples, using text from the knowledge base. Every step lands in a hash-chained audit log that anyone can re-verify and replay.

The model (DeepSeek-V4.1-Flash) retrieves context, proposes and explains. Code decides. The solution maps each pipeline node to UAE texts and to global practice, so the exercise doubles as a policy sandbox: it tests whether the rules, not only the network, hold up under an AI-caused incident.

## 2. Description of the use case

The problem: telecom regulators and operators need to rehearse cross-institution incidents caused or worsened by AI in the network, and to find where the rules are silent, before a real outage finds it for them. Existing practice has three gaps:

1. Tabletop exercises are run by people with slides. They are rare, costly, and the "who knew what when" is reconstructed afterwards, so information asymmetry between institutions is not tested.
2. When AI assistants are used for policy questions, their answers are not tied to the text of the law. A confident paraphrase of a licence clause is indistinguishable from a made-up one.
3. Gap analysis after an exercise is a narrative. There is no record that links a stated gap to the clause that is missing, the incident step that exposed it, and the foreign rule that covers it.

How the solution closes them: (1) institutions are agents with separate inboxes, and injects are released in stages to the institutions that would really receive them; (2) the gate rejects any claim whose quote is not verbatim in a passage that agent retrieved, and the rejection is fed back, never repaired; (3) gaps come out of a duty matrix and a rule table, each gap carries its UAE text (or the absence of one) and a verified global example, and the whole run is a replayable audit log.

Three scenarios, each grounded in real incidents and regulator actions held in the knowledge base. The operator, OpCo, is fictional and every inject is synthetic.

| | Incident | Institutions | Real grounding |
|---|---|---|---|
| S1 | A closed-loop optimiser auto-approves a core change that skipped the sandbox stage. Region R2 loses emergency-call routing, and the vendor asks for subscriber logs to be sent offshore. | NOC, REG, EMS, CSC, DPA | AT&T 2024 (FCC report), Optus 2023 (ACMA), Rogers 2022 (CRTC). No official report names AI as a root cause, so the AI optimiser is a labelled extrapolation. |
| S3 | A SIM-swap fraud model update refuses about 2,750 legitimate prepaid and roaming customers, who then cannot receive banking passcodes. | NOC, REG, DPA, FIN | FCC 23-95, ACMA identity-verification penalties 2025-2026 |
| S2 | A vendor update widens a support chatbot's retrieval scope, and prompt injection leaks other subscribers' data. | NOC, DPA, CSC, REG | FCC DA 24-892 (vendor breach), Moffatt v Air Canada, Dutch DPA chatbot report |

Institutions: NOC is the operator (licensee); REG is TDRA; DPA is the UAE Data Office; CSC is the Cyber Security Council; EMS is NCEMA and the 999 centre; FIN is the Central Bank (S3 only).

## 3. Use case requirements

Requirements per node of the Y.3172 pipeline (section 4 gives the mapping):

- SRC and C: an agent sees only the injects released to it and the messages other agents chose to share. Inject release follows a fixed timeline per scenario.
- PP: the knowledge base is chunked at clause level (4,079 chunks from 61 sources), each source pinned by SHA-256 with its official URL and a status (VERIFIED, SECONDARY, HISTORICAL, UNVERIFIED). Retrieval is scoped to the layers an institution's mandate covers.
- M: the model returns a structured JSON assessment; free text never counts.
- P: a claim is accepted only if (a) every quote is verbatim (after Unicode and whitespace normalisation), at least 20 characters, from a chunk that agent retrieved; (b) obligations and global examples cite VERIFIED sources; (c) action verbs are in the institution's mandate, and every mandate verb carries the clause it comes from, itself checked against the KB (`python -m tabletop check-data`); (d) cited injects were released to that agent; (e) any deadline exists in the rule table. Malformed output is rejected with a reason, never repaired.
- D: high-impact verbs (change rollback, moving sites to another core, model rollback, changing the fraud threshold, disabling a chatbot tool, restoring its scope, a minimised data export) need human-in-the-loop approval after the gate. Accepted shares and notifications are routed only to the institutions named.
- SINK: every event goes to an append-only, hash-chained log; the first event records the hashes of the KB, scenario, answer key, mandates, rules and prompt template; replay must reproduce every gate verdict.
- Closed loop: actions change the twin, and the run reports whether the invariants hold at the end (S1: every region reaches emergency services, no subscriber data offshore; S3: legitimate pass rate at least 99% with fraud still blocked; S2: no leaks while at least 95% of benign queries still succeed).

## 4. Mapping with ITU-T Y.3172, the Readiness 2.0 Report, and domain-specific policies

| Node | Use case (telecom incident tabletop) | Readiness 2.0 Report (dimensions) | Documents in the KB |
|---|---|---|---|
| SRC | Scenario injects; network telemetry from the twin; KB source documents | 13 Digital Infrastructure; 1 Data/Model Marketplace (curated, pinned KB) | Licence 2/2026; Telecom Law and its Executive Order; ITU-T Y.3090 (digital twin network) |
| C | Each institution's inbox: released injects plus items others shared | 7 Strategy Alignment (who must tell whom) | Licence 2/2026 Art. 12.9.2 (inform TDRA "as soon as possible"); CRTC 2025-225 and 47 CFR 4.9 as global notification examples |
| PP | Clause-level chunking; BM25 retrieval scoped to the institution's mandate layers | 3 Cross-Domain Correlation Analysis (telecom, data, cyber, finance texts in one index) | ITU-T Y.3174 (data handling for ML); PDPL for personal data in logs |
| M | The model producing a structured assessment | 5 Level of Integration of AI in Workflows | 3GPP TS 28.105 (AI/ML management); ETSI TS 104 223 (securing AI); NIST AI RMF and AI 600-1 |
| P | `gate.py`: verbatim quote, provenance, source status, mandate, inject, deadline | 10 AI & Policies (policy checked against text); 8 Collaboration with AI | UAE AI Charter 2024 and AI Ethics Principles (human oversight); EU AI Act (human oversight, transparency) |
| D | `coordinator.py`: routing, HITL approval of high-impact verbs, duty matrix, rule-table clocks | 6 Human Interface; 9 Impacts of Humans in AI Integration | PDPL (cross-border transfer); TDRA Consumer Protection Regulations; Cyber Strategy 2019 |
| SINK | Audit log, gap matrix, replay page | 10 AI & Policies (policy gaps as output) | GDPR Art. 33, NIS2 Art. 23, FCC 23-95 as global comparators |
| MLFO | `engine.py`: stage schedule, model choice, stage loop | 7 Strategy Alignment | ITU-T Y.3172 |
| ML sandbox | The exercise itself, run against the digital twin instead of a live network | 10 AI & Policies (metric: Policy Sandbox); 11 AI for Inclusion (metric: Digital Twins) | ITU-T Y.3181 (ML sandbox); ITU-T Y.3090 |

Per scenario, the dimensions the incident tests most (official names): S1: 13 Digital Infrastructure, 10 AI & Policies, 6 Human Interface. S3: 11 AI for Inclusion (the false lockouts fall on prepaid and roaming users), 10 AI & Policies, 9 Impacts of Humans in AI Integration (the fix is a human review queue). S2: 6 Human Interface, 10 AI & Policies, 5 Level of Integration of AI in Workflows (a GenAI bot wired into account tools).

Each institution's mandate is sourced from UAE texts. Examples: NOC may `notify` REG under Licence 2/2026 Art. 12.9.2; REG may `open_incident` and `request_report` under the Telecom Law and `issue_direction` under the licence; DPA may `request_breach_report` and `assess_transfer` under Federal Decree-Law 45/2021 (PDPL); CSC may `issue_advisory` under the Cyber Strategy 2019. EMS and FIN verbs with no UAE legal basis in the KB are kept, marked as having an empty basis, and counted as a finding. Some UAE AI-governance documents could only be found as summaries; they are UNVERIFIED and the gate will not accept them as evidence.

## 5. Error scenarios

Each scenario releases its injects in stages, so institutions start with incomplete, unevenly distributed information. Each one also includes a question no source in the KB can answer; there the correct behaviour is to say "insufficient evidence", not to make something up.

S1, automated change cuts emergency calls.
1. T+0: NOC alone sees an auto-approved change ticket with "sandbox stage: skipped".
2. T+3: core site A isolates; 6 of 15 R2 sites lose service and R2 has no emergency-call path. Only NOC sees the alarm.
3. EMS sees 999 traffic from R2 drop to near zero, without knowing why.
4. The vendor asks NOC for 24 h of core logs with MSISDNs and IMSIs, uploaded to a cloud region abroad; CSC separately sees the scheduled bulk upload.
5. A journalist asks TDRA whether AI runs the network unsupervised; TDRA has not been notified.
6. Unanswerable: the TDRA duty officer asks within how many hours the licence requires notification. The licence says "as soon as possible", so a number is a fabrication.

S3, fraud model locks out legitimate customers: NOC sees refusals up tenfold after model v2; banks tell FIN that customers abroad cannot receive passcodes; analysis shows refusals concentrate on prepaid and roaming profiles (about 2,750 legitimate requests); customers complain to DPA and REG about automated decisions with no explanation or appeal. Unanswerable: which UAE instrument sets SIM-replacement authentication rules (none in the KB).

S2, chatbot leaks personal data: a customer posts a screenshot showing another subscriber's address; logs show about 1,200 affected sessions since a vendor update; CSC learns the injection technique is being sold; a data subject complains directly to DPA. Unanswerable: the breach-notification deadline in hours (the PDPL leaves it to Executive Regulations not yet issued).

Where the solution faces controversy, and how it handles it:

- Fixing one thing breaks another. The twin encodes the trade-off as invariants. In S3, "unblock everyone" restores legitimate customers but fails the fraud-block invariant; the accepted fix is a model rollback plus a human review queue. In S2, "turn the bot off" stops the leak but fails the benign-service invariant; the accepted fix is restoring retrieval scope and disabling the account tool. The coordinator logs an objective conflict when an action repairs one invariant and breaks another.
- Forensics versus privacy. In S1 the vendor wants subscriber logs to diagnose the fault, which pulls against PDPL cross-border rules. In the twin, the full export leaves subscriber identifiers offshore and fails an invariant; the minimised export (MSISDN and IMSI dropped) clears the pending request without them, and as a high-impact verb it needs human approval after the gate.
- Who has to act. Several institutions can act on the same incident, and some duties have no owner. The duty matrix makes this explicit: a duty nobody accepted becomes a gap, and two institutions claiming an exclusive duty becomes an overlap.
- The model may be wrong with confidence. The gate does not trust it: a fluent paraphrase of a clause is rejected as not verbatim, and the rejection is shown to the agent and logged. The replay page shows every rejected claim next to the source text it misquoted.
- Is the AI being blamed fairly? No official report on the real outages names AI as the root cause. The AI optimiser and fraud model are labelled extrapolations, and the report says so.

## 6. Evaluation

Setup: 3 recorded runs per scenario with DeepSeek-V4.1-Flash, plus 3 ungated baselines per scenario (one omniscient prompt over the whole KB, same model) scored by the same gate. I wrote and froze the answer keys in commit `bfbebaf`, before the first live run; their hash is in every run's first event. A second set of runs with DeepSeek-V4-Pro is kept in `runs/pro-v4/` as a second-model record.

Metrics: citation validity (share of claims whose evidence passes the verbatim check), mandate and inject violations attempted and blocked, action, obligation and gap recall against the keys, correct abstention on the unanswerable inject, and whether the twin invariants hold at the end.

Numbers from `eval/results.md` (generated by `python -m tabletop eval` from the committed logs; mean, with min-max over 3 runs where they differ). KB: 61 sources, 4,079 chunks, 54 VERIFIED.

| Gated agents | S1 | S3 | S2 |
|---|---|---|---|
| Claims / rejected by gate | 2714 / 80 | 1506 / 84 | 1670 / 47 |
| Citation validity | 0.99 | 0.99 (0.98-0.99) | 0.98 |
| Action recall | 0.86 | 1.00 | 0.83 |
| Obligation recall | 0.67 | 0.83 (0.50-1.00) | 0.22 (0.00-0.33) |
| Gap recall, agents | 1.00 | 1.00 | 0.94 (0.83-1.00) |
| Correct abstention | 3/3 | 3/3 | 3/3 |
| Twin restored | 3/3 | 3/3 | 2/3 |
| Chains verified | 3/3 | 3/3 | 3/3 |

| Ungated baseline (same model) | S1 | S3 | S2 |
|---|---|---|---|
| Claims the gate would reject | 80/115 | 73/95 | 44/81 |
| Gap recall, ungated / gated | 0.39 / 0.22 | 0.53 / 0.47 | 0.33 / 0.33 |

With the gate in the loop, agents' claims almost always carry a verbatim, retrieved, verified quote. The same model asked once with the whole KB and no gate makes claims the gate would reject 54-77% of the time, and finds at most about half the key gaps even before the gate. The weakest number is S2 obligation recall: agents named the breach duty but rarely quoted the PDPL article the key expects. Agent runs used commit 864d039, baselines 0988762. Recall is relative to my own keys, frozen before the first live run.

To check any number: `verify-log` recomputes a run's chain, `replay` re-executes it from the recorded model responses and must give identical gate verdicts, and `eval` recomputes the tables (all `python -m tabletop ...`). `kb export` writes the KB in the ITU reference toolkit's InputDocs layout for ChromaDB.

## 7. Policy gaps and standards gaps derived from the mapping exercise

Gaps come from three places: the duty matrix (a duty nobody accepted), the rule table (a UAE duty with no fixed clock while global peers have one), and agent-proposed gaps that passed the gate. The main ones, each with the global text it is compared against:

| Gap | UAE text | Global examples |
|---|---|---|
| No fixed outage-notification deadline | Licence 2/2026 Art. 12.9.2 "as soon as possible" | CRTC 2025-225: 2 h to the regulator, 30 min to 911 centres; 47 CFR 4.9: 120 min, PSAP 30 min; NIS2 Art. 23: 24 h early warning |
| No duty to notify emergency services directly | Same article | CRTC 2025-225; 47 CFR 4.9(h); Australian Bean review response |
| No control on automated or AI-driven network changes | None in the telecom texts collected. The closest UAE text, the Cabinet's 2026 Agentic AI framework, covers federal government services, and its text is not published | ITU-T Y.3172 and Y.3181 (ML sandbox before deployment); EU AI Act; FCC AT&T 2024 report |
| Breach-notification deadline waits on unissued Executive Regulations | PDPL | GDPR Art. 33: 72 h |
| Right to object to automated decisions has no procedure yet | PDPL | GDPR Art. 22 |
| No UAE rule on SIM-swap authentication or notification | None found in the KB | FCC 23-95; 47 CFR 64.2010; ACMA Optus and Telstra actions |
| No duty to disclose that a customer is talking to an AI system | TDRA Consumer Protection Regulations Art. 26.7.2 rules out non-human agents in complaint conversations, but there is no general disclosure duty | EU AI Act; Moffatt v Air Canada |

"None found in the KB" means none in the 19 UAE sources I collected. It does not mean no such rule exists anywhere. These are domain gaps set against global practice, not recommendations for the UAE.

Limits and honesty notes:

- The model's reasoning shown in the page is the agent's structured rationale (observation, rule, inference) plus the reasoning text the API returns. Neither is claimed to be a verified chain of thought.
- Recall is relative to answer keys I wrote. They were frozen before any live run, but they are still one person's keys.
- The twin models only the layer each incident touches. It is not a protocol emulator.
- The human-in-the-loop step in recorded runs is a scripted facilitator that approves a high-impact action only after the gate has accepted it.
- Injects are synthetic and OpCo is fictional. Real incidents are cited only as grounding.
