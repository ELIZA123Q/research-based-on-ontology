#!/usr/bin/env python3
import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]

SCHEMAS = {
    "target_research": ROOT / "schemas" / "标的研究输出结构.json",
    "framework": ROOT / "schemas" / "通用投研框架结构.json",
    "template_card": ROOT / "schemas" / "投研模板卡片结构.json",
    "evidence_matrix": ROOT / "schemas" / "跨材料证据矩阵结构.json",
    "quality": ROOT / "schemas" / "质量检查结构.json",
}

EXAMPLES = [
    (ROOT / "examples" / "11_标的研究输出样例.json", "target_research"),
    (ROOT / "examples" / "05_通用投研框架样例.json", "framework"),
    (ROOT / "examples" / "10_投研模板卡片样例.json", "template_card"),
    (ROOT / "examples" / "09_跨材料证据矩阵样例.json", "evidence_matrix"),
    (ROOT / "examples" / "08_质量检查样例.json", "quality"),
]


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validator(name):
    schema = load_json(SCHEMAS[name])
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def expect_invalid(v, data, label):
    if v.is_valid(data):
        raise AssertionError(f"{label} unexpectedly passed validation")


def main():
    validators = {name: validator(name) for name in SCHEMAS}
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    for ref in [
        "references/00_入门术语表.md",
        "references/04_半导体标的研究校准.md",
    ]:
        if not (ROOT / ref).exists():
            raise AssertionError(f"missing reference: {ref}")
        if ref not in skill_text:
            raise AssertionError(f"SKILL.md does not reference {ref}")

    for phrase in [
        "通用研究输出要求",
        "前置验证",
        "商业转化",
        "履约或兑现",
        "经营指标变化",
        "市场预期变化",
        "缺失环节标记为待验证",
        "阻断信号必须作用于状态假设",
        "结论级别必须受证据等级约束",
    ]:
        if phrase not in skill_text:
            raise AssertionError(f"SKILL.md missing generic research requirement: {phrase}")

    io_text = (ROOT / "references/A02_Skill输入输出说明.md").read_text(encoding="utf-8")
    for phrase in [
        "已验证环节",
        "缺失环节",
        "市场预期变化",
        "反证、阻断或待验证条件",
    ]:
        if phrase not in io_text:
            raise AssertionError(f"A02 missing generic output constraint: {phrase}")
    for phrase in [
        "| 标的研究输出 |",
        "| 通用投研框架 |",
        "| 投研模板卡片 |",
    ]:
        if phrase not in io_text:
            raise AssertionError(f"A02 missing target framework output: {phrase}")
    for phrase in [
        "| 材料清单 |",
        "| 单篇材料本体化解读 |",
        "| 模板影响评估 |",
        "| 跨材料证据矩阵 |",
    ]:
        if phrase in io_text:
            raise AssertionError(f"A02 contains upstream extraction output outside target framework boundary: {phrase}")

    semiconductor_text = (ROOT / "references/04_半导体标的研究校准.md").read_text(encoding="utf-8")
    if "通用研究输出要求以 `SKILL.md` 为准" not in semiconductor_text:
        raise AssertionError("semiconductor calibration must defer generic requirements to SKILL.md")
    for phrase in [
        "sell-through",
        "EDA/IP",
        "AI/HBM/先进封装",
        "设备公司",
        "材料公司",
        "设计公司",
        "制造和封测",
        "反证链",
    ]:
        if phrase not in semiconductor_text:
            raise AssertionError(f"semiconductor framework calibration missing: {phrase}")

    for example_path, schema_name in EXAMPLES:
        validators[schema_name].validate(load_json(example_path))

    bad_target = load_json(ROOT / "examples" / "11_标的研究输出样例.json")
    bad_target["估值与资产影响"]["合规边界"] = "可进一步测算目标价。"
    expect_invalid(
        validators["target_research"],
        bad_target,
        "target output without compliance boundary",
    )

    bad_card = load_json(ROOT / "examples" / "10_投研模板卡片样例.json")
    bad_card["证据来源"]["独立原始来源数量"] = 1
    expect_invalid(
        validators["template_card"],
        bad_card,
        "historical template without enough independent sources",
    )

    print("touyan-biaodi-yanjiu-kuangjia: OK")


if __name__ == "__main__":
    main()
