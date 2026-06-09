---
name: touyan-source-search-and-data-registry
description: 为投研本体生产 Agent 提供统一的信息与数据搜索、来源登记和材料质量评估。输入研究主题和下游任务单，输出 _artifacts/sources/ 下的 source_materials/、source_registry.json、source_search_log.md 和 source_quality_assessment.md。
metadata:
  short-description: 投研来源搜索与登记
---

# 信息与数据搜索 Skill

## 定位

本 Skill 是投研本体生产流程的入口。围绕研究主题统一搜索、登记和评估来源材料。产出三类结果：可追溯材料文件、结构化来源登记、质量评估报告；并为 6-8 Evidence Episode 归一与校验 Skill 提供 `episode_seed`。

## 规范引用

本 Skill 的完整操作要求、字段 schema、搜索策略、质量门槛、受限内容处理、边界情况和交接约定，全部定义在：

| 规范文件 | 内容 |
|---------|------|
| `./references/信息与数据搜索要求.md` | 搜索策略与数据源、source_registry.json 字段规范（17 字段）、材料质量评估（7 章结构）、受限内容处理、搜索日志、质量门槛、边界情况、下游交接约定 |

## 输入

| 文件 | 必填 | 说明 |
|------|------|------|
| research_topic.md | 必填 | 研究主题、范围、产业链环节、关键对象和核心变量 |
| downstream_task_list.md | 可选 | 冷启动输出的下游任务提示 |
| user_source_preferences.md | 可选 | 用户指定的优先数据源、排除来源、搜索偏好 |
| raw_materials/ | 可选 | 用户提供的原始材料目录 |

## 输出

| 文件 | 说明 |
|------|------|
| `_artifacts/sources/source_materials/` | 原始材料目录，按 policies/announcements/financial_reports/industry_data/reports/news/data_extracts/restricted/ 分类 |
| `_artifacts/sources/source_registry.json` | 结构化来源登记（字段定义见 `./references/信息与数据搜索要求.md` 第 4 节） |
| `_artifacts/sources/source_search_log.md` | 搜索日志（结构见 `./references/信息与数据搜索要求.md` 第 6 节） |
| `_artifacts/sources/source_quality_assessment.md` | 材料质量评估报告（7 章结构见 `./references/信息与数据搜索要求.md` 第 5 节） |

`source_registry.json` 中每份材料应尽量提供 `episode_seed`，供 6-8 消费；6-1 不直接抽取正式 EvidenceFact。

## 禁止事项

除核心规范定义的公共禁止事项外，本 Skill 额外禁止：

- 不判断本体覆盖等级（covered / not_covered / partially_covered / conflicting / out_of_scope）
- 不输出 gap_items.json、replay_report.md、ontology_bundle_vN/ 或 optimized_ontology_vN.json
- 不输出评测结论或发布结论
- 不把分析师预测、评级、目标价、推荐语、收益率推断或仓位表达登记为事实观测
- 不用无法追溯的材料支撑关键事实
- 不伪造、不推测、不以 AI 生成内容冒充搜索结果
- 不直接抽取或确认 EvidenceFact；正式 episode、claim 和 fact 由 6-8 归一校验
