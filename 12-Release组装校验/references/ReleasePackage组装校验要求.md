# ReleasePackage 组装校验要求

本文件定义投研本体生产 Agent 最终交付包的组装和校验规则。本 Skill 只检查生产侧交付是否完整、命名一致、边界清楚，不评测本体质量，不做发布判断。

公共文件契约见 `../../../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`。

## 1. 必备结构

`release_package/` 必须包含：

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
  _artifacts/
    artifact_manifest.yaml
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

建议同时包含：

```text
_compat/
  optimized_ontology_vN.json
```

缺少 `00_release_manifest.yaml`、bundle 任一模块、`docs/` 任一必备文件或 `_artifacts/artifact_manifest.yaml`，均为 BLOCK。

## 2. Artifacts 规则

`_artifacts/` 必须整体输出，用于日后审计。它可以包含：

- `inputs/`
- `sources/`
- `material_graph/`
- `evidence_graph/`
- `patches/`
- `gap_discovery/`
- `historical_replay/`
- `task_merge/`
- `evaluation_results/`
- `reasoning_runs/`

`artifact_manifest.yaml` 必须记录每个归档产物的路径、产生 Skill、输入来源、对应本体版本、是否进入正式本体、是否仅作线索和可选 checksum。

`material_graph/` 建议包含 `document_chunk_index.yaml`、`candidate_objects.yaml`、`candidate_relations.yaml`、`candidate_state_variables.yaml`、`candidate_events_signals.yaml`、`evidence_fragment_index.yaml` 和 `extraction_quality_report.md`。

`evidence_graph/` 建议包含 `evidence_episodes.yaml`、`evidence_claims.yaml`、`evidence_facts.yaml`、`invalidation_candidates.yaml` 和 `evidence_graph_validation_report.md`。

`patches/` 建议包含 `patch_ledger.yaml`、`patch_merge_report.md` 和 `rejected_patch_requests.yaml`。

`reasoning_runs/` 可为空，但若存在推理应用或推理反馈，必须归档 `inference_run_{id}.yaml`。

普通使用主入口是 `00_release_manifest.yaml`、`ontology_bundle_vN/` 和 `docs/`，不是 `_artifacts/`。

## 3. 版本规则

- `ontology_bundle_vN/` 的 `vN` 必须与 `00_ontology_manifest.yaml.version` 对齐或有明确映射说明。
- `_compat/optimized_ontology_vN.json` 若存在，必须标记为兼容导出，并与 bundle 版本一致。
- 文档中的版本号、研究主题、本体 ID 和生成时间不得互相矛盾。
- 后续版本必须递增，不得覆盖旧包。
- 若输入文件名包含“副本”“草稿”“临时”，必须正式命名后再组装，或 BLOCK 并说明。

## 4. 校验清单

| 类别 | 检查项 | 失败等级 |
|---|---|---|
| 文件齐全 | manifest、8 个 bundle 模块、3 个 docs、artifact manifest 全部存在 | BLOCK |
| 命名规范 | 文件名符合第 1 节 | BLOCK |
| Bundle 有效 | YAML 可解析；manifest 列出 8 个模块 | BLOCK |
| 主干完整 | concepts、objects、relations、actions 四个 Palantir 主干存在 | BLOCK |
| 推理可读 | reasoning、evidence、governance、optimization_handoff 存在且职责不混 | BLOCK/WARN |
| 版本一致 | 文件名、manifest、docs、compat 版本一致 | BLOCK/WARN |
| Artifacts | `_artifacts/artifact_manifest.yaml` 能索引过程产物 | BLOCK/WARN |
| Material Graph | 若本轮运行 6-1b，`_artifacts/material_graph/` 文件齐全并被 artifact_manifest 索引 | WARN |
| Evidence Graph | 若本轮运行 6-8，`_artifacts/evidence_graph/` 文件齐全并被 artifact_manifest 索引 | WARN |
| Patch Ledger | 若本轮存在 patch queue 或优化合并，`_artifacts/patches/patch_ledger.yaml` 被 artifact_manifest 索引 | WARN |
| Reasoning Runs | 若本轮有推理反馈，`_artifacts/reasoning_runs/` 被 artifact_manifest 索引 | WARN |
| 来源可追溯 | evidence 或 production_notes 能解释关键证据来源 | BLOCK/WARN |
| 人类可读 | `docs/ontology_guide.md` 引用本体 ID、版本和边界 | WARN |
| 评测交接 | `docs/evaluation_handoff.md` 说明评测范围、材料和缺口 | WARN |
| 越权内容 | 不含买卖建议、目标价、收益率预测、仓位建议 | BLOCK |
| 冲突文本 | 交付中没有“已发布”“通过评测”等越权表述 | BLOCK |
| 追溯一致 | 关键 ID 在 bundle、docs、artifacts 中可互相定位 | WARN |

## 5. BLOCK 与 WARN

`BLOCK` 表示不能组装正式候选包。必须修复后重跑。

`WARN` 表示可以组装候选包，但 `package_check_report.md` 或 `00_release_manifest.yaml.validation` 必须说明风险、影响和建议修复。

不得用 WARN 掩盖缺文件、越权内容、YAML 无法解析或版本严重冲突。

## 6. 组装输出

标准目录：

```text
release_package/
  00_release_manifest.yaml
  ontology_bundle_vN/
  docs/
  _compat/
  _artifacts/
package_check_report.md
```

`package_check_report.md` 可选但建议始终生成；也可把校验结果写入 `00_release_manifest.yaml.validation`。

## 7. 结论口径

结论只能使用：

- `ready_for_evaluation`
- `ready_with_warnings`
- `blocked`

不得使用 `allow_publish`、`published`、`passed_evaluation` 或类似发布结论。

## 8. 禁止事项

- 不修改 `ontology_bundle_vN/` 或 `_compat/optimized_ontology_vN.json`。
- 不输出 `published_ontology_bundle_vN/`、`evaluation_result.json` 或 `release_decision.md`。
- 不输出任何发布或评测结论。
- 不把“可交给评测”写成“已通过评测”。
