---
name: touyan-cailiao-tupu-yuchuli
description: 将研报、公告、新闻、财报、会议纪要等非结构化投研材料，预处理为可追溯、可复核、可被后续本体工程使用的候选图谱结构。借鉴 neo4j-labs/llm-graph-builder 的 Document→Chunk→Entity→Relationship 分层抽取思路，受 schema 约束，每个候选元素必须挂接原文证据片段。输出 _artifacts/material_graph/ 下的候选对象、候选关系、候选状态变量、候选事件与信号、证据片段索引和待人工复核清单。
metadata:
  short-description: 投研材料图谱预处理
---

# 投研材料图谱预处理 Skill

## 定位

本 Skill 是投研本体生产流程中「材料入图前处理」的专门环节。它把散落在研报、公告、新闻、财报、会议纪要、访谈记录、产业链资料等非结构化或半结构化投研材料中的信息，转化为结构化、图谱化、可追溯的候选素材。

它不是直接生成权威本体的 Skill，也不是投研推理 Skill，而是专门负责「材料拆解→结构化抽取→证据挂载→候选图谱生成」的中间能力。

## 工程思路来源

本 Skill 重点吸收 `neo4j-labs/llm-graph-builder` 的四个核心经验：

1. **分层拆解**：材料应先被拆分为 Document → Chunk → Entity → Relationship 等层次，而不是直接从整篇材料生成结论。
2. **Schema 约束**：抽取过程应优先按照既定对象类型、关系类型和属性字段进行，避免 AI 自由发明结构。schema 约束来源采用三级降级：
   - **第一级**：当前 `ontology_bundle_vN/` 或 `base_ontology_bundle/` 的 schema（适用于已有本体的优化轮次）
   - **第二级**：`spec/schemas/` 公共规范 schema（适用于新主题冷启动首轮）
   - **第三级**：Skill 内置默认枚举（仅兜底，所有抽取结果标记 `pending_review`）
3. **证据挂载**：每一个候选对象、候选关系、候选信号和候选判断都必须挂接原文证据片段，保留来源、位置、时间、材料名称和可信度信息。
4. **图谱化可检索**：抽取结果应支持图谱化查看和检索，便于后续人工复核、问题定位和材料追溯。

## 在管线中的位置

```
01-信息与数据搜索
  → 02-材料图谱预处理（本 Skill）
  → 03-冷启动（首轮）或直接进入 04（优化轮）
  → 04-证据归一与校验
  → 05-缺口发现（直接消费 evidence_claims.yaml）
```

本 Skill 产出供 04-证据归一消费。04 负责时间归一和 claim 归并，本 Skill 负责实体-关系图谱的结构化抽取和证据钉住。

## 规范引用

| 规范文件 | 内容 |
|---------|------|
| `./references/材料图谱预处理要求.md` | 完整的分层抽取规则、schema 约束策略、输出结构规范、证据挂载要求、质量门槛和边界情况 |

## 输入

| 输入 | 必填 | 说明 |
|------|------|------|
| `source_materials/` | 必填 | 01-信息与数据搜索 输出的来源材料原文或摘录 |
| `source_registry.json` | 必填 | 01-信息与数据搜索 输出的来源登记，提供材料元信息 |
| `source_quality_assessment.md` | 可选 | 01-信息与数据搜索 输出的质量评估，辅助判断材料可信度 |
| `research_topic.md` | 必填 | 研究主题、范围、产业链边界 |
| `ontology_schema/` | 可选 | 本体 schema 约束，三级降级：1) ontology_bundle 的 schema；2) spec/schemas/；3) 内置默认枚举（标记 pending_review） |
| `downstream_task_list.md` | 可选 | 冷启动或用户给出的任务提示，用于确定抽取侧重 |

至少应提供可追溯的材料原文；否则只输出阻断说明和最小输入要求。

## 输出

| 文件 | 说明 |
|------|------|
| `_artifacts/material_graph/material_scope.md` | 材料范围说明：处理了哪些材料、覆盖范围、未处理材料及原因 |
| `_artifacts/material_graph/document_chunk_index.yaml` | Document/Chunk 清单：每份材料的拆分方案、chunk 边界、chunk 摘要 |
| `_artifacts/material_graph/candidate_objects.yaml` | 候选对象清单：行业、环节、公司、产品、技术路线、原材料、设备、客户、供应商、政策、事件、资产等 |
| `_artifacts/material_graph/candidate_relations.yaml` | 候选关系清单：上下游、供需、竞争、替代、依赖、影响、验证、约束等 |
| `_artifacts/material_graph/candidate_state_variables.yaml` | 候选状态变量清单：价格、库存、产能、订单、出货量、份额、成本、毛利率、需求、供给、政策强度、市场预期、资金关注度等 |
| `_artifacts/material_graph/candidate_events_signals.yaml` | 候选事件与信号清单：事件、信号、催化因素、反证条件、不确定性 |
| `_artifacts/material_graph/evidence_fragment_index.yaml` | 证据片段索引：每条抽取结果到原文片段的映射，包含来源材料、chunk、位置、原文引用、证据强度 |
| `_artifacts/material_graph/extraction_quality_report.md` | 抽取质量说明：覆盖率、schema 匹配率、置信度分布、未解析项 |
| `_artifacts/material_graph/pending_review_items.md` | 待人工复核清单：证据不足、来源不清、表述含糊、关系方向不确定、多解释可能的内容 |

## 输出边界

- 所有候选结果必须保留来源，不得脱离原文自行补充，不得把推测性内容写成确定事实。
- 候选对象和关系的 `recordStatus` 统一为 `candidate`，不做 `confirmed`。
- 不输出 `ontology_bundle_vN/`、`base_ontology_bundle/` 或 `_compat/*.json`。
- 不输出 `evidence_episodes.yaml`、`evidence_claims.yaml`、`evidence_facts.yaml`（那是 6-8 的职责）。
- 不输出 `gap_items.json` 或覆盖等级判断（那是 2-1 的职责）。
- 不输出投资建议、目标价、评级、收益率预测或仓位建议。

## 与 6-8 的分工

| 维度 | 6-1b 材料图谱预处理 | 6-8 Evidence Episode 归一 |
|------|---------------------|--------------------------|
| 关注点 | 实体-关系图谱的结构化抽取 | 证据的时间归一和 claim 归并 |
| 核心操作 | Document→Chunk→Entity→Relationship | Episode→Claim→Fact 归并 |
| 证据粒度 | 每个候选挂原文片段（chunk、位置、原文引用） | Claim 归并为 Fact，管理有效期和失效 |
| 时间处理 | 记录材料中的业务时间，不做归一 | 统一 business_time、valid_from/to、observed_at、learned_at |
| 输出 | 候选图谱结构 | Temporal Evidence Layer |

## 禁止事项

除核心规范定义的公共禁止事项外，本 Skill 额外禁止：

- 不脱离原文自行补充对象、关系或状态变量
- 不把推测性内容（预测、判断、分析师观点）写成确定事实
- 不把无法追溯原文位置的内容标记为有效候选
- 不用模型常识补全材料中没有表达的信息
- 不修改 `ontology_bundle_vN/`、`base_ontology_bundle/` 或兼容 JSON
- 不输出 EvidenceClaim、EvidenceFact 或覆盖判断（那是其他 Skill 的职责）
- 不生成买卖建议、目标价、收益率预测或仓位建议
- 不对冲突材料做合并裁决（保留冲突，标注待复核）
