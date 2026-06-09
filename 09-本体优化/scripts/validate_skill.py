#!/usr/bin/env python3
import json
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = ROOT.parent.parent / "spec" / "投研本体核心规范"

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
LOCAL_REQUIRED_FILES = [
    "SKILL.md",
    "core_manifest.json",
    "references/03_优化逻辑与证据决策.md",
    "references/04_行业产品校准包接口.md",
    "references/05_运行编排与治理规则.md",
    "schemas/本体优化输出结构.json",
    "schemas/核心规范变更建议输出结构.json",
    "scripts/apply_optimization_delta.py",
    "examples/01_本体优化输出样例.json",
]
SKILL_REQUIRED_PHRASES = [
    "touyan-benti-youhua",
    "ontology_bundle_vN/",
    "_compat/optimized_ontology_vN.json",
    "docs/production_notes.md",
    "auto_batches",
    "core_fit_assessment",
    "core_change_proposals",
    "references/03_优化逻辑与证据决策.md",
    "references/05_运行编排与治理规则.md",
    "../../spec/投研本体核心规范/references/01_投研本体核心说明.md",
    "../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md",
    "../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md",
    "不做行业本体冷启动",
]


def read(path):
    return path.read_text(encoding="utf-8")


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def assert_exists(path):
    if not path.exists():
        raise AssertionError(f"missing file: {path}")


def assert_core_contract():
    assert_exists(CORE_ROOT)
    for rel_path in CORE_SCHEMA_FILES:
        local_path = ROOT / rel_path
        core_path = CORE_ROOT / rel_path
        assert_exists(local_path)
        assert_exists(core_path)
        if read(local_path) != read(core_path):
            raise AssertionError(f"local schema drift from core canonical: {rel_path}")
        yaml.safe_load(read(local_path))

    for rel_path in CORE_REFERENCE_FILES:
        assert_exists(CORE_ROOT / rel_path)

    manifest = load_json(ROOT / "core_manifest.json")
    for removed_ref in CORE_REFERENCE_FILES:
        if removed_ref in manifest.get("managed_files", {}):
            raise AssertionError(f"core_manifest should not manage deleted local reference: {removed_ref}")


def assert_skill_text():
    skill_text = read(ROOT / "SKILL.md")
    for phrase in SKILL_REQUIRED_PHRASES:
        if phrase not in skill_text:
            raise AssertionError(f"SKILL.md missing required phrase: {phrase}")


def assert_schema_and_examples():
    for schema_name in ["本体优化输出结构.json", "核心规范变更建议输出结构.json"]:
        schema = load_json(ROOT / "schemas" / schema_name)
        jsonschema.Draft202012Validator.check_schema(schema)

    for example_path in sorted((ROOT / "examples").glob("*.json")):
        load_json(example_path)


def main():
    for rel_path in LOCAL_REQUIRED_FILES:
        assert_exists(ROOT / rel_path)
    assert_core_contract()
    assert_skill_text()
    assert_schema_and_examples()
    print("OK: ontology optimization skill validated")


if __name__ == "__main__":
    main()
