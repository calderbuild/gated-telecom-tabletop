# Global sources: curation notes (2026-10-05)

42 records in `global.json`, all `VERIFIED` (primary text read and pinned). Raw files are in `kb/raw/` (gitignored); the sha256 in each record is of that file. Text layers are in `kb/text/<ID>.txt`.

## How the text layers were made

- PDFs: `pdftotext -layout`, then whitespace collapsed per line and blank lines dropped. Removed: running headers and footers (`Rec. ITU-T Y.31xx (mm/yyyy) n`, `ETSI`, `3GPP TS 28.105 version ... ETSI TS 128 105 ...`, `NIST AI 100-1 AI RMF 1.0`, `Page n`, `BoR (23) 93`, `Federal Communications Commission DA 24-xxx`, the AI Ready running title, the Bean `OFFICIAL` banner and title), bare page numbers next to page breaks, and TOC dot-leader lines. GSMA and CRS are multi-column, so they were extracted in reading order (no `-layout`) to stop columns interleaving.
- Ligatures (ﬁ ﬂ ﬀ ﬃ ﬄ), non-breaking spaces and soft hyphens were normalised. No other characters were changed.
- Jina markdown (EUR-Lex, ACMA, CRTC backgrounder): the proxy preamble, site navigation and EUR-Lex footer were cut. Markdown link and heading syntax was removed, keeping the link text. Spaces were restored where the proxy glued link text to its neighbours (`(ACMA)investigationfound` became `(ACMA) investigation found`). Spaces were also restored after point markers that EUR-Lex renders in separate cells (`1.In the case` became `1. In the case`, `(a)point` became `(a) point`). A bare point marker on its own line was joined to the next line.
- HTML pages: tags were stripped and the lines cut to the article body (from the title or date line to the share or feedback block).
- Tables (Y.3173 Table 7-2, NIST 600-1 action tables, 3GPP attribute tables) are flattened row by row. Cell order is kept, but a cell that wraps lands on its own line.
- A heading like `1 Scope`, `3.2.6 machine learning sandbox: ...`, `Article 23`, `ANNEX III`, `§ 4.9 ...` or `15.22 § 14 ...` starts its own line. In the FCC orders, paragraph numbers (`13. Accordingly, IT IS ORDERED ...`) start the line.

## Per source: what I did and caveats

