---
name: touyan-tuili
description: 当用户提供一个或多个投研本体，并希望围绕事件、观点、研报、标的、组合或客户问题做链路推理时使用。输出 reasoning_result、scenario_output、ontology_feedback 和 compliance_check。本 Skill 不创建或优化本体，不绕过本体编造链路，不生成投资建议、目标价、收益率预测或仓位建议。
metadata:
  short-description: 投研推理
---

# 投研推理 Skill

## 定位

本 Skill 是投研本体的应用推理入口。它基于当前输入本体，把用户问题映射为“对象-状态变量-传导关系-假设-验证信号-反证条件-资产影响线索”的结构化推理结果。引入 Temporal Evidence Layer 后，它还要按 business time 检索当前有效 evidence，排除已失效 claim，并记录 InferenceRun。

本 Skill 使用本体，不维护本体。命中不足、弱推理、误触发或漏触发只写入 `ontology_feedback`，供缺口发现或优化流程处理。

## 输入基座

必须提供或能定位一个本体基座：

| 输入 | 说明 |
|---|---|
| `ontology_bundle_vN/` | 单一本体，优先读取。 |
| `_compat/optimized_ontology_vN.json` / 旧单体 `ontology` | 兼容输入。 |
| 多 bundle 组合 | 必须先登记范围、冲突和共同对象。 |
| 材料质量、变更说明、来源摘要 | 可选。仅用于理解本体成熟度和限制。 |
| `_artifacts/evidence_graph/evidence_claims.yaml` / `evidence_facts.yaml` | 可选但建议。用于检索当前有效证据和失效证据。 |
| `_artifacts/patches/patch_ledger.yaml` | 可选。用于理解本体增量演化和近期变更依据。 |

没有本体基座时，不得凭常识生成“本体推理结果”。涉及最新事件、政策、公告、价格、市场数据或公司动态时，必须核验事实和发布时间，并保留可追溯来源。

## 核心依据

冲突裁定顺序如下：

1. 当前任务提供的本体输入
2. 当前本体 `07_governance.yaml` 中的 `retrieval_policy`（若存在）——推理检索策略的机器可读契约，优先级高于本 Skill 的默认遍历规则
3. `../../spec/投研本体核心规范/schemas/objects.yaml`
4. `../../spec/投研本体核心规范/schemas/relations.yaml`
5. `../../spec/投研本体核心规范/schemas/actions.yaml`
6. `../../spec/投研本体核心规范/schemas/governance.yaml`——retrieval_policy 的正式 schema 定义
7. `../../spec/投研本体核心规范/schemas/reasoning_trace.yaml`——RuleApplication 和 ReasoningStep 的正式 schema 定义
8. `../../spec/投研本体核心规范/references/01_投研本体核心说明.md`
9. `../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md`
10. `../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`
11. `references/A03_研报级输出说明.md`
12. `schemas/投研推理输出结构.json`
13. `examples/*`

## 输出模式

用户未指定时，默认输出通用投研推理版。

| 模式 | 触发 | 输出重点 |
|---|---|---|
| 通用投研推理 | 一般问题 | 触发点、链路、假设、验证、反证。 |
| 事件影响推理 | 新闻、政策、订单、价格变化 | 事件事实、本体命中、变量和传导路径。 |
| 观点拆解 | “这个逻辑成立吗” | 显性逻辑、隐含假设、证据缺口和竞争解释。 |
| 研报链路抽取 | 研报、纪要、观点材料 | 核心逻辑、共识/非共识、缺口反馈。 |
| 投资经理质询 | “该问什么” | 质询清单、证据要求、定价问题和风险暴露。 |
| 客户解释 | “客户怎么说” | 通俗说明、事实/推断/风险分层。 |
| 标的/组合暴露 | 公司、持仓、组合 | 共同变量、差异驱动、资产暴露。 |
| 研究资产沉淀 | “沉淀成框架” | 可复用变量、链路、信号和本体缺口。 |
| 研报级输出 | 明确要求完整研报 | 使用 `references/A03_研报级输出说明.md`。 |

## 工作流程

1. **确认本体基座**：读取 bundle manifest、版本、范围、对象、关系、来源和限制。
2. **读取 Retrieval Policy**：优先读取 `07_governance.yaml` 中的 `retrieval_policy`，获取 entry_points、traversal_order、required_checks、source_authority_ranking、freshness_policy、fallback_policy 和 blocking_rules。若 `governance_capabilities` 不含 `retrieval_policy` 或 `07_governance.yaml` 不包含 `retrieval_policy`，回退到本 Skill 的默认遍历规则（见「关系检索规则」节）。
3. **识别用户意图**：选择输出模式、目标角色和回答粒度。
4. **解析概念和边界**：先读取 `01_concepts.yaml`，判断用户词汇的定义、同义词、范围状态和是否映射到业务对象。
5. **映射对象和变量**：在 `02_objects.yaml` 和 `05_reasoning.yaml` 内定位行业、公司、产品、材料、事件、资产和状态变量。
6. **检索关系和传导**：按 `retrieval_policy.traversal_order`（若有）或默认遍历规则，沿 `03_relations.yaml` 的显式概念映射、业务结构关系、变量传导、假设、信号、判断和资产影响关系进行图遍历。
7. **检索 Temporal Evidence**：按 `retrieval_policy.source_authority_ranking` 和 `retrieval_policy.freshness_policy`（若有）过滤 evidence，排除 `invalidatedAt` 已存在、`validTo` 早于目标时间或被 `claimInvalidatesClaim` 覆盖的证据。
8. **执行 Required Checks**：按 `retrieval_policy.required_checks`（若有）在每个遍历阶段执行信号检查、反证检查、市场预期检查和催化剂检查。缺失检查项不得沉默跳过——应记录为 gap 或降低置信度。
9. **形成链路推理**：输出触发点、状态变化、传导路径、成立条件、验证信号和反证条件。
10. **处理缺失和弱命中**：缺概念、缺边界、缺映射、缺对象、缺关系、缺证据或链路断点必须写入 `ontology_feedback`，不得伪装成已存在链路。
11. **记录 RuleApplication 和 ReasoningStep**：按 `schemas/reasoning_trace.yaml` 的定义，为每条被调用的规则生成 `RuleApplication` 记录，为每一步图谱导航生成 `ReasoningStep` 记录。两者通过 `inference_run_id` 关联到 `InferenceRun`。
12. **记录 InferenceRun**：写入使用的对象、关系、evidence claims、被排除的 invalid claims、推理链、置信度和 candidate_patch_requests。
13. **生成场景化表达**：按模式输出研究员版、质询版、客户解释版、组合暴露版或研报版。
14. **合规检查**：区分事实、估算、假设、判断和情景，不给交易建议。

