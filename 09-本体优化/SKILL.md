---
name: touyan-benti-youhua
description: 当已有 base_ontology_bundle、ontology_bundle_vN 或兼容旧本体，需要基于材料、缺口任务单、历史回放建议、评测修复项或推理反馈优化投研本体时使用。输出 ontology_bundle_vN/、_compat/optimized_ontology_vN.json 和 production_notes，并可附结构化运行结果。本 Skill 不做冷启动，不直接修改核心规范，不生成投资建议、目标价、收益率预测或仓位建议。
metadata:
  short-description: 投研本体优化
---

# 投研本体优化 Skill

## 定位

本 Skill 是材料驱动的本体优化器。它消费已有本体、优化任务、证据材料和诊断结果，完成概念层、对象、关系、动作、状态变量、传导、信号、情景、资产线索和治理记录的修正。

本 Skill 不创建无基座本体。没有 `base_ontology_bundle/`、`ontology_bundle_vN/` 或兼容旧本体时，只说明无法优化原因、最小输入要求和建议先运行冷启动 Skill。

## 输入

| 输入 | 要求 |
|---|---|
| `base_ontology_bundle/` / `ontology_bundle_vN/` | 必填其一。作为本轮优化基座，必须保留 `00_ontology_manifest.yaml` 和模块文件。 |
| `_compat/base_ontology.json` / `_compat/optimized_ontology_vN.json` / 旧单体 JSON | 可选兼容输入。缺 bundle 时允许读取，但输出必须升级为 bundle。 |
| `optimization_plan` / `next_optimization_plan` | 可选但建议。承接缺口发现、历史回放、评测、推理反馈或用户修订任务。 |
| `_artifacts/task_merge/patch_request_queue.yaml` | 可选但建议。6-4 产出的候选 PatchRequest 队列，是 patch ledger 的主要输入。 |
| `_artifacts/evidence_graph/evidence_episodes.yaml` / `evidence_claims.yaml` / `evidence_facts.yaml` | 可选但建议。6-8 产出的 Temporal Evidence Layer，用于证据评估、失效判断和 patch 支撑。 |
| `base_ontology_identity` | patch 批次建议提供，包含版本、hash 和 bundle manifest。 |
| `richness_reference_ontology` | 可选。只作为候选来源，不替代基座。 |
| 外部材料 | 可选。用于证据评估、补证和候选内容确认。 |
| `optimization_run_mode` | 默认 `auto_batches`，也可为 `single_batch` 或 `full_rebuild_review`。 |
| `optimization_mode` | 普通批次默认 `patch`，完整审计为 `full`。 |

## 核心依据

冲突裁定顺序如下：

1. 输入本体、用户显式范围和本轮任务单
2. `../../spec/投研本体核心规范/schemas/objects.yaml`
3. `../../spec/投研本体核心规范/schemas/relations.yaml`
4. `../../spec/投研本体核心规范/schemas/actions.yaml`
5. `../../spec/投研本体核心规范/references/01_投研本体核心说明.md`
6. `../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md`
7. `../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`
8. `references/03_优化逻辑与证据决策.md`
9. `references/04_行业产品校准包接口.md`
10. `references/05_运行编排与治理规则.md`
11. `schemas/本体优化输出结构.json`
12. `schemas/核心规范变更建议输出结构.json`
13. `examples/*`

本目录内的公共 schema copy 仅用于单独安装和本地校验；在本仓库中，公共规范以 `../../spec/投研本体核心规范` 为准。

## 工作流程

1. **确认基座和范围**：读取 bundle manifest、概念层、对象/关系规模、证据覆盖和已知限制；兼容 JSON 需先映射为 bundle 模块。
2. **归并任务单和 patch queue**：读取 `optimization_plan`、`patch_request_queue.yaml`、缺口、历史回放、评测修复、推理反馈和用户请求，形成 `gap_buckets` 和本轮候选 PatchRequest。
3. **选择批次**：默认 `auto_batches`，单批处理 1-3 个同主题簇缺口；P0 优先，依赖未满足的缺口顺延。
4. **评估证据和动作**：每个 add/update/strengthen/keep/deprecate/reject 动作必须绑定 evidence_episode_ids、evidence_claim_ids、任务或诊断理由；缺少 evidence ids 的高风险任务只能延后、补证或拒绝。
5. **优化概念层**：遇到新术语、范围冲突、同义词、交叉产业或边界不清时，先更新 `01_concepts.yaml` 或写入概念更新阻断项，再决定是否映射到业务对象。
6. **执行 patch 或 full 优化**：普通批次可先产出 `optimization_delta`，但最终必须合并为完整 `ontology_bundle_vN/`，并追加 `PatchLedgerItem`。
7. **做核心适配判断**：判断是实例可表达、临时 workaround 还是必须提出核心规范变更。
8. **执行稳定性审计**：检查前后差异、变更预算、任务遵循、scope_type 一致性、概念边界一致性和丰富性保留。
9. **生成正式交付**：输出权威 bundle、兼容 JSON、生产说明和可审计 artifacts。

## 硬性规则

