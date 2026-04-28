---
title: "PAX Creation Guide"
description: "Everything you need to create and submit a PAX package to the marketplace."
---

## What Is a PAX?

A **PAX** (Portable Analytical eXpertise) is a portable knowledge package that captures everything needed to understand and analyze a domain:

- **Constructs** — the concepts and variables (e.g. `gdp_per_capita`, `civil_war_onset`)
- **Findings** — empirical results with structured statistics
- **Sources** — papers and references with methodology metadata
- **Propositions** — theoretical claims about how constructs relate
- **Playbooks** — reproducible analysis workflows

Anyone can create a PAX from research papers, domain expertise, or business knowledge and submit it to the marketplace.

<div style="padding: 1.25rem 1.5rem; background: var(--pt-panel); border: 1px solid var(--pt-line); border-left: 3px solid var(--term-accent); border-radius: 0; margin: 1.5rem 0;">
  <p style="font-weight: 600; color: var(--pt-ink); margin-bottom: 0.25rem;">Create PAX packages with your AI assistant</p>
  <p style="font-size: 0.9rem; color: var(--pt-dim); margin-bottom: 0.75rem;">Download the full creation guide and feed it to any LLM (ChatGPT, Claude, Gemini, Llama) along with your source material — papers, reports, or internal data — and get a valid PAX out. No Praxis runtime required.</p>
  <a href="/PAX_CREATION_GUIDE.md" download class="t-guide-download-btn">Download Creation Guide</a>
  <a href="/PAX_USAGE_GUIDE.md" download class="t-guide-download-btn" style="margin-left: 0.5rem;">Download Usage Guide</a>
</div>

## PAX Types

| Type | When to Use | Typical Size |
|------|-------------|--------------|
| <span class="badge badge-paper">paper</span> | Single research paper | 5-15 constructs, 4-10 findings, 1 source |
| <span class="badge badge-topic">topic</span> | Research topic spanning multiple papers | 6-30 constructs, 10-50 findings, 3-15 sources |
| <span class="badge badge-field">field</span> | Entire research field | 30-100+ constructs, 50-300+ findings, 20-150 sources |
| <span class="badge badge-enterprise">enterprise</span> | Business/industry domain | 5-20 constructs, variable findings |
| <span class="badge badge-engine">engine</span> | Analytical method package | 0-5 constructs, bundled engines |

**Start with a Paper PAX.** Read one paper, extract its contribution. It's the easiest way to learn the format, and you can build up to topics and fields from there.

## Pack Structure

Every PAX is a directory with this layout:

```
my-pack-name/
  pax.yaml                  # Manifest (required)
  knowledge/
    domain.json             # Domain definition (required)
    constructs.json         # Construct definitions (required)
    sources.json            # Source/paper metadata (required)
    findings.json           # Empirical findings (required)
    propositions.json       # Theoretical claims (recommended)
    construct_relationships.json  # Causal/correlational links (recommended)
    canonical_constructs.json     # Concept declarations (v3, optional)
    construct_relations.json      # Lattice between concepts (v3, optional)
  playbooks/
    quick_start.yaml        # Analysis workflow (recommended)
```

## Key Files

### pax.yaml — The Manifest

Every pack needs a manifest with these required fields:

```yaml
name: my-research-topic          # kebab-case, unique
version: "1.0.0"                 # semantic versioning
description: >
  One to three sentences describing what this PAX covers.
schema_version: "3.0"
pax_type: topic                  # paper | topic | field | enterprise | engine
author: "Your Name"
created: "2026-04-09"
license: ""                      # set per-pack; leave empty if unspecified
tags: [economics, development]
provides:
  constructs: [construct_id_1, construct_id_2]
  sources: [author_year_2024]
  findings: [finding_id_1]
  propositions: []
  playbooks: [quick_start]
  engines: []
```

**Required:** `name`, `version`, `description`, `schema_version`, `pax_type`

### constructs.json — What Concepts Exist

An array of construct objects. Each construct is a distinct variable or concept:

```json
[
  {
    "id": "gdp_per_capita",
    "display_name": "GDP Per Capita",
    "construct_type": "quantifiable",
    "definition": "Gross domestic product divided by total population, measured in constant 2015 USD PPP.",
    "measurement_level": "ratio",
    "aliases": [
      {"alias": "GDP/capita", "alias_type": "abbreviation"},
      {"alias": "per capita income", "alias_type": "synonym"}
    ]
  }
]
```

**Required:** `id` (snake_case), `display_name`, `construct_type`, `definition`
<br>**construct_type:** `quantifiable`, `concept`, `process`, `composite`, `outcome`

### findings.json — What We Know

Each finding is ONE specific empirical claim:

```json
[
  {
    "source_id": "author_year_2024",
    "domain_id": "my_domain",
    "finding_text": "GDP per capita is positively associated with life expectancy (beta=0.42, SE=0.08, p<0.001, N=1200).",
    "construct_ids": ["gdp_per_capita", "life_expectancy"],
    "direction": "positive",
    "confidence": "strong",
    "method_used": "OLS regression with country fixed effects",
    "effect_size_value": 0.42,
    "effect_size_se": 0.08,
    "p_value": 0.001,
    "sample_size": 1200,
    "effect_size_type": "beta",
    "model_specification": "OLS with country and year FE, clustered SE",
    "covariates_controlled": ["population", "trade_openness"],
    "unit_of_analysis": "country_year",
    "sample_n": 1200,
    "scope_conditions": "OECD members, 1990-2020"
  }
]
```

