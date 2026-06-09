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
    "schemas/本体缺口发现输出结构.json",
    "schemas/本体缺口发现输出结构.yaml",
    "examples/01_AI芯片研报逻辑缺口发现样例.json",
    "examples/02_AI芯片研报逻辑缺口发现样例.yaml",
]
SKILL_REQUIRED_PHRASES = [
    "touyan-benti-quekou-faxian",
    "ontology_bundle_vN",
    "target_file",
    "缺口发现报告",
    "缺口发现结果交接块",
    "optimization_plan",
    "gap_recommendations",
    "fully_covered",
    "schema_gap",
    "../../spec/投研本体核心规范/references/01_投研本体核心说明.md",
    "../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md",
    "../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md",
    "不修改本体",
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
    json_schema = load_json(ROOT / "schemas" / "本体缺口发现输出结构.json")
    jsonschema.Draft202012Validator.check_schema(json_schema)
    yaml.safe_load(read(ROOT / "schemas" / "本体缺口发现输出结构.yaml"))
    load_json(ROOT / "examples" / "01_AI芯片研报逻辑缺口发现样例.json")
    yaml.safe_load(read(ROOT / "examples" / "02_AI芯片研报逻辑缺口发现样例.yaml"))


def main():
    for rel_path in LOCAL_REQUIRED_FILES:
        assert_exists(ROOT / rel_path)
    assert_core_contract()
    assert_skill_text()
    assert_schema_and_examples()
    print("OK: gap discovery skill validated")


if __name__ == "__main__":
    main()
