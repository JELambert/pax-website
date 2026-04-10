# PAX Usage Guide — For Any LLM or Agent

> **What is this?** A generic guide for using any Praxis PAX (Portable Analytical eXpertise) package. Feed this document + a downloaded PAX to any LLM or agent, and it can reason over the knowledge, synthesize findings, and — if code-capable — run analyses.
>
> **Companion to:** `PAX_CREATION_GUIDE.md` (how to *build* a PAX). This guide is how to *use* one.

---

## What's in a PAX?

A PAX is a directory of YAML and JSON files containing structured domain knowledge. Every PAX follows the same structure:

```
my-pax-name/
├── pax.yaml                           # Manifest — what this PAX covers
├── knowledge/
│   ├── domain.json (or domains.json)  # Research domain definition(s)
│   ├── constructs.json                # Variables and concepts
│   ├── sources.json                   # Papers, datasets, other references
│   ├── findings.json                  # Empirical claims with statistics
│   ├── propositions.json              # Theoretical claims (optional)
│   └── construct_relationships.json   # Causal/correlational links (optional)
└── playbooks/
    └── quick_start.yaml               # Reproducible analysis workflow (optional)
```

---

## Understanding Each File

### `pax.yaml` — The Manifest

Tells you what this PAX is about. Key fields:
- `name`: unique identifier (kebab-case)
- `description`: what the PAX covers
- `pax_type`: paper (single study), topic (multiple papers), field (whole discipline), enterprise (business domain)
- `provides`: lists of all construct IDs, source IDs, finding IDs in the package

### `knowledge/constructs.json` — The Building Blocks

An array of **constructs** — the atomic concepts, variables, and measures in this domain. Each has:

| Field | What It Tells You |
|-------|-------------------|
| `id` | Unique identifier (snake_case) |
| `display_name` | Human-readable name |
| `construct_type` | quantifiable, concept, process, composite, or outcome |
| `definition` | What this construct means |
| `formal_definition` | Precise academic definition (if available) |
| `operational_definition` | How it's actually measured in practice |
| `measurement_level` | nominal, ordinal, interval, or ratio |
| `aliases` | Alternative names and abbreviations |
| `measures` | How it's operationalized (specific instruments/data sources) |

**How to use constructs:** These are your vocabulary. When reasoning about the domain, use these construct IDs to connect findings, relationships, and propositions. If you're asked about something not in the construct list, say so — it may be a gap.

### `knowledge/sources.json` — Where the Knowledge Comes From

An array of papers, datasets, and other references. Each has:

| Field | What It Tells You |
|-------|-------------------|
| `id` | Source identifier (author_year pattern) |
| `title` | Full title |
| `authors`, `year`, `doi` | Citation metadata |
| `methodology_summary` | How the study was conducted |
| `sample_size` | N |
| `study_design` | rct, quasi_experimental, observational_longitudinal, etc. |
| `key_limitations` | Known weaknesses |
| `replication_status` | replicated, failed_replication, not_attempted, unknown |

**How to use sources:** When citing findings, always reference the source. Use `methodology_summary` and `study_design` to assess evidence quality. Note limitations when they affect the finding's reliability.

### `knowledge/findings.json` — What We Know

An array of **findings** — specific empirical claims linking constructs. This is the most important file. Each finding has:

| Field | What It Tells You |
|-------|-------------------|
| `finding_text` | Natural language description of the claim |
| `construct_ids` | Which constructs are involved |
| `direction` | positive, negative, null, conditional, unknown |
| `confidence` | strong, moderate, weak, foundational, unknown |
| `effect_size` | Narrative summary of the effect |
| `method_used` | Statistical method and sample |

**Structured statistics** (when available — use these for precise reasoning):

| Field | What It Tells You |
|-------|-------------------|
| `effect_size_value` | Numeric coefficient (β, OR, r, d, etc.) |
| `effect_size_se` | Standard error of the estimate |
| `p_value` | Statistical significance |
| `sample_size` | N for this specific finding |
| `r_squared` | Model fit (R²) |
| `ci_lower`, `ci_upper` | Confidence interval bounds |
| `effect_size_type` | What kind of effect: beta, odds_ratio, hazard_ratio, correlation_r, cohens_d |
| `model_specification` | Full model description |
| `covariates_controlled` | What was controlled for |

