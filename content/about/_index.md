---
title: "About PAX Marketplace"
description: "PAX (Portable Analytical eXpertise) packages give your AI structured, evidence-backed domain knowledge — for researchers, analysts, data scientists, and business strategists alike."
---

## What is PAX?

**PAX** (Portable Analytical eXpertise) is a portable knowledge package you can load into any AI assistant to give it structured, evidence-backed expertise in a specific domain.

Think of a PAX pack as the difference between asking your AI "what do you know about income inequality?" versus giving it a curated briefing built from real research — with specific statistics, named methodologies, traceable sources, and analysis workflows ready to run.

PAX works for any domain where evidence matters: academic research, business analytics, policy analysis, data science, epidemiology, economics, political science, and more. Packs are designed to be composable — constructs connect across domains, so expertise built for one pack reinforces another.

Each pack bundles:

- **Constructs** — the key concepts in the domain, defined precisely so they connect theory, data, and analysis
- **Findings** — empirical results with specific statistics, effect sizes, and methodological notes
- **Sources** — the papers, datasets, and reports the findings trace back to
- **Analysis workflows** — step-by-step analytical methods, not just knowledge

---

## How to Use a Pack

### Quick Start — works with any AI, no setup required

1. Find a pack in the marketplace and click **Download**
2. Extract the archive and open the included `llm-context.md` file
3. Paste the contents into your AI assistant (ChatGPT, Claude, Gemini — any will work)
4. Your AI now has structured domain expertise backed by real research

That's it. No installation, no accounts, no configuration. A pack in your context window is a meaningful upgrade over asking a general-purpose AI about a topic from scratch.

---

### Create and Share — contribute your own expertise

Have deep knowledge in a domain? PAX gives it structure and makes it shareable.

1. Read the [pack creation guide](/guide/) to understand the format
2. Build your pack from your own research, domain knowledge, or literature review
3. Upload at [submit.pax-market.com](https://submit.pax-market.com)
4. After review, your pack goes live on the marketplace

No coding required. If you can organize your knowledge into constructs and findings, you can publish a pack.

---

### Full System — Praxis MCP server for power users

[Praxis](https://github.com/JELambert/praxis) is an open-source MCP server that integrates PAX packs directly into AI agent workflows. For analysts and researchers who want automated pipelines:

- Import packs directly into Praxis
- Run cross-pack gap analysis and synthesis
- Execute playbooks as structured, multi-step analytical workflows
- Build and publish new packs programmatically

```
praxis_import_pax("pack-name.pax.tar.gz", install=True)
```

Praxis is the right choice if you're running repeated analysis workflows, working across many packs simultaneously, or building AI-assisted research infrastructure.

---

## PAX Types

| Type | Scope | Example |
|------|-------|---------|
| **Paper** | A single study, fully decomposed — constructs, findings, methods, and sources from one paper | `fearon-laitin-2003` |
| **Topic** | Multiple studies on a focused research question | `happiness-economics` |
| **Field** | Comprehensive coverage of an entire research field | `economic-growth-panel` |
| **Engine** | An analytical method — regression, survival analysis, causal inference, ML — packaged for reuse | `survival-analysis` |
| **Enterprise** | A business or industry domain (private, not published on the marketplace) | — |

---

## Why PAX?

When you ask a general-purpose AI about a research domain, you get prose summaries — averaged, sometimes wrong, impossible to trace back to a source. PAX is different:

- **Structured statistics, not summaries** — findings include specific effect sizes, confidence intervals, sample sizes, and methods, not paraphrased claims
- **Traceable to sources** — every finding links to the paper or dataset it came from, so you can verify and go deeper
- **Constructs that travel** — the same construct (say, "state capacity" or "credit risk score") can appear in multiple packs, and Praxis uses that to synthesize across domains
- **Workflows, not just knowledge** — analysis playbooks turn expertise into repeatable, executable steps

The goal is AI that reasons from evidence, not AI that sounds plausible.

---

## Contributing

Anyone can submit a pack. If you have domain expertise — in any field — you can package it and share it with the marketplace.

- **Create a pack**: Follow the [creation guide](/guide/) to structure your knowledge
- **Submit for review**: Upload at [submit.pax-market.com](https://submit.pax-market.com)
- **Praxis users**: Publish directly with `praxis_publish_pax()` or open a pull request on [GitHub](https://github.com/JELambert/pax-market)

Packs go through a review before publication to verify structure and source quality. The goal is a marketplace where every pack genuinely improves what an AI can do with it.