| ID | Raw obtained from | Caveat |
|---|---|---|
| ITU-T-Y3172/3173/3174/3177/3181 | research/kb-raw copies; sha prefixes match telecom-kb-sources.md G1-G5 | none |
| ITU-T-Y3090 | itu.int dologin_pub (200 PDF, 26 pp) | none |
| ITU-AI-READY-2 | research/kb-raw (sha prefix 71191768d46b6077 matches G8) | none |
| ITU-RR-ART15 | Official free download `R-REG-RR-2024-ZIP-E.zip` (72 MB, sha256 53fa7399…b499); raw = `RR-Vol 1-E.docx` from that zip | Text layer is an extract: No. 1.169 (definition of harmful interference) plus all of Article 15. The rest of Volume 1 is not in it. |
| EU-AIA, EU-AIA-OMNIBUS, EU-NIS2, EU-GDPR | r.jina.ai of the ELI `/oj` pages (EUR-Lex returns an AWS WAF challenge to curl) | AIA and GDPR are the original OJ texts, not consolidated. AIA Art. 113 must be read with OMNIBUS. In OMNIBUS, each amending point of Art. 1 is one long line. |
| NIST-AI-RMF, NIST-AI-600-1, GSMA-RAI-ROADMAP, ETSI-TS-104223, 3GPP-TS-28105, BEREC-BOR-23-93 | research/kb-raw `.bin` files; all checked as real PDFs, and the sha prefixes match G9, G13, G14 and G16-G18 | 3GPP: 3GPP lists newer versions than the ETSI V19.3.0 publication. BEREC predates the adopted AI Act text. |
| US-FCC-ATT-2024-REPORT | docs.fcc.gov TXT | none |
| US-FCC-DA-24-842 | docs.fcc.gov PDF (the TXT is the same 2-page Order) | The adopting Order only. The Consent Decree body is not in this attachment. |
| US-FCC-DA-24-892, US-FCC-DA-24-649 | docs.fcc.gov PDF | Footnotes interleave with the body at page ends. |
| US-FCC-23-95 | govinfo FR HTML | Hard-wrapped at about 70 columns, as published. |
| US-CFR-47-4-9 | eCFR versioner API, point-in-time 2026-10-01 (needs `--compressed`) | eCFR is an editorial compilation, not the official edition. |
| US-CFR-47-64-2010 | Same API (extra record, added to answer Q5) | same |
| US-CRS-CROWDSTRIKE | congress.gov CRS PDF IF12717.1 | A primary CRS product, not a regulator. |
| CA-CRTC-2025-225 | crtc.gc.ca serves Cloudflare to curl, to Jina, and to the Chrome browser (it requires a human check, which I did not attempt). Raw = Wayback `id_` capture of the official page, 2026-04-11 | Paragraph numbers are HTML auto-numbered `<ol>` items, so they are absent from the text layer. The decision PDF is behind the same wall. **Status call for the lead:** I marked this VERIFIED because it is the unmodified official page served by archive.org. Downgrade it if Wayback copies must not count as primary. The same applies to CA-CRTC-ROGERS-XONA, UK-OFCOM-BT-999-2024 and AU-BEAN-REVIEW-RESPONSE. |
| CA-CRTC-2025-225-BG | Jina (direct canada.ca fetch timed out) | Does not state the clocks. |
| CA-CRTC-ROGERS-XONA | Wayback capture of the CRTC letter lt240704 | Primary, but it is only the CRTC cover letter. **The Xona executive summary itself was not obtained**: the CRTC OTF page is behind Cloudflare and has no Wayback capture. Root-cause facts (ACL filter removal, no overload limit) stay secondary and are not in this text. |
| CA-ISED-MOU-2022 | Direct ised-isde.canada.ca HTML | Effective Date is defined in the text as September 9, 2022. |
| CA-MOFFATT-2024 | The tribunal's own decisions site (`?iframe=true` view of item 525448). CanLII returned a CAPTCHA and was not used. | Small-claims decision. |
| AU-BEAN-REVIEW-RESPONSE | Direct download timed out. Jina's PDF extraction was garbled, so I discarded it. Raw = Wayback `id_` capture of the official PDF (created 2024-04-30, 15 pp) | The text keeps the PDF's own glitches ("obligation s"). |
| AU-ACMA-* (5) | acma.gov.au timed out directly; fetched through Jina | Media releases only. The Optus vendor-default quotes in scenario-validation §2.1 ("pre-set safety limits", "does not absolve Optus of accountability") **are not in AU-ACMA-OPTUS-2024**. They would come from the ACMA investigation report, which was not fetched. The Telstra SIM-swap release does not name the instrument. |
| AU-OAIC-OPTUS-2025, UK-FCA-ACCOUNTS-2023, META-OUTAGE-2021 | Direct HTML | Meta is a company statement, not a regulator. |
| UK-OFCOM-BT-999-2024 | Cloudflare (Jina also blocked); Wayback capture of 2026-05-07 | Resolves the scenario-validation "[verify] Ofcom GC": the legal basis given is the Communications Act 2003 s105A(1) plus reg. 9 of the Electronic Communications (Security Measures) Regulations 2022, not a General Condition. |
| NL-AP-CHATBOT-2024 | Direct HTML, the AP's own English page (found through the Dutch page's hreflang) | Replaces the Dutch NOS article. Status upgraded from SECONDARY to VERIFIED because this is the regulator's primary page. |

Not done:
- CRTC 2025-225 PDF (Cloudflare).
- Xona executive summary (Cloudflare, no archive capture).
- ACMA investigation reports (the media releases only).
- The FCC Federal Register notice announcing the SIM-swap compliance date: none was found, and the eCFR shows the paragraph (h) compliance note still in place (see Q5).

## Verification answers (verbatim from the text layers)

