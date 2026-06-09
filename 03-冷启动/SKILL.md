---
name: touyan-hangye-chanye-bentilengqidong
description: 当用户只给出行业、产业链环节、公司、产品、政策、宏观变量或事件主题，需要生成第一版本投研本体骨架时使用。输入自然语言研究焦点，输出候选 base_ontology_bundle、兼容 base_ontology.json、材料缺口、材料收集计划和下游优化任务。本 Skill 只生成候选结构，不确认事实，不输出投资建议、目标价、收益率预测或仓位建议。
metadata:
  short-description: 投研本体冷启动
---

# 投研本体冷启动 Skill

## 定位

本 Skill 是投研本体的冷启动入口。它在材料不足或尚无本体时，先生成概念层，再把用户的研究主题转成一份最小可用候选本体（MVO），用于后续材料搜索、缺口发现、历史回放和材料驱动优化。

冷启动权威产物是 `base_ontology_bundle/`。其中所有新增概念、对象、关系、变量、传导、信号、情景和资产线索默认是 `candidate`，必须带模板依据、待验证说明或材料缺口。

如需兼容旧流程，可同时导出 `_compat/base_ontology.json`。兼容 JSON 是派生视图，不是新流程权威入口。

## 输入

| 输入 | 要求 |
|---|---|
| 用户自然语言主题 | 必填。可以是行业、公司、产品、产业链环节、政策、宏观变量或事件。 |
| 已知范围约束 | 可选。包括市场、资产类别、时间窗口、地域、公司池或产业链边界。 |
| 用户已有材料 | 可选。只能作为线索，不得把未经核验内容升级为确认事实。 |
| 下游任务偏好 | 可选。用于决定材料缺口和优化任务优先级。 |

输入为空、过短、互相矛盾或无法识别实体时，只输出澄清问题和候选研究路径，不生成完整本体。

## 核心依据

冲突裁定顺序如下：

1. `../../spec/投研本体核心规范/schemas/objects.yaml`
2. `../../spec/投研本体核心规范/schemas/relations.yaml`
3. `../../spec/投研本体核心规范/schemas/actions.yaml`
4. `../../spec/投研本体核心规范/references/01_投研本体核心说明.md`
5. `../../spec/投研本体核心规范/references/02_投研本体建模规格说明.md`
6. `../../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`
7. `references/03_冷启动模板库.md`
8. `schemas/行业本体冷启动输出结构.json`
9. `examples/*`

本目录内的 schema copy 仅用于单独安装和本地校验；在本仓库中，公共规范以 `../../spec/投研本体核心规范` 为准。

## 范围识别

先识别 `ontology_scope.scope_type`，再选择模板。允许值为：

`industry`、`supply_chain`、`product_track`、`company_research`、`policy_theme`、`macro_theme`、`event_theme`、`uncertain`。

当置信度低于 0.7 时，必须输出 `candidate_research_paths`，包括默认路径、最多 2 条备选路径和待确认问题。不得在范围不清时强行生成单一路径的完整本体。

## 工作流程

1. **识别研究焦点**：输出 `research_context`，包含焦点名称、焦点类型、用户输入摘要、主研究问题、置信度和待确认项。
2. **划定本体范围**：输出 `ontology_scope`，说明范围类型、默认假设、备选范围和排除边界。
3. **选择冷启动模板**：读取 `references/03_冷启动模板库.md`，输出 `template_application`、`template_composition` 和 `template_pressure_test`。
4. **生成概念层**：在 `base_ontology_bundle/01_concepts.yaml` 中输出 `ConceptScheme`、`Concept`、概念关系和 `ConceptBoundary`，先说明研究范围、关键术语、同义词、纳入/排除/相邻/交叉边界和来源要求。
5. **生成候选本体骨架**：按 bundle 模块输出对象、关系、动作、推理、证据、治理和优化交接；不要把所有内容混入单一对象数组。
6. **显性化待验证内容**：输出 `template_hypotheses`、`judgment_templates`、`asset_impact_clues`，并标明它们只是候选线索。
7. **生成材料缺口和收集计划**：输出 `material_gap_list`、`material_collection_plan` 和 `downstream_optimization_tasks`。
8. **执行 MVO 质量检查**：输出 `mvo_quality_gate`、`cold_start_quality_notes` 和 `validation_errors`。

