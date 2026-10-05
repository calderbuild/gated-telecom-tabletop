# UAE KB curation notes (2026-10-05)

Every quote below is copied programmatically from the committed text layer in `kb/text/<ID>.txt`, and each text layer comes from the raw file pinned in `manifest.d/uae.json`.

## Source table

| ID | status | binding | text bytes |
|---|---|---|---|
| UAE-TEL-LAW | VERIFIED | true | 51255 |
| UAE-TEL-EXEC | VERIFIED | true | 40471 |
| UAE-LIC-2-2026 | VERIFIED | true | 45121 |
| UAE-TDRA-CPR-2 | VERIFIED | true | 140715 |
| UAE-TELEMKT-56-2024 | VERIFIED | true | 12146 |
| UAE-TDRA-PR-2026 | SECONDARY | false | 4466 |
| UAE-PDPL | VERIFIED | true | 40899 |
| UAE-AI-CHARTER-2024 | VERIFIED | false | 3930 |
| UAE-AI-ETHICS-2022 | VERIFIED | false | 57481 |
| UAE-AI-STRATEGY-2031 | VERIFIED | false | 59966 |
| UAE-CABINET-AGENTIC-2026 | SECONDARY | false | 8569 |
| UAE-CSC-AI-POLICY | UNVERIFIED | false | 3559 |
| UAE-CSC-CIIP | UNVERIFIED | false | 811 |
| UAE-CYBER-STRATEGY-2019 | VERIFIED | false | 7619 |
| UAE-NCEMA-7000-2012 | HISTORICAL | false | 174195 |
| UAE-FAAID-2026 | SECONDARY | false | 6541 |
| UAE-PRESS-DU-OUTAGE-2026 | SECONDARY | false | 956 |
| UAE-PRESS-SIMSWAP-COURT-2022 | SECONDARY | false | 3421 |
| UAE-PRESS-CBUAE-OTP-2025 | SECONDARY | false | 5091 |

## Findings that change earlier research

1. **CPR v2.0 has a second AI-relevant clause.** `research/telecom-kb-sources.md` says Art 25.14 is the only AI clause in any TDRA instrument. In fact Art 26.7.2 rules out "non-human agents" in conversations with consumers about complaints. This bears directly on S2 (the GenAI customer-care bot). Source: UAE-TDRA-CPR-2:

> 26.6. Licensees shall maintain an adequate number of properly trained personal to receive, process, and respond to Consumer Complaints in a timely and prompt manner.
> 26.7. The provisions of sub-article 26.6:
> 26.7.1. apply in all cases regardless of which Mandatory Channel is used; and
> 26.7.2. preclude the use of non-human agents by Licensees in conversations with Consumers regarding Consumer Complaints.

2. **The TDRA "Executive Order" file in `research/kb-raw/execorder.pdf` is only a one-page cover.** The full Executive Order is a different file on the same TDRA page (see UAE-TEL-EXEC below). Its Art 11(7) refers to free services "in emergency cases".
3. **The organiser "NCEMA 7000:2021" PDF is not the standard.** It is a self-assessment checklist by a consulting firm. No 2021 text is in the KB.
4. **CBUAE OTP.** The National article does not carry "Notice 2025/3057" or the 2026-03-31 deadline that `research/scenario-validation.md` §2.3 cites. Those details need another source, or they should be dropped.
5. **NCEMA 2012 says TRA owns the telecom business continuity plan** (quoted under NCEMA below). That is a useful UAE anchor for "who coordinates a telecom outage", but the edition is HISTORICAL, so `tabletop/kb.py` leaves it out of the retrieval index.

## Per source

