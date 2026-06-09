---
name: touyan-evaluation-input-generation
description: 当需要为评测 Skill 准备参考材料、题源材料、热点材料、数据需求、evidence graph 输入、patch ledger 输入、inference run 样本和交接说明时使用。支持主题预备、本体驱动和评测后回补三种模式，输出 _artifacts/evaluation_results/evaluation_data_inputs/ 和 docs/evaluation_handoff.md。本 Skill 不评分，不发布，不修改候选本体。
metadata:
  short-description: 评测数据输入生成
---

# 评测数据输入生成 Skill

## 定位

本 Skill 是生产 Agent 和评测 Agent 之间的数据桥梁。它只准备评测输入材料和交接说明，不执行评测、不输出发布结论、不修改评测集和候选本体。

完整作业规则见 `./references/评测数据输入生成要求.md`。

## 输入

| 文件 | 必填 | 说明 |
|---|---|---|
| `ontology_bundle_vN/` | 模式 B 必填优先 | 候选本体，评测主体。 |
| `_compat/optimized_ontology_vN.json` | 可选 | 兼容回退输入。 |
| `docs/production_notes.md` | 可选 | 优化过程、版本变更、来源限制和未解决问题。 |
| `_artifacts/sources/source_material_summary.md` | 可选 | 来源材料摘要。 |
| `_artifacts/evidence_graph/` | 可选 | EvidenceEpisode、EvidenceClaim、EvidenceFact 和失效候选。 |
| `_artifacts/patches/patch_ledger.yaml` | 可选 | 增量 patch 审计输入。 |
| `_artifacts/reasoning_runs/` | 可选 | 推理运行记录样本。 |
| `source_materials/` | 可选 | 原始来源材料。 |
| `source_registry.json` | 可选 | 来源登记。 |
| 评测补充请求 | 模式 C 必填 | 评测 Skill 返回的数据缺口。 |

## 输出

| 文件 | 说明 |
|---|---|
| `_artifacts/evaluation_results/evaluation_data_inputs/` | 结构化评测数据输入包。 |
| `docs/evaluation_handoff.md` | 给评测 Skill 的交接说明。 |

## 禁止事项

- 不输出发布结论。
- 不输出逐题评分或维度评分。
- 不输出 `evaluation_fix_report` 或 `optimization_plan`。
- 不修改评测集。
- 不修改候选本体。
