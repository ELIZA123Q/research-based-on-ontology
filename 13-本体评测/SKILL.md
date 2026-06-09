---
name: touyan-benti-pingce
description: 当需要判断完整投研本体是否足以支撑目标范围内的推理、解释、验证和反证时使用。输入 ontology_bundle、target_scope、评测题和参考材料，输出逐题评分、发布判断、评测可信度和优化任务单。本 Skill 不修改本体，不输出 ontology_bundle 或 optimized_ontology，不生成投资建议、目标价、收益率预测或仓位建议。
metadata:
  short-description: 投研本体评测
---

# 投研本体评测 Skill

## 定位

本 Skill 是投研本体的发布前能力评测器。它回答：当前本体在目标范围内，是否足以支撑高质量、可解释、可验证、可反证的投研推理。

本 Skill 只做评测、评分、发布判断和修复任务单，不创建或修改本体。

## 输入

| 输入 | 要求 |
|---|---|
| `ontology_bundle_vN/` | 必填优先。完整候选本体 bundle。 |
| `_compat/optimized_ontology_vN.json` / 旧单体 `ontology` | 兼容输入。缺 bundle 时可用，但降低输入形态可信度。 |
| `target_scope` | 必填。本次评测服务的投研推理范围。 |
| `scope_type` | 建议提供。使用核心规范七类枚举；缺失时可推断但降低可信度。 |
| `eval_questions` | 可选。包括 baseline、type_specific、hotspot、challenge。 |
| `reference_materials` | 可选。用于核验事实、热点和主流逻辑。 |
| `evaluation_data_inputs` | 可选。由 6-6 生成的数据输入包。 |
| `_artifacts/evidence_graph/` | 可选但建议。用于评测 episode 覆盖、claim 可追溯、失效事实过滤能力。 |
| `_artifacts/patches/patch_ledger.yaml` | 可选。用于评测增量合并审计能力。 |
| `_artifacts/reasoning_runs/` | 可选。用于评测推理运行记录完整性。 |
| `release_threshold` | 可选。缺失时使用 `references/02_评分阈值与发布判断.md` 默认阈值。 |

## 核心依据

冲突裁定顺序如下：

1. 当前任务显式提供的本体、范围、问题集、参考材料和发布阈值
2. `../../spec/投研本体核心规范/schemas/objects.yaml`
3. `../../spec/投研本体核心规范/schemas/relations.yaml`
4. `../../spec/投研本体核心规范/schemas/actions.yaml`
5. `../../spec/投研本体核心规范/references/01_投研本体核心说明.md`
6. `../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md`
7. `../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`
8. `references/01_评测问题设计.md`
9. `references/02_评分阈值与发布判断.md`
10. `references/03_修复建议与优化交接.md`
11. `schemas/本体评测输出结构.json`
12. `examples/*`

## 评测流程

1. **展开评测数据输入包**：若存在 `evaluation_data_inputs`，展开为参考材料、题源材料、热点材料、数据需求和未解决数据项。
2. **确认本体和范围**：检查本体版本、目标范围、scope_type、对象/关系规模和使用限制。
3. **生成或检查问题集**：先读取 `01_concepts.yaml` 判断题目是否在范围内，再覆盖 baseline、type_specific、hotspot、challenge 四层，并保证题目与目标范围一致。
4. **基于本体回答问题**：优先调用本体对象、关系、变量、信号和边界条件；本体外补充必须标注。
5. **评测 Temporal Evidence Layer**：检查 episode 覆盖、claim 可追溯、当前有效事实过滤、失效事实保留、patch ledger 审计和 inference run 完整性。
6. **逐题评分**：按覆盖度、传导完整度、解释清晰度、可验证性、边界条件、反证能力、结论可用性、本体调用一致性评分。
7. **计算发布指标**：统计总分、核心题通过率、严重失败数、核心链条断裂数、验证信号覆盖率、图谱可生成性、数据满足率和 temporal evidence 可用性。
8. **输出发布判断**：给出 `allow_publish`、`conditional_publish`、`reject_publish` 或 `insufficient_evidence`。
9. **生成修复任务单**：把失败题和弱项映射为 `optimization_plan`，说明证据要求、优先级和停止条件；修复项必须尽量指向 `target_file`、`target_path`、`target_id`。