**1. 47 CFR 4.9 (US-CFR-47-4-9, eCFR as of 2026-10-01).**
- § 4.9(e)(1): "All wireless service providers shall submit electronically a Notification to the Commission within 120 minutes of discovering that they have experienced on any facilities that they own, operate, lease, or otherwise utilize, an outage of at least 30 minutes duration:"
- § 4.9(e)(4): "Not later than 72 hours after discovering the outage, the provider shall submit electronically an Initial Communications Outage Report to the Commission. Not later than 30 days after discovering the outage, the provider shall submit electronically a Final Communications Outage Report to the Commission."
- § 4.9(h)(4): "Cable, satellite, wireless, wireline, interconnected VoIP, and covered 911 service providers shall provide a 911 outage notification to a potentially affected 911 special facility as soon as possible, but no later than within 30 minutes of discovering that they have experienced on any facilities that they own, operate, lease, or otherwise utilize, an outage that potentially affects a 911 special facility, as defined in § 4.5(e)."
- § 4.9(h)(5) (follow-up): "... shall send the first follow-up notification to potentially affected 911 special facilities no later than two hours after the initial contact."
- Summary for wireless: Notification within 120 minutes, Initial report within 72 hours, Final report within 30 days. PSAP (911 special facility) notification within 30 minutes, with the first follow-up within 2 hours.

**2. NIS2 Art. 23(4) (EU-NIS2).**
- "(a) without undue delay and in any event within 24 hours of becoming aware of the significant incident, an early warning, ..."
- "(b) without undue delay and in any event within 72 hours of becoming aware of the significant incident, an incident notification, ..."
- "(d) a final report not later than one month after the submission of the incident notification under point (b), ..."

**3. GDPR (EU-GDPR).**
- Art. 33(1): "In the case of a personal data breach, the controller shall without undue delay and, where feasible, not later than 72 hours after having become aware of it, notify the personal data breach to the supervisory authority competent in accordance with Article 55, unless the personal data breach is unlikely to result in a risk to the rights and freedoms of natural persons."
- Art. 34(1): "When the personal data breach is likely to result in a high risk to the rights and freedoms of natural persons, the controller shall communicate the personal data breach to the data subject without undue delay."
- Art. 22(1): "The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning him or her or similarly significantly affects him or her."
- Art. 49(1), first subparagraph, derogations (a)-(g). Items without quotation marks are my short labels, not the text:
  - (a) explicit consent after being informed of the risks
  - (b) necessary for a contract with the data subject or pre-contractual measures
  - (c) a contract concluded in the data subject's interest
  - (d) "the transfer is necessary for important reasons of public interest"
  - (e) "the transfer is necessary for the establishment, exercise or defence of legal claims"
  - (f) vital interests where the data subject cannot consent
  - (g) a public register
  - The second subparagraph adds the narrow compelling-legitimate-interests transfer.
  - Each point is a separate line in the text, so quote it from there.

**4. ITU RR Art. 15 (ITU-RR-ART15).**
- No. 1.169: "harmful interference: Interference which endangers the functioning of a radionavigation service or of other safety services or seriously degrades, obstructs, or repeatedly interrupts a radiocommunication service operating in accordance with Radio Regulations (CS)."
- 15.1 § 1: "All stations are forbidden to carry out unnecessary transmissions, or the transmission of superfluous signals, or the transmission of false or misleading signals, or the transmission of signals without identification (except as provided for in Article 19)."
- 15.2 § 2: "Transmitting stations shall radiate only as much power as is necessary to ensure a satisfactory service."
- 15.22 § 14: "It is essential that Member States exercise the utmost goodwill and mutual assistance in the application of the provisions of Article 45 of the Constitution and of this Section to the settlement of problems of harmful interference."
- 15.25 § 17: "Administrations shall cooperate in the detection and elimination of harmful interference, ..."