- **UAE-TEL-LAW**: the TDRA consolidated print (`research/kb-raw/telecomlaw.pdf`, sha256 `de1ab5b117b7dedac89cbbf5e499d2c532e2488a191aa3ebd6624f252fba9585`, 54 pp) is image-only, and `research/kb-raw/telecomlaw_uae.bin` was an empty file. I fetched uaelegislation.gov.ae/en/legislations/1132 through Jina because a direct fetch returns 403 (Cloudflare). Raw is that Jina markdown. For the text layer I stripped the index, the logos and the markdown syntax (`**`, `####`, links). The portal text embeds amending provisions for the Etisalat corporation law, and those carry their own `Article (25)`, `(31)`, `(33)` and `(47)` headings inside the law. The chunker will treat them as article headings.
- **UAE-TEL-EXEC**: on TDRA, the "Resolution No (3) of 2004 Issuing the Executive Order" link (`research/kb-raw/execorder.pdf`, sha256 `c6cfc1b6e2e13345109a1b3f238c385eb1dc0777f41a9afa04d7c1368d392368`) is a one-page scan. I checked it by OCR: it shows only the preamble, "Article One Definitions" and "Article Seventy Five". The full 75-article text sits behind the other TDRA link, "Decision of the Supreme Committee ... No. (3) of 2004" (28 pp, with a text layer), and that is the file I used. The two files give different dates. The cover reads "Issued in Abu Dhabi on 28/12/2004 Corresponding to: 14 Sha'ban 1425 H", and the full text reads "Dated: 14th Sha'ban 1425H Corresponding to: 28th September 2004". I recorded 2004-09-28. Three definitions in Art 1 were laid out in two columns and extracted interleaved. I restored each to term-then-definition order without changing any words.
- **UAE-LIC-2-2026**: from `pdftotext -bbox` output I kept the English column (words with x < 316 pt) and dropped Arabic script. I also dropped English-only rows that sit in the Arabic column (the address block in 16.1 is printed twice). Wrapped lines are rejoined into paragraphs. I removed the page header "Licence No (2) of (2026)", the page numbers and a table-of-contents line. Clause 12.9.2 reads correctly (quoted below). The file TDRA serves today is byte-identical to `research/kb-raw/etisalat2026.pdf`.
  - I left out the du Licence 3/2026 on purpose because it uses the same template: https://tdra.gov.ae/-/media/About/LICENSING/EN/Licence-32026-EITC-Public.ashx, sha256 `ccafd4ed2d5a960bc1fb2ff27c6161a95a948ee2547ac13b87589a79ddcf7924`. I re-downloaded it on 2026-10-05 and it is identical to `research/kb-raw/du2026.pdf`.
- **UAE-TDRA-CPR-2**: extracted with `pdftotext -layout`. I removed the running header, the "Page N" lines and the TOC, and rejoined wrapped lines. The bytes are identical to the organiser copy.
- **UAE-TELEMKT-56-2024**: same method. I removed the inline running footer "Cabinet Resolution 2024 Concerning the Telemarketing Regulations N" and rebuilt the Art 1 definition table as `Term : definition` lines. The source reads "Do Not Connect Register (DNCR)", and I kept that verbatim.
- **UAE-TDRA-PR-2026**: the page is dated 12/08/2026 and quotes "from connected networks to intelligent, autonomous networks, where artificial intelligence becomes an integral part of the intelligence of the network itself." I marked it SECONDARY. The gate only checks status, so a VERIFIED press release could back an obligation, and SECONDARY prevents that.
- **UAE-PDPL**: official English text from uaelegislation.gov.ae/en/legislations/1972, fetched through Jina. `research/kb-raw/pdpl_1972.bin` was a Cloudflare block page. Of the organiser files, `01_.../Federal Decree Law No 45 of 2021 on Personal Data Protection.pdf` is Arabic only, with no English text. `02_.../2.1_PDPL_Federal_Decree-Law_45_of_2021.pdf` is an unofficial English/Japanese translation (labelled "非公式な英訳"). I compared Arts 2, 9 and 18 against it. The substance matches but the wording differs (its Art 9 has "immediately upon becoming aware ... report ... to the Office"), so I used the portal text. The Executive Regulations had still not been issued as of June 2026, per Morgan Lewis (UAE-FAAID-2026). I took no date from memory: the record's date, 2022-01-02, is the entry into force stated in Art 31.
- **UAE-AI-CHARTER-2024 / UAE-AI-ETHICS-2022 / UAE-AI-STRATEGY-2031**: all three organiser PDFs are the real documents, not stubs. The `.md` files beside them are stubs whose AI-written abstracts contain errors (the PDPL stub, for example, says "Art. 24 (automated decision-making)", but that is Art 18). The official URLs return 403 (Charter) or 404 (Ethics, Strategy) from here, so the sha256 values are of the organiser copies. In the Charter I restored broken "Th"/"ff" ligature glyphs. Ethics and Strategy are printed as two-page spreads, so I split each sheet into left and right halves before extraction to keep the reading order. Charts in the Strategy extract as fragments.
- **UAE-CABINET-AGENTIC-2026**: organiser 1.3 `.md` is a stub, but organiser 1.3 `.html` is the Government of Dubai Media Office release on the 18 May 2026 Cabinet meeting. The same file is also saved as 9.1, 13.2 and 14.2. I re-fetched it from mediaoffice.ae at its canonical URL and the article body matches. It is an official announcement, not an instrument. It approves:
  - a framework that has ministries move at least 50% of federal services and operations to Agentic AI within two years
  - a training programme for 80,000 employees
  - a national digital-health AI policy

  Its only telecom content is the review of TDRA's 2025 activity report and telecom membership of the Digital Wellbeing council. It is relevant to government AI agents in general, not to telco obligations. I included it as SECONDARY.