## 关系检索规则

**优先级说明**：若 `07_governance.yaml` 的 `retrieval_policy` 存在，其 `traversal_order`、`required_checks`、`source_authority_ranking`、`freshness_policy`、`fallback_policy` 和 `blocking_rules` 优先于以下默认规则。以下规则仅在 `retrieval_policy` 缺失或不完整时作为回退。

- 先找业务结构关系：`segmentConnectsToSegment`、`companyRelatesToCompany`、`productRelatesToProduct`、`materialUsedInProduct`、`assetExposedToTarget`、`eventRelatesToEvent`、`eventAffectsVariable`。
- 用户词汇先经过 `Concept`、`conceptIncludes`、`conceptOverlapsWith`、`conceptExcludes`、`ConceptBoundary` 和 `conceptMapsToObject` 解析范围与映射。
- 再找变量和观测挂载：`observedOn`、`anchoredOn`、`eventProducesObservation`。
- 变量传导必须经过 `StateVariablePropagation` 与 `propagatesFrom` / `propagatesTo`。
- 假设链必须经过事件、变量、信号和假设关系。
- 判断链必须经过假设、信号和判断关系。
- 资产影响只能从判断、假设或变量链路派生，再连接资产；不得从新闻直接跳到股价或估值结论。
- Evidence claim 检索必须遵守时间过滤：目标 business time 早于 `validFrom` 或晚于 `validTo` 的 claim 不得作为当前有效证据。
- `claimStatus=invalidated/superseded/rejected/quarantined` 的 claim 不得作为当前有效证据，但可进入“历史上曾经有效/被排除证据”说明。

## 输出

用户要求 JSON、结构化结果或自动评估时，按 `schemas/投研推理输出结构.json` 输出：

```json
{
  "reasoning_result": {},
  "scenario_output": {},
  "ontology_feedback": {},
  "compliance_check": {}
}
```

`reasoning_result` 包含本体上下文、问题理解、证据包、本体检索、推理链、关键假设、验证信号、反证条件、数据缺口和置信度。

`scenario_output` 按用户场景生成表达结果，必须声明模式、目标角色和输出章节。

`ontology_feedback` 记录缺失对象、缺失关系、弱推理、误触发、漏触发、证据空白和建议补充材料；反馈项应尽量包含 `target_file`、`target_path`、`target_id` 和可选 `legacy_path`。

`compliance_check` 记录事实/估算/预测/假设/判断是否分层，以及是否避开禁止内容。

每次推理还应归档：

```text
_artifacts/reasoning_runs/
  inference_run_{id}.yaml
  inference_run_{id}/
    rule_applications.yaml
    reasoning_steps.yaml
```

`inference_run` 至少包含：

```yaml
question: ""
business_time: ""
ontology_version: ""
center_objects: []
used_relations: []
used_evidence_claims: []
excluded_invalid_claims: []
signals: []
counters: []
reasoning_chain: []
confidence: medium
ontology_feedback: []
candidate_patch_requests: []
rule_application_ids: []
reasoning_step_ids: []
```

`rule_applications.yaml` 中每条记录（按 `schemas/reasoning_trace.yaml` 的 RuleApplication 定义）：

```yaml
- rule_id: ""
  inference_run_id: ""
  step_order: 1
  input_state_changes: []
  consumed_signals: []
  checked_counters: []
  market_expectation_checked: false
  catalyst_checked: false
  conclusion: ""
  confidence: medium
  evidence_refs: []
  trace_id: ""
```

`reasoning_steps.yaml` 中每条记录（按 `schemas/reasoning_trace.yaml` 的 ReasoningStep 定义）：

```yaml
- inference_run_id: ""
  step_order: 1
  step_type: relation_traversal
  input_object_ids: []
  relations_traversed: []
  output_object_ids: []
  evidence_consumed: []
  decision: ""
  confidence: medium
  rule_application_id: ""
  trace_id: ""
```

推理反馈需要反哺生产时，进入 `ontology_feedback` 或 `candidate_patch_requests`，再由缺口发现、任务合并和优化 Skill 处理；本 Skill 不直接修改本体。

## 禁止事项

- 不绕过本体基座凭常识补链路。
- 不把单一新闻直接推成长周期结论。
- 不使用已失效、被替代、被隔离或超出有效期的 claim 作为当前有效证据。
- 不把分析师预测、评级、目标价或推荐语当作事实观测。
- 不输出买卖建议、目标价、收益率预测或仓位建议。

## 本地校验

```bash
python3 scripts/validate_skill.py
```
