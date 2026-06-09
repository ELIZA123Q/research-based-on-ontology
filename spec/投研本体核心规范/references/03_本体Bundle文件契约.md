# 03-本体 Bundle 文件契约

本文定义投研本体在生产、评测和推理闭环中的模块化文件形态。它是所有 Skill 读写本体文件时的公共契约。

## 1. 权威形态

新版本本体以目录形式交付：

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
```

冷启动首版使用同构目录：

```text
base_ontology_bundle/
  00_ontology_manifest.yaml
  01_concepts.yaml
  02_objects.yaml
  03_relations.yaml
  04_actions.yaml
  05_reasoning.yaml
  06_evidence.yaml
  07_governance.yaml
  08_optimization_handoff.yaml
```

若需兼容旧流程，可同时导出 JSON：

```text
_compat/
  optimized_ontology_vN.json
  base_ontology.json
```

兼容 JSON 是派生导出，不是新流程的权威入口。发生冲突时，以 `ontology_bundle_vN/` 或 `base_ontology_bundle/` 为准。

## 2. 模块职责

| 文件 | 职责 | 不放入 |
|---|---|---|
| `00_ontology_manifest.yaml` | 本体 ID、版本、父版本、范围、业务时间、模块索引、兼容导出、校验状态。 | 具体对象实例、过程日志。 |
| `01_concepts.yaml` | 概念层：术语口径、概念类型、同义词、边界裁定、概念关系、概念到对象映射规则。 | 具体公司、产品、事件实例。不得复制对象 description；definition 只写术语口径（这个词涵盖什么、不涵盖什么、与易混淆术语的区别）。 |
| `02_objects.yaml` | 对象实例层：业务对象、可观察对象、推理判断对象、来源治理对象。 | 关系实例、证据矩阵、优化任务。 |
| `03_relations.yaml` | 关系实例层：业务结构、变量挂载、推理关系、资产映射、证据追溯。 | 对象字段、自然语言暗示关系。 |
| `04_actions.yaml` | 动作契约和动作实例：核心动作类型、agent runtime actions、ActionAudit 策略。 | `suggested_actions` 这类优化交接任务。 |
| `05_reasoning.yaml` | 推理应用层：状态模型、事件模型、传导模板、假设信号、阻断条件、情景路径、判断和资产影响路径。 | 来源全文、人工审核队列、推理运行日志。 |
| `06_evidence.yaml` | 证据层：来源文档、EvidenceEpisode、EvidenceClaim、EvidenceFact、状态观测、证据矩阵、有效期和失效引用。 | 质量治理结论、下一轮优化任务、未经合并的 patch 请求。 |
| `07_governance.yaml` | 治理层：retrieval_policy（推理检索策略的机器可读契约）、缺证、人工复核、质量检查、未解析对象/关系、丰富性保留。 | 正式对象关系主体、评测发布结论、推理运行日志。 |
| `08_optimization_handoff.yaml` | 生产交接层：PatchRequest 摘要、normalization_actions、remaining_gaps、next_optimization_plan、patch ledger 摘要。 | 本体运行时 actions、正式推理主体、未审证据事实。 |

## 3. Palantir 式主干

本体实例必须能按以下顺序读取：

1. `01_concepts.yaml` 定义语义和范围。
2. `02_objects.yaml` 定位对象。
3. `03_relations.yaml` 连接对象。
4. `04_actions.yaml` 定义可执行动作和审计。
5. `05_reasoning.yaml` 组织投研推理视图。
6. `06_evidence.yaml` 追溯证据。
7. `07_governance.yaml` 暴露质量、缺口和复核。
8. `08_optimization_handoff.yaml` 交接下一轮生产任务。

`reasoning` 是应用视图，不替代 `objects`、`relations` 和 `actions`。推理链中涉及的对象、关系和动作必须能回到前三个主干文件。

## 4. Release Package

生产 Agent 的最终候选交付目录使用：

```text
release_package/
  00_release_manifest.yaml
  ontology_bundle_vN/
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

