# 投研本体 Skill 协作关系

本文描述投研本体相关 Skill 之间的整体编排关系。公共文件契约见 `../spec/投研本体核心规范/references/03_本体Bundle文件契约.md`。

## 主流程

```text
用户输入主题或材料
   ↓
信息与数据搜索 → 材料图谱预处理
   ↓
冷启动 Skill → base_ontology_bundle/
   ↓
证据归一 → 缺口发现 → 历史案例 → 历史回放 → 任务合并
   ↓
本体优化 Skill → ontology_bundle_vN/
   ↓
人类可读解析 → 评测数据输入 → Release 组装校验（含来源摘要）
   ↓
release_package/
   ↓
评测 Skill
   ├── 通过/有条件/拒绝/证据不足：评测结论只存在于评测输出
   └── 修复任务：回到生产任务合并和本体优化
   ↓
推理 Skill
   └── inference_run / ontology_feedback：先归一为 EvidenceEpisode，再回到缺口发现、历史回放或优化
```

## 角色分工

| 阶段 | Skill | 权威输出 | 角色 |
|---|---|---|---|
| 主题初建 | 冷启动 Skill | `base_ontology_bundle/` | 生成候选骨架、概念层和材料缺口。 |
| 材料来源 | 信息与数据搜索 Skill | `_artifacts/sources/` | 登记和评估来源，不修改本体。 |
| 材料图谱 | 材料图谱预处理 Skill | `_artifacts/material_graph/` | 按 Document→Chunk→Entity→Relationship 分层抽取候选图谱结构。 |
| 证据归一 | 证据归一与校验 Skill | `_artifacts/evidence_graph/` | 消费材料图谱，生成 EvidenceEpisode、EvidenceClaim、EvidenceFact 和失效候选。 |
| 覆盖诊断 | 缺口发现 Skill | `_artifacts/gap_discovery/` | 直接消费 evidence_claims.yaml，内部生成 gap_reference_view，输出缺口、任务和优化交接。 |
| 历史验证 | 历史回放 Skill | `_artifacts/historical_replay/` | 校验链路、阻断、误触发和漏触发。 |
| 任务合并 | 生产任务合并 Skill | `_artifacts/task_merge/` | 合并诊断和反馈，生成路径化任务单和 patch request queue。 |
| 候选本体 | 本体优化 Skill | `ontology_bundle_vN/`、`_artifacts/patches/` | 生成完整候选本体 bundle、兼容 JSON 和 patch ledger。 |
| 交付准备 | 解析、评测输入 Skill | `docs/` 和 `_artifacts/evaluation_results/` | 准备人类阅读和评测交接。 |
| 组装发布 | Release 组装校验 Skill | `release_package/` | 组装校验交付包，生成 source_material_summary.md。 |
| 发布前校验 | 评测 Skill | `evaluation_result.json` 等评测输出 | 评分和发布判断，不修改本体。 |
| 应用推理 | 推理 Skill | `reasoning_result`、`inference_run`、`ontology_feedback` | 使用本体和当前有效 evidence，不维护本体。 |

## 反馈闭环

评测未通过时：

1. 评测 Skill 输出 `evaluation_fix_report` 和可选 `optimization_plan`。
2. Evidence Episode 归一与校验 Skill 把评测反馈和回补材料转成 evidence graph。
3. 生产任务合并 Skill 把评测问题转成 bundle 路径化任务和 patch request queue。
4. 本体优化 Skill 生成新的 `ontology_bundle_vN+1/` 和 patch ledger。
5. 重新进入交付准备和评测。

推理阶段发现问题时：

1. 推理 Skill 输出 `inference_run` 和 `ontology_feedback`。
2. Evidence Episode 归一与校验 Skill 把推理反馈转成 EvidenceEpisode / EvidenceClaim。
3. 缺口发现或历史回放 Skill 把反馈转成诊断建议和 candidate patch request。
4. 生产任务合并 Skill 合并任务和 patch request queue。
5. 本体优化 Skill 修复 bundle、追加 patch ledger，重新评测。

## 发布口径

- `base_ontology_bundle/`：冷启动候选骨架，不能作为正式推理基座。
- `ontology_bundle_vN/`：待评测候选本体。
- `published_ontology_bundle_vN/`：通过发布流程后才能成为正式推理基座。

生产 Agent 不输出 `published_ontology_bundle_vN/`。发布结论只由评测/发布流程产生。