## 问题层级

| 层级 | 用途 | 发布影响 |
|---|---|---|
| `baseline` | 固定基准题，保证版本间可比 | 参与硬门槛。 |
| `type_specific` | 按七类本体覆盖核心能力 | 参与硬门槛。 |
| `hotspot` | 用近期事件、政策、公告或数据压力测试 | 影响实战就绪度和修复建议。 |
| `challenge` | 少量半随机题，防止过拟合 | 影响总分和可信度。 |

设计、权重和阈值见 `references/01_评测问题设计.md` 与 `references/02_评分阈值与发布判断.md`。

## 评分边界

- 评测本体能力，不评判真实投资收益。
- 热点题涉及最新事件、政策、公告、价格或公司动态时，必须使用可追溯来源；无法核验时不能作为 critical failure。
- 数据缺口导致可验证性或边界条件不达标时，应降级发布判断，并把数据需求写入任务单。
- 图谱可生成性失败时，必须点名缺失关系类型，例如 `segmentConnectsToSegment`、`companyRelatesToCompany`、`productRelatesToProduct`、`materialUsedInProduct`、`eventAffectsVariable`。
- 概念边界不清时，必须把失败项归因到 `01_concepts.yaml`，例如缺 `Concept`、缺 `ConceptBoundary` 或缺 `conceptMapsToObject`。
- 若推理题依赖动态事实，必须检查使用证据是否有 EvidenceEpisode/EvidenceClaim 追溯，是否排除了 invalidated claim。
- Patch ledger 缺失不必自动导致发布失败，但会降低 evidence/consistency 相关评分，并生成治理修复任务。

## Evidence Graph 评测维度

| 维度 | 检查点 |
|---|---|
| episode 覆盖 | 关键材料、历史案例、推理反馈和评测反馈是否形成 EvidenceEpisode。 |
| claim 可追溯 | 关键 claim 是否能回到 episode、source、原文位置和业务时间。 |
| 失效过滤 | 推理是否排除 invalidated/superseded/rejected/quarantined claim。 |
| 历史保留 | 被替代或失效的证据是否保留历史，而非物理删除。 |
| patch ledger 审计 | 正式变更是否能追溯到 PatchRequest、evidence ids、合并理由和 merge_status。 |
| inference run 完整性 | 推理运行是否记录中心对象、使用证据、排除证据、链路和反馈。 |

## 输出

输出严格 JSON 对象，符合 `schemas/本体评测输出结构.json`。必须包含：

```json
{
  "evaluation_metadata": {},
  "question_set_assessment": {},
  "evaluation_summary": {},
  "threshold_check": {},
  "dimension_scores": {},
  "question_level_results": [],
  "critical_failures": [],
  "ontology_issue_mapping": {},
  "evaluation_fix_report": {},
  "optimization_plan": [],
  "optimization_handoff": {},
  "compliance_check": {},
  "readable_report": "",
  "data_requirements_checklist": [],
  "data_sourcing_summary": {},
  "data_driven_score_adjustments": {},
  "temporal_evidence_assessment": {},
  "patch_ledger_assessment": {},
  "inference_run_assessment": {}
}
```

不得输出 `ontology_bundle` 或 `optimized_ontology`。

`readable_report` 控制在 800-1500 字，包含发布判定、维度分析、关键失败项和下一步。修复项必须可追溯到题目、失败原因和受影响本体组件。

## 禁止事项

- 不为了让本体通过评测而绕过本体基座自由发挥。
- 不直接新增 confirmed 对象、关系、变量、信号或资产影响。
- 不把热点新闻直接写成稳定本体逻辑。
- 不输出买卖建议、目标价、收益率预测或仓位建议。

## 本地校验

```bash
python3 scripts/validate_skill.py
```
