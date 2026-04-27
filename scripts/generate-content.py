#!/usr/bin/env python3
"""
generate-content.py — Website-side Hugo content generator.

Reads artifacts/full-catalog.json (produced by the registry) and writes:
  - content/pax/<name>/index.md       (Hugo content pages)
  - content/constructs/<id>/index.md  (Hugo construct detail pages)
  - data/registry.json                (from artifacts/registry.json)
  - static/registry.json              (from artifacts/registry.json)
  - data/constructs.json              (from artifacts/constructs.json)
  - static/pax/*.pax.tar.gz           (from artifacts/pax/)
"""

import json
import os
import re
import shutil
import sys
import tarfile
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT    = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = Path(os.environ.get("PAX_ARTIFACTS_DIR", REPO_ROOT / "artifacts"))
CONTENT_DIR  = REPO_ROOT / "content" / "pax"
CONSTRUCTS_CONTENT_DIR = REPO_ROOT / "content" / "constructs"
PLAYBOOKS_CONTENT_DIR  = REPO_ROOT / "content" / "playbooks"
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
# Construct page generation
# ---------------------------------------------------------------------------

def slugify_construct_id(construct_id: str) -> str:
    """Convert a construct id to a clean URL slug (lowercase, underscores→hyphens)."""
    slug = construct_id.lower()
    slug = slug.replace("_", "-")
    # Strip any characters that aren't alphanumeric, hyphens, or dots
    slug = re.sub(r"[^a-z0-9\-.]", "", slug)
    # Collapse consecutive hyphens
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug


def generate_construct_pages(constructs: dict):
    """Write content/constructs/{id}/index.md for every construct in constructs.json."""
    CONSTRUCTS_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Build set of valid slugs for pruning
    valid_slugs = set()
    for construct_id in constructs:
        slug = slugify_construct_id(construct_id)
        if slug:
            valid_slugs.add(slug)

    # Prune stale construct dirs not present in current data
    removed = 0
    for child in CONSTRUCTS_CONTENT_DIR.iterdir():
        if child.is_dir() and child.name not in valid_slugs:
            shutil.rmtree(child)
            removed += 1
    if removed:
        print(f"Pruned {removed} stale construct dirs from {CONSTRUCTS_CONTENT_DIR}")

    written = 0
    skipped = 0
    for construct_id, c in constructs.items():
        slug = slugify_construct_id(construct_id)
        if not slug:
            print(f"  SKIP: construct id '{construct_id}' produced empty slug", file=sys.stderr)
            skipped += 1
            continue

        is_bridge = (c.get("pack_count", 0) >= 2)
        # Lower weight = higher priority; bridges sort before single-pax constructs
        weight = 100 if is_bridge else 200

        packs_list = []
        for p in c.get("packs", []):
            packs_list.append({
                "pack": p.get("pack", ""),
                "pack_title": p.get("pack_title", ""),
                "direction": p.get("direction", None) or None,
                "finding_count": p.get("finding_count", 0),
            })

        fm = {
            "title": c.get("display_name", construct_id),
            "construct_id": construct_id,
            "display_name": c.get("display_name", construct_id),
            "definition": c.get("definition", ""),
            "aliases": c.get("aliases", []),
            "pack_count": c.get("pack_count", 0),
            "packs": packs_list,
            "is_bridge": is_bridge,
            "weight": weight,
        }
        # Include construct_type if available
        if c.get("construct_type"):
            fm["construct_type"] = c["construct_type"]

        out_dir = CONSTRUCTS_CONTENT_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        lines = ["---"]
        lines.append(yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).strip())
        lines.append("---")
        lines.append("")
        (out_dir / "index.md").write_text("\n".join(lines))
        written += 1

    print(f"Wrote {written} construct pages to {CONSTRUCTS_CONTENT_DIR}")
    if skipped:
        print(f"Skipped {skipped} constructs with unslugifiable ids")


# ---------------------------------------------------------------------------
# Playbook page generation
# ---------------------------------------------------------------------------