`_artifacts/` 必须整体输出，用于日后审计、复盘、回滚和二次优化；它不是普通使用者入口。主入口是 `00_release_manifest.yaml`、`ontology_bundle_vN/` 和 `docs/`。

## 5. 读写兼容规则

- 新 producer 必须输出 bundle；可选输出 `_compat/*.json`。
- 新 consumer 必须优先读取 bundle；缺失时可读取 `_compat/*.json` 或旧单体 JSON。
- 任务单、缺口、评测修复和推理反馈必须使用 `target_file`、`target_path`、`target_id` 指向 bundle 内模块。
- 旧字段路径可作为 `legacy_path` 保留，例如 `optimized_ontology.objects`。
- 不得把评测结果、推理运行结果、搜索日志或历史回放报告写入本体主体；它们进入 `_artifacts/`。
- Material Graph 的 Document/Chunk、候选对象关系和证据片段索引进入 `_artifacts/material_graph/`；它是 Evidence Graph 的上游材料结构化视图，不是正式本体。
- Evidence Graph 的详细 episode、claim、fact、失效候选进入 `_artifacts/evidence_graph/`；只有经优化 Skill 合并、适合正式交付的摘要进入 `06_evidence.yaml`。
- Patch ledger 的完整增量审计进入 `_artifacts/patches/`；`08_optimization_handoff.yaml` 只保留面向下一轮生产的摘要和队列。

## 6. 最小校验

Bundle 至少满足以下检查项。本清单是 bundle 质量的权威校验来源，合并了《02》§8 的质量门槛维度。

### 6.1 Bundle 结构完整性

- `00_ontology_manifest.yaml` 存在且列出 8 个模块。
- `01_concepts.yaml` 至少声明概念范围和边界；冷启动允许全为 candidate。
- `02_objects.yaml`、`03_relations.yaml`、`04_actions.yaml` 存在，即使为空也要说明原因。
- `08_optimization_handoff.yaml` 只能记录生产交接，不得作为正式本体推理主体。

### 6.2 元数据与版本

- 有清楚的 `ontology_metadata`（ontology_id、ontology_version、parent_version、created_by、updated_by、change_reason），研究范围和版本来源可追溯。

### 6.3 对象质量

- 核心对象有稳定 ID、类型、名称、状态和来源说明。
- `01_concepts.yaml` 中有概念层对象（ConceptScheme、Concept、ConceptBoundary），说明核心研究范围、关键术语、纳入/排除/交叉边界和来源。

### 6.4 关系质量

- 关系端点必须能解析到 `02_objects.yaml` 中存在的对象实例，无法解析进入 `07_governance.yaml`。
- 核心关系端点存在、方向合法、语义属性明确。

### 6.5 可观测维度与推理链

- 关键状态变量可观察，关键观测可追溯。
- 主要传导链有端点、方向、时滞、边界条件和验证信号。
- 假设、判断、情景和资产影响之间链路清楚。

### 6.6 证据可追溯性

- 证据引用必须能解析到 `06_evidence.yaml` 或进入缺证项。
- `06_evidence.yaml` 中的 EvidenceClaim 必须至少能追溯到 EvidenceEpisode 或 SourceDocument；不能追溯的 claim 只能进入 `07_governance.yaml` 或 `_artifacts/evidence_graph/` 的 quarantine/rejected 区。
- 关键新增对象、关系、信号和判断能追溯到 EvidenceEpisode / EvidenceClaim，或明确标记为模板候选。

### 6.7 Temporal Evidence Layer 合规

- 失效证据不得物理删除；必须通过 `invalidatedAt`、`invalidatedBy`、`supersedes`、`supersededBy` 或 `claimInvalidatesClaim` 表达。
- 失效证据保留历史并能解释失效依据。

### 6.8 Patch Ledger 审计