- **UAE-CSC-AI-POLICY / UAE-CSC-CIIP**: csc.gov.ae still fails from here. Direct curl hits a TLS reset (`SSL_ERROR_SYSCALL`), Jina times out or loses the connection, and Wayback through Jina is blocked (403). The text layer is the u.ae summary page, and the status is UNVERIFIED. The AI-policy summary does contain "ensuring human oversight in critical decision-making" and "an automated response framework for AI/ML security incidents", but only in summary form.
- **UAE-CYBER-STRATEGY-2019**: re-downloaded from tdra.gov.ae/userfiles/assets/Lw3seRUaIMd.pdf and identical to the organiser copy. It is a 28-slide TRA deck, so the text layer is slide fragments.
- **NCEMA 7000:2021**: not obtained. The organiser file `05_Business_Continuity/5.1_NCEMA_7000_2021_BCM_Standard.pdf` is the "NCEMA 7000 Self-Assessment Checklist" by Continuity & Resilience (CORE), created in 2020, and it refers to the 2015 edition. ncema.gov.ae times out both from curl and through Jina. In its place I added the official 2012 edition from the organiser dataset (`5.1b_NCEMA_7000_2012_BCM_Standard_v1.pdf`, AE/HSC/NCEMA 7000:2012 v1, 116 pp) as **UAE-NCEMA-7000-2012**, status HISTORICAL. I could not verify a direct NCEMA file URL, so `url` is the NCEMA publications page.
- **NCEMA Crisis Communication Guidelines (5.2)**: the `.md` is a stub with a generic abstract that points to the NCEMA publications index, and `5.2_NCEMA_Portal.html` is a portal page. There is no document and no traceable file URL, so I did not include it.
- **TDRA QoS framework (3.2 `.md`) and National Frequency Plan (3.4 `.md`)**: both are stubs with an AI-written abstract and a link to a TDRA index page, and neither has a document behind it. I did not include them. The only real file in that folder is `3.4_TDRA_Spectrum_Management_White_Paper_2023.pdf`, which is not on my list and which I did not ingest.
- **UAE-FAAID-2026 and the press items**: the text layers keep the article body only. I removed site navigation, the "Recommended" and "Also read" widgets, and image captions. The du article mentions neither 999 nor TDRA.
- **Reproducibility**: the HTML and Jina raw files come from dynamic pages, so `kb fetch` will download them again but the sha256 will not match. The PDFs are stable.

## Verification answers

### Licence 2/2026 (UAE-LIC-2-2026)

> 12.9.2 In the case of any unplanned interruption of a Telecommunication Service, other than minor interruptions, the Licensee shall inform the TDRA, any interconnecting Other Licensed Operators and relevant Customers as soon as possible as to the reason(s) for the interruption as well as the manner and time frames in which the interruption will be resolved.

