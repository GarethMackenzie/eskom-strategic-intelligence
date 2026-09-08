# Eskom Strategic Intelligence
### Municipal Debt • Electricity Demand • Coal Supply-Chain Risk
**Latest non-scenario evidence: 2 September 2026 · Final integrity release · Freshness derived from the governed source register**

---

## 1. Executive Summary

Eskom's FY2026 results, announced 31 August 2026, report a second consecutive annual profit
(R30.3 billion). [FACT] Municipal arrears grew 17.9% to R111.6 billion at year-end and were
reported at R119.9 billion by June 2026. [FACT] Electricity sales volume declined 6.2% to 178 TWh
over the same period, while plant availability (EAF) improved from 60.6% to 65.16%. [FACT] Eskom's
aggregate physical-security crime disclosure (which spans cable, coal, fuel, and several other
categories together, not coal specifically) showed incidents down 13% and estimated losses down
18% to R191 million. [FACT, QUALIFIED] NERSA's revenue path indicates an 8.83% average increase for
FY2027/28, while NERSA's detailed retail tariff structure and customer-category allocation were
under consultation from 2 September 2026.

This report documents what the available evidence supports on each of these three questions,
what it does not yet support, and how superficially similar values with different scopes are kept
separate (Section 4.4). Recommendations are scoped to what current evidence can defend; several
requested analyses (municipality-level debt ranking, segment-level sales decomposition, a
coal-specific crime series) remain open research items, documented in `docs/limitations.md` rather
than filled with estimates.

## 2. Scope

This final integrity release corrects the municipal-debt history and source scopes, establishes a
canonical SQLite-to-Power-BI path, removes hardcoded semantic comparators and strengthens automated
and runtime release gates. See `docs/technical_audit.md`.

## 3. Data and Methodology

See `docs/methodology.md` for the evidence taxonomy and `docs/data_source_register.csv` for every
figure's provenance, now including a `source_tier` column (A1 = direct official document, A2 =
direct official press release, B = secondary reporting of a primary event, C = archival/contextual)
that is kept separate from `originating_entity` — a number originating with Eskom but reported only
by a news outlet is tier B, not tier A, regardless of how accurate it turns out to be.

## 4. Municipal Debt Analysis

**[FACT]** Gross municipal arrear debt grew R17 billion (17.9%) to R111.6 billion at FY2026
year-end, reaching R119.9 billion by June 2026 on Eskom's own in-year disclosure. **[FACT]**
Municipalities represent an estimated 40–44% of Eskom's total electricity sales. **[FACT]** Eskom
excluded R15.8 billion of billed-but-uncollectable revenue from its FY2026 income statement.

### 4.1 A longer view
[FACT] Eskom's official comparable fiscal-year-end series now covers FY2015–FY2026: R5.0bn,
R6.0bn, R9.4bn, R13.6bn, R19.9bn, R28.0bn, R35.3bn, R44.8bn, R58.5bn, R74.4bn, R94.6bn and
R111.6bn. FY2024→FY2025 growth was approximately 27%, followed by 18% in FY2026. The dashboard
derives both YoY change and the FY2015–FY2026 CAGR dynamically from the first, prior and latest
available observations; no comparator value is embedded in DAX.

