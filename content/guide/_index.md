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

<div style="padding: 1.25rem 1.5rem; background: var(--color-surface); border: 1px solid var(--color-border); border-left: 3px solid var(--color-accent); border-radius: 0.5rem; margin: 1.5rem 0;">
  <p style="font-weight: 600; color: var(--color-text); margin-bottom: 0.25rem;">Create PAX packages with your AI assistant</p>
  <p style="font-size: 0.9rem; color: var(--color-text-muted); margin-bottom: 0.75rem;">Download the full creation guide and feed it to any LLM (ChatGPT, Claude, Gemini, Llama) along with your source material — papers, reports, or internal data — and get a valid PAX out. No Praxis runtime required.</p>
  <a href="/PAX_CREATION_GUIDE.md" download class="download-btn" style="text-decoration: none; font-size: 0.85rem;">Download Creation Guide</a>
  <a href="/PAX_USAGE_GUIDE.md" download style="text-decoration: none; font-size: 0.85rem; padding: 0.75rem 1.5rem; background: var(--color-surface-hover); color: var(--color-text); font-weight: 600; border-radius: 0.5rem; border: 1px solid var(--color-border); margin-left: 0.5rem;">Download Usage Guide</a>
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
schema_version: "2.0"
pax_type: topic                  # paper | topic | field | enterprise | engine
author: "Your Name"
created: "2026-04-09"
license: CC-BY-4.0
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
    "covariates_controlled": ["population", "trade_openness"]
  }
]
```

**Required:** `source_id`, `domain_id`, `finding_text`, `construct_ids`, `direction`
<br>**Always include structured statistics** (effect_size_value, p_value, sample_size) when available. Set to `null` if not reported — never guess.

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
- `schema_version` is `"2.0"`
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

- [Download PAX Creation Guide](/PAX_CREATION_GUIDE.md) — the full v2 spec for building packs. Give this + your source material to any LLM and get a valid PAX out.
- [Download PAX Usage Guide](/PAX_USAGE_GUIDE.md) — how to use a downloaded PAX with any LLM or agent. Give this + a pack to any AI assistant.
- [View creation spec on GitHub](https://github.com/JELambert/praxis/blob/main/docs/PAX_CREATION_GUIDE.md) — browse the full spec online
