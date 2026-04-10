#!/usr/bin/env python3
"""
generate-content.py — Website-side Hugo content generator.

Reads artifacts/full-catalog.json (produced by the registry) and writes:
  - content/pax/<name>/index.md  (Hugo content pages)
  - data/registry.json           (from artifacts/registry.json)
  - static/registry.json         (from artifacts/registry.json)
  - data/constructs.json         (from artifacts/constructs.json)
  - static/pax/*.pax.tar.gz      (from artifacts/pax/)
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT    = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = Path(os.environ.get("PAX_ARTIFACTS_DIR", REPO_ROOT / "artifacts"))
CONTENT_DIR  = REPO_ROOT / "content" / "pax"
DATA_DIR     = REPO_ROOT / "data"
STATIC_DIR   = REPO_ROOT / "static"


# ---------------------------------------------------------------------------
# Hugo content generation (extracted from generate-from-git.py)
# ---------------------------------------------------------------------------

def generate_body(pack: dict) -> str:
    sections = []

    domain = pack.get("domain")
    if domain and domain.get("display_name"):
        parts = [f"**Domain:** {domain['display_name']}"]
        if domain.get("description"):
            parts.append(f"\n{domain['description']}")
        meta = []
        if domain.get("temporal_scope"):
            meta.append(f"**Temporal scope:** {domain['temporal_scope']}")
        if domain.get("population"):
            meta.append(f"**Population:** {domain['population']}")
        if meta:
            parts.append("\n" + " | ".join(meta))
        sections.append("\n".join(parts))

    findings = pack.get("findings_detail", [])
    if findings:
        lines = ["## Key Findings", ""]
        for f in findings[:8]:
            text = f.get("finding_text", "")
            if text:
                meta_parts = [p for p in [f.get("direction"), f.get("confidence")] if p]
                suffix = f" *({', '.join(meta_parts)})*" if meta_parts else ""
                lines.append(f"- {text}{suffix}")
        if len(findings) > 8:
            lines.append(f"\n*...and {len(findings) - 8} more findings*")
        sections.append("\n".join(lines))

    props = pack.get("propositions_detail", [])
    if props:
        lines = ["## Theoretical Propositions", ""]
        for p in props:
            text = p.get("proposition_text", "")
            if text:
                arrow = {"positive": "+", "negative": "−", "null": "∅"}.get(p.get("direction", ""), "→")
                lines.append(f"- [{arrow}] {text}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def write_content_page(pack: dict, body: str):
    out_dir = CONTENT_DIR / pack["name"]
    out_dir.mkdir(parents=True, exist_ok=True)

    year = 0
    created = pack.get("created", "")
    if created:
        ym = re.search(r'(\d{4})', str(created))
        if ym:
            year = int(ym.group(1))

    fm = {k: v for k, v in pack.items() if k not in ("download_sha256",)}
    fm["pax_name"] = pack["name"]
    fm["weight"] = 10000 - year

    lines = ["---"]
    lines.append(yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).strip())
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body)
        lines.append("")
    (out_dir / "index.md").write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    catalog_path = ARTIFACTS_DIR / "full-catalog.json"
    if not catalog_path.exists():
        print(f"ERROR: {catalog_path} not found", file=sys.stderr)
        sys.exit(1)

    packs = json.loads(catalog_path.read_text())
    print(f"Loaded {len(packs)} packs from {catalog_path}")

    # Write Hugo content pages
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    for pack in packs:
        body = generate_body(pack)
        write_content_page(pack, body)
    print(f"Wrote {len(packs)} content pages to {CONTENT_DIR}")

    # Copy data files
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ("registry.json", "constructs.json"):
        src = ARTIFACTS_DIR / fname
        if src.exists():
            shutil.copy2(src, DATA_DIR / fname)
            print(f"Copied {fname} -> data/")
        else:
            print(f"WARNING: {src} not found, skipping", file=sys.stderr)

    # Copy registry.json to static/ as well
    reg_src = ARTIFACTS_DIR / "registry.json"
    if reg_src.exists():
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reg_src, STATIC_DIR / "registry.json")
        print("Copied registry.json -> static/")

    # Copy tar.gz archives from artifacts/pax/ to static/pax/
    artifacts_pax = ARTIFACTS_DIR / "pax"
    static_pax = STATIC_DIR / "pax"
    if artifacts_pax.exists():
        static_pax.mkdir(parents=True, exist_ok=True)
        count = 0
        for archive in artifacts_pax.glob("*.pax.tar.gz"):
            shutil.copy2(archive, static_pax / archive.name)
            count += 1
        print(f"Copied {count} archives -> static/pax/")
    else:
        print(f"WARNING: {artifacts_pax} not found, no archives copied", file=sys.stderr)

    print("Done.")


if __name__ == "__main__":
    main()