**5. FCC 23-95 compliance date.**
- US-FCC-23-95, DATES: "Effective January 8, 2024, except for revisions to 47 CFR 52.37(c), 52.37(d), 52.37(e), 52.37(g) (instruction 3), 64.2010(h)(2), 64.2010(h)(3), 64.2010(h)(4), 64.2010(h)(5), 64.2010(h)(6), and 64.2010(h)(8) (instruction 6), which contain information collection requirements and are delayed indefinitely. The FCC will publish a document in the Federal Register announcing the effective date for those Sections."
- US-FCC-DA-24-649 ¶2 (adopted and released July 5, 2024): "This will effectively result in a single synchronized timeframe: compliance with the rules in their entirety, including those not subject to the PRA, will not be required until OMB completes review of the information collection requirements associated with the Order, and the Commission publishes a notice in the Federal Register announcing the compliance date."
- US-CFR-47-64-2010 (eCFR as of 2026-10-01) still reads: "Compliance with this paragraph (h) will not be required until this paragraph is removed or contains a compliance date."
- Status: I found no compliance-date notice. The current eCFR text suggests none has taken effect for § 64.2010(h). "Not found" is not the same as "absent", and I did not search the Federal Register exhaustively.

**6. EU AI Act.**
- Annex III point 2 (EU-AIA): "2. Critical infrastructure: AI systems intended to be used as safety components in the management and operation of critical digital infrastructure, road traffic, or in the supply of water, gas, heating or electricity."
- Art. 50(1): "Providers shall ensure that AI systems intended to interact directly with natural persons are designed and developed in such a way that the natural persons concerned are informed that they are interacting with an AI system, unless this is obvious from the point of view of a natural person who is reasonably well-informed, observant and circumspect, taking into account the circumstances and the context of use. ..."
- Art. 73 timelines:
  - (2): "... not later than 15 days after the provider or, where applicable, the deployer, becomes aware of the serious incident."
  - (3), for a widespread infringement or an Art. 3(49)(b) incident: "... immediately, and not later than two days after the provider or, where applicable, the deployer becomes aware of that incident."
  - (4), for a death: "... but not later than 10 days after the date on which the provider or, where applicable, the deployer becomes aware of the serious incident."
- Art. 113 as amended (EU-AIA-OMNIBUS, Art. 1 point (40)): "(c) Chapter III, Sections 1, 2, and 3, with the exception of Article 6(5), shall apply from: (i) 2 December 2027 as regards AI systems classified as high-risk pursuant to Article 6(2) and Annex III; and (ii) 2 August 2028 as regards AI systems classified as high-risk pursuant to Article 6(1) and Annex I;"
- Also in point (40): "(d) Articles 102 to 110 shall apply from 27 July 2026."
- The omnibus was done at Strasbourg on 8 July 2026. Under Art. 4 it enters into force on the third day after OJ publication.

**7. ITU-T clauses.**
- Y.3172 3.2.6 (ITU-T-Y3172): "machine learning sandbox: An environment in which machine learning models can be trained, tested and their effects on the network evaluated." NOTE: "A machine learning sandbox is designed to prevent a machine learning application from affecting the network, or to restrict the usage of certain machine learning functionalities."
- Y.3172 policy node: clause 8.1 (High-level architectural components), item 1) Machine learning pipeline. It reads: "• P (policy): This node enables the application of policies to the output of the model node." NOTE 5: "This node can be used, for example, to minimize impact when the output of machine learning is applied to a live ML underlay network. Specific rules can be put in place by a network operator to safeguard the sanity of the network, e.g., major upgrades may be done only at night time or when data traffic in the network is low." There is no separate numbered clause for the P node.
- Y.3090 3.2.1 (ITU-T-Y3090): "digital twin network: A virtual representation of a physical network. It is useful for analysing, diagnosing, emulating and controlling the physical network based on data, model and interface, to achieve the real-time interactive mapping between the physical network and virtual twin network."
- Y.3173 Table 7-2 "Network intelligence levels":
  - Column headings: Network intelligence level | Dimensions: Action implementation, Data collection, Analysis, Decision, Demand mapping.
  - Row labels, from ML-Int-level-003 (six bullet lines in the text, each starting "• "): "L0: Manual network operation;", "L1: Assisted network operation;", "L2: Preliminary intelligence;", "L3: Intermediate intelligence;", "L4: Advanced intelligence;", "L5: Full intelligence."
  - NOTE 1 to the table: "For each network intelligence level, the decision process has to support intervention by human being, i.e., decisions and execution instructions provided by a human being have the highest authority."
