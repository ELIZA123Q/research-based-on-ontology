#!/usr/bin/env python3
import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]

SCHEMAS = {
    "materials": ROOT / "schemas" / "材料清单结构.json",
    "single": ROOT / "schemas" / "单篇材料本体化解读结构.json",
    "impact": ROOT / "schemas" / "模板影响评估结构.json",
    "evidence_matrix": ROOT / "schemas" / "跨材料证据矩阵结构.json",
    "quality": ROOT / "schemas" / "质量检查结构.json",
}

EXAMPLES = [
    (ROOT / "examples" / "07_材料清单样例.json", "materials"),
    (ROOT / "examples" / "03_单篇材料本体化解读样例.json", "single"),
    (ROOT / "examples" / "04_模板影响评估样例.json", "impact"),
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
        "references/00_入门使用路由.md",
        "references/04_半导体材料抽取校准.md",
    ]:
        if not (ROOT / ref).exists():
            raise AssertionError(f"missing reference: {ref}")
        if ref not in skill_text:
            raise AssertionError(f"SKILL.md does not reference {ref}")

    for phrase in [
        "通用抽取校准要求",
        "前置验证",
        "商业转化",
        "履约或兑现",
        "经营指标变化",
        "资产影响线索",
        "反证信号",
        "不得自动补齐",
    ]:
        if phrase not in skill_text:
            raise AssertionError(f"SKILL.md missing generic extraction requirement: {phrase}")

    io_text = (ROOT / "references/A02_Skill输入输出说明.md").read_text(encoding="utf-8")
    for phrase in [
        "已验证环节",
        "缺失环节",
        "市场预期变化",
        "反证、阻断或待验证条件",
        "资产影响线索",
    ]:
        if phrase not in io_text:
            raise AssertionError(f"A02 missing generic output constraint: {phrase}")
    for phrase in [
        "| 单篇材料本体化解读 |",
        "| 模板影响评估 |",
        "| 跨材料证据矩阵 |",
    ]:
        if phrase not in io_text:
            raise AssertionError(f"A02 missing material extraction output: {phrase}")
    for phrase in [
        "| 标的研究输出 |",
        "| 通用投研框架 |",
        "| 投研模板卡片 |",
    ]:
        if phrase in io_text:
            raise AssertionError(f"A02 contains downstream output outside material extraction boundary: {phrase}")

    semiconductor_text = (ROOT / "references/04_半导体材料抽取校准.md").read_text(encoding="utf-8")
    if "通用抽取校准要求以 `SKILL.md` 为准" not in semiconductor_text:
        raise AssertionError("semiconductor calibration must defer generic requirements to SKILL.md")
    for phrase in [
        "发出商品",
        "验收",
        "sell-through",
        "EDA/IP",
        "AI、HBM、先进封装",
        "订单链条",
        "反证与阻断信号",
    ]:
        if phrase not in semiconductor_text:
            raise AssertionError(f"semiconductor calibration missing: {phrase}")

    for example_path, schema_name in EXAMPLES:
        validators[schema_name].validate(load_json(example_path))

    expect_invalid(
        validators["single"],
        {
            "材料信息": {
                "文档标题": "空壳",
                "文档类型": "研报",
                "发布时间": "未提供",
            },
            "本体化抽取": {},
            "质量提示": [],
        },
        "empty extraction",
    )

    bad_matrix = load_json(ROOT / "examples" / "09_跨材料证据矩阵样例.json")
    bad_matrix["材料范围"]["历史样本数量"] = 0
    expect_invalid(
        validators["evidence_matrix"],
        bad_matrix,
        "historical support without historical samples",
    )

    print("touyan-cailiao-bentihua-chouqu: OK")


if __name__ == "__main__":
    main()