**How to use findings:**
- Group by construct pair to see consensus/contradiction
- Weight by confidence level and sample size
- Note null findings (direction="null") — non-significance IS evidence
- Use structured statistics for precise comparisons when available

### `knowledge/propositions.json` — What Theory Says

Formal theoretical claims linking two constructs. Each has:
- `proposition_text`: the claim itself
- `construct_from` / `construct_to`: cause → effect
- `direction`: positive, negative, conditional, contested
- `theoretical_basis`: which theory supports this
- `scope_conditions`: when/where this holds

**How to use propositions:** These are the theoretical framework. Compare propositions to findings — does the evidence support the theory? Where are the gaps between what theory predicts and what evidence shows?

### `knowledge/construct_relationships.json` — The Causal Map

Explicit relationships between constructs:
- `construct_from` → `construct_to`
- `relationship_type`: causal, correlational, mediating, moderating, compositional
- `mechanism`: how/why the relationship operates
- `strength`: strong, moderate, weak

**How to use relationships:** These form a causal graph. Trace pathways from predictors to outcomes. Identify mediators and moderators. When asked "how does X affect Y?", follow the relationship chain and cite the mechanisms.

### `playbooks/*.yaml` — Analysis Recipes

Reproducible analysis workflows with steps like:
- Correlation matrices
- Regression models
- Data quality checks
- Expected results and validation criteria

**How to use playbooks:** See Tier 2 (code-capable agents) below for execution instructions.

---

## Tier 1: Knowledge Synthesis (Any LLM, No Code)

These tasks require only reading and reasoning over the JSON files. Any LLM can do them.

### Evidence Synthesis

**Prompt:** "Based on this PAX's findings, what does the evidence say about [construct X]?"

**How to answer:**
1. Find all findings where `construct_ids` includes the target construct
2. Group by direction (positive, negative, null)
3. Weight by confidence level (strong > moderate > weak)
4. Note the methods used and sample sizes
5. Flag contradictions where findings disagree
6. Cite sources for each claim

### Gap Identification

**Prompt:** "What are the knowledge gaps in this PAX?"

**How to answer:**
1. Find constructs that appear in no findings → unmeasured concepts
2. Find construct pairs in `construct_relationships` with no corresponding findings → untested relationships
3. Find propositions with no supporting findings → unvalidated theories
4. Check for constructs with only one source → single-study evidence
5. Look for constructs with weak/unknown confidence only → uncertain areas

### Causal Chain Analysis

**Prompt:** "Trace the causal pathway from [A] to [B]"

**How to answer:**
1. Start with construct A in `construct_relationships`
2. Follow outgoing relationships until you reach B
3. At each link, cite the mechanism and supporting findings
4. Note the strength of each link (strong/moderate/weak)
5. Identify the weakest link in the chain

### Evidence Comparison

**Prompt:** "Does [external claim] agree with this PAX's evidence?"

**How to answer:**
1. Identify which constructs the claim involves
2. Find all relevant findings in the PAX
3. Compare the claimed direction and magnitude against findings
4. Note whether the claim's methodology is similar to the PAX's sources
5. Assess whether scope conditions match

### Meta-Level Assessment

**Prompt:** "How mature is the evidence in this PAX?"

**How to answer:**
1. Count findings by confidence level
2. Count constructs with vs. without findings
3. Check replication_status of sources (replicated > not_attempted)
4. Assess methodological diversity (multiple study_design types = stronger)
5. Note the temporal range (old findings may be outdated)

---

## Tier 2: Running Analyses (Code-Capable Agents)

If your agent can execute Python (Claude Code, OpenAI Codex, Google Gemini with code), you can set up a local database and run playbook analyses.

### Step 1: Set Up SQLite Database

```python
import sqlite3
import json

conn = sqlite3.connect("pax_knowledge.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Create tables
c.executescript("""
CREATE TABLE IF NOT EXISTS constructs (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    construct_type TEXT,
    definition TEXT,
    formal_definition TEXT,
    operational_definition TEXT,
    measurement_level TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    source_type TEXT,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER,
    methodology_summary TEXT,
    sample_size INTEGER,
    study_design TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    domain_id TEXT,
    finding_text TEXT NOT NULL,
    construct_ids TEXT,
    direction TEXT,
    effect_size TEXT,
    confidence TEXT,
    effect_size_value REAL,
    effect_size_se REAL,
    p_value REAL,
    sample_size INTEGER,
    r_squared REAL,
    effect_size_type TEXT,
    model_specification TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS construct_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    construct_from TEXT,
    construct_to TEXT,
    relationship_type TEXT,
    direction TEXT,
    strength TEXT,
    mechanism TEXT
);

CREATE TABLE IF NOT EXISTS propositions (
    id TEXT PRIMARY KEY,
    proposition_text TEXT,
    construct_from TEXT,
    construct_to TEXT,
    direction TEXT,
    theoretical_basis TEXT,
    scope_conditions TEXT
);
""")
```

