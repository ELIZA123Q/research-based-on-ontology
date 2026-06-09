#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent.parent
MANIFEST_NAME = "core_manifest.json"
CORE_SCHEMA_FILES = [
    "schemas/objects.yaml",
    "schemas/relations.yaml",
    "schemas/actions.yaml",
]
CORE_REFERENCE_FILES = [
    "references/01_投研本体核心说明.md",
    "references/02_投研本体建模规格说明.md",
    "references/03_本体Bundle文件契约.md",
]
CORE_STRUCTURAL_FILES = [
    "schemas/concepts.yaml",
    "schemas/ontology_bundle.yaml",
]
MANAGED_CORE_FILES = CORE_REFERENCE_FILES + CORE_SCHEMA_FILES + CORE_STRUCTURAL_FILES
DEPENDENT_SKILL_DIRS = [
    "skills/01-信息与数据搜索",
    "skills/02-材料图谱预处理",
    "skills/03-冷启动",
    "skills/04-证据归一与校验",
    "skills/05-缺口发现",
    "skills/06-历史案例生成",
    "skills/07-历史回放校验",
    "skills/08-生产任务合并",
    "skills/09-本体优化",
    "skills/10-人类可读解析",
    "skills/11-评测数据输入生成",
    "skills/12-Release组装校验",
    "skills/13-本体评测",
    "skills/14-投研推理",
]


def read(path):
    return path.read_text(encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path):
    if not path.exists():
        raise AssertionError(f"missing core manifest: {path.relative_to(WORKSPACE)}")
    with path.open(encoding="utf-8") as f:
        manifest = json.load(f)
    if manifest.get("manifest_type") != "touyan_core_manifest":
        raise AssertionError(f"invalid core manifest type: {path.relative_to(WORKSPACE)}")
    if manifest.get("core_name") != "touyan-bentiguifan-hexin":
        raise AssertionError(f"invalid core manifest name: {path.relative_to(WORKSPACE)}")
    if not manifest.get("core_version"):
        raise AssertionError(f"core manifest missing core_version: {path.relative_to(WORKSPACE)}")
    return manifest


def assert_manifest_hashes(manifest, root, rel_paths):
    managed = manifest.get("managed_files", {})
    for rel_path in rel_paths:
        if rel_path not in managed:
            raise AssertionError(f"manifest missing managed file: {root.name}/{rel_path}")
        path = root / rel_path
        if not path.exists():
            raise AssertionError(f"manifest file missing: {root.name}/{rel_path}")
        actual_hash = sha256(path)
        if actual_hash != managed[rel_path]:
            raise AssertionError(
                f"manifest hash mismatch: {root.name}/{rel_path} "
                f"expected {managed[rel_path]} got {actual_hash}"
            )


