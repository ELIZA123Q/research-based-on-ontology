---
name: touyan-historical-case-generation
description: 当需要为历史回放 Skill 准备真实、可追溯、避免事后信息泄漏的历史案例材料时使用。输入研究主题、来源材料和任务提示，输出 _artifacts/historical_replay/ 下的 historical_materials/、historical_case_generation_report.md 和 replay_task_list.md。本 Skill 不判断本体是否通过，不输出回放结论，不修改本体。
metadata:
  short-description: 历史案例材料生成
---

# 历史案例生成 Skill

## 定位

本 Skill 为历史回放校验准备案例素材。它选择历史事件，冻结 t0 时点可得信息，整理 t0 后真实结果，并形成回放任务单。

完整作业规则见 `./references/历史案例生成要求.md`。

## 输入

| 文件 | 必填 | 说明 |
|---|---|---|
| `research_topic.md` | 必填 | 研究主题、范围和时间窗口。 |
| `source_materials/` | 可选 | 6-1 输出来源材料。 |
| `source_registry.json` | 可选 | 来源登记。 |
| `reference_materials/` | 可选 | 6-2 输出的研究逻辑材料。 |
| `gap_items.json` | 可选 | 缺口发现输出的结构化缺口。 |
| `downstream_task_list.md` | 可选 | 冷启动或用户给出的任务提示。 |

## 输出

| 文件 | 说明 |
|---|---|
| `_artifacts/historical_replay/historical_materials/` | 按案例组织的 t0 信息包和 t0 后验证结果。 |
| `_artifacts/historical_replay/historical_case_generation_report.md` | 案例选择依据、来源、t0 冻结说明和数据缺口。 |
| `_artifacts/historical_replay/replay_task_list.md` | 供历史回放 Skill 使用的回放任务单。 |

## 禁止事项

- 不判断本体支持或不支持案例。
- 不输出 `replay_report.md` 或 `historical_cases.json`。
- 不输出 `ontology_bundle_vN/` 或 `optimized_ontology_vN.json`。
- 不用事后结果污染 t0 信息包。
- 不只选成功案例或有利案例。
