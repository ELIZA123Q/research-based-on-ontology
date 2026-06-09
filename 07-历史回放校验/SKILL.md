---
name: touyan-benti-lishi-huifang-xiaoyan
description: 当已有 base_ontology_bundle、ontology_bundle_vN 或兼容旧本体，需要用历史案例校验传导链、阻断条件、变量颗粒度、时间滞后、误触发、漏触发和资产影响边界时使用。输出历史回放校验报告、诊断建议和 optimization_plan。本 Skill 不修改本体，不输出 ontology_bundle，不生成投资建议、目标价、收益率预测或仓位建议。
metadata:
  short-description: 本体历史回放校验
---

# 投研本体历史回放校验 Skill

## 定位

本 Skill 用历史样本检验已有本体是否能在 t0 时点基于当时可得信息做出合理推理。它不是事后复盘文章生成器，而是本体有效性测试器。引入 Temporal Evidence Layer 后，本 Skill 还需要记录 t0 可见 evidence、验证窗口内的新 evidence、以及对旧 claim/signal/relation 的失效或替代候选。

本 Skill 只输出诊断、校验建议和 `optimization_plan`，不直接修改本体。

## 输入

| 输入 | 要求 |
|---|---|
| `base_ontology_bundle/` / `ontology_bundle_vN/` | 必填其一。作为待校验本体，优先读取。 |
| `_compat/base_ontology.json` / `_compat/optimized_ontology_vN.json` / 旧单体 JSON | 兼容输入。 |
| `historical_cases` | 必填或可由材料生成。必须包含事件、t0、t0 可得信息、验证窗口、实际结果和来源。 |
| `_artifacts/evidence_graph/evidence_episodes.yaml` / `evidence_claims.yaml` | 可选。用于标记 t0 可见证据、事后证据和失效候选。 |
| `validation_focus` | 可选。限定对象、变量、关系、传导链、信号、阻断条件或资产影响。 |
| `ontology_feedback` | 可选。来自推理失败、误触发、漏触发或证据空白反馈。 |

缺少历史样本时，不得标记“历史支持”；只能输出需要补样本的诊断和任务。

## 核心依据

冲突裁定顺序如下：

1. 当前输入本体、历史案例和用户限定范围
2. `../../spec/投研本体核心规范/schemas/objects.yaml`
3. `../../spec/投研本体核心规范/schemas/relations.yaml`
4. `../../spec/投研本体核心规范/schemas/actions.yaml`
5. `../../spec/投研本体核心规范/references/01_投研本体核心说明.md`
6. `../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md`
7. `../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`
8. `schemas/本体历史回放校验输出结构.json`
9. `examples/*`

## 工作流程

1. **确认本体和范围**：读取 bundle manifest、`01_concepts.yaml`、范围、对象、关系、传导模板、假设、信号、情景和资产影响线索。
2. **拆解可校验断言**：把本体项拆成可被历史样本验证的 claim，例如对象有效性、变量可观察性、关系方向、传导机制、假设解释力、信号有效性、阻断条件、资产影响边界。
3. **构造样本集**：样本必须覆盖正向触发、反向失败、边界样本和留出样本。不得只选支持本体的案例。
4. **冻结 t0 信息**：每个案例必须列出 t0 可得信息、信息来源和禁止使用的事后信息。
5. **执行时间回放**：基于 t0 信息运行本体预期链路，再与验证窗口内实际结果比较。
6. **生成 temporal replay evidence**：记录每个案例中 t0 可见的 `evidence_episode_ids` / `evidence_claim_ids`、验证窗口内新增证据、被排除的事后信息和 claim 有效状态。
7. **诊断本体问题**：识别过度泛化、变量过粗、时滞错误、缺阻断条件、弱信号、误触发、漏触发、证据缺口、失效证据未过滤和资产跳跃。
8. **生成失效候选**：对历史上误触发、范围收窄、被新事实替代或证据质量降级的 claim/signal/relation 输出 `invalidation_candidates`。
9. **生成校验建议**：每条建议绑定历史案例、受影响本体组件、evidence ids 和失效候选。
10. **生成优化任务单**：把可执行建议转成 `optimization_plan`，并写明材料要求、优先级、停止条件和禁止事项；任务项尽量提供 `target_file`、`target_path`、`target_id` 和可选 `legacy_path`。

