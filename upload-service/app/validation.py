"""Pack validation logic — mirrors .github/workflows/validate-pack.yml exactly."""

import json
from pathlib import Path

import yaml

from .models import ValidationResult
from .security import validate_pack_name

REQUIRED_MANIFEST = ["name", "version", "description", "pax_type", "schema_version"]
VALID_TYPES = ["paper", "topic", "field", "engine", "enterprise"]
VALID_SCHEMA_VERSIONS = ["1.0", "2.0"]


def validate_manifest(manifest: dict) -> tuple[list[str], list[str]]:
    """Validate pax.yaml contents. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_MANIFEST:
        if not manifest.get(field):
            errors.append(f"Missing required field: {field}")

    pax_type = manifest.get("pax_type")
    if pax_type and pax_type not in VALID_TYPES:
        errors.append(f"Invalid pax_type: {pax_type}. Must be one of: {', '.join(VALID_TYPES)}")

    sv = str(manifest.get("schema_version", ""))
    if sv and sv not in VALID_SCHEMA_VERSIONS:
        errors.append(f"Unrecognized schema_version: {sv}. Must be one of: {', '.join(VALID_SCHEMA_VERSIONS)}")

    return errors, warnings


def validate_knowledge_json(knowledge_dir: Path) -> tuple[list[str], list[str]]:
    """Validate JSON files in knowledge/. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not knowledge_dir.is_dir():
        return errors, warnings

    for json_file in knowledge_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"knowledge/{json_file.name}: invalid JSON: {e}")
            continue

        # Quality check: warn on empty constructs
        if json_file.name == "constructs.json":
            if isinstance(data, list) and len(data) == 0:
                warnings.append("No constructs defined in constructs.json")

    return errors, warnings


def validate_pack(pack_root: Path) -> ValidationResult:
    """Full validation of a pack directory. Returns structured result."""
    errors: list[str] = []
    warnings: list[str] = []
    pack_name = None

    # Must have pax.yaml
    manifest_path = pack_root / "pax.yaml"
    if not manifest_path.exists():
        errors.append("Missing pax.yaml manifest")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    # Parse manifest
    try:
        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)
    except Exception as e:
        errors.append(f"Invalid pax.yaml: {e}")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    if not isinstance(manifest, dict):
        errors.append("pax.yaml must be a YAML mapping")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    pack_name = manifest.get("name")

    # Validate pack name format
    if pack_name:
        name_error = validate_pack_name(pack_name)
        if name_error:
            errors.append(name_error)

    # Validate manifest fields
    m_errors, m_warnings = validate_manifest(manifest)
    errors.extend(m_errors)
    warnings.extend(m_warnings)

    # Validate knowledge JSON files
    knowledge_dir = pack_root / "knowledge"
    k_errors, k_warnings = validate_knowledge_json(knowledge_dir)
    errors.extend(k_errors)
    warnings.extend(k_warnings)

    # Validate playbook YAML files if present
    playbooks_dir = pack_root / "playbooks"
    if playbooks_dir.is_dir():
        for pb_file in playbooks_dir.glob("*.yaml"):
            try:
                with open(pb_file) as f:
                    yaml.safe_load(f)
            except Exception as e:
                errors.append(f"playbooks/{pb_file.name}: invalid YAML: {e}")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        pack_name=pack_name,
    )