> 12.5 Testing and Assurance
> The Licensee shall periodically test and validate the effectiveness of its resilience, redundancy and contingency arrangements, including through the simulation of failures affecting international connectivity. The Licensee shall maintain adequate records of such testing and shall provide the same to the TDRA upon request.

> 9.5.1 The Licensee shall ensure that Customers shall have free access to the emergency call service numbers designated by the TDRA for Emergency Calls.

Art 12.3 and 12.4, headings and text:

> 12.3 Elimination of Single Points of Failure
> The Licensee shall ensure that its Telecommunications Network architecture is designed to minimize, to the maximum extent reasonably practicable, any single points of failure that may materially impact the availability or performance of Telecommunications Services.
> 12.4 Redundancy, Backup, Disaster Recovery and Failover Mechanisms
> The Licensee shall implement and maintain appropriate redundancy, diversity, backup, disaster recovery and failover arrangements across its Telecommunications Network, including international gateways, transmission infrastructure, core network elements, supporting systems and other critical network assets, to support the continuity and timely restoration of Telecommunications Services in the event of equipment failure, network disruption, natural disaster, cyber incident or any other event that may adversely affect the operation of the Licensed Network. Such arrangements shall be maintained in an operational state at all times and shall be periodically tested to verify their effectiveness.

Keyword check on the English text layer, case-insensitive: "artificial intelligence" 0, "automated" 0, "algorithm" 0, "machine learning" 0. A check on raw `pdftotext` output for the whole PDF (both languages) for "artificial|automat|algorithm" also returns 0.

Related, Art 8.1:

> 8.1 Public Emergencies
> If a competent authority declares that a public emergency has arisen, the Licensee shall comply with any direction whatsoever that may be given by the TDRA or other competent authority with respect to the property of the Licensee or its use or operation thereof.

### PDPL (UAE-PDPL)

> Article (9) Reporting Personal Data Breach
> 1. In addition to the obligations of the Controller stipulated in this Decree by Law, the Controller shall, at the time it becomes aware of the existence of any breach or violation of Personal Data of the Data Subject that would prejudice the privacy, confidentiality and security of data, notify the Bureau of such breach or violation and the investigation rights within the period and in accordance with the measures and requirements set by the Executive Regulations of this Decree by Law, provided that the reporting is accompanied by the following data and documents:
> a. A description of the nature of the breach or violation, its form, causes, approximate number and records.
> b. Details of the appointed Data Protection Officer.
> c. Potential and expected effects of the breach or violation.
> d. Corrective measures and actions taken or suggested by it to confront such violation and reduce its negative impacts.
> e. Documents of the violation and corrective actions taken by it.
> f. Any other requirements required by the Bureau
> 2. In all cases, the Controller shall notify the Data Subject in the event that the violation or breach would prejudice the privacy and confidentiality of the security of his/her Personal Data within the period and in accordance with the measures and requirements set by the Executive Regulations of this Decree by Law. It shall inform him/her of the measures taken by it.
> 3. If the Processor becomes aware of any breach of Personal Data, it shall notify the Controller of such breach as soon as it becomes aware of the same. the Controller shall in turn inform the Bureau in accordance with Clause (1) of this Article.
> 4. After receiving the notification from the Controller, the Bureau shall verify the reasons for the violation to ensure the integrity of the security measures taken, and impose the administrative penalties referred to in Article (26) of this Decree by Law in the event that a violation of its provisions and decisions issued in implementation of it is proven against the Controller or the Processor.

> Article (18) Right to Processing and Automated Processing
> 1. The Data Subject shall have the right to object to any decisions resulting from automated processing, including profiling, particularly those decisions which have legal impact on or adversely affect the Data Subject.
> 2. Notwithstanding Paragraph 1 of this Article, the Data Subject may not object to the decisions resulting from automated processing in the following cases:
> a. If the automated processing is agreed upon under the contract made between the Data Subject and the Controller.
> b. If the automated processing is required under other legislations which are applicable in the State.
> c. If the Data Subject gives prior consent to the automated processing as set out in Article (6) of this Decree by Law.
> 3. The Controller shall adopt appropriate measures to protect the privacy and confidentiality of the Data Subject's Personal Data in the cases referred to in Paragraph 2 of this article and shall not cause any prejudice to the Data Subject's rights.
> 4. The Controller shall include the human element in reviewing automated processing decisions at the request of the Data Subject.

