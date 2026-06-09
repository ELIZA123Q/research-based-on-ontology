---
name: touyan-evidence-episode-normalization
description: 当需要把来源材料、material_graph、历史案例、推理反馈、评测反馈或结构化数据统一整理为 Temporal Evidence Layer 时使用。输入 source_registry、source_materials、_artifacts/material_graph、历史回放材料、推理运行反馈或评测反馈，输出 _artifacts/evidence_graph/ 下的 evidence_episodes.yaml、evidence_claims.yaml、evidence_facts.yaml、invalidation_candidates.yaml 和 evidence_graph_validation_report.md。本 Skill 不修改 ontology_bundle，不判断本体覆盖，不输出投资建议。
metadata:
  short-description: Evidence Episode 归一与校验
---

# Evidence Episode 归一与校验 Skill

## 定位

本 Skill 是 Temporal Evidence Layer 的入口。它把材料、历史案例、推理反馈和评测反馈统一整理为可追溯、可失效、可被 patch 和推理使用的 evidence graph。

它只做证据归一和校验，不修改 Palantir 本体主干，不输出 `ontology_bundle_vN/`，不判断本体覆盖，也不生成发布结论。

完整作业规则见 `./references/EvidenceEpisode归一与校验要求.md`。

## 输入

| 文件 | 必填 | 说明 |
|---|---|---|
| `source_registry.json` | 可选但建议 | 6-1 输出的来源登记，提供 episode seed。 |
| `source_materials/` | 可选 | 来源材料原文或摘录。 |
| `source_quality_assessment.md` | 可选 | 来源质量和限制说明。 |
| `_artifacts/material_graph/` | 可选但优先 | 6-1b 输出的 Document/Chunk、候选对象关系和证据片段索引，用于生成更稳定的 claim。 |
| `_artifacts/historical_replay/` | 可选 | 历史案例、回放证据、失效候选。 |
| `_artifacts/reasoning_runs/` | 可选 | 推理运行和推理失败反馈。 |
| `_artifacts/evaluation_results/` | 可选 | 评测反馈、失败题和补证需求。 |
| `ontology_bundle_vN/` | 可选 | 只用于对象 ID 对齐和映射校验，不得被修改。 |

至少应提供一种可追溯输入；否则只输出阻断说明和最小输入要求。

## 输出

| 文件 | 说明 |
|---|---|
| `_artifacts/evidence_graph/evidence_episodes.yaml` | EvidenceEpisode 列表，记录摄入来源、业务时间、系统摄入时间、可靠性、限制和 groupId。 |
| `_artifacts/evidence_graph/evidence_claims.yaml` | EvidenceClaim 列表，记录最小主张、claim 类型、来源位置、有效期、状态、可映射对象和禁止映射目标。 |
| `_artifacts/evidence_graph/evidence_facts.yaml` | EvidenceFact 列表，由一个或多个 claim 归并而来，只能作为正式对象、观测、信号或关系候选来源。 |
| `_artifacts/evidence_graph/invalidation_candidates.yaml` | 新 claim/fact 对旧 claim/fact/signal/relation 的失效、替代或降级候选。 |
| `_artifacts/evidence_graph/evidence_graph_validation_report.md` | 归一质量、可追溯性、时间字段、受限内容、未解析对象和可交接性检查。 |

## 输出边界

- `EvidenceEpisode` 是一次摄入事件，不是正式业务对象。
- `EvidenceClaim` 是最小证据主张，不等于正式本体对象、关系、信号或判断。
- `EvidenceFact` 是结构化事实候选，不能绕过优化 Skill 进入正式本体。
- 受限内容只能进入 quarantined / restricted 记录，不得作为事实观测。
- 本 Skill 可生成 `PatchRequest` 候选线索，但不得合并 patch。

## 与其他 Skill 的关系

```text
01-信息与数据搜索
  -> 02-材料图谱预处理
  -> 04-证据归一与校验（本 Skill）
  -> 05-缺口发现（内部生成 gap_reference_view，直接消费 evidence_claims.yaml）
```

02 负责把材料拆成 Document/Chunk/候选对象关系并钉住原文片段；04 负责证据归一、时间、来源和 claim；05 负责判断本体是否覆盖这些逻辑。

## 禁止事项

- 不修改 `ontology_bundle_vN/`、`base_ontology_bundle/` 或 `_compat/*.json`。
- 不输出 `gap_items.json`、`optimization_task_items.json`、`patch_ledger.yaml` 或发布判断。
- 不把预测、评级、目标价、推荐语、收益率推断或仓位表达登记为事实观测。
- 不把无法追溯原文位置的材料升级为 active claim。
- 不用模型常识补充材料中没有表达的事实。