def assert_core_schema_semantics():
    objects = yaml.safe_load(read(ROOT / "schemas/objects.yaml"))
    concepts = yaml.safe_load(read(ROOT / "schemas/concepts.yaml"))
    relations = yaml.safe_load(read(ROOT / "schemas/relations.yaml"))
    actions = yaml.safe_load(read(ROOT / "schemas/actions.yaml"))
    bundle = yaml.safe_load(read(ROOT / "schemas/ontology_bundle.yaml"))

    object_types_dict = objects.get("object_types", {})
    object_types = set(object_types_dict)
    for required_type in [
        "ConceptScheme",
        "Concept",
        "ConceptBoundary",
        "Industry",
        "Segment",
        "Company",
        "Product",
        "Material",
        "Asset",
        "StateVariable",
        "StateVariableObservation",
        "StateVariablePropagation",
        "Event",
        "StateHypothesis",
        "Signal",
        "JudgmentOutput",
        "AssetImpact",
        "InvestmentThesis",
        "SourceDocument",
        "EvidenceEpisode",
        "EvidenceClaim",
        "EvidenceFact",
        "PatchRequest",
        "PatchLedgerItem",
        "InferenceRun",
        "ActionAudit",
        "ReviewRecord",
    ]:
        if required_type not in object_types:
            raise AssertionError(f"objects.yaml missing object type: {required_type}")

    # concepts.yaml 语义校验
    concept_layer = concepts.get("concept_layer_structure", {})
    hierarchy_types = {h["type"] for h in concept_layer.get("hierarchy", [])}
    for ct in ["ConceptScheme", "Concept", "ConceptBoundary"]:
        if ct not in hierarchy_types:
            raise AssertionError(f"concepts.yaml hierarchy missing type: {ct}")
        if ct not in object_types:
            raise AssertionError(f"concepts.yaml references type {ct} not in objects.yaml")

    quality_rules = concepts.get("quality_rules", {})
    rules = quality_rules.get("rules", [])
    if not rules:
        raise AssertionError("concepts.yaml quality_rules.rules is empty")

    # ontology_bundle.yaml 语义校验
    container_meta = bundle.get("ontology_container_metadata", {})
    if not container_meta:
        raise AssertionError("ontology_bundle.yaml missing ontology_container_metadata")
    bundle_required = container_meta.get("required_fields", {})
    for field in ["ontology_id", "ontology_version", "created_by", "updated_by", "change_reason", "ontology_quality"]:
        if field not in bundle_required:
            raise AssertionError(f"ontology_bundle.yaml missing required field: {field}")
    quality_props = bundle_required.get("ontology_quality", {}).get("properties", {})
    for qf in ["coverage_score", "evidence_score", "consistency_score", "reasoning_score"]:
        if qf not in quality_props:
            raise AssertionError(f"ontology_bundle.yaml ontology_quality missing: {qf}")

    for relation_name, relation in relations.get("relation_types", {}).items():
        for endpoint in relation.get("source_types", []) + relation.get("target_types", []):
            if endpoint not in object_types:
                raise AssertionError(f"{relation_name} references unknown object type: {endpoint}")
        for prop_name, prop in relation.get("properties", {}).items():
            if "required" not in prop:
                raise AssertionError(f"{relation_name}.{prop_name} missing required flag")

    for action_name, action in actions.get("actions", {}).items():
        target_type = action.get("target_type")
        if target_type and target_type not in object_types:
            raise AssertionError(f"{action_name} references unknown target_type: {target_type}")
        outputs = action.get("outputs", {})
        if not outputs.get("create_action_audit"):
            raise AssertionError(f"{action_name} must create action audit")

    # 状态机语义校验：actions.yaml 是状态机的权威承载位置
    state_machine = actions.get("state_machine_summary", {})
    if not state_machine:
        raise AssertionError("actions.yaml missing state_machine_summary")
    for obj_type, sm in state_machine.items():
        if obj_type not in object_types:
            raise AssertionError(f"state_machine_summary references unknown type: {obj_type}")
        field = sm.get("field")
        if field and obj_type in object_types_dict:
            obj_fields = object_types_dict[obj_type].get("fields", {})
            if field not in obj_fields:
                raise AssertionError(f"state_machine field {obj_type}.{field} not in objects.yaml")


def assert_dependent_contract(core_manifest):
    core_hashes = core_manifest["managed_files"]
    canonical_refs = {
        f"../../spec/投研本体核心规范/{rel_path}": core_hashes[rel_path]
        for rel_path in CORE_REFERENCE_FILES
    }

    for skill_dir in DEPENDENT_SKILL_DIRS:
        skill_path = WORKSPACE / skill_dir
        manifest = load_manifest(skill_path / MANIFEST_NAME)

        if manifest.get("canonical_core_root") != "../../spec/投研本体核心规范":
            raise AssertionError(f"{skill_dir}/{MANIFEST_NAME} missing canonical_core_root")

        if set(manifest.get("managed_files", {})) != set(CORE_SCHEMA_FILES):
            raise AssertionError(f"{skill_dir}/{MANIFEST_NAME} should manage schema copies only")

        if manifest.get("canonical_reference_files") != canonical_refs:
            raise AssertionError(f"{skill_dir}/{MANIFEST_NAME} canonical references mismatch")

        for rel_path in CORE_SCHEMA_FILES:
            local_path = skill_path / rel_path
            core_path = ROOT / rel_path
            if not local_path.exists():
                raise AssertionError(f"missing local schema copy: {skill_dir}/{rel_path}")
            if read(local_path) != read(core_path):
                raise AssertionError(f"schema copy drift: {skill_dir}/{rel_path}")
            if manifest["managed_files"][rel_path] != core_hashes[rel_path]:
                raise AssertionError(f"{skill_dir}/{MANIFEST_NAME} schema hash drift: {rel_path}")

        for rel_path in CORE_REFERENCE_FILES + CORE_STRUCTURAL_FILES:
            local_ref = skill_path / rel_path
            if local_ref.exists():
                raise AssertionError(f"{skill_dir} should not keep duplicate core file: {rel_path}")


def main():
    for rel_path in MANAGED_CORE_FILES:
        path = ROOT / rel_path
        if not path.exists():
            raise AssertionError(f"missing core file: {rel_path}")

    core_manifest = load_manifest(ROOT / MANIFEST_NAME)
    if set(core_manifest.get("managed_files", {})) != set(MANAGED_CORE_FILES):
        raise AssertionError("core manifest managed_files mismatch")
    assert_manifest_hashes(core_manifest, ROOT, MANAGED_CORE_FILES)
    assert_core_schema_semantics()
    assert_dependent_contract(core_manifest)
    print("touyan-bentiguifan-hexin: OK")


if __name__ == "__main__":
    main()
