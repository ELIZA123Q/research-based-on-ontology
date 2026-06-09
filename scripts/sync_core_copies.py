#!/usr/bin/env python3
import hashlib
import json
import shutil
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
CORE_DIR = WORKSPACE / "spec" / "投研本体核心规范"

CORE_VERSION = "2026-06-09.2"
MANIFEST_NAME = "core_manifest.json"
SCHEMA_FILES = [
    "schemas/objects.yaml",
    "schemas/relations.yaml",
    "schemas/actions.yaml",
]
REFERENCE_FILES = [
    "references/01_投研本体核心说明.md",
    "references/02_投研本体建模规格说明.md",
    "references/03_本体Bundle文件契约.md",
]
STRUCTURAL_FILES = [
    "schemas/concepts.yaml",
    "schemas/ontology_bundle.yaml",
]
SKILL_DIRS = [
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


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest():
    files = {}
    for rel_path in SCHEMA_FILES + REFERENCE_FILES + STRUCTURAL_FILES:
        path = CORE_DIR / rel_path
        if not path.exists():
            raise FileNotFoundError(f"missing canonical core file: {rel_path}")
        files[rel_path] = sha256(path)
    return {
        "manifest_type": "touyan_core_manifest",
        "core_name": "touyan-bentiguifan-hexin",
        "core_version": CORE_VERSION,
        "managed_files": files,
    }


def build_skill_manifest(core_manifest):
    core_hashes = core_manifest["managed_files"]
    return {
        "manifest_type": "touyan_core_manifest",
        "core_name": "touyan-bentiguifan-hexin",
        "core_version": CORE_VERSION,
        "canonical_core_root": "../../spec/投研本体核心规范",
        "managed_files": {rel_path: core_hashes[rel_path] for rel_path in SCHEMA_FILES},
        "canonical_reference_files": {
            f"../../spec/投研本体核心规范/{rel_path}": core_hashes[rel_path]
            for rel_path in REFERENCE_FILES
        },
    }


def write_manifest(path, manifest):
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


def main():
    manifest = build_manifest()
    write_manifest(CORE_DIR / MANIFEST_NAME, manifest)

    for skill_dir_name in SKILL_DIRS:
        skill_dir = WORKSPACE / skill_dir_name
        if not skill_dir.exists():
            raise FileNotFoundError(f"missing skill directory: {skill_dir_name}")
        for rel_path in SCHEMA_FILES:
            source = CORE_DIR / rel_path
            target = skill_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        write_manifest(skill_dir / MANIFEST_NAME, build_skill_manifest(manifest))

    print(f"synced core manifest {manifest['core_version']} to {len(SKILL_DIRS)} skills")


if __name__ == "__main__":
    main()