## 建模规则

- 冷启动必须生成显式业务结构关系。不能只用 `positionInChain`、对象排序或描述字段暗示上下游、客户、供应、替代、事件影响或资产暴露。
- 冷启动必须先生成 `01_concepts.yaml`。半导体、光通信、硅光、先进封装等术语先作为 `Concept` 定义范围和边界，再映射到 `Industry`、`Segment`、`Product`、`Material` 等业务对象。
- `Concept` 不能替代业务对象；只有需要进入图谱和推理的概念，才通过 `conceptMapsToObject` 映射到正式对象。
- 概念定义和边界裁定应优先绑定权威来源。无来源时保持 `candidate`、`draft` 或 `disputed`，并写入材料缺口。
- 行业和产业链模板优先生成 `segmentConnectsToSegment`。
- 产品赛道模板优先生成 `productRelatesToProduct` 和 `materialUsedInProduct`。
- 公司研究模板优先生成 `companyRelatesToCompany`、`companyParticipatesInSegment` 和 `assetExposedToTarget`。
- 事件主题模板优先生成 `eventRelatesToEvent`、`eventAffectsVariable` 和 `eventProducesObservation`。
- 缺少端点、方向、关系语义或最低证据时，不补边，写入 `material_gap_list`。
- 冷启动不得生成 `StateVariableObservation`，除非用户提供了可追溯事实材料且字段可校验。
- 冷启动不得生成正式 `JudgmentOutput`、确认级 `AssetImpact` 或投资建议。

## 输出

输出严格 JSON 对象，符合 `schemas/行业本体冷启动输出结构.json`。必须包含：

```json
{
  "research_context": {},
  "ontology_scope": {},
  "candidate_research_paths": [],
  "template_application": {},
  "template_composition": {},
  "template_pressure_test": {},
  "template_candidate_list": [],
  "base_ontology_bundle": {},
  "base_ontology": {},
  "template_hypotheses": [],
  "judgment_templates": [],
  "template_signals": [],
  "blocking_templates": [],
  "scenario_paths": [],
  "asset_impact_clues": [],
  "material_gap_list": [],
  "material_collection_plan": [],
  "mvo_quality_gate": {},
  "cold_start_task_template": {},
  "cold_start_quality_notes": [],
  "validation_errors": [],
  "missing_reference_files": [],
  "readable_report": ""
}
```

正式文件输出必须包含：

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
_compat/base_ontology.json
cold_start_report.md
downstream_task_list.md
```

`base_ontology` 字段和 `_compat/base_ontology.json` 只用于兼容旧消费者；下游新流程必须优先读取 `base_ontology_bundle/`。

`readable_report` 用 800-1500 字说明：研究范围、模板选择、骨架规模、核心传导、主要缺口、MVO 结果和下一步材料任务。报告必须说明候选性质，不得把模板假设写成已确认事实。

## 禁止事项

- 不确认行业事实，不输出已验证观测。
- 不跳过概念边界直接生成业务对象。
- 不输出 `ontology_bundle_vN/` 或 `_compat/optimized_ontology_vN.json`。
- 不因模板存在就补齐缺失关系端点。
- 不把新闻标题、研报观点或 AI 摘要升级为本体事实。
- 不输出买卖建议、目标价、收益率预测或仓位建议。
- 不修改核心规范；如发现 schema 无法表达，只记录候选核心变更建议。

## 本地校验

```bash
python3 scripts/validate_skill.py
```