Art 2 (the exclusions are in clause 2, and the banking exclusion is 2(f)). Item numbering is verbatim from the portal:

> Article (2) Scope of Application of the Decree by Law
> 1.Provisions of this Decree by Law shall apply to the processing of all or part of the Personal Data by means of electronic systems which operate automatically, or by other means, by the following:
> 2.Each Data Subject residing in the State or having a place of business in it.
> b.Each Controller or Processor residing in the State and carrying out the activities of processing Personal Data of Data Subjects inside and outside the State.
> c.Each Controller or Processor residing outside the State and carrying out the activities of processing Personal Data of Data Subjects inside the State.
> 2.Provisions of this Decree by Law shall not apply to the following:
> a.Government Data
> b.Governmental entities which control or process Personal Data.
> c.Personal Data held by the security and judicial authorities
> d.A Data Subject who processes his/her data for personal purposes.
> e.Personal Health Data that has legislation regulating its protection and processing.
> f.Personal banking and credit data and information that have legislation regulating their protection and processing.
> g.Companies and establishments located in free zones in the Country and have special legislations regarding Personal Data protection.

> Article (22) Cross-Border Transfer and Sharing of Personal Data for Processing Purposes if a Proper Protection Level is Available
> Personal Data may be transferred to outside of the State in the following cases approved by the Bureau:
> 1. The State or Province to which the Personal Data is transferred shall have legislations addressing Personal Data Protection. This includes most significant provisions, measures, controls, stipulations and rules related to the protection of the privacy and confidentiality of the Date Subject's Personal Data, and his/her ability to exercise their legal rights. The State or the Province shall also have a judicial o regulatory authority imposing appropriate measures against the Controller or the Processor.
> 2. If the State joins a bilateral or multilateral agreement related to the protection of Personal Data concluded with countries to which the Personal Data is transferred.

> Article (23) Cross-Border Transfer and Sharing of Personal Data for Processing Purposes if a Proper Protection Level is not Available
> 1. Notwithstanding Article (22) of this Decree by Law, Personal Data may be transferred to outside the State in the following cases:
> a. Companies, operating in countries where there are no laws for Data Protection, may transfer data under a contract or agreement obligating the companies in such countries to adopt measures, controls and requirements set out in this Decree by Law, in addition to provisions forcing the Controller or the Processor to adopt appropriate measures which are imposed by a judicial or regulatory authority in such countries as set out in the contract.
> b. If there is an explicit consent granted by the Data Subject to transfer his/her Personal Data outside the State, provided that such transfer shall not contradict the public or security interest of the State.
> c. If the transfer is necessary to fulfil obligations and establish rights before judicial entities, exercise or defend the same.
> d. If the transfer is necessary to sign or implement a contract made between the Controller and the Data Subject, or between the Controller and third parties to serve the interest of the Data Subject.
> e. If the transfer is necessary to implement an action related to an international judicial cooperation.
> f. If the transfer is necessary to protect the public interest.
> 2. The Executive Regulations of this Decree by Law set forth the controls and stipulations referred to in Paragraphs (1) of this Article, which should be observed during the transfer of data outside the State.

### CPR v2.0 (UAE-TDRA-CPR-2)

Each requested clause is shown with its parent clause for context. "35" in 24.6 is a footnote marker.

> 4.15. The following conditions shall apply in circumstances where a Service is purchased at a Licensee’s business centre:

> 4.15.2. the Licensee shall verify the identity of the Subscriber;

> 4.17. The following conditions shall apply in circumstances where a Service is purchased via a telephone call to/from a Licensee’s call centre:

> 4.17.1. the Licensee shall verify the identity of the Subscriber;

> 20.11. The following conditions shall apply in circumstances where an Additional Service is purchased via a telephone call to/from a Licensee’s call centre:

