# 本体生产 Agent I/O Contracts

## 1. 定位

本文定义投研本体生产 Agent 及其可调用 Skill 的文件级输入输出契约。公共本体文件形态以 `../spec/投研本体核心规范/references/03_本体Bundle文件契约.md` 为准。

核心原则：

- 本体生产 Agent 负责编排和版本生产。
- 冷启动 Skill 是唯一 `base_ontology_bundle/` 生产者。
- 本体优化 Skill 是唯一 `ontology_bundle_vN/` 生产者。
- `_compat/*.json` 只是兼容导出，不是新流程权威入口。
- 缺口发现、历史回放、评测数据生成只输出材料、诊断、任务单或交接输入。
- 人类可读解析只解释最终候选本体，不新增本体内容。
- 最终发布判断由评测 Agent 或评测 Skill 完成。

## 2. 通用命名

| 类型 | 新契约 | 兼容/旧契约 |
|---|---|---|
| 冷启动本体 | `base_ontology_bundle/` | `_compat/base_ontology.json` |
| 优化本体 | `ontology_bundle_vN/` | `_compat/optimized_ontology_vN.json` |
| 当前输入本体 | `current_ontology_bundle/` 或 `ontology_bundle_vN/` | `current_ontology.json` |
| 最终候选交付 | `release_package/` | 不适用 |
| 中间审计材料 | `release_package/_artifacts/` | 可归档旧散文件 |

## 3. Release Package

最终输出固定为：

```text
release_package/
  00_release_manifest.yaml
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
  docs/
    ontology_guide.md
    production_notes.md
    evaluation_handoff.md
  _compat/
    optimized_ontology_vN.json
  _artifacts/
    artifact_manifest.yaml
    inputs/
    sources/
    material_graph/
    evidence_graph/
    patches/
    gap_discovery/
    historical_replay/
    task_merge/
    evaluation_results/
    reasoning_runs/
```

`_artifacts/` 必须整体输出，便于日后审计、复盘、回滚和二次优化；它不得作为普通使用者主入口。

## 4. Skill I/O

### 冷启动 Skill

输入：

- `research_topic.md`
- `user_scope_request.md` 可选
- `source_materials/` 可选
- `ontology_core_spec` 可选

输出：

- `base_ontology_bundle/`
- `_compat/base_ontology.json` 可选但建议
- `cold_start_report.md`
- `downstream_task_list.md`

禁止输出：

- `ontology_bundle_vN/`
- `_compat/optimized_ontology_vN.json`
- 已发布本体
- 买卖建议、目标价、收益率预测或仓位建议

### 信息与数据搜索 Skill

`source_registry.json` 是本 Skill 独占维护的来源材料登记账本。其他 Skill 不得直接修改 `source_registry.json`。如需记录派生信息（chunk、episode、claim、case、graph node 等），应在各自产物目录中生成独立索引文件，通过 `source_id` / `material_id` / `chunk_id` 回链。

输出：

- `_artifacts/sources/source_materials/`
- `_artifacts/sources/source_registry.json`
- `_artifacts/sources/source_search_log.md`
- `_artifacts/sources/source_quality_assessment.md`

### 材料图谱预处理 Skill

输入：

- `research_topic.md`
- `_artifacts/sources/source_materials/`
- `_artifacts/sources/source_registry.json`
- `spec/schemas/` 或 `ontology_bundle_vN/` 的 schema（三级降级）
- `_artifacts/sources/source_quality_assessment.md` 可选

输出：

- `_artifacts/material_graph/material_scope.md`
- `_artifacts/material_graph/document_chunk_index.yaml`
- `_artifacts/material_graph/candidate_objects.yaml`
- `_artifacts/material_graph/candidate_relations.yaml`
- `_artifacts/material_graph/candidate_state_variables.yaml`
- `_artifacts/material_graph/candidate_events_signals.yaml`
- `_artifacts/material_graph/evidence_fragment_index.yaml`
- `_artifacts/material_graph/extraction_quality_report.md`
- `_artifacts/material_graph/pending_review_items.md`