### 4.2 Concentration
[FACT] A provincial breakdown identifies Mpumalanga (R30.5 billion) and Free State (R29.1 billion)
as the two highest-exposure provinces, per a single secondary source citing an Eskom-reported
figure. This covers 2 of 9 provinces; a complete provincial or municipality-level ranking is not
yet available (Data Gap #1, partially closed).

### 4.3 Debt-relief programme compliance
[FACT] Of 71 municipalities participating in the National Treasury Municipal Debt Relief
Programme, a Parliamentary record (PMG, source-tier A1) indicates 15 have consistently met
programme conditions, while a separate Parliamentary answer reported by MyBroadband indicates 61
were found consistently non-compliant, with National Treasury moving to terminate persistent
defaulters. [FACT] A written Parliamentary reply from the Minister of Finance states that
debt-relief participants accumulated R47.173 billion in *new* arrears since April 2023, despite
participating in a programme intended to reduce old debt. [FACT] National Treasury temporarily
withheld quarterly equitable-share transfers from 69 non-compliant municipalities in July 2026.
Taken together, these indicate the debt-relief programme's compliance rate is low relative to its
71 participants, and that participation alone has not prevented further arrears accumulation for a
majority of those municipalities. This is a description of the programme's observed compliance
pattern, not an assessment of the programme's design.

### 4.4 Scope reconciliation: total arrears vs debt-relief approvals
[FACT] The previous release's apparent conflict is resolved. Eskom's CFO testimony of approximately
R74bn (March 2024) and approximately R95bn (March 2025) is consistent with Eskom's exact official
series of R74.4bn and R94.6bn. National Treasury's R55.3bn is the approved legacy-debt amount across
71 Municipal Debt Relief Programme applications, based on the R58.5bn owed at 31 March 2023. It is
not FY2024 total arrears. The data model therefore stores the R55.3bn programme amount separately
and does not retain a false alternate total-arrears series.

### 4.5 Case study — City of Johannesburg / City Power
[FACT] On 17 May 2026, Eskom issued formal notice under the Promotion of Administrative Justice
Act of its intent to interrupt supply over R5.255 billion in accumulated overdue debt. [FACT] On
21 August 2026, following mediation involving the Minister of Electricity and Energy, Eskom
confirmed the debt was settled in full and withdrew the PAJA process. This provides a documented
example of a mediated resolution process for large-municipality disputes; it does not by itself
establish that mediation is the generally effective approach for the debt-relief programme's
broader compliance problem described in Section 4.3, which spans a much larger number of smaller,
more persistently non-compliant municipalities.

**[SCENARIO — Eskom management's stated base case, not a certainty]** Eskom states arrears could
reach approximately R358 billion by FY2031 absent further intervention. No underlying year-by-year
growth model accompanying this figure was located, so it cannot be independently stress-tested; it
is carried in this project as a single terminal value.

## 5. Electricity Sales Analysis

**[FACT]** Total sales fell 6.2% to 178 TWh (from 189.7 TWh). **[FACT]** Revenue rose 4.1% to
R354.7 billion, driven by a NERSA-approved average tariff increase of 12.74% for direct customers
and 11.32% for municipal bulk purchases effective FY2026 — figures now confirmed against NERSA's
own decision document, correcting a Phase 1 error that applied the direct-customer rate uniformly.

**[CALCULATION]** Blended average realised revenue was approximately R1.99/kWh (R354.7bn ÷ 178
TWh); this masks differences across customer categories not yet available at segment level (Data
Gap #2).

**[INTERPRETATION]** Eskom's own commentary attributes the volume decline to smelter curtailments,
mining-sector weakness, and growing self-generation. This project treats these as Eskom's stated
drivers, associated with the observed decline, not independently established as causal absent a
regression-based decomposition this phase does not include.

**[FACT]** Energy Availability Factor rose from 60.6% to 65.16% over the same period sales fell.
**[INTERPRETATION]** Producing more reliable capacity for a shrinking customer base raises a
fixed-cost recovery question, which is one plausible reading of why Eskom has concurrently pursued
large-customer demand initiatives described below; this is offered as one interpretation among
others, not a proven single explanation.

**[FACT — evidence-supported existing interventions]** NERSA approved concessionary pricing
(62c/kWh) for two ferrochrome smelter operators effective June 2026, and Eskom has a separate
agreement with Manganese Metal Company. These are Eskom's own commercial responses; this project's
contribution is describing their observable characteristics (targeted, price-sensitive, large
industrial loads), not originating the strategy.

### 5.1 Tariff path and the 8.83% regulatory update

**[FACT]** The implemented FY2026/27 averages are 8.76% for Eskom direct customers from 1 April
2026 and 9.01% for municipal bulk purchases from 1 July 2026. **[FACT, QUALIFIED]** NERSA's MYPD6
settlement/re-determination path indicates an 8.83% estimated average price increase for FY2027/28,
intended from 1 April 2027 and subject to the Regulatory Clearing Account qualification recorded
in the regulator's statement. NERSA's official 2 September 2026 document placed the detailed
retail tariff structural adjustment and allocation across customer categories under consultation.

The dashboard therefore separates three concepts: approved/implemented FY2026/27 averages, the
FY2027/28 average revenue path, and the pending customer-category structure. It does not present
8.83% as every customer's final bill increase. The baseline-100 cumulative index is an arithmetic
illustration of the published average paths only; it is not a bill forecast.

## 6. Coal Supply-Chain Risk Analysis

**[FACT — scope-critical]** Eskom's FY2026 aggregate physical-security disclosure (incidents down
13%, losses down 18% to R191 million, arrests up 18% to 505, recoveries up 38% to R34 million, 13
convictions) spans cable theft, coal theft, coal diversion, fuel-oil theft, illegal connections,
meter tampering, ghost vending, vandalism and sabotage together. **No coal-specific subtotal is
published.** Two individually-sourced cases located in this project (a fuel-oil theft at Camden
Power Station and a valve theft at Tutuka Power Station) are both non-coal, which indicates the
absence of a sourced coal-specific example in this project's research to date — not that coal
incidents are absent from Eskom's operations. Eskom's own procurement of specialist coal/fuel-crime
investigators (reported by the Sunday Times, single-sourced) names coal theft, diversion, and
quality manipulation as current, named risk categories.

**Case register.** Both sourced cases remain at "Arrest" status in this project's records; no
source located in this pass confirms subsequent charge, conviction, or sentencing for either case.
This is reported as the current known state, not as evidence those cases will not progress further.

**Risk framework.** A conceptual risk taxonomy (Supplier, Transport, Coal Quality, Delivery
Variance, Incident History, Geographic, Control Effectiveness) is documented in
`docs/data_model.md` based on the categories Eskom itself names. No composite score is calculated:
doing so without loss-weighted, category-level incident data would manufacture precision the
evidence does not support.

## 7. Cross-Cutting Findings

1. Municipalities represent a large share of Eskom's revenue base (40–44%) and are the primary
   source of arrears growth — these are two views of a related customer-concentration exposure,
   not two independent problems.
2. Plant-performance improvement (EAF) and volume decline occurred concurrently in FY2026; this
   project treats their relationship as associative, pending a causal analysis this phase does not
   include.
3. Eskom's aggregate security-crime metrics improved in FY2026, but the category most frequently
   discussed publicly as a priority risk (coal) is the one not separately disclosed in that
   improvement — a gap in transparency at the category level, not necessarily in Eskom's underlying
   security performance.
4. The municipal debt-relief programme shows a pattern of low overall compliance (15 of 71
   consistently compliant per one Parliamentary source) alongside continued new-arrears
   accumulation among participants (R47.173 billion since April 2023) — a programme-design and
   enforcement question this project does not attempt to resolve.

## 8. Strategic Options

For each of the three strategic problems, options are evaluated against what current evidence
actually supports, following the structured recommendation format below (Step 17).

### 8.1 Municipal Debt

| Field | Detail |
|---|---|
| **Problem** | Rising municipal arrears (R111.6bn, +17.9% YoY) with low debt-relief programme compliance (15/71 consistently compliant) |
| **Evidence** | Sections 4.1–4.3; DS001, DS002, DS023, DS031–DS033 |
| **Recommendation** | Extend the equitable-share-withholding and DAA (Distribution Agency Agreement) mechanisms already in use for a subset of municipalities, prioritised by an exposure × compliance-history scoring approach, rather than treating all 71 programme participants uniformly |
| **Evidence classification** | Analytically supported recommendation (the mechanisms are evidence-supported existing interventions per DS033/DS023; the prioritisation approach is this project's proposal) |
| **Expected mechanism** | Concentrating limited Treasury/Eskom intervention capacity on the highest-exposure, most persistently non-compliant municipalities, rather than spreading effort evenly |
| **Expected impact direction** | Reduction in new-arrears accumulation rate among prioritised municipalities (direction only; no monetary benefit is modelled, since no per-municipality cost/benefit data exists) |
| **Implementation difficulty** | High — requires municipality-level data this project does not have (Data Gap #1) |
| **Dependencies** | Closing Data Gap #1 (municipality-level arrears + compliance history) |
| **Risk** | Prioritisation without complete municipality-level data could misallocate attention |
| **Owner/stakeholder** | National Treasury / Eskom Distribution / Department of Electricity and Energy |
| **Time horizon** | Medium-term (requires data infrastructure before implementation) |
| **Success KPI** | New-arrears accumulation rate among prioritised municipalities, tracked quarterly |
| **Data required** | Municipality-level arrears, payment history, DAA/programme status (Data Gap #1) |
| **Confidence level** | Medium — mechanism is evidence-supported; prioritisation logic is untested |

### 8.2 Declining Demand

| Field | Detail |
|---|---|
| **Problem** | 6.2% sales decline concurrent with improving plant availability |
| **Evidence** | Section 5; DS006, DS012, DS025 |
| **Recommendation** | Continue and monitor the effectiveness of negotiated large-customer pricing agreements (already in place per DS025) using a defined before/after volume-retention metric per customer |
| **Evidence classification** | Evidence-supported existing intervention (the agreements exist); the monitoring framework is this project's proposal |
| **Expected mechanism** | Retaining price-sensitive industrial load that would otherwise self-generate or curtail, protecting fixed-cost recovery |
| **Expected impact direction** | Positive for volume retention among covered customers; effect on overall 178 TWh base not separately quantifiable without segment data (Data Gap #2) |
| **Implementation difficulty** | Low (agreements already exist) for monitoring; the underlying negotiation strategy is already Eskom's own |
| **Dependencies** | Segment-level sales data to measure effectiveness (Data Gap #2) |
| **Risk** | Concessionary pricing to large customers could be perceived as cross-subsidised by other tariff classes without transparent reporting |
| **Owner/stakeholder** | Eskom Commercial/Key Accounts, NERSA (approval authority) |
| **Time horizon** | Short-term for monitoring setup; ongoing thereafter |
| **Success KPI** | Volume retention rate for large-customer agreement participants vs. a comparable non-participant cohort |
| **Data required** | Segment/customer-level sales volumes (Data Gap #2) |
| **Confidence level** | Low-Medium — mechanism is plausible and Eskom has acted on it, but no outcome data yet exists to confirm effectiveness |

### 8.3 Coal Supply-Chain Risk

| Field | Detail |
|---|---|
| **Problem** | No coal-specific incident/loss series exists despite coal being named as a current priority risk category |
| **Evidence** | Section 6; DS014–DS018 (aggregate), DS019, DS026–DS028 |
| **Recommendation** | Disaggregate the existing physical-security KPI disclosure by category (at minimum: coal vs. all-other) in future reporting periods |
| **Evidence classification** | Proposal requiring pilot/testing (this is a reporting-transparency recommendation, not a security-operations recommendation this project is qualified to make) |
| **Expected mechanism** | Category-level disclosure would allow the specific "is coal theft increasing or decreasing" question to be answered directly rather than inferred from an aggregate that includes seven other categories |
| **Expected impact direction** | Improves external analytical capability and public accountability; no direct effect on the underlying crime rate is claimed |
| **Implementation difficulty** | Depends on Eskom's internal incident-classification system already supporting this breakdown (unknown — not assessed) |
| **Dependencies** | Internal Eskom data systems (not something this project can verify from public sources) |
| **Risk** | None identified from a data-integrity standpoint; a security-operations risk assessment is outside this project's scope |
| **Owner/stakeholder** | Eskom Security & Group Risk, potentially SAPS/Hawks coordination bodies (NATJOINTS) |
| **Time horizon** | Next annual reporting cycle |
| **Success KPI** | Presence of a category-disaggregated physical-security disclosure in the FY2027 results |
| **Data required** | None additional — this is a disclosure-format recommendation, not a data-collection one |
| **Confidence level** | Low — this project cannot confirm whether Eskom already collects this data internally and simply doesn't disclose it, or doesn't collect it at this granularity at all |

## 9. Implementation Roadmap

Ordered by dependency: (1) retrieve a complete municipality-level arrears and payment-history
dataset for full Data Gap #1 closure; (2) retrieve a sales-by-category table for Data Gap #2;
(3) search SAPS/Hawks, SIU and Portfolio Committee disclosures for coal-specific security data;
(4) extend the long-run electricity-sales and EAF series; and (5) publish to an authorised Power BI
Service workspace only if a browser-interactive report and permission model are required.

## 10. KPI Framework
See `docs/kpi_dictionary.md`.

## 11. Risks and Limitations
See `docs/limitations.md`. The municipal-debt history and R55.3bn scope defect are closed. Granular
municipality, customer-segment and coal-specific security gaps remain, as does long-run sales/EAF
history. The estimated 2-3 GW surplus-capacity statement remains contextual rather than a live KPI.

## 12. Data Gaps
See `docs/limitations.md`.

## 13. Sources
See `docs/data_source_register.csv` — 40 entries as of this release review, each with a
`source_tier` distinct from `originating_entity`.
