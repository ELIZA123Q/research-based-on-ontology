---
name: touyan-benti-quekou-faxian
description: 当已有 base_ontology_bundle、ontology_bundle_vN 或兼容旧本体，需要用研报、访谈、复盘材料、新闻事件或推理失败反馈检查本体表达缺口时使用。它抽取外部研究逻辑，对照本体生成缺口发现报告和可执行优化交接块。本 Skill 不修改本体，不输出 ontology_bundle，不生成投资建议、目标价、收益率预测或仓位建议。
metadata:
  short-description: 投研本体缺口发现
---

# 投研本体缺口发现 Skill

## 定位

本 Skill 是投研本体表达能力诊断器。它回答：外部研究逻辑中哪些概念边界、对象、变量、关系、信号、情景、资产映射或证据链，当前本体无法表达、表达不完整、表达过粗、分类错误或证据不足。

本 Skill 只输出诊断和任务单，不执行材料搜索，不修改完整本体，不替代优化 Skill。

## 输入

必须提供一个本体基座：

| 输入 | 说明 |
|---|---|
| `base_ontology_bundle/` | 冷启动候选本体，优先读取。 |
| `ontology_bundle_vN/` | 已优化候选本体，优先读取。 |
| `_compat/base_ontology.json` / `_compat/optimized_ontology_vN.json` / 旧单体 JSON | 兼容输入。 |
| 多 bundle 组合 | 必须先登记范围和冲突。 |

还必须提供至少一种触发来源：

| 来源 | 用途 |
|---|---|
| 研报、访谈、调研、政策、新闻、历史案例 | 抽取外部研究逻辑。 |
| `_artifacts/evidence_graph/evidence_claims.yaml` | 04-证据归一 产出的证据主张，是本 Skill 的优先输入。内部会生成 `_work/gap_reference_view/` 按来源和逻辑类型组织，供诊断和阅读（不对外交付）。 |
| `_artifacts/sources/source_registry.json` | 来源登记，用于追溯材料元信息。 |
| `ontology_feedback` | 从推理失败中识别缺失节点、弱链路、误触发或漏触发。 |
| `external_reference_materials/` | 可选。用户提供的额外参考材料。 |

没有本体基座时，不得凭材料生成优化计划；只能说明无法判断覆盖，并列出最小输入要求。

## 核心依据

冲突裁定顺序如下：

1. 当前输入本体和用户限定范围
2. `../../spec/投研本体核心规范/schemas/objects.yaml`
3. `../../spec/投研本体核心规范/schemas/relations.yaml`
4. `../../spec/投研本体核心规范/schemas/actions.yaml`
5. `../../spec/投研本体核心规范/references/01_投研本体核心说明.md`
6. `../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md`
7. `../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`
8. `schemas/本体缺口发现输出结构.yaml`
9. `schemas/本体缺口发现输出结构.json`
10. `examples/*`

## 工作流程

1. **确认本体范围**：读取版本、范围、对象/关系规模、证据覆盖和已知限制。多本体输入时先记录边界与冲突。
2. **识别来源可靠性**：记录来源类型、发布时间、业务时间、发布主体、原文位置和可靠性。
3. **生成内部缺口发现视图**：从 `evidence_claims.yaml` 生成 `_work/gap_reference_view/`，按来源和逻辑类型（事实观测、分析假设、传导逻辑、验证信号、反证条件、情景路径、资产映射、作者判断、受限内容）组织，供后续诊断和人工阅读。
4. **抽取外部研究逻辑**：从 evidence claims 中拆成事实观测、分析假设、传导逻辑、验证信号、反证条件、情景路径、资产映射、作者判断和受限内容。
5. **逐条覆盖对照**：先检查 `01_concepts.yaml` 是否能解释术语、范围和边界，再按 `02_objects.yaml`、`03_relations.yaml`、`04_actions.yaml`、`05_reasoning.yaml`、`06_evidence.yaml`、`07_governance.yaml` 检查覆盖。
6. **生成缺口建议**：输出 `gap_recommendations`，说明缺口类型、覆盖等级、建议动作、证据要求、收益和风险；可执行缺口必须尽量提供 `target_file`、`target_path`、`target_id` 和可选 `legacy_path`。
7. **控制本体膨胀**：对低可靠、低价值、单一来源、不可验证或越界内容执行 `defer` 或 `reject`。
8. **生成候选补丁请求**：把适合后续修复的缺口转成 `candidate_patch_requests`，每项绑定 `evidence_episode_ids`、`evidence_claim_ids`、目标层、目标文件、目标路径、建议动作和审核状态。
9. **生成优化任务单**：把适合后续修复的缺口转成 `optimization_plan`，并写明材料要求、停止条件和禁止事项。
10. **输出报告和交接块**：报告给人读，交接块和候选 patch 请求给后续 Skill 执行。

## 缺口类型

`gap_type` 必须使用 schema 中的 7 类枚举，不得随意新增顶层类型。