def slugify_playbook_id(playbook_id: str) -> str:
    """Convert a playbook id to a clean URL slug (same rules as construct slugs)."""
    slug = playbook_id.lower()
    slug = slug.replace("_", "-")
    slug = re.sub(r"[^a-z0-9\-.]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug


def extract_playbook_steps(pax_slug: str, playbook_id: str) -> list:
    """Extract and normalize step data from the pax archive for a given playbook.

    Returns a list of normalized step dicts, or an empty list if the archive
    or playbook YAML is unavailable.
    """
    archive_path = STATIC_DIR / "pax" / f"{pax_slug}.pax.tar.gz"
    if not archive_path.exists():
        print(f"  WARNING: archive not found: {archive_path}", file=sys.stderr)
        return []

    member_path = f"playbooks/{playbook_id}.yaml"
    try:
        with tarfile.open(archive_path, "r:gz") as tf:
            try:
                f = tf.extractfile(member_path)
            except KeyError:
                print(f"  WARNING: {member_path} not found in {archive_path.name}", file=sys.stderr)
                return []
            if f is None:
                return []
            raw = yaml.safe_load(f.read().decode("utf-8"))
    except Exception as exc:
        print(f"  WARNING: could not read {archive_path.name}: {exc}", file=sys.stderr)
        return []

    if not isinstance(raw, dict):
        return []

    raw_steps = raw.get("steps", [])
    if not isinstance(raw_steps, list):
        return []

    normalized = []
    for s in raw_steps:
        if not isinstance(s, dict):
            continue
        # Determine op_type and op_name
        if "action" in s:
            op_type = "action"
            op_name = s["action"]
        elif "engine" in s:
            op_type = "engine"
            op_name = s["engine"]
        else:
            op_type = "action"
            op_name = s.get("id", "")

        depends_on = s.get("depends_on", [])
        if depends_on is None:
            depends_on = []

        normalized.append({
            "step": s.get("step", len(normalized) + 1),
            "id": s.get("id", ""),
            "display_name": s.get("display_name", s.get("id", "")),
            "op_type": op_type,
            "op_name": op_name,
            "depends_on": depends_on,
            "params": s.get("params", {}),
            "expected_results": s.get("expected_results", {}),
            "on_failure": s.get("on_failure", ""),
            "compare_to_kb": bool(s.get("compare_to_kb", False)),
        })

    return normalized


def generate_playbook_pages(catalog: list):
    """Write content/playbooks/{pax-slug}--{playbook-slug}/index.md for every playbook."""
    PLAYBOOKS_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Build set of valid combined slugs for pruning
    valid_slugs = set()
    for pack in catalog:
        pax_slug = pack["name"]
        for pb in pack.get("playbooks_detail", []):
            pb_slug = slugify_playbook_id(pb.get("id", ""))
            if pb_slug:
                combined = f"{pax_slug}--{pb_slug}"
                valid_slugs.add(combined)

    # Prune stale playbook dirs not present in current catalog
    removed = 0
    for child in PLAYBOOKS_CONTENT_DIR.iterdir():
        if child.is_dir() and child.name not in valid_slugs:
            shutil.rmtree(child)
            removed += 1
    if removed:
        print(f"Pruned {removed} stale playbook dirs from {PLAYBOOKS_CONTENT_DIR}")

    written = 0
    skipped = 0
    steps_extracted = 0
    weight = 100

    for pack in catalog:
        pax_slug = pack["name"]
        pax_title = pack.get("title", pax_slug)
        pax_type = pack.get("pax_type", "field")

        for pb in pack.get("playbooks_detail", []):
            pb_id = pb.get("id", "")
            pb_slug = slugify_playbook_id(pb_id)
            if not pb_slug:
                print(f"  SKIP: playbook id '{pb_id}' in '{pax_slug}' produced empty slug", file=sys.stderr)
                skipped += 1
                continue

            combined = f"{pax_slug}--{pb_slug}"
            out_dir = PLAYBOOKS_CONTENT_DIR / combined
            out_dir.mkdir(parents=True, exist_ok=True)

            # Extract step data from archive
            steps = extract_playbook_steps(pax_slug, pb_id)
            if steps:
                steps_extracted += 1

            fm = {
                "title": pb.get("display_name", pb_id),
                "playbook_id": pb_id,
                "display_name": pb.get("display_name", pb_id),
                "description": pb.get("description", ""),
                "estimated_runtime": pb.get("estimated_runtime", ""),
                "step_count": pb.get("step_count", 0),
                "engines_used": pb.get("engines_used", []),
                "parent_pax": pax_slug,
                "parent_pax_title": pax_title,
                "parent_pax_type": pax_type,
                "weight": weight,
            }
            if steps:
                fm["steps"] = steps

            lines = ["---"]
            lines.append(yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).strip())
            lines.append("---")
            lines.append("")
            (out_dir / "index.md").write_text("\n".join(lines))
            written += 1
            weight += 1

    print(f"Wrote {written} playbook pages to {PLAYBOOKS_CONTENT_DIR}")
    print(f"Extracted step data for {steps_extracted}/{written} playbooks")
    if skipped:
        print(f"Skipped {skipped} playbooks with unslugifiable ids")


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

    valid_names = {p["name"] for p in packs}

    # Prune stale content dirs for packs no longer in the catalog
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    removed_content = 0
    for child in CONTENT_DIR.iterdir():
        if child.is_dir() and child.name not in valid_names:
            shutil.rmtree(child)
            removed_content += 1
    if removed_content:
        print(f"Pruned {removed_content} stale content dirs from {CONTENT_DIR}")

    # Write Hugo content pages
    for pack in packs:
        body = generate_body(pack)
        write_content_page(pack, body)
    print(f"Wrote {len(packs)} content pages to {CONTENT_DIR}")

    # Prune stale archives in static/pax/ for packs no longer in the catalog
    static_pax = STATIC_DIR / "pax"
    if static_pax.exists():
        removed_archives = 0
        for archive in static_pax.glob("*.pax.tar.gz"):
            name = archive.name[: -len(".pax.tar.gz")]
            if name not in valid_names:
                archive.unlink()
                removed_archives += 1
        if removed_archives:
            print(f"Pruned {removed_archives} stale archives from {static_pax}")

    # Copy data files
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ("registry.json", "constructs.json"):
        src = ARTIFACTS_DIR / fname
        if src.exists():
            shutil.copy2(src, DATA_DIR / fname)
            print(f"Copied {fname} -> data/")
        else:
            print(f"WARNING: {src} not found, skipping", file=sys.stderr)

    # Generate playbook detail pages
    generate_playbook_pages(packs)

    # Generate construct detail pages
    constructs_path = DATA_DIR / "constructs.json"
    if constructs_path.exists():
        constructs = json.loads(constructs_path.read_text())
        generate_construct_pages(constructs)
    else:
        # Try from artifacts directly
        constructs_src = ARTIFACTS_DIR / "constructs.json"
        if constructs_src.exists():
            constructs = json.loads(constructs_src.read_text())
            generate_construct_pages(constructs)
        else:
            print("WARNING: constructs.json not found, skipping construct pages", file=sys.stderr)

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
