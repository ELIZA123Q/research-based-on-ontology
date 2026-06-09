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
    "references/01_评测问题设计.md",
    "references/02_评分阈值与发布判断.md",
    "references/03_修复建议与优化交接.md",
    "schemas/本体评测输出结构.json",
    "examples/01_本体评测样例.json",
]
SKILL_REQUIRED_PHRASES = [
    "touyan-benti-pingce",
    "ontology_bundle",
    "target_file",
    "target_scope",
    "eval_questions",
    "allow_publish",
    "conditional_publish",
    "reject_publish",
    "insufficient_evidence",
    "optimization_plan",
    "references/01_评测问题设计.md",
    "references/02_评分阈值与发布判断.md",
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
    schema = load_json(ROOT / "schemas" / "本体评测输出结构.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    load_json(ROOT / "examples" / "01_本体评测样例.json")


def main():
    for rel_path in LOCAL_REQUIRED_FILES:
        assert_exists(ROOT / rel_path)
    assert_core_contract()
    assert_skill_text()
    assert_schema_and_examples()
    print("OK: ontology evaluation skill validated")


if __name__ == "__main__":
    main()