- `PatchRequest` 不等于正式改动；只有本体优化 Skill 合并并写入 `PatchLedgerItem` 后，才能进入正式对象、关系、动作或推理模块。
- patch ledger 能说明每次增量改动的来源、目标、合并状态和理由。

### 6.9 推理运行记录

- 推理运行记录进入 `_artifacts/reasoning_runs/`，不得写成正式判断或发布结论。
- 推理运行记录能说明使用了哪些证据、排除了哪些失效证据。

### 6.10 跨模块一致性

- **概念-对象映射**：每个 `scopeStatus=in_scope` 的 Concept 必须至少有一条 `conceptMapsToObject` 关系指向 `02_objects.yaml` 中存在的对象实例。无映射的 in_scope Concept 视为「范围已声明但未实例化」，进入 `07_governance.yaml` 的未解析项。
- **概念与对象不复写**：Concept.definition 只写术语口径（涵盖范围、排除边界、与易混淆术语的区别）；Object.description 只写实例属性。两者内容不得互相复制。校验时若发现相同或高度近似的文本跨模块出现，标记为 WARN。

### 6.11 治理与合规边界

- 未解决问题、缺证项、拒绝项和延后项显式记录于 `07_governance.yaml`。
- 不包含买卖建议、目标价、收益率预测或仓位建议。

## 7. Temporal Evidence Layer

Temporal Evidence Layer 是证据记忆层，不替代 Palantir 本体主干。完整对象定义（EvidenceEpisode、EvidenceClaim、EvidenceFact）见 `schemas/objects.yaml`，时间字段契约和归档规则见 `schemas/ontology_bundle.yaml` 的 `temporal_evidence_contract`。此处仅给出归档路径速查：

```text
_artifacts/evidence_graph/
  evidence_episodes.yaml / evidence_claims.yaml / evidence_facts.yaml
  invalidation_candidates.yaml / evidence_graph_validation_report.md
```

核心原则：新证据先形成 EvidenceEpisode → EvidenceClaim，不得直接写入正式主干；失效证据标记而非物理删除；推理默认使用当前有效证据，历史回放可读取当时有效证据。

## 8. Patch Ledger 与推理运行

Patch Ledger 和推理运行的完整契约见 `schemas/ontology_bundle.yaml` 的 `patch_ledger_contract` 和 `inference_run_contract`。推理轨迹对象（RuleApplication、ReasoningStep）定义见 `schemas/reasoning_trace.yaml`。

核心原则：PatchRequest 只能表达候选改动，优化 Skill 是唯一正式合并者；InferenceRun 记录每次推理的完整上下文；推理反馈通过 PatchRequest 反哺生产。

## 9. Retrieval Policy — 推理检索的机器可读契约

推理 Skill 的检索策略（entry_points、traversal_order、required_checks、source_authority_ranking、freshness_policy、fallback_policy、blocking_rules）的权威定义见 `schemas/governance.yaml` 的 `retrieval_policy` 段。推理 Skill 必须优先读取 `07_governance.yaml` 中的检索配置；仅当缺失时才回退到 Skill 自身的默认规则。

## 10. Reasoning Trace — 推理轨迹的结构化记录

`RuleApplication` 和 `ReasoningStep`（定义见 `schemas/reasoning_trace.yaml`）服务于三个下游场景：

| 场景 | 用途 |
|---|---|
| 历史回放 | 使用 t0 时刻的 RuleApplication 复现推理路径，对比 t0 判断与事后结果。 |
| 推理评测 | 统计哪些规则、信号、反证的组合导致推理成功或失败；识别系统性弱推理模式。 |
| 本体优化 | 基于高频使用的规则/关系优化本体结构；基于常被漏掉的信号/反证补充本体缺口。 |

两者不是投研领域实体，归档在 `_artifacts/reasoning_runs/inference_run_{id}/` 下。RuleApplication 记录「规则如何被消费」；ReasoningStep 记录「图谱如何被导航」；两者互补。 