> 20.11.1. the Licensee shall verify the identity of the Subscriber by asking the relevant security questions, or by following such other procedures used by the Licensee for identification purposes;

> 24.1. In the event of any inconsistency between any of the provisions of this Article 24 and any of the provisions of the Data Protection Law the provisions of the DPL shall prevail to the extent necessary to remove any such inconsistency.

> 24.6. Licensees must obtain a Subscriber’s prior consent 35 before sharing any Subscriber Information with its affiliates and/or other third parties not directly involved in the provision of the telecommunications services ordered by the Subscriber.

> 25.14. Licensees shall waive the charges for directory enquiries in circumstances where:
> 25.14.1. the Consumer’s enquiry is processed by an artificial intelligence assistance (AIA); and
> 25.14.2. the AIA could not return the requested telephone number.

### Telecom law (UAE-TEL-LAW)

These articles give TDRA its functions and powers:
- Art 12: oversight of the sector and Licensees
- Art 13: objectives
- Art 14: power to issue regulations, items 1 to 23
- Art 10(a): Board competences, including issuing, extending, suspending and cancelling licences
- Art 81 BIS: judicial-officer capacity for Authority staff

> Article (12)
> The Authority is responsible for overseeing the telecommunications sector and Licensees in accordance with this Decree-Law and its implementing regulations and the directives issued by the High Committee. The Authority shall make appropriate recommendations to the High Committee about the general policy of the sector. At the end of each financial year the Authority shall submit to the High Committee a report on its activities during the preceding year.

> Article (14)
> Subject to provisions of the law, TDRA shall have the power to issue regulations, orders, resolutions and procedures in relation to the following:
> 1. Tariff, charges and fees levied by licensees as determined by the Board of Directors.
> 2. The Interconnection of and access to Telecommunication Networks and Telecommunication Services provided by the licensees, and the co-location of assets and sharing of infrastructure by such licensees, including the terms, conditions and prices of such Interconnection, access, co-location and sharing, the time-scales and rules for the negotiation and finalization between such operators of agreements in relation to the foregoing matters and the dispute resolution policies between the parties to such agreements.
> 3. The terms, level and scope of services provided by the licensees to users, including the standards and quality of service provided, the terms and conditions of supply of such services, the handling and resolution of user complaints and disputes, the provision of information to users, the use of user information and provision of bills to users.
> 4. Regulation and preservation of competition in telecommunication sector without prejudice to applicable laws and regulations.

Emergencies: no article of the law mentions emergencies, disasters or crises; I searched for "emergenc", "disaster" and "crisis". The nearest provision is Art 10(a)(3):

> 3. Issue any general guidelines or instructions related to the Telecommunication Sector, based upon the requirements of the national security or international relations, after being approved by the Cabinet.

The Executive Order (UAE-TEL-EXEC) does mention emergency cases, in Art 11(7):

> Article (11)
> The Authority may issue regulations, instructions, resolutions and rules to achieve the following:
> 7. the Licensees provisioning with free of charge Telecommunication Services in emergency cases;

### NCEMA 7000

I did not obtain the 2021 edition, so I cannot answer for it. In the 2012 edition (UAE-NCEMA-7000-2012, HISTORICAL) I found no clause that sets a reporting or notification deadline in hours or days, and no duty to report to NCEMA. The closest clauses:

> 8.9.4 Spread BCM awareness among external stakeholders. The entity shall notify its suppliers and beneficiaries of their responsibilities to meet the requirements to achieve BC and communicate BC documents, as appropriate.

> A.9.2.1 Reviewing the supplier’s BC status and ensuring it is acceptable to the entity; Integrating its Incident Management procedures with the supplier, to ensure there is a formal process for timely notification by either party in the event of a disruption; Implementing acceptable levels of cost effective resilience into the business operations to mitigate failure of the third-party; and

> Where a local or federal government has established an Authority to oversee activities in a particular sector, there shall be a Crisis and Emergency Response Plan tailored to such Sector and implemented by the leading body in it. For instance, the Telecommunications Regulatory Authority is responsible for developing a Telecom Business Continuity plan in the UAE.
