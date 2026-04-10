# PAX v2 Specification & Creation Guide

> **Schema version:** 2.0 — Last updated: 2026-04-09
>
> This document is the canonical specification for PAX v2. All future PAX schema changes are documented here. For v1→v2 migration context, see `docs/adr/ADR-007-pax-v2-schema-evolution.md`.

## What Is This Document?

A self-contained guide for creating Praxis PAX (Portable Analytical eXpertise) packages. You can:

1. **Feed it to any LLM** (ChatGPT, Claude, Gemini, Llama) with source material → get a valid PAX out
2. **Use it as a spec** to build PAX tooling in any language
3. **Validate PAX packages** against the schema and checklist below

**No Praxis runtime required.** This guide produces static files (YAML + JSON). The output can be validated offline, then imported into any Praxis instance or published to the [PAX Marketplace](https://pax-market.com).

---

## What Is a PAX?

A PAX is a portable knowledge package that captures everything needed to understand and analyze a domain — academic, business, or applied:

- **What concepts exist** (constructs with formal/operational definitions)
- **What we know** (findings with structured statistics)
- **Where we learned it** (sources with methodology metadata)
- **How concepts relate** (construct relationships)
- **What theories say** (propositions with scope conditions)
- **How to analyze it** (playbooks — reproducible analysis workflows)

### PAX Types

| Type | When to Use | Typical Size | Example |
|------|-------------|--------------|---------|
| `paper` | Single research paper | 5-15 constructs, 4-10 findings, 1 source | Fearon & Laitin (2003) on civil war onset |
| `topic` | Research topic spanning multiple papers | 6-30 constructs, 10-50 findings, 3-15 sources | Democratic peace theory |
| `field` | Entire research field or comprehensive body of work | 30-100+ constructs, 50-300+ findings, 20-150 sources | Bartel computational materials science (142 papers) |
| `enterprise` | Business/industry domain | 5-20 constructs, variable findings, internal + external sources | SaaS customer churn prediction |
| `engine` | Analytical method package (no domain knowledge) | 0-5 constructs, bundled Python engines | Bayesian regression methods |

**Paper PAX** — Start here. Read one paper, extract its contribution. Good for building up a topic incrementally.

**Topic PAX** — Synthesize multiple papers on a theme. Requires cross-paper construct alignment and often has propositions that span sources.

**Field PAX** — Comprehensive coverage of a researcher's body of work or an entire subdiscipline. Usually built by extending a topic PAX repeatedly. May have sub-domains with `parent_domain_id`.

**Enterprise PAX** — Business analytics domain. Uses the same schema but constructs are often KPIs, findings come from internal analyses, and playbooks encode business-relevant workflows.

---

## Output Structure

Produce the following files:

```
my-pax-name/
├── pax.yaml                           # Manifest (required)
├── knowledge/
│   ├── domain.json                    # Domain definition (required)
│   ├── constructs.json                # Construct definitions (required)
│   ├── sources.json                   # Source/paper metadata (required)
│   ├── findings.json                  # Empirical findings (required)
│   ├── propositions.json              # Theoretical claims (recommended)
│   └── construct_relationships.json   # Causal/correlational links (recommended)
└── playbooks/
    └── quick_start.yaml               # Analysis workflow (recommended)
```

---

## Step-by-Step Extraction Protocol

### Step 1: Classify Your Input

Read the source material and determine:
- **PAX type**: paper (single paper), topic (multiple papers on a theme), field (comprehensive coverage), enterprise (business domain)
- **Method type(s)**: regression, experimental/RCT, qualitative, theoretical, meta-analysis, descriptive, ML/predictive
- **Unit of analysis**: country-year, individual, firm, dyad, patient, product, customer, etc.
- **Domain scope**: What research field or business area does this cover?

**For a single paper:** Extract exactly what the paper claims.
**For a topic:** Identify the shared constructs across papers, note where findings agree or conflict.
**For a field:** Organize into sub-domains with a parent domain, expect 50+ constructs.
**For enterprise:** Map business metrics to constructs, internal analyses to findings.

### Step 2: Create the Manifest (`pax.yaml`)

```yaml
name: dukalskis-et-al-2024-transnational-repression    # kebab-case, unique
version: "1.0.0"
description: >
  First large-N quantitative study of domestic drivers of transnational
  repression. Tests the hypothesis that authoritarian crackdowns at home
  increase subsequent likelihood of repressing citizens abroad.
schema_version: "2.0"
pax_type: paper          # paper | topic | field | enterprise | engine
author: "Dukalskis, Alexander; Furstenberg, Saipira; Hellmeier, Sebastian; Scales, Redmond"
created: "2024-01-15"
license: CC-BY-4.0
tags: [transnational-repression, authoritarianism, human-rights, V-Dem]
provides:
  constructs:
    - transnational_repression_binary
    - domestic_repression_cli
    - diplomatic_capacity_abroad
    # ... list all construct IDs
  sources:
    - dukalskis_et_al_2024
  findings:
    - dukalskis_2024_finding_0
    - dukalskis_2024_finding_1
    # ... list all finding IDs
  propositions:
    - domestic_crackdown_causes_tr
    - diplomatic_capacity_amplifies_tr
  playbooks:
    - quick_start
  engines: []             # list registered engine IDs the PAX uses
```

**Required fields:** name, version, description, schema_version, pax_type
**pax_type values:**
- `paper` — single paper
- `topic` — research topic (multiple papers)
- `field` — entire research field
- `enterprise` — business/industry domain
- `engine` — analytical method package

### Step 3: Define the Domain (`knowledge/domain.json`)

```json
{
  "id": "transnational_repression",
  "display_name": "Transnational Repression",
  "description": "State repression of citizens beyond national borders — threats, surveillance, abductions, assassinations targeting diaspora and exiles.",
  "temporal_scope": "1991-2019",
  "population": "Authoritarian regimes (88 states, country-year panel)",
  "level_of_analysis": "macro",
  "research_questions": [
    "Does domestic repression predict transnational repression?",
    "What role does diplomatic capacity play in enabling TR?"
  ]
}
```

**Required:** id (snake_case), display_name, description
**level_of_analysis:** micro, meso, macro, cross-level, dyadic

### Step 4: Extract Constructs (`knowledge/constructs.json`)

Constructs are the atomic building blocks — every variable, concept, or measurable thing.

```json
[
  {
    "id": "transnational_repression_binary",
    "display_name": "Transnational Repression (Binary)",
    "construct_type": "outcome",
    "definition": "Binary indicator equal to 1 if an authoritarian state carried out one or more transnational repression events against its own citizens abroad in a given country-year. Source: AAAD database (Dukalskis 2021).",
    "domain_ids": ["transnational_repression"],
    "source_id": "dukalskis_et_al_2024",
    "formal_definition": "TR ∈ {0, 1} where TR=1 iff count of AAAD events > 0 in country-year t.",
    "operational_definition": "Coded from the Authoritarian Actions Abroad Database (AAAD), which records threats, arrests, extraditions, abductions, and assassinations.",
    "measurement_level": "nominal",
    "aliases": [
      {"alias": "TR", "alias_type": "abbreviation"},
      {"alias": "extraterritorial repression", "alias_type": "synonym"}
    ],
    "measures": [
      "AAAD binary indicator (Dukalskis 2021)",
      "Freedom House transnational repression report"
    ]
  },
  {
    "id": "domestic_repression_cli",
    "display_name": "Domestic Repression (V-Dem CLI)",
    "construct_type": "quantifiable",
    "definition": "Inverted V-Dem Civil Liberties Index measuring intensity of domestic state repression. Higher values = more repression. Aggregates physical violence, political civil liberties, and private civil liberties sub-indices. Lagged one year.",
    "domain_ids": ["transnational_repression"],
    "source_id": "dukalskis_et_al_2024",
    "formal_definition": "CLI_inv = 1 - CLI, where CLI is the V-Dem Civil Liberties Index (v2x_civlib).",
    "operational_definition": "V-Dem v12 Civil Liberties Index, inverted so higher = more repressive, lagged t-1.",
    "measurement_level": "interval",
    "aliases": [
      {"alias": "V-Dem civil liberties", "alias_type": "synonym"},
      {"alias": "CLI", "alias_type": "abbreviation"}
    ],
    "measures": ["V-Dem v12 v2x_civlib (inverted, lagged)"]
  }
]
```

**Required:** id (snake_case), display_name, construct_type, definition
**construct_type values:** quantifiable, concept, process, composite, outcome
**Recommended (v2):** formal_definition, operational_definition, measurement_level, aliases, measures

**Rules:**
- One construct per distinct variable or concept
- Definition must be at least one full sentence
- Include how it's measured (operationalization)
- Include aliases (abbreviations, synonyms) for dedup matching
- `measurement_level`: nominal, ordinal, interval, ratio

### Step 5: Register Sources (`knowledge/sources.json`)

```json
[
  {
    "id": "dukalskis_et_al_2024",
    "source_type": "academic_paper",
    "title": "The Long Arm and the Iron Fist: Authoritarian Crackdowns and Transnational Repression",
    "authors": "Dukalskis, Alexander; Furstenberg, Saipira; Hellmeier, Sebastian; Scales, Redmond",
    "year": 2024,
    "doi": "10.1177/00220027231188896",
    "abstract": "Investigates domestic determinants of transnational repression...",
    "methodology_summary": "Country-year panel regression (logistic) with country and year fixed effects, bias-reducing score adjustments (bife package). Robustness: negative binomial, rare events logit, lagged DV.",
    "sample_size": 857,
    "population_description": "88 authoritarian regimes, 1991-2019 (country-year panel)",
    "study_design": "observational_longitudinal",
    "key_limitations": "AAAD captures reported events only (detection bias); excludes digital surveillance; country-year aggregation may miss within-year dynamics",
    "replication_status": "not_attempted",
    "data_availability": "public",
    "journal": "Journal of Conflict Resolution",
    "url": "https://doi.org/10.1177/00220027231188896"
  }
]
```

**Required:** id (snake_case), source_type, title
**source_type values:** academic_paper, journal_article, book, book_chapter, working_paper, report, dataset, manual
**Recommended (v2):** methodology_summary, sample_size, study_design, key_limitations, journal

**study_design values:** rct, quasi_experimental, observational_longitudinal, observational_cross_sectional, case_study, meta_analysis, review, theoretical

### Step 6: Extract Findings (`knowledge/findings.json`)

This is the most critical step. Each finding is ONE specific empirical claim.

```json
[
  {
    "source_id": "dukalskis_et_al_2024",
    "domain_id": "transnational_repression",
    "finding_text": "Domestic repression is positively and significantly associated with subsequent transnational repression: β=1.09, SE=0.20, p<0.001 (logistic regression with country/year FE, N=857). First large-N quantitative confirmation that domestic crackdowns predict TR.",
    "construct_ids": ["transnational_repression_binary", "domestic_repression_cli"],
    "direction": "positive",
    "effect_size": "β=1.09 (SE=0.20), p<0.001 — bivariate logistic with country/year FE",
    "method_used": "logistic regression with country and year fixed effects, bias-reducing score adjustments (bife), N=857",
    "confidence": "strong",
    "finding_type": "empirical",
    "evidence_type": "quantitative",
    "state": "provisional",

    "effect_size_value": 1.09,
    "effect_size_se": 0.20,
    "p_value": 0.001,
    "sample_size": 857,
    "r_squared": null,
    "ci_lower": null,
    "ci_upper": null,
    "effect_size_type": "beta",
    "model_specification": "logistic regression with country and year fixed effects, bias-reducing score adjustments (bife)",
    "covariates_controlled": []
  },
  {
    "source_id": "dukalskis_et_al_2024",
    "domain_id": "transnational_repression",
    "finding_text": "Domestic repression remains significant after full controls: β=0.83, SE=0.26, p<0.01 (Model 2, N=731). Controls: polity score, elections, leader tenure, military dimension, party dimension, population, GDP per capita, state capacity.",
    "construct_ids": ["transnational_repression_binary", "domestic_repression_cli"],
    "direction": "positive",
    "effect_size": "β=0.83 (SE=0.26), p<0.01 — full controls model",
    "method_used": "logistic regression with country/year FE, full controls, N=731",
    "confidence": "strong",
    "finding_type": "empirical",
    "evidence_type": "quantitative",
    "state": "provisional",

    "effect_size_value": 0.83,
    "effect_size_se": 0.26,
    "p_value": 0.01,
    "sample_size": 731,
    "effect_size_type": "beta",
    "model_specification": "logistic regression with country/year FE, bias-reducing score adjustments",
    "covariates_controlled": ["polity_score", "elections", "leader_tenure", "military_dimension", "party_dimension", "population", "gdp_per_capita", "state_capacity"]
  }
]
```

**Required:** source_id, domain_id, finding_text (≥20 chars), construct_ids (≥1), direction
**direction values:** positive, negative, null, conditional, unknown
**confidence values:** strong, moderate, weak, unknown
**finding_type values:** empirical, theoretical, normative, mechanism, methodological
**evidence_type values:** quantitative, qualitative, mixed, theoretical

**Structured Statistics (v2 — ALWAYS populate when available):**

| Field | Type | Description |
|-------|------|-------------|
| effect_size_value | number | The numeric coefficient (β, OR, r, d, HR, etc.) |
| effect_size_se | number | Standard error of the estimate |
| p_value | number | p-value (use 0.001 for p<0.001) |
| sample_size | integer | N for this specific model |
| r_squared | number | Model R² if reported |
| ci_lower | number | Lower bound of confidence interval |
| ci_upper | number | Upper bound of confidence interval |
| effect_size_type | string | What kind: beta, odds_ratio, hazard_ratio, correlation_r, cohens_d, risk_ratio |
| model_specification | string | Full model spec (e.g. "OLS with clustered SE by country") |
| covariates_controlled | array | List of control variable names |

**Set to null if not available. Never guess.**

**Finding Extraction Rules:**
1. 4-10 findings per paper (more for large papers)
2. One specific claim per finding — not a paper summary
3. Include NULL findings (direction="null") — they are as important as significant ones
4. Each finding references exactly the constructs involved (usually 2)
5. `effect_size` (text) is for narrative summary; structured fields are for computation
6. Always specify the method, sample size, and controls

### Step 7: Define Propositions (`knowledge/propositions.json`)

Propositions are theoretical claims — the "why" behind findings.

```json
[
  {
    "id": "domestic_crackdown_causes_tr",
    "proposition_text": "An increase in domestic repression leads to subsequent transnational repression, because crackdowns drive dissidents abroad who become targets, and activate state surveillance of international links.",
    "construct_from": "domestic_repression_cli",
    "construct_to": "transnational_repression_binary",
    "direction": "positive",
    "domain_id": "transnational_repression",
    "source_id": "dukalskis_et_al_2024",
    "theoretical_basis": "Authoritarian survival theory; regime-diaspora threat perception",
    "scope_conditions": "Authoritarian regimes only; lagged effect (t-1 → t); amplified by diplomatic capacity"
  }
]
```

**Required:** id, proposition_text, construct_from, construct_to
**Recommended:** direction, theoretical_basis, scope_conditions

### Step 8: Define Construct Relationships (`knowledge/construct_relationships.json`)

Explicit causal/correlational links between constructs.

```json
[
  {
    "construct_from": "domestic_repression_cli",
    "construct_to": "transnational_repression_binary",
    "relationship_type": "causal",
    "direction": "positive",
    "strength": "strong",
    "mechanism": "Domestic crackdowns drive dissidents abroad and activate state surveillance of international links, increasing TR likelihood.",
    "source_id": "dukalskis_et_al_2024"
  },
  {
    "construct_from": "diplomatic_capacity_abroad",
    "construct_to": "transnational_repression_binary",
    "relationship_type": "moderating",
    "direction": "positive",
    "strength": "moderate",
    "mechanism": "Diplomatic infrastructure provides logistical means to execute TR in host countries, amplifying the domestic repression → TR pathway.",
    "source_id": "dukalskis_et_al_2024"
  }
]
```

**Required:** construct_from, construct_to, relationship_type
**relationship_type values:** causal, correlational, mediating, moderating, compositional
**strength values:** strong, moderate, weak

### Step 9: Create a Playbook (`playbooks/quick_start.yaml`)

A reproducible analysis workflow.

```yaml
id: quick_start
display_name: "Quick Start — Transnational Repression"
description: "Core analysis replicating the main findings."
estimated_runtime: "1-2 minutes"
requires_data: true

steps:
  - id: data_quality_check
    step: 1
    display_name: "Data Quality Gate"
    action: data_quality_gate
    params:
      constructs:
        - transnational_repression_binary
        - domestic_repression_cli
      min_observations: 50
      max_missing_pct: 0.20
    on_failure: abort

  - id: predictor_correlations
    step: 2
    display_name: "Correlations — Key Predictors"
    engine: correlation_matrix
    params:
      variables:
        - transnational_repression_binary
        - domestic_repression_cli
        - diplomatic_capacity_abroad
    expected_results:
      transnational_repression_binary↔domestic_repression_cli:
        direction: positive

  - id: core_logistic
    step: 3
    display_name: "Core Model — Logistic Regression"
    engine: logistic_regression
    depends_on: [predictor_correlations]
    params:
      outcome: transnational_repression_binary
      predictors:
        - domestic_repression_cli
        - diplomatic_capacity_abroad
    compare_to_kb: true
    expected_results:
      domestic_repression_cli:
        direction: positive
```

---

## Validation Checklist

Before submitting your PAX, verify:

### Manifest (`pax.yaml`)
- [ ] `name` is kebab-case (e.g. `my-research-topic`)
- [ ] `version` is semver (e.g. `1.0.0`)
- [ ] `description` is 1-3 sentences
- [ ] `schema_version` is `"2.0"`
- [ ] `pax_type` is one of: paper, topic, field, enterprise, engine
- [ ] `provides` lists all entity IDs from knowledge files

### Domain (`domain.json`)
- [ ] `id` is snake_case
- [ ] `description` is at least one sentence
- [ ] `level_of_analysis` is specified

### Constructs (`constructs.json`)
- [ ] Every construct has a unique snake_case `id`
- [ ] Every `definition` is at least one full sentence (≥10 characters)
- [ ] `construct_type` is one of: quantifiable, concept, process, composite, outcome
- [ ] At least one outcome-type construct exists
- [ ] `domain_ids` references the domain from domain.json
- [ ] Aliases included for common abbreviations/synonyms
- [ ] `measurement_level` specified (nominal/ordinal/interval/ratio)

### Sources (`sources.json`)
- [ ] Every source has a unique snake_case `id` (pattern: `author_year`)
- [ ] `methodology_summary` is filled in
- [ ] `sample_size` is specified
- [ ] `study_design` is one of the valid values

### Findings (`findings.json`)
- [ ] Every finding has `source_id` matching a source in sources.json
- [ ] Every finding has `domain_id` matching the domain
- [ ] Every finding has at least one `construct_id` from constructs.json
- [ ] `finding_text` is ≥20 characters and describes ONE specific claim
- [ ] Null findings included (direction="null") for non-significant results
- [ ] **Structured statistics populated** when available:
  - [ ] `effect_size_value` (the numeric coefficient)
  - [ ] `effect_size_se` (standard error)
  - [ ] `p_value`
  - [ ] `sample_size`
  - [ ] `effect_size_type` specified (beta, odds_ratio, etc.)
  - [ ] `model_specification` describes the full model
  - [ ] `covariates_controlled` lists control variables
- [ ] Fields set to `null` (not omitted) when not available

### Construct Relationships (`construct_relationships.json`)
- [ ] Every relationship references constructs from constructs.json
- [ ] `relationship_type` specified
- [ ] `mechanism` explains how/why

### Cross-File Consistency
- [ ] All `construct_ids` in findings exist in constructs.json
- [ ] All `source_id` values in findings exist in sources.json
- [ ] All construct IDs in relationships exist in constructs.json
- [ ] `provides` in pax.yaml lists all entity IDs

---

## ID Conventions

| Entity | Pattern | Examples |
|--------|---------|----------|
| PAX name | kebab-case | `democratic-peace`, `bartel-comp-materials` |
| Domain | snake_case | `transnational_repression`, `climate_economics` |
| Construct | snake_case | `gdp_per_capita`, `civil_war_onset` |
| Source | author_year | `fearon_laitin_2003`, `dukalskis_et_al_2024` |
| Proposition | snake_case descriptive | `poverty_increases_conflict_risk` |
| Playbook | snake_case | `quick_start`, `full_replication` |

---

## Common Mistakes

1. **Findings that summarize instead of claim.** Bad: "The paper studies X." Good: "X increases Y by β=0.34 (p<0.01, N=500)."
2. **Missing null findings.** If a regression coefficient is not significant, that IS a finding with direction="null".
3. **Constructs without operationalization.** Always say how it's measured, not just what it means.
4. **Effect sizes trapped in prose.** Put β=0.34 in `effect_size_value`, not just in `finding_text`.
5. **Missing covariates.** If the paper controls for GDP, population, etc., list them in `covariates_controlled`.
6. **Forgetting construct relationships.** If the paper tests A→B, create a relationship entry.

---

## Multi-Source Examples by PAX Type

### Topic PAX: Democratic Peace Theory

A topic PAX synthesizes multiple papers. The key challenge is **construct alignment** — different papers may measure the same concept differently.

```yaml
# pax.yaml
name: democratic-peace
pax_type: topic
description: "Why democracies rarely fight each other — regime type, economic interdependence, and international organizations."
```

**Sources:** 5 papers (Doyle 1986, Maoz & Russett 1993, Oneal & Russett 1999, Gartzke 2007, Hegre 2014)
**Constructs:** `joint_democracy` (quantifiable), `mid_onset` (outcome), `trade_interdependence` (quantifiable), `igo_membership_overlap` (quantifiable), `capitalist_peace` (concept)
**Findings:** 15 findings across 5 papers — some agree (democracy reduces MID), some contest (Gartzke: it's capitalism, not democracy)
**Propositions:** "Joint democracy reduces interstate conflict" with scope_conditions="post-1945 dyads"

**Key pattern:** The same construct (`joint_democracy`) appears in multiple sources with different operationalizations. Use `measures` to list them all and `aliases` for variant names.

### Field PAX: Computational Materials Science

A field PAX covers an entire research program. Expect sub-domains.

```json
// domain.json — primary domain
{
  "id": "bartel_comp_materials",
  "display_name": "Bartel Computational Materials Science",
  "description": "ML for property prediction, autonomous synthesis, perovskite stability, battery materials..."
}

// Additional domains with parent linkage:
[
  {"id": "perovskite_stability", "parent_domain_id": "bartel_comp_materials", ...},
  {"id": "battery_materials", "parent_domain_id": "bartel_comp_materials", ...},
  {"id": "autonomous_synthesis", "parent_domain_id": "bartel_comp_materials", ...}
]
```

**Key pattern:** Use `parent_domain_id` to organize sub-domains. Constructs and findings spread across sub-domains. The export system will collect all child domains automatically.

### Enterprise PAX: SaaS Churn

```yaml
name: saas-customer-churn
pax_type: enterprise
description: "Customer churn prediction and retention drivers for B2B SaaS."
```

```json
// constructs.json
[
  {
    "id": "monthly_churn_rate",
    "display_name": "Monthly Churn Rate",
    "construct_type": "outcome",
    "definition": "Percentage of paying customers who cancel or don't renew in a given month.",
    "operational_definition": "Churned customers / total active customers at month start × 100",
    "measurement_level": "ratio",
    "measures": ["Stripe subscription cancellation events", "Manual cancellation tracking in CRM"]
  },
  {
    "id": "feature_adoption_score",
    "display_name": "Feature Adoption Score",
    "construct_type": "quantifiable",
    "definition": "Composite score (0-100) measuring how many core product features a customer actively uses.",
    "operational_definition": "Count of distinct core features used in last 30 days / total core features × 100",
    "measurement_level": "ratio"
  }
]

// findings.json
[
  {
    "source_id": "internal_analysis_2026q1",
    "domain_id": "saas_customer_churn",
    "finding_text": "Feature adoption score > 60% reduces monthly churn by 40% compared to low-adoption cohort.",
    "construct_ids": ["feature_adoption_score", "monthly_churn_rate"],
    "direction": "negative",
    "confidence": "strong",
    "effect_size_value": 0.60,
    "effect_size_type": "odds_ratio",
    "sample_size": 5000,
    "p_value": 0.001,
    "model_specification": "logistic regression with cohort and tenure controls",
    "covariates_controlled": ["customer_tenure_months", "plan_tier", "company_size"]
  }
]
```

**Key pattern:** Enterprise PAX often has `dataset` or `manual` source types and findings from internal analyses rather than published papers.

---

## What Happens Next

Once you have the files:

1. **Validate offline** — Check against the checklist above
2. **Import into Praxis** — Use `praxis_import_pax` or `praxis_install_pax` pointing at the directory
3. **Or publish** — Submit to the PAX marketplace at [pax-market.com](https://pax-market.com)
4. **Agents use it** — Any Praxis-connected agent can install the PAX and immediately run analyses

The PAX is the unit of portable expertise. Build it once, use it everywhere.

---

## Controlled Vocabularies Reference

These are the canonical enum values for all PAX fields. The Praxis codebase parses this section at runtime — changes here propagate automatically to validation, MCP tool schemas, and LLM extraction prompts.

<!-- PAX_SCHEMA_START — do not remove this marker -->

**pax_type values:** paper, topic, field, enterprise, engine

**source_type values:** academic_paper, journal_article, book, book_chapter, working_paper, report, dataset, manual, synthetic

**construct_type values:** quantifiable, concept, process, composite, outcome

**direction values:** positive, negative, null, conditional, unknown

**confidence values:** strong, moderate, weak, foundational, unknown

**finding_type values:** empirical, theoretical, normative, mechanism, methodological

**evidence_type values:** quantitative, qualitative, mixed, theoretical, exploratory

**finding_state values:** provisional, confirmed, contested, superseded, retracted

**level_of_analysis values:** micro, meso, macro, cross-level, dyadic

**measurement_level values:** nominal, ordinal, interval, ratio

**relationship_type values:** causal, correlational, mediating, moderating, compositional

**study_design values:** rct, quasi_experimental, observational_longitudinal, observational_cross_sectional, case_study, meta_analysis, review, theoretical

**effect_size_type values:** beta, odds_ratio, hazard_ratio, risk_ratio, correlation_r, cohens_d, eta_squared

**strength values:** strong, moderate, weak

**alias_type values:** synonym, abbreviation, operationalization

<!-- PAX_SCHEMA_END — do not remove this marker -->

---

## Version History

This document is the canonical PAX specification. All schema changes are recorded here.

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-04-07 | Structured statistics on findings (effect_size_value, SE, p, N, CI, model_spec, covariates). Enriched source metadata (methodology, study_design, sample_size, limitations, replication). Construct provenance (formal/operational definitions, measurement_level, provenance chain). Construct relationships (causal/correlational with mechanism). Engine documentation (parameters, assumptions, diagnostics, interpretation). Playbook enhancements (data quality gates, conditional branching, parameter variants). Quality scoring adds statistical_richness, relationship_coverage, source_depth sub-scores. See ADR-007. |
| 1.0 | 2026-04-05 | Initial PAX format: manifest, domain, constructs (with aliases/measures), sources, findings, propositions, playbooks, engine registry, data sources. |

### Planned for v2.1
- Finding TTL/expiration for business metrics that decay
- Data freshness requirements on playbook steps
- KPI constructs with target_value and threshold fields
- Construct scope (org-specific vs. universal)