**Required:** `source_id`, `domain_id`, `finding_text`, `construct_ids`, `direction`
<br>**Always include structured statistics** (effect_size_value, p_value, sample_size) when available. Set to `null` if not reported — never guess.
<br>**v3 fields:** `unit_of_analysis` is a controlled vocabulary (e.g. `country_year`, `firm_quarter`, `individual`, `dyad_year`) — see the full creation guide for the complete list. `sample_n` and `scope_conditions` document the analytic sample.

### sources.json — Where We Learned It

```json
[
  {
    "id": "author_year_2024",
    "source_type": "academic_paper",
    "title": "The Full Paper Title",
    "authors": "Last, First; Last2, First2",
    "year": 2024,
    "doi": "10.1234/example",
    "methodology_summary": "Panel regression with country/year FE, N=1200",
    "sample_size": 1200,
    "study_design": "observational_longitudinal"
  }
]
```

### domain.json — The Research Domain

```json
{
  "id": "my_domain",
  "display_name": "My Research Domain",
  "description": "What this domain covers in one to three sentences.",
  "temporal_scope": "1990-present",
  "population": "Countries worldwide",
  "level_of_analysis": "macro"
}
```

## Construct Backbone (v3)

PAX v3 distinguishes **conceptual constructs** (what you are trying to measure) from **operationalizations** (the specific coding rule used to measure it). Two papers that both measure "civil war onset" using different battle-death thresholds — UCDP's 25 vs. Fearon & Laitin 2003's 1000 — are operationalizing the same concept differently. They should share a `canonical_id` and each declare its own `operationalization_id`.

This is the mechanism that lets cross-PAX bridges work as **identity** rather than name-matching. Without canonical_id, two PAX that both define `civil_war_onset` end up as two unrelated rows in the constructs table — Praxis cannot tell they refer to the same concept. With it, both rows point at `concept:civil_war_onset` and Praxis can answer "what does the literature say about civil war onset?" across every installed PAX.

### Worked example: FL2003

```json
{
  "id": "civil_war_onset",
  "display_name": "Civil War Onset",
  "construct_type": "outcome",
  "definition": "Binary indicator of whether a country-year saw the start of a civil war.",
  "canonical_id": "concept:civil_war_onset",
  "operationalization_id": "op:civil_war_onset.fl2003_1000_deaths",
  "coding_rule": "First country-year with cumulative battle-related deaths >= 1000, deaths concentrated in one country, government as one combatant, organized armed opposition, at least 100 deaths on each side."
}
```

A second PAX modeling the same concept with UCDP's threshold would declare:

```json
{
  "id": "civil_war_onset",
  "canonical_id": "concept:civil_war_onset",
  "operationalization_id": "op:civil_war_onset.ucdp_25_deaths",
  "coding_rule": "First country-year with >= 25 battle-related deaths in a state-based armed conflict (UCDP/PRIO definition)."
}
```

Both rows point at the same `concept:civil_war_onset` canonical, so findings across the two PAX can be aligned even though their measurement thresholds differ.

### New optional knowledge files

- **`canonical_constructs.json`** — declares concepts this PAX defines (or extends). Required if you reference a `canonical_id` that does not yet exist in the registry.
- **`construct_relations.json`** — declares typed relations between canonicals (e.g. `causes`, `refines`, `measures`, `composed_of`). Enables lattice/pathway queries across PAX.

### Minting governance

If you declare a `canonical_id` that doesn't exist yet, Praxis runs cosine similarity against existing canonicals to catch near-duplicates. Above 0.80 similarity, the mint is rejected unless you re-call with `force=True` and a written `justification` (logged to a governance audit trail). Below 0.70 the mint proceeds. Existing v2 PAX without `canonical_id` continue to work unchanged — the field is opt-in.

For the full reference (field rules, `refines` semantics, `PRAXIS_ALLOW_PROVISIONAL_CANONICALS`, the Concept vs. Operationalization deep-dive), see the [Creation Guide download](#downloadable-guides).

## ID Conventions

| Entity | Format | Example |
|--------|--------|---------|
| PAX name | kebab-case | `democratic-peace` |
| Domain | snake_case | `transnational_repression` |
| Construct | snake_case | `gdp_per_capita` |
| Source | author_year | `fearon_laitin_2003` |
| Playbook | snake_case | `quick_start` |

## Validation Checklist

Before submitting, verify:

- `name` is kebab-case and unique
- `version` is semver (e.g. `1.0.0`)
- `schema_version` is `"3.0"`
- `pax_type` is one of: paper, topic, field, enterprise, engine
- All JSON files are valid JSON
- Every `construct_id` referenced in findings exists in constructs.json
- Every `source_id` referenced in findings exists in sources.json
- Finding text is at least 20 characters and describes ONE specific claim
- Null findings included (`direction: "null"`) for non-significant results
- Structured statistics populated when available (not guessed)

## How to Submit

1. **Create** your PAX following the structure above
2. **Zip** the pack directory: `zip -r my-pack.zip my-pack-name/`
3. **Upload** at [submit.pax-market.com](https://submit.pax-market.com) (sign in with GitHub)
4. **Validation** runs automatically — you'll see errors immediately if something's wrong
5. **Review** — we check for quality, then merge
6. **Live** — your pack appears on the marketplace within minutes of merge

## Downloadable Guides

Feed these to any LLM to create or use PAX packages:

- [Download PAX Creation Guide](/PAX_CREATION_GUIDE.md) — the full v3 spec for building packs. Give this + your source material to any LLM and get a valid PAX out.
- [Download PAX Usage Guide](/PAX_USAGE_GUIDE.md) — how to use a downloaded PAX with any LLM or agent. Give this + a pack to any AI assistant.
- [View creation spec on GitHub](https://github.com/JELambert/praxis/blob/main/docs/PAX_CREATION_GUIDE.md) — browse the full spec online
