# 本体生产流程

公共文件契约见 `../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`。

## 流程总览

```text
用户输入
  -> 输入识别与生产模式判断
  -> 信息与数据搜索
  -> 材料图谱预处理（Document→Chunk→Entity→Relationship）
  -> 冷启动或读取已有 bundle
  -> 证据归一与校验
  -> 缺口发现（内部从 evidence_claims 生成 gap_reference_view）
  -> 历史案例生成
  -> 历史回放
  -> 生产任务合并
  -> 本体优化
  -> 人类可读解析
  -> 评测数据输入生成
  -> release package 组装与校验（含 source_material_summary.md 生成）
  -> 交给评测 Agent
```

不是每一轮都必须调用全部步骤。Agent 根据输入类型、已有材料和用户目标选择最小必要流程，但不得跳过冷启动 Skill 生成 `base_ontology_bundle/`，也不得跳过本体优化 Skill 生成 `ontology_bundle_vN/`。

## 场景 A：新主题冷启动

适用条件：

- 用户只给研究主题或关键词。
- 没有可用 `current_ontology_bundle/`、`ontology_bundle_vN/` 或兼容旧本体。

流程：

1. 读取 `research_topic.md`、`raw_materials/` 和用户约束。
2. 调用信息与数据搜索 Skill，生成 `source_materials/`、`source_registry.json`、`source_search_log.md` 和 `source_quality_assessment.md`。
3. 调用材料图谱预处理 Skill，将 `source_materials/` 按 Document→Chunk→Entity→Relationship 分层拆解，schema 约束优先使用 `spec/schemas/` 公共规范（冷启动首轮），生成 `_artifacts/material_graph/`。
4. 调用冷启动 Skill，参考候选图谱结构，生成 `base_ontology_bundle/`、可选 `_compat/base_ontology.json`、`cold_start_report.md` 和 `downstream_task_list.md`。
5. 调用证据归一与校验 Skill，消费 `_artifacts/material_graph/`，生成 `_artifacts/evidence_graph/evidence_episodes.yaml`、`evidence_claims.yaml`、`evidence_facts.yaml`、`invalidation_candidates.yaml` 和 `evidence_graph_validation_report.md`。
6. 调用缺口发现 Skill，基于 `base_ontology_bundle/` 和 `evidence_claims.yaml`（内部生成 `_work/gap_reference_view/`），输出 `gap_report.md`、`gap_items.json`、`optimization_suggestions.md`、`candidate_patch_requests.yaml` 和 `restricted_items.md`。
7. 调用历史案例生成 Skill，生成 `historical_materials/`、`historical_case_generation_report.md` 和 `replay_task_list.md`。
8. 调用历史回放 Skill，基于 `base_ontology_bundle/`、`historical_materials/` 和 `replay_task_list.md` 输出 `historical_cases.json`、`replay_report.md`、`evidence_chain.md`、`temporal_replay_evidence.yaml` 和 `invalidation_candidates.yaml`。
9. 调用生产任务合并 Skill，输出 `optimization_task_list.md`、`optimization_task_items.json`、`patch_request_queue.yaml` 和 `priority_decision.md`。
10. 调用本体优化 Skill，生成 `ontology_bundle_vN/`、`_compat/optimized_ontology_vN.json` 和 `_artifacts/patches/patch_ledger.yaml`。
11. 调用人类可读解析 Skill，生成 `docs/ontology_guide.md`。
12. 调用评测数据输入生成 Skill，生成 `_artifacts/evaluation_results/evaluation_data_inputs/` 和 `docs/evaluation_handoff.md`。
13. 调用 Release Package 组装与校验 Skill，聚合来源材料元数据生成 `source_material_summary.md`，组装并输出 `release_package/`。

结束条件：

- `release_package/` 文件齐全。
- `_artifacts/` 全量归档。
- 没有输出发布结论。

## 场景 B：已有本体优化

适用条件：

- 用户提供 `current_ontology_bundle/`、`ontology_bundle_vN/`、`base_ontology_bundle/` 或兼容 JSON。
- 用户希望吸收新材料、缺口发现、历史回放、评测反馈、推理反馈或修订请求。

流程：