## 样本规则

| 案例类型 | 用途 | 最低要求 |
|---|---|---|
| `positive_trigger` | 本体链路应该被触发的正面案例 | 至少 1 例。 |
| `negative_failure` | 看似应触发但实际失败或未兑现的反面案例 | 至少 1 例。 |
| `boundary_case` | 检查边界条件、时滞、阈值和适用范围 | 至少 1 例。 |
| `holdout_case` | 未参与构建的独立验证案例 | 至少 1 例。 |

若无法满足四类覆盖，必须降低结论置信度，并把补样本写入 `optimization_plan`。

## t0 防泄漏规则

- t0 是本体应当开始判断的业务时间，不一定等于材料发布时间。
- `t0_available_information` 只能包含 t0 当时可获得的信息。
- t0 之后披露的财报、公告、价格结果、复盘结论和最终影响不能进入 t0 预期链。
- 可以在 `actual_outcome` 使用 t0 后结果评估命中与否，但必须与 t0 输入分离。
- 每个案例必须有 `leakage_guardrail`，说明如何避免事后信息污染。

## 诊断规则

常见诊断项包括：

| 问题 | 处理 |
|---|---|
| 传导命中但解释不足 | 补传导机制、变量口径、证据或时滞。 |
| 正向案例漏触发 | 检查缺变量、缺事件关系、缺信号或阈值过高。 |
| 反向案例误触发 | 检查缺阻断条件、竞争解释、情景分叉或边界条件。 |
| 边界样本失效 | 拆变量、补适用范围、补阈值或降级假设。 |
| 概念边界失效 | 补 `ConceptBoundary`、调整 `scopeStatus` 或修正 `conceptMapsToObject`。 |
| 资产影响跳跃 | 补判断到资产的中间链路、定价状态和验证信号。 |
| 来源不可追溯 | 补 `SourceDocument` 和来源关系，或降低证据等级。 |

## 输出

输出严格 JSON 对象，符合 `schemas/本体历史回放校验输出结构.json`。必须包含：

```json
{
  "historical_validation_context": {},
  "assertion_decomposition": [],
  "historical_case_set": {},
  "case_replays": [],
  "ontology_diagnostics": {},
  "validation_recommendations": {},
  "ontology_health": {},
  "optimization_plan": [],
  "optimization_handoff": {},
  "compliance_check": {},
  "readable_report": ""
}
```

不得包含 `ontology_bundle` 或 `optimized_ontology`。

同时输出以下归档文件：

```text
_artifacts/historical_replay/temporal_replay_evidence.yaml
_artifacts/historical_replay/invalidation_candidates.yaml
```

`temporal_replay_evidence.yaml` 至少记录：

```yaml
- case_id: ""
  t0_business_time: ""
  t0_visible_evidence_episode_ids: []
  t0_visible_evidence_claim_ids: []
  post_t0_excluded_claim_ids: []
  validation_window_claim_ids: []
  triggered_signals: []
  missed_signals: []
  invalidated_claim_ids: []
```

`invalidation_candidates.yaml` 至少记录：

```yaml
- invalidation_id: INV-YYYYMMDD-001
  source_case_id: ""
  new_evidence_claim_id: ""
  target_type: EvidenceClaim|Signal|Relation|StateHypothesis|JudgmentOutput
  target_id: ""
  invalidation_type: expired|contradicted|superseded|scope_changed|misfire
  invalidation_reason: ""
  requires_review: true
```

`readable_report` 控制在 800-1500 字，包含结论、案例分析、指标与诊断、下一步。详情表格可使用 `<details>` 折叠。

## 禁止事项

- 不用事后结果污染 t0 判断。
- 不只选择成功案例或支持本体的案例。
- 不把历史回放写成投资复盘或收益归因。
- 不把研报预测、评级、目标价或推荐语作为事实观测。
- 不把 `invalidation_candidates.yaml` 当作正式失效动作；正式失效或废弃必须由优化 Skill 或对应动作合并。
- 不输出买卖建议、目标价、收益率预测或仓位建议。

## 本地校验

```bash
python3 scripts/validate_skill.py
```
