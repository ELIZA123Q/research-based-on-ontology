#!/usr/bin/env python3
"""Apply an ontology optimization delta to a full ontology output."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


CATEGORY_SPECS: dict[str, tuple[str, str, str]] = {
    "source_documents": ("source_documents", "id", "source_document_id"),
    "evidence_claims": ("evidence_claims", "id", "claim_id"),
    "objects": ("objects", "id", "object_id"),
    "relations": ("relations", "id", "relation_id"),
    "state_variables": ("state_variables", "objectId", "object_id"),
    "state_observations": ("state_observations", "objectId", "object_id"),
    "propagation_templates": ("propagation_templates", "objectId", "object_id"),
    "hypotheses": ("hypotheses", "objectId", "object_id"),
    "signals": ("signals", "objectId", "object_id"),
    "events": ("events", "objectId", "object_id"),
    "judgment_outputs": ("judgment_outputs", "objectId", "object_id"),
    "asset_impacts": ("asset_impacts", "objectId", "object_id"),
    "investment_theses": ("investment_theses", "objectId", "object_id"),
    "blocking_conditions": ("blocking_conditions", "objectId", "object_id"),
    "scenario_paths": ("scenario_paths", "objectId", "object_id"),
    "asset_impact_clues": ("asset_impact_clues", "objectId", "object_id"),
    "suggested_actions": ("suggested_actions", "suggestedActionId", "suggested_action_id"),
    "evidence_matrix": ("evidence_matrix", "claim", "claim"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True, help="Full base ontology output or ontology JSON.")
    parser.add_argument("--delta", type=Path, required=True, help="Optimization delta JSON.")
    parser.add_argument("--output", type=Path, required=True, help="Path for merged full output JSON.")
    parser.add_argument("--allow-hash-mismatch", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def extract_ontology(document: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if "optimized_ontology" in document:
        return document["optimized_ontology"], document
    if "ontology_bundle" in document:
        return document["ontology_bundle"], document
    return document, None


def extract_delta(document: dict[str, Any]) -> dict[str, Any]:
    if "optimization_delta" in document:
        return document["optimization_delta"]
    return document


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def index_items(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    return {item[key]: idx for idx, item in enumerate(items) if key in item}


def add_items(ontology: dict[str, Any], category: str, items: list[dict[str, Any]]) -> int:
    path, key, _ = CATEGORY_SPECS[category]
    target = ontology.setdefault(path, [])
    index = index_items(target, key)
    changed = 0
    for item in items:
        item_key = item.get(key)
        if not item_key:
            raise ValueError(f"added_{category} item missing key {key}")
        if item_key in index:
            raise ValueError(f"added_{category} duplicates existing item: {item_key}")
        target.append(deepcopy(item))
        index[item_key] = len(target) - 1
        changed += 1
    return changed


def update_items(ontology: dict[str, Any], category: str, items: list[dict[str, Any]]) -> int:
    path, key, delta_key = CATEGORY_SPECS[category]
    target = ontology.setdefault(path, [])
    index = index_items(target, key)
    changed = 0
    for item in items:
        item_key = item.get(delta_key) or item.get(key)
        if not item_key:
            raise ValueError(f"updated_{category} item missing key {delta_key} or {key}")
        if item_key not in index:
            raise ValueError(f"updated_{category} references missing item: {item_key}")
        fields = item.get("updated_fields")
        if not isinstance(fields, dict):
            raise ValueError(f"updated_{category} item missing updated_fields: {item_key}")
        target[index[item_key]] = deep_merge(target[index[item_key]], fields)
        changed += 1
    return changed


def mark_items(ontology: dict[str, Any], category: str, action: str, items: list[dict[str, Any]]) -> int:
    operation = {"deprecated": "deprecate", "rejected": "reject"}[action]
    path, key, delta_key = CATEGORY_SPECS[category]
    target = ontology.setdefault(path, [])
    index = index_items(target, key)
    changed = 0
    for item in items:
        item_key = item.get(delta_key) or item.get(key)
        if not item_key:
            raise ValueError(f"{action}_{category} item missing key {delta_key} or {key}")
        if item_key not in index:
            raise ValueError(f"{action}_{category} references missing item: {item_key}")
        target_item = deepcopy(target[index[item_key]])
        target_item["operation"] = operation
        if item.get("reason"):
            if "reviewNote" in target_item:
                target_item["reviewNote"] = item["reason"]
            else:
                target_item["reason"] = item["reason"]
        if item.get("evidenceRefs"):
            target_item["evidenceRefs"] = item["evidenceRefs"]
        if item.get("updated_fields"):
            target_item = deep_merge(target_item, item["updated_fields"])
        target[index[item_key]] = target_item
        changed += 1
    return changed


def apply_delta(ontology: dict[str, Any], delta: dict[str, Any]) -> tuple[dict[str, Any], int]:
    merged = deepcopy(ontology)
    changes = delta.get("delta_changes", {})
    if not isinstance(changes, dict):
        raise ValueError("optimization_delta.delta_changes must be an object")

    count = 0
    for category in CATEGORY_SPECS:
        count += add_items(merged, category, changes.get(f"added_{category}", []))
        count += update_items(merged, category, changes.get(f"updated_{category}", []))
        count += mark_items(merged, category, "deprecated", changes.get(f"deprecated_{category}", []))
        count += mark_items(merged, category, "rejected", changes.get(f"rejected_{category}", []))

    for dotted_path, value in changes.get("container_updates", {}).items():
        current: Any = merged
        parts = dotted_path.split(".")
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = deepcopy(value)
        count += 1

    return merged, count


def main() -> None:
    args = parse_args()
    base_document = load_json(args.base)
    delta_document = load_json(args.delta)
    base_ontology, base_wrapper = extract_ontology(base_document)
    delta = extract_delta(delta_document)

    metadata = delta.get("delta_metadata", {})
    expected_hash = metadata.get("base_hash")
    actual_hash = canonical_hash(base_ontology)
    if expected_hash and expected_hash != actual_hash and not args.allow_hash_mismatch:
        raise SystemExit(f"base hash mismatch: expected {expected_hash}, got {actual_hash}")

    merged_ontology, applied_count = apply_delta(base_ontology, delta)
    if base_wrapper is None:
        result: dict[str, Any] = merged_ontology
    else:
        result = deepcopy(base_wrapper)
        result["optimized_ontology"] = merged_ontology
        _ = applied_count
        _ = actual_hash

    write_json(args.output, result)


if __name__ == "__main__":
    main()