- Y.3181 clause 1 Scope (ITU-T-Y3181): "This Recommendation provides an architectural framework for the machine learning (ML) sandbox in the context of integrating machine learning in future networks including IMT-2020."

**8. CRTC 2025-225 (CA-CRTC-2025-225).**
- "Major primary service outage: TSPs must notify the Commission, ISED, and FPT EMOs within two hours. Originating network providers are encouraged to notify PSAPs of an outage affecting voice and text services within 30 minutes;"
- "Major 9-1-1 service outage: 9-1-1 network providers and originating network providers must notify (i) PSAPs within 30 minutes; and (ii) the Commission, ISED, and FPT EMOs within two hours;"
- "Major wireless public alerting service outage: WSPs must notify (i) FPT EMOs within 30 minutes, and (ii) the Commission and ISED within two hours; and"
- "Major specialized service outage: TSPs must notify the Commission and ISED within two hours."
- Post-outage report: "TSPs must submit a post-outage report to the Commission within 30 days of restoring the services affected by a major service outage."
- Effective date: "These requirements will become effective on 4 November 2025."
- Correction to scenario-validation row "Rogers": notifying 9-1-1 centres (PSAPs) is mandatory only for 9-1-1 outages. For major primary outages it is "encouraged", not required.

**9. FCC AT&T report (US-FCC-ATT-2024-REPORT).** All three fragments in scenario-validation row 1 are verbatim:
- "... and preventing more than 25,000 calls to Public Safety Answering Points (PSAPs or 911 call centers)."
- "This triggered an automated response that shut down all network connections to prevent the traffic from propagating further into the network."
- "... a configuration error, a lack of adherence to AT&T Mobility’s internal procedures, a lack of peer review, a failure to adequately test after installation, inadequate laboratory testing, insufficient safeguards and controls to ensure approval of changes affecting the core network, ..."
- The same report also says "blocking more than 92 million voice calls".

**10. Bean review government response (AU-BEAN-REVIEW-RESPONSE).** All three are "Agreed."
- Recommendation 1: "Mandatory requirements should be put in place, by augmenting existing requirements or otherwise, to: • More clearly and explicitly articulate precisely what is expected of network operators in regard to ensuring calls are delivered to Triple Zero • Include specific obligation s that network operators wilt towers in the event of loss of connectivity to a core network, ensuring calls to Triple Zero can be carried by other networks."
- Recommendation 3: "To ensure (to the extent possible) continuous access to Triple Zero, carriers must conduct 6-monthly end-to-end testing of all aspects of the Triple Zero ecosystem within and across networks. The end to end detection testing should include: • Network functionality and capability during outages of various types • Behaviour of all known devices in different circumstances • Interoperability of all parts of the ecosystem (from originating carrier, to ECP, to ESO answering point) during outages. Any identified deficiencies must be reported to the ACMA and be accompanied by a remediation plan with timetable. This requirement should be mandated in a standard or determination."
- Recommendation 5: "Require carriers, through a standard or determination, to share real time network information detailing outages with relevant emergency services organisations and other appropriate entities, including the body referred to in Recommendation 2."

## Other checks against scenario-validation §2.1

- Telstra 2024 (AU-ACMA-TELSTRA-2024): "neglected to update its backup phone data" and "473 breaches" are both present.
- Optus 2026 (AU-ACMA-OPTUS-2026): "The recurrence of a major network outage affecting emergency calls so soon after the November 2023 outage is a significant concern" and "1,005 occasions" are both present.
- Meta (META-OUTAGE-2021): "a bug in that audit tool prevented it from properly stopping the command" is present.
- Moffatt (CA-MOFFATT-2024): "It should be obvious to Air Canada that it is responsible for all the information on its website. It makes no difference whether the information comes from a static page or a chatbot."
- FCC 23-95: "should not be used to delay legitimate SIM change requests" is present.

## Reproducing

The build scripts live in the session scratchpad and are not committed: `build.py` produces the text layers from `raw/`, and `manifest.py` produces `global.json`. Every cleanup rule they apply is listed above.
