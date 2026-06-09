#!/usr/bin/env python3
"""Validate all registered skills by reading skill_registry.yaml.

Reads each skill's `path` from the registry, discovers its validate script
at `{path}/scripts/validate_skill.py`, and runs them all.  Skills without
a validate script are reported as warnings, not errors.
"""
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)


WORKSPACE = Path(__file__).resolve().parents[1]
REGISTRY = WORKSPACE / "touyan-ontology-production-agent" / "skill_registry.yaml"

# The core spec has its own validator, not registered as a task skill
CORE_VALIDATOR = "spec/投研本体核心规范/scripts/validate_core.py"


def load_registry(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def discover_validators(registry: dict) -> list[tuple[str, Path]]:
    """Return list of (label, absolute_path) for every validator found."""
    validators: list[tuple[str, Path]] = []

    # Core spec validator
    core_path = WORKSPACE / CORE_VALIDATOR
    if core_path.exists():
        validators.append((CORE_VALIDATOR, core_path))

    # Task skill validators from registry
    skills = registry.get("skills", {})
    for _key, entry in skills.items():
        skill_dir = entry.get("path", "")
        script_path = WORKSPACE / skill_dir / "scripts" / "validate_skill.py"
        if script_path.exists():
            validators.append((f"{skill_dir}/scripts/validate_skill.py", script_path))

    return validators


def main():
    if not REGISTRY.exists():
        print(f"Registry not found: {REGISTRY}", file=sys.stderr)
        raise SystemExit(2)

    registry = load_registry(REGISTRY)
    validators = discover_validators(registry)

    if not validators:
        print("No validators discovered.", file=sys.stderr)
        raise SystemExit(1)

    print(f"Discovered {len(validators)} validator(s)\n")

    failures = []
    for label, path in validators:
        print(f"==> {label}")
        result = subprocess.run([sys.executable, str(path)], cwd=WORKSPACE)
        if result.returncode != 0:
            failures.append((label, f"exit {result.returncode}"))

    # Report skills in registry that lack a validate script
    skills = registry.get("skills", {})
    for key, entry in skills.items():
        skill_dir = entry.get("path", "")
        script_path = WORKSPACE / skill_dir / "scripts" / "validate_skill.py"
        if not script_path.exists():
            print(f"[warn] {skill_dir}: no validate_skill.py found (skipped)")

    if failures:
        print("\nvalidation failed:")
        for label, reason in failures:
            print(f"- {label}: {reason}")
        raise SystemExit(1)

    print("\nall touyan ontology skill validators passed")


if __name__ == "__main__":
    main()