| `gap_type` | 使用场景 |
|---|---|
| `object_gap` | 缺研究对象、事件、来源文档、关键锚点，或缺 `Concept`、`ConceptScheme`、`ConceptBoundary` 等概念层锚点。 |
| `state_variable_gap` | 缺状态变量、变量口径、变量粒度或状态观测。 |
| `relation_gap` | 缺业务结构关系、传导关系、假设依赖、来源追溯或动作链。 |
| `signal_gap` | 缺验证、催化、跟踪、削弱、阻断信号或信号状态。 |
| `scenario_path_gap` | 缺 base/upside/downside、反证路径、竞争解释或修复路径。 |
| `asset_mapping_gap` | 缺资产锚点、资产影响、预期差、估值锚或定价状态。 |
| `schema_gap` | 核心 schema 无法准确表达该类逻辑。 |

子类写入 `suggested_change`、`scope_boundary` 或 `handoff_requirement`，不要增加非 schema 字段。

## 覆盖等级

| 等级 | 判定标准 |
|---|---|
| `fully_covered` | 对象、变量、关系、信号、证据、时间和动作链均能表达。 |
| `partially_covered` | 主链路存在，但口径、观测、信号、情景、资产映射或来源不完整。 |
| `weakly_covered` | 只能用过粗对象、泛化字段或文本说明承接，推理会丢关键结构。 |
| `not_covered` | 没有可承接该逻辑的对象、关系、字段或路径。 |
| `conflicting` | 当前本体与来源逻辑或核心规范冲突。 |
| `out_of_scope` | 逻辑有价值，但超出当前本体范围或本轮目标。 |

`fully_covered` 不能只看对象是否存在。只有表达能力、证据质量、一致性和推理可用性都满足时，才算完整覆盖。

## 建议动作

`operation` 使用 schema 枚举：`add`、`split`、`merge`、`downgrade`、`supplement_evidence`、`revise_relation`、`add_blocking_signal`、`defer`、`reject`。

| 情况 | 建议动作 |
|---|---|
| 缺对象、变量、观测、传导、假设、信号、判断或资产影响 | `add` |
| 变量过粗、主题变量进入推理链 | `split` |
| 对象重复、口径重叠 | `merge` |
| 判断、假设或信号状态与证据不匹配 | `downgrade` |
| 缺来源、事实观测、验证信号或交叉验证 | `supplement_evidence` |
| 关系端点、方向、挂载对象或来源追溯错误 | `revise_relation` |
| 出现明确阻断条件 | `add_blocking_signal` |
| 单一弱来源、收益不明确或证据不足 | `defer` |
| 越界、低价值、不可验证或违反合规边界 | `reject` |

## 输出

正式交付为两个文件：

| 文件 | 格式 | 用途 |
|---|---|---|
| `{研究主题}_缺口发现报告.md` | Markdown | 面向投研人员和本体维护者，结论先行说明覆盖状态、关键缺口和下一步。 |
| `{研究主题}_缺口发现结果交接块.yaml` | YAML | 面向后续 AI / Skill，包含结构化缺口、优化计划、材料要求、约束和禁止事项。 |
| `candidate_patch_requests.yaml` | YAML | 面向 08-任务合并 和 09-优化，记录由缺口触发的候选 PatchRequest，不代表正式改动。 |
| `restricted_items.md` | Markdown | 受限内容清单及隔离说明。 |

YAML 必须符合 `schemas/本体缺口发现输出结构.yaml`，并包含：

- `gap_discovery_context`
- `logic_extraction`
- `ontology_coverage_assessment`
- `gap_recommendations`
- `optimization_plan`
- `handoff_block`
- `optimization_handoff`
- `compliance_check`

`candidate_patch_requests.yaml` 每项至少包含：

```yaml
patch_request_id: PRQ-YYYYMMDD-001
source_gap_ids: []
evidence_episode_ids: []
evidence_claim_ids: []
target_layer: object
target_file: 02_objects.yaml
target_path: ""
target_id: ""
suggested_operation: add
reason: ""
semantic_risk: medium
review_status: pending
```

两份文件中的 `discovery_id`、`gap_id`、`plan_id` 必须一致。`optimization_plan` 是任务单，不等于已完成修改。

## 报告要求

Markdown 报告控制在 800-1500 字，详情使用 `<details>` 折叠。必须包含：

1. 结论：覆盖充分度、严重缺口、膨胀风险和材料可靠性。
2. 覆盖分析：按研究主题说明 fully/partially/weak/not/conflicting/out_of_scope。
3. 关键缺口：列出最重要的 P0/P1 缺口、影响和修复方向。
4. 下一步：映射到 `optimization_plan` 的可执行行动。

## 禁止事项

- 不修改本体，不输出 `ontology_bundle_vN/` 或 `optimized_ontology`。
- 不跳过材料可靠性判断直接生成修复动作。
- 不把预测、评级、目标价、推荐语、收益率推断或仓位表达映射为事实观测。
- 不自动应用 `schema_gap`，只输出核心变更建议或阻断说明。
- 不把 `candidate_patch_requests.yaml` 当作已合并补丁；正式合并只能由本体优化 Skill 执行。
- 不把概念层缺失直接当作业务对象缺失；应先说明需要补概念定义、边界裁定还是概念到对象映射。
- 不生成买卖建议、目标价、收益率预测或仓位建议。

## 本地校验

```bash
python3 scripts/validate_skill.py
```