这些产物进入 `_artifacts/sources/`，并通过 `episode_seed` 交给 Evidence Episode 归一与校验 Skill；只通过 `docs/production_notes.md` 和 `06_evidence.yaml` 摘要进入最终交付。

### 材料图谱预处理 Skill

输入：

- `source_materials/`
- `source_registry.json`
- `source_quality_assessment.md` 可选
- `research_topic.md`
- `ontology_schema/` 可选

输出：

- `_artifacts/material_graph/material_scope.md`
- `_artifacts/material_graph/document_chunk_index.yaml`
- `_artifacts/material_graph/candidate_objects.yaml`
- `_artifacts/material_graph/candidate_relations.yaml`
- `_artifacts/material_graph/candidate_state_variables.yaml`
- `_artifacts/material_graph/candidate_events_signals.yaml`
- `_artifacts/material_graph/evidence_fragment_index.yaml`
- `_artifacts/material_graph/extraction_quality_report.md`
- `_artifacts/material_graph/pending_review_items.md`

本 Skill 只做材料拆解、候选图谱抽取和证据片段挂载，不输出 EvidenceClaim、EvidenceFact 或覆盖判断。

### Evidence Episode 归一与校验 Skill

输入：

- `source_registry.json`、`source_materials/`、`source_quality_assessment.md` 可选
- `_artifacts/material_graph/` 可选但优先
- `_artifacts/historical_replay/`、`_artifacts/reasoning_runs/`、`_artifacts/evaluation_results/` 可选
- `ontology_bundle_vN/` 可选，只用于 ID 对齐和映射校验

输出：

- `_artifacts/evidence_graph/evidence_episodes.yaml`
- `_artifacts/evidence_graph/evidence_claims.yaml`
- `_artifacts/evidence_graph/evidence_facts.yaml`
- `_artifacts/evidence_graph/invalidation_candidates.yaml`
- `_artifacts/evidence_graph/evidence_graph_validation_report.md`

本 Skill 不修改本体，不判断覆盖，不输出 patch ledger。

### 缺口发现 Skill

输入：

- `base_ontology_bundle/`、`ontology_bundle_vN/` 或兼容 JSON
- `_artifacts/evidence_graph/evidence_claims.yaml` 优先
- `_artifacts/sources/source_registry.json`
- `ontology_feedback` 可选
- `external_reference_materials/` 可选

内部生成 `_work/gap_reference_view/`（不对外交付）。

输出：

- `_artifacts/gap_discovery/gap_report.md`
- `_artifacts/gap_discovery/gap_items.json`
- `_artifacts/gap_discovery/optimization_suggestions.md`
- `_artifacts/gap_discovery/candidate_patch_requests.yaml`
- `_artifacts/gap_discovery/restricted_items.md`

任务和缺口必须能用 `target_file`、`target_path`、`target_id` 指向 bundle 模块；旧路径可写入 `legacy_path`。

### 历史案例生成 Skill

输出：

- `historical_materials/`
- `historical_case_generation_report.md`
- `replay_task_list.md`

这些产物进入 `_artifacts/historical_replay/`。

### 历史回放 Skill

输入：

- `base_ontology_bundle/`、`ontology_bundle_vN/` 或兼容 JSON
- `historical_materials/`
- `replay_task_list.md`

输出：

- `historical_cases.json`
- `replay_report.md`
- `evidence_chain.md`
- `temporal_replay_evidence.yaml`
- `invalidation_candidates.yaml`

诊断和优化计划必须指向 bundle 模块，不得直接修改本体。

### 生产任务合并 Skill

输入：

- 缺口发现、历史回放、评测缺陷、推理反馈、用户修订请求中的一个或多个。

输出：

- `optimization_task_list.md`
- `optimization_task_items.json`
- `patch_request_queue.yaml`
- `priority_decision.md`