- 最终权威产物必须是完整 `ontology_bundle_vN/`，不得把未合并的 `optimization_delta` 当作交付。
- Evidence Graph 不能直接写入正式对象、关系、动作或推理模块；必须经本 Skill 审核、合并并写入 patch ledger。
- `patch_request_queue.yaml` 中的 pending 项不代表正式改动；合并、拒绝、延后或失败必须写入 `_artifacts/patches/patch_ledger.yaml`。
- AI 新增、更新或强化内容默认 `recordStatus=candidate`。只有输入已为 `confirmed` 且本轮只是 `keep`，才可保留 `confirmed`。
- 二手新闻、AI 摘要、无原文位置材料只能作为线索，不能支撑关键确认。
- 市场价格变化可以作为定价信号，不能替代基本面验证。
- 研报预测、评级、目标价、推荐语、收益率推断和仓位表达不得作为 `StateVariableObservation`。
- 不得静默删除基座中未被反证且能合法表达的对象、关系或推理链。
- 不得绕过 `01_concepts.yaml` 把相邻、交叉或待确认概念直接生成业务对象。
- 概念定义、边界裁定和概念映射必须绑定来源、任务或诊断理由。
- 无法映射、证据不足、端点缺失、字段冲突或越界内容必须进入 `07_governance.yaml` 或 `08_optimization_handoff.yaml`。

## 核心适配

每个重大结构改动必须写入 `core_fit_assessment`：

| 分类 | 处理 |
|---|---|
| `instance_fit` | 现有 schema 可准确表达，允许正常实例改动。 |
| `instance_workaround_with_core_debt` | 现有 schema 可临时表达但语义不理想，允许候选级实例，并绑定核心变更建议。 |
| `core_required` | 现有 schema 会导致语义失真，禁止硬凑实例，进入核心变更建议。 |

本 Skill 不直接修改 `../../spec/投研本体核心规范`。核心对象、关系、动作、公共枚举或状态机变更必须输出独立 `core_change_proposals`。

## 正式输出

生产交付必须包含：

```text
ontology_bundle_vN/
  00_ontology_manifest.yaml
  01_concepts.yaml
  02_objects.yaml
  03_relations.yaml
  04_actions.yaml
  05_reasoning.yaml
  06_evidence.yaml
  07_governance.yaml
  08_optimization_handoff.yaml
_compat/optimized_ontology_vN.json
docs/production_notes.md
_artifacts/patches/
  patch_ledger.yaml
  patch_merge_report.md
  rejected_patch_requests.yaml
```

可归档到 `_artifacts/task_merge/`：

- `optimization_report.md`
- `change_log.md`
- `unresolved_questions.md`

Patch ledger 归档到 `_artifacts/patches/`：

- `patch_ledger.yaml`：append-only 账本，记录每个 PatchRequest 的合并、拒绝、延后或失败。
- `patch_merge_report.md`：本轮合并说明、证据依据、风险和核心适配结果。
- `rejected_patch_requests.yaml`：因证据不足、越界、核心变更阻断或低价值而拒绝的请求。

需要 API 或自动编排时，可同时输出符合 `schemas/本体优化输出结构.json` 的结构化 JSON。结构化 JSON 至少包含：

- `optimization_run_mode`
- `optimization_mode`
- `ontology_bundle`
- `optimized_ontology`
- `optimization_report`
- `optimization_run_log`
- `readable_report`

其中 `optimized_ontology` 仅作为兼容字段；`readable_report` 是简明优化摘要，不替代 6-5 人类可读解析报告。

## 与下游交付的关系

- `source_material_summary.md` 由 6-5b 来源材料摘要生成 Skill 产出，并进入 `_artifacts/sources/`。
- `docs/ontology_guide.md` 由 6-5 人类可读解析 Skill 产出。
- `docs/evaluation_handoff.md` 由 6-6 评测数据输入生成 Skill 产出。
- `release_package/` 由 6-7 Release Package 组装校验 Skill 产出。

本 Skill 不把历史回放报告、缺口发现报告、材料搜索日志等中间产物放入最终 release package，但可在 `docs/production_notes.md` 中引用它们的任务 ID 和证据 ID。

本 Skill 可以把 `EvidenceEpisode`、`EvidenceClaim`、`EvidenceFact` 的正式摘要写入 `06_evidence.yaml`；详细 evidence graph 仍归档在 `_artifacts/evidence_graph/`。

`ontology_bundle_vN/01_concepts.yaml` 必须回答研究范围、术语、同义词、纳入/排除/相邻/交叉边界和概念到业务对象的映射，不替代 `02_objects.yaml` 和 `03_relations.yaml`。

## 条件加载

- 优化逻辑、scope_type、证据动作和 playbook 判断时，加载 `references/03_优化逻辑与证据决策.md`。
- 行业校准包命中时，先加载 `references/04_行业产品校准包接口.md`，再加载对应 `references/industry_packs/*.md`。
- 运行模式、patch 合并、gap 分级、批次选择和停止条件判断时，加载 `references/05_运行编排与治理规则.md`。
- 输出结构化 JSON 时，加载 `schemas/本体优化输出结构.json`。
- 输出核心变更建议时，加载 `schemas/核心规范变更建议输出结构.json`。

## 禁止事项

- 不做行业本体冷启动。
- 不直接修改核心规范。
- 不把外部材料中的观点直接写成 confirmed 事实。
- 不绕过 patch_request_queue / PatchLedgerItem 直接静默修改正式本体。
- 不输出 `base_ontology_bundle/` 或 `published_ontology_bundle_vN/`。
- 不输出买卖建议、目标价、收益率预测或仓位建议。

## 本地校验

```bash
python3 scripts/validate_skill.py
```