### Step 2: Load Knowledge Files

```python
def load_json(path):
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

# Load constructs
for c in load_json("knowledge/constructs.json"):
    conn.execute(
        "INSERT OR IGNORE INTO constructs (id, display_name, construct_type, definition, "
        "formal_definition, operational_definition, measurement_level) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (c["id"], c["display_name"], c.get("construct_type"),
         c.get("definition"), c.get("formal_definition"),
         c.get("operational_definition"), c.get("measurement_level"))
    )

# Load sources
for s in load_json("knowledge/sources.json"):
    conn.execute(
        "INSERT OR IGNORE INTO sources (id, source_type, title, authors, year, "
        "methodology_summary, sample_size, study_design) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (s["id"], s.get("source_type"), s["title"], s.get("authors"),
         s.get("year"), s.get("methodology_summary"),
         s.get("sample_size"), s.get("study_design"))
    )

# Load findings
for f in load_json("knowledge/findings.json"):
    cids = f.get("construct_ids", [])
    if isinstance(cids, list):
        cids = ",".join(cids)
    conn.execute(
        "INSERT INTO findings (source_id, domain_id, finding_text, construct_ids, "
        "direction, effect_size, confidence, effect_size_value, effect_size_se, "
        "p_value, sample_size, r_squared, effect_size_type, model_specification) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (f.get("source_id"), f.get("domain_id"), f["finding_text"], cids,
         f.get("direction"), f.get("effect_size"), f.get("confidence"),
         f.get("effect_size_value"), f.get("effect_size_se"),
         f.get("p_value"), f.get("sample_size"), f.get("r_squared"),
         f.get("effect_size_type"), f.get("model_specification"))
    )

# Load relationships
import os
if os.path.exists("knowledge/construct_relationships.json"):
    for r in load_json("knowledge/construct_relationships.json"):
        conn.execute(
            "INSERT INTO construct_relationships (construct_from, construct_to, "
            "relationship_type, direction, strength, mechanism) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (r["construct_from"], r["construct_to"], r["relationship_type"],
             r.get("direction"), r.get("strength"), r.get("mechanism"))
        )

# Load propositions
if os.path.exists("knowledge/propositions.json"):
    for p in load_json("knowledge/propositions.json"):
        conn.execute(
            "INSERT OR IGNORE INTO propositions (id, proposition_text, construct_from, "
            "construct_to, direction, theoretical_basis, scope_conditions) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (p["id"], p["proposition_text"], p.get("construct_from"),
             p.get("construct_to"), p.get("direction"),
             p.get("theoretical_basis"), p.get("scope_conditions"))
        )

conn.commit()
print(f"Loaded: {conn.execute('SELECT COUNT(*) FROM constructs').fetchone()[0]} constructs, "
      f"{conn.execute('SELECT COUNT(*) FROM findings').fetchone()[0]} findings, "
      f"{conn.execute('SELECT COUNT(*) FROM sources').fetchone()[0]} sources")
```

### Step 3: Query the Knowledge Base

```python
# Find all findings about a specific construct
def findings_for(construct_id):
    return conn.execute(
        "SELECT * FROM findings WHERE construct_ids LIKE ?",
        (f"%{construct_id}%",)
    ).fetchall()

# Get the causal graph
def causal_graph():
    return conn.execute(
        "SELECT construct_from, construct_to, relationship_type, direction, strength, mechanism "
        "FROM construct_relationships"
    ).fetchall()

# Evidence consensus for a construct pair
def consensus(construct_a, construct_b):
    rows = conn.execute(
        "SELECT direction, confidence, effect_size_value, source_id "
        "FROM findings WHERE construct_ids LIKE ? AND construct_ids LIKE ?",
        (f"%{construct_a}%", f"%{construct_b}%")
    ).fetchall()
    return rows
```

### Step 4: Run Playbook Analyses

Playbooks are YAML files with analysis steps. Each step specifies an engine and parameters.

