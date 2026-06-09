---
name: touyan-production-task-merge
description: 合并缺口发现、历史回放、评测缺陷、推理反馈和用户修订请求，形成本体优化 Skill 可执行的 bundle 路径化优化任务单与 patch_request_queue.yaml。输入多种诊断来源，输出 optimization_task_list.md、optimization_task_items.json、patch_request_queue.yaml 和 priority_decision.md。
metadata:
  short-description: 本体生产任务合并
---

# 生产任务合并 Skill

## 定位

本 Skill 是本体优化前的任务编排器。把多个诊断来源合并为一份去重、排序、可执行的任务单，并把可进入增量治理的事项整理为 `patch_request_queue.yaml`。它回答本轮优化的核心决策：修什么、为什么修、用什么修、写入哪个 bundle 模块、哪些必须本轮、哪些延后、哪些拒绝。

## 规范引用

本 Skill 的完整操作要求、字段 schema、归一化映射、去重算法、优先级排序、补证回路和边界处理，全部定义在：

| 规范文件 | 内容 |
|---------|------|
| `./references/生产任务合并要求.md` | 诊断来源归一化映射、13 字段任务项结构、去重算法、四维加权优先级排序（含补证可行性评分）、补证回路（含退出条件与死循环防护）、拒绝吸收规则、输出格式、边界情况 |

## 输入

可接收以下一种或多种诊断来源（最少需要缺口诊断或历史回放报告之一）：

| 来源 | 文件 | 产生者 |
|------|------|--------|
| 缺口诊断 | gap_report.md | 缺口发现 Skill (2-1) |
| 缺口清单 | gap_items.json | 缺口发现 Skill (2-1) |
| 优化建议 | optimization_suggestions.md | 缺口发现 Skill (2-1) |
| 候选补丁请求 | candidate_patch_requests.yaml | 缺口发现 Skill (2-1) |
| 回放报告 | replay_report.md | 历史回放 Skill (2-2) |
| 历史案例 | historical_cases.json | 历史回放 Skill (2-2) |
| 证据链 | evidence_chain.md | 历史回放 Skill (2-2) |
| 时间回放证据 | temporal_replay_evidence.yaml / invalidation_candidates.yaml | 历史回放 Skill (2-2) |
| 评测报告 | evaluation_report.md | 评测 Skill (4) |
| 缺陷工单 | defect_tickets.json | 评测 Skill (4) |
| 推理反馈 | ontology_feedback.json | 推理 Skill (5) |
| 推理运行记录 | inference_run_{id}.yaml | 推理 Skill (5) |
| 用户修订 | user_revision_request.md | 用户/研究员 |

## 输出

| 文件 | 说明 |
|------|------|
| optimization_task_list.md | 人类可读任务单（按 P0→P3 排序，结构见 `./references/生产任务合并要求.md` 第 8 节） |
| optimization_task_items.json | 结构化任务清单（JSON 数组，字段定义见 `./references/生产任务合并要求.md` 第 3 节，必须尽量包含 `target_file`、`target_path`、`target_id`、`legacy_path`） |
| patch_request_queue.yaml | 面向优化 Skill 的候选 PatchRequest 队列，记录 evidence ids、目标路径、操作、语义风险和合并前置条件。 |
| priority_decision.md | 优先级决策说明（结构见 `./references/生产任务合并要求.md` 第 7 节） |

## 禁止事项

除核心规范定义的公共禁止事项外，本 Skill 额外禁止：

- 不修改本体
- 不输出 ontology_bundle_vN/ 或 optimized_ontology_vN.json
- 不将缺少证据的任务标记为已完成
- 不把 patch_request_queue 中的事项标记为已合并；合并状态只能由本体优化 Skill 写入 patch ledger
- 不输出发布结论
- 不使用模糊表达描述 expected_change（如"优化""完善""改进"）
- 不为拒绝项提供空洞理由（如"不需要""不采纳"）