1. 读取现有 bundle；若只有旧 JSON，先作为兼容输入登记，并在优化产物中导出 bundle。
2. 读取可选输入：`raw_materials/`、缺口发现、历史回放、评测反馈、推理反馈和用户修订。
3. 缺少外部研究材料时，调用信息与数据搜索 Skill。
4. 对新材料，调用材料图谱预处理 Skill，schema 约束优先使用当前本体版本的 schema，抽取候选图谱结构。
5. 对新材料、新事件、历史案例、评测反馈或推理反馈，调用证据归一与校验 Skill，消费候选图谱结构形成 evidence graph。
6. 需要补强覆盖时，调用缺口发现 Skill（内部从 evidence_claims.yaml 生成 gap_reference_view）。
7. 需要验证传导链、阻断条件、时间有效性或历史解释力时，调用历史案例生成和历史回放 Skill。
8. 调用生产任务合并 Skill，形成 bundle 路径化的优化任务单和 patch_request_queue。
9. 调用本体优化 Skill，生成 `ontology_bundle_vN+1/`、`_compat/optimized_ontology_vN+1.json` 和 patch ledger。
10. 调用人类可读解析 Skill，生成 `docs/ontology_guide.md`。
11. 调用评测数据输入生成 Skill，生成评测交接。
12. 调用 Release Package 组装与校验 Skill（含 source_material_summary.md 生成）。

## 场景 C：评测未通过后的修复

适用条件：

- 用户提供评测报告或缺陷票据。

流程：

1. 读取候选 bundle、`evaluation_report.md` 和 `defect_tickets.json`。
2. 将评测失败项转为带 `target_file`、`target_path`、`target_id` 的生产修复任务。
3. 数据不足时，调用信息与数据搜索或评测数据输入生成 Skill 回补材料。
4. 将回补材料和评测反馈送入证据归一与校验 Skill。
5. 覆盖不足时，调用缺口发现 Skill（内部从 evidence_claims.yaml 生成 gap_reference_view）。
6. 传导、阻断、误触发、漏触发问题时，调用历史案例生成和历史回放 Skill。
7. 调用生产任务合并 Skill，生成 patch_request_queue。
8. 调用本体优化 Skill，生成修复版 `ontology_bundle_vN+1/` 和 patch ledger。
9. 重新生成文档、评测交接和 release package（含 source_material_summary.md）。

禁止事项：

- 不修改评测集。
- 不根据隐藏评测答案定向优化。
- 不将评测未通过修复直接标记为发布通过。

## 场景 D：只有材料、没有本体

流程：

1. 从材料中识别研究主题和范围。
2. 调用信息与数据搜索 Skill 补充来源登记。
3. 调用材料图谱预处理 Skill，将材料按 Document→Chunk→Entity→Relationship 分层拆解，抽取候选图谱结构。
4. 调用证据归一与校验 Skill，消费候选图谱结构形成 evidence graph。
5. 调用冷启动 Skill 生成 `base_ontology_bundle/`。
6. 按场景 A 的缺口发现步骤继续生产。

限制：

- 不得直接用材料生成 `ontology_bundle_vN/`。
- 必须先形成 `base_ontology_bundle/` 或要求用户提供已有本体。

## 场景 E：只要求生成评测前候选包

适用条件：

- 用户已提供 `ontology_bundle_vN/` 和必要说明，只要求打包交付评测。

流程：

1. 读取 `ontology_bundle_vN/`、生产说明、来源摘要、未解决问题和兼容 JSON。
2. 调用人类可读解析 Skill，生成 `docs/ontology_guide.md`。
3. 调用评测数据输入生成 Skill，生成 `docs/evaluation_handoff.md`。
4. 调用 Release Package 组装与校验 Skill。

## 通用停止规则

Agent 在以下情况下停止生产并输出阻断说明：

- 缺少本体且无法冷启动。
- 缺少可追溯材料，且用户要求生成事实观测或历史验证结论。
- 用户要求输出发布结论、买卖建议、目标价、收益率预测或仓位建议。
- 输入包含隐藏评测答案或要求按隐藏答案定向优化。
- 本轮无法生成 `ontology_bundle_vN/`，但用户要求继续交付评测。
