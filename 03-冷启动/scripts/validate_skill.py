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
    "references/03_冷启动模板库.md",
    "schemas/行业本体冷启动输出结构.json",
    "examples/01_AI芯片行业本体冷启动样例.json",
]
SKILL_REQUIRED_PHRASES = [
    "touyan-hangye-chanye-bentilengqidong",
    "base_ontology_bundle",
    "_compat/base_ontology.json",
    "material_gap_list",
    "material_collection_plan",
    "MVO",
    "scope_type",
    "references/03_冷启动模板库.md",
    "../../spec/投研本体核心规范/references/01_投研本体核心说明.md",
    "../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md",
    "../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md",
    "不输出投资建议",
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
    managed = manifest.get("managed_files", {})
    for removed_ref in CORE_REFERENCE_FILES:
        if removed_ref in managed:
            raise AssertionError(f"core_manifest should not manage deleted local reference: {removed_ref}")


def assert_skill_text():
    skill_text = read(ROOT / "SKILL.md")
    for phrase in SKILL_REQUIRED_PHRASES:
        if phrase not in skill_text:
            raise AssertionError(f"SKILL.md missing required phrase: {phrase}")


def assert_schema_and_examples():
    schema = load_json(ROOT / "schemas" / "行业本体冷启动输出结构.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    load_json(ROOT / "examples" / "01_AI芯片行业本体冷启动样例.json")

    template_text = read(ROOT / "references" / "03_冷启动模板库.md")
    for scope_type in [
        "industry",
        "supply_chain",
        "product_track",
        "company_research",
        "policy_theme",
        "macro_theme",
        "event_theme",
    ]:
        if scope_type not in template_text:
            raise AssertionError(f"template library missing scope type: {scope_type}")


def main():
    for rel_path in LOCAL_REQUIRED_FILES:
        assert_exists(ROOT / rel_path)
    assert_core_contract()
    assert_skill_text()
    assert_schema_and_examples()
    print("OK: cold-start skill validated")


if __name__ == "__main__":
    main()