结构化任务项必须包含可选字段：`target_file`、`target_path`、`target_id`、`legacy_path`、`evidence_episode_ids`、`evidence_claim_ids`、`invalidation_candidate_ids`、`semantic_risk`、`merge_precondition`。

### 本体优化 Skill

输入：

- `base_ontology_bundle/`、`ontology_bundle_vN/` 或兼容 JSON
- `optimization_task_list.md`
- `optimization_task_items.json` 可选
- `patch_request_queue.yaml` 可选
- `_artifacts/evidence_graph/` 可选
- 缺口、历史回放、评测修复、推理反馈、来源材料可选

输出：

- `ontology_bundle_vN/`
- `_compat/optimized_ontology_vN.json`
- `docs/production_notes.md` 或可归档的 `optimization_report.md`、`change_log.md`、`unresolved_questions.md`
- `_artifacts/patches/patch_ledger.yaml`
- `_artifacts/patches/patch_merge_report.md`
- `_artifacts/patches/rejected_patch_requests.yaml`

本 Skill 不生成 `docs/ontology_guide.md` 和 `docs/evaluation_handoff.md`。

### 人类可读解析 Skill

输入：

- `ontology_bundle_vN/` 优先
- `_compat/optimized_ontology_vN.json` 兼容
- `docs/production_notes.md` 或归档过程文件

输出：

- `docs/ontology_guide.md`

### 评测数据输入生成 Skill

输入：

- `ontology_bundle_vN/` 优先
- `_compat/optimized_ontology_vN.json` 兼容
- `source_materials/`、`source_registry.json` 可选
- `_artifacts/evidence_graph/` 可选
- `_artifacts/patches/patch_ledger.yaml` 可选
- `_artifacts/reasoning_runs/` 可选

输出：

- `_artifacts/evaluation_results/evaluation_data_inputs/`
- `_artifacts/evaluation_results/evaluation_data_inputs/evidence_graph_input.yaml`
- `_artifacts/evaluation_results/evaluation_data_inputs/patch_ledger_input.yaml`
- `_artifacts/evaluation_results/evaluation_data_inputs/inference_run_samples.yaml`
- `docs/evaluation_handoff.md`

不得输出评测结论或优化计划。

### Release Package 组装与校验 Skill

输入：

- `00_release_manifest.yaml`
- `ontology_bundle_vN/`
- `docs/ontology_guide.md`
- `docs/production_notes.md`
- `docs/evaluation_handoff.md`
- `_artifacts/sources/source_registry.json`
- `_artifacts/sources/source_quality_assessment.md`
- `_compat/optimized_ontology_vN.json` 可选但建议
- `_artifacts/artifact_manifest.yaml`
- `_artifacts/material_graph/` 可选但建议
- `_artifacts/evidence_graph/` 可选但建议
- `_artifacts/patches/` 可选但建议
- `_artifacts/reasoning_runs/` 可选

职责包含聚合来源材料元数据生成 `source_material_summary.md`（原 6-5b 逻辑已并入）。

输出：

- `release_package/`（含 `docs/source_material_summary.md`）
- `_artifacts/sources/source_material_summary.md`（审计归档）
- `package_check_report.md` 可选，或写入 `00_release_manifest.yaml.validation`

## 5. 最终交付检查

必须包含：

- `00_release_manifest.yaml`
- `ontology_bundle_vN/` 八个模块文件
- `docs/ontology_guide.md`
- `docs/production_notes.md`
- `docs/evaluation_handoff.md`
- `docs/source_material_summary.md`
- `_artifacts/artifact_manifest.yaml`
- `_artifacts/material_graph/` 若本轮运行 02-材料图谱预处理
- `_artifacts/evidence_graph/` 若本轮运行 04-证据归一
- `_artifacts/patches/` 若本轮存在 patch queue 或优化合并

不得包含：

- `published_ontology_vN.*`
- `evaluation_result.json`
- `release_decision.md`
- `allow_publish`、`conditional_publish`、`reject_publish`、`insufficient_evidence`
- 买卖建议、目标价、收益率预测、仓位建议
