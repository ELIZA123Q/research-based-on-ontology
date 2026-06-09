# Evidence Episode 归一与校验要求

本文件定义如何把来源材料、历史案例、推理反馈、评测反馈和结构化数据归一为 Temporal Evidence Layer。本 Skill 只做证据归一、时间字段补齐和质量校验，不修改正式本体。

## 1. 输入优先级

1. 用户明确提供的研究范围、时间窗口和排除边界。
2. `source_registry.json` 中可追溯、可靠性不低于 low 且与主题相关的材料。
3. `source_quality_assessment.md` 中标记为可用于缺口发现、历史回放、优化或评测的材料。
4. `_artifacts/material_graph/` 中的 Document/Chunk、候选对象关系、候选信号和证据片段索引。
5. `_artifacts/historical_replay/` 中的 t0 信息包、回放证据、误触发、漏触发和失效候选。
6. `_artifacts/reasoning_runs/` 中的推理反馈、未命中项和候选 patch 请求。
7. `_artifacts/evaluation_results/` 中的评测失败项和补证需求。

没有可追溯输入时，不生成 evidence claims，只输出阻断说明。

## 2. EvidenceEpisode

每次材料或反馈摄入生成一个 `EvidenceEpisode`。

最小字段：

```yaml
- id: EPI-YYYYMMDD-001
  title: ""
  episodeType: source_material
  sourceDocumentId: ""
  sourcePathOrUrl: ""
  publishTime: ""
  businessTime: ""
  ingestedAt: ""
  sourceReliability: high
  episodeStatus: ingested
  originalLocation: ""
  textSpan: ""
  limitations: []
  groupId: ""
```

规则：

- `source_material` episode 应优先来自 6-1 的 `source_registry.json`。
- 若存在 6-1b 的 `_artifacts/material_graph/evidence_fragment_index.yaml`，claim 的 `evidenceLocation` 应优先绑定到 fragment/chunk ID，再回链到原始 source。
- `historical_case` episode 必须区分 t0 可见信息和事后验证信息。
- `reasoning_feedback` episode 只能作为本体反馈或 patch 线索，不得直接作为事实观测。
- `evaluation_feedback` episode 只能作为修复任务来源，不得按隐藏答案定向优化。

## 3. EvidenceClaim

一条 claim 只表达一个事实、估算、预测、假设、传导、信号、反证、情景、资产映射或受限内容。

最小字段：

```yaml
- id: ECL-YYYYMMDD-001
  episodeIds: [EPI-YYYYMMDD-001]
  claimText: ""
  normalizedClaim: ""
  claimType: fact_observation
  claimStatus: candidate
  sourceStatementType: fact
  evidenceLocation: ""
  confidence: 0.0
  validFrom: ""
  validTo: ""
  observedAt: ""
  learnedAt: ""
  invalidatedAt: ""
  invalidatedBy: ""
  supersedes: []
  supersededBy: []
  allowedTargetObjectTypes: []
  mustNotMapTo: []
  scope: ""
  restrictions: []
```

`claimType` 使用核心规范枚举：

```text
fact_observation / estimate / forecast / assumption / transmission_logic /
validation_signal / falsification_condition / scenario_path / asset_mapping /
author_judgment / restricted_item
```

规则：

- `fact_observation` 必须来自公告、财报、政策原文、官方数据、可追溯行业数据或可核验新闻事实。
- `forecast`、`author_judgment`、`restricted_item` 不得映射为 `StateVariableObservation`。
- `transmission_logic` 可以作为传导候选，但必须保留边界条件和方向。
- `falsification_condition` 可作为 weakening/blocking 信号候选。
- 无原文位置、无来源时间或无法追溯的 claim 必须标记为 `quarantined` 或 `rejected`。

## 4. EvidenceFact

`EvidenceFact` 是多个 claim 归并后的结构化事实候选。

最小字段：

```yaml
- id: EF-YYYYMMDD-001
  factText: ""
  normalizedFact: ""
  factStatus: candidate
  factScope: ""
  confidence: 0.0
  validFrom: ""
  validTo: ""
  observedAt: ""
  learnedAt: ""
  invalidatedAt: ""
  invalidatedBy: ""
  sourceClaimIds: []
```

规则：

- EvidenceFact 必须由 claim 支撑，不得凭常识生成。
- 多个来源冲突时，不合并成单一事实；保留冲突 claim，并生成 `invalidation_candidates.yaml` 或冲突说明。
- EvidenceFact 只能作为正式对象、观测、信号或关系候选来源。

## 5. Invalidation Candidates

当新 claim/fact 显示旧 claim/fact/signal/relation 不再成立、适用范围变窄、证据质量降级或被替代时，输出失效候选。

最小字段：

```yaml
- invalidation_id: INV-YYYYMMDD-001
  new_evidence_claim_id: ECL-YYYYMMDD-010
  target_type: EvidenceClaim
  target_id: ECL-YYYYMMDD-001
  invalidation_type: superseded
  invalidation_reason: ""
  valid_to_suggestion: ""
  confidence: medium
  requires_review: true
```

失效候选不等于正式失效；正式本体对象、关系、信号或判断的失效必须由优化 Skill 或对应动作合并。

## 6. Validation Report

`evidence_graph_validation_report.md` 至少包含：

1. 输入范围和来源概览。
2. Episode 数量、类型、可靠性和时间覆盖。
3. Claim 数量、类型、状态和受限内容统计。
4. Fact 归并结果和冲突说明。
5. 失效候选和需要人工确认项。
6. 可交接给 6-2、2-1、2-2、6-4、3、5 的内容。
7. 阻断项和修复建议。

## 7. 交接规则

- 给 6-1b：消费其 material graph，不回写候选对象关系。
- 给 6-2：交接 `evidence_claims.yaml` 和 `evidence_facts.yaml`，由 6-2 生成缺口发现 reference view。
- 给 2-2：交接历史 episode、t0 evidence 和失效候选。
- 给 6-4：交接可转成 patch queue 的 evidence claim 和 invalidation candidate。
- 给 3：交接待审核 evidence 和 patch 支撑关系，正式合并仍由优化 Skill 决定。
- 给 5：交接当前有效 claim、失效 claim 和可按 business_time 过滤的证据包。

## 8. 禁止事项

- 不修改正式本体。
- 不生成正式 patch ledger。
- 不判断本体覆盖。
- 不输出投资建议、目标价、收益率预测或仓位建议。
- 不把受限内容或无法追溯材料升级为事实观测。