```python
import yaml

# Load a playbook
with open("playbooks/quick_start.yaml") as f:
    playbook = yaml.safe_load(f)

print(f"Playbook: {playbook.get('display_name', playbook.get('id'))}")
print(f"Steps: {len(playbook.get('steps', []))}")

for step in playbook.get("steps", []):
    print(f"\n--- Step: {step.get('display_name', step.get('id'))} ---")
    engine = step.get("engine", step.get("action"))
    params = step.get("params", {})
    print(f"Engine: {engine}")
    print(f"Params: {params}")
    expected = step.get("expected_results", {})
    if expected:
        print(f"Expected: {expected}")
```

**Running a correlation matrix:**
```python
import pandas as pd
import numpy as np

# Get findings with numeric effect sizes for a set of constructs
constructs_of_interest = params.get("variables", [])

# Query findings
findings_data = []
for cid in constructs_of_interest:
    rows = findings_for(cid)
    for r in rows:
        if r["effect_size_value"] is not None:
            findings_data.append({
                "construct": cid,
                "effect_size": r["effect_size_value"],
                "source": r["source_id"],
                "direction": r["direction"],
            })

if findings_data:
    df = pd.DataFrame(findings_data)
    print(df.groupby("construct")["effect_size"].describe())
```

**Running a regression (if you have raw data):**
```python
# If the PAX includes data or you've downloaded it:
import statsmodels.api as sm

# Example: OLS regression
outcome = params.get("outcome")
predictors = params.get("predictors", [])

# Load data (from data/ directory or external source)
# data = pd.read_csv("data/cache/your_data.csv")
# X = data[predictors]
# y = data[outcome]
# model = sm.OLS(y, sm.add_constant(X)).fit()
# print(model.summary())
```

### Step 5: Compare Results to KB Findings

After running an analysis, compare your results to the PAX's findings:

```python
def compare_to_kb(your_beta, your_p, construct_a, construct_b):
    """Compare your analysis result to what the KB says."""
    kb_findings = consensus(construct_a, construct_b)
    
    print(f"\nYour result: β={your_beta:.3f}, p={your_p:.4f}")
    print(f"KB has {len(kb_findings)} relevant finding(s):\n")
    
    for f in kb_findings:
        kb_beta = f["effect_size_value"]
        if kb_beta is not None:
            diff = abs(your_beta - kb_beta)
            print(f"  KB: β={kb_beta:.3f} ({f['direction']}, {f['confidence']})")
            print(f"  Δ = {diff:.3f} — {'consistent' if diff < 0.2 else 'DIVERGENT'}")
        else:
            print(f"  KB: {f['direction']} ({f['confidence']}) — no numeric effect size")
```

---

## Common Questions

**Q: How do I know if a PAX is high quality?**
Check: Does it have findings with structured statistics (effect_size_value, p_value)? Are sources well-documented (methodology_summary, study_design)? Does it have construct relationships? Does it have multiple sources? The more of these it has, the richer the PAX.

**Q: Can I combine multiple PAX?**
Yes — if constructs share the same IDs across PAX, their findings can be compared. Load multiple PAX into the same SQLite database. Constructs with the same ID represent the same concept.

**Q: What if a PAX has no playbooks?**
You can still do everything in Tier 1 (knowledge synthesis). For analysis, use the construct definitions and relationships to design your own analysis — the PAX tells you *what to measure* and *what to expect*, even without a playbook.

**Q: What's the relationship between this guide and Praxis?**
Praxis is the full runtime — PostgreSQL, MCP tools, 19 statistical engines, semantic search. This guide enables a lightweight subset using just the knowledge files. For full analytical capability (engine execution, KB comparison, data resolution), install Praxis and use `praxis_install_pax`.

---

## Quick Reference: File → What You Can Do

| File | Tier 1 (No Code) | Tier 2 (Code) |
|------|-------------------|---------------|
| `constructs.json` | Understand the domain vocabulary | Query by type, find gaps |
| `sources.json` | Assess evidence quality | Filter by design, year |
| `findings.json` | Synthesize evidence, find consensus | Statistical comparison, meta-analysis |
| `propositions.json` | Evaluate theoretical claims | Test against findings |
| `construct_relationships.json` | Trace causal chains | Build causal graphs |
| `playbooks/*.yaml` | Understand expected analyses | Execute with pandas/statsmodels |
