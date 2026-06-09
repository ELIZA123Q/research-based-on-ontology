---
name: touyan-release-package-builder
description: 组装并校验投研本体生产 Agent 的最终 release_package。输入 release manifest、ontology_bundle、docs、_artifacts 和可选 _compat，输出 release_package/ 和 package_check_report.md。
metadata:
  short-description: Release Package 组装校验
---

# Release Package 组装与校验 Skill

## 定位

本 Skill 是投研本体生产 Agent 的最终收口步骤。检查候选交付文件是否齐全、命名是否正确、版本是否一致、概念层和边界是否清楚，并检查 material_graph、evidence_graph、patches、reasoning_runs 等审计归档是否按契约进入 `_artifacts/`，最终组装 release_package/。

此外，本 Skill 负责聚合来源材料元数据生成 `source_material_summary.md`（原 6-5b 逻辑已并入），作为 release_package 的独立交付物。

**"可以交给评测 Agent"只表示生产侧文件完整，不表示本体通过评测或已发布。**

## 规范引用

本 Skill 的完整校验清单（16 项）、失败处理流程、版本号管理、输出规范和边界情况，全部定义在：

| 规范文件 | 内容 |
|---------|------|
| `./references/ReleasePackage组装校验要求.md` | bundle 文件齐全性、Palantir 主干完整性、版本一致性、artifacts 审计归档、越权内容、BLOCK/WARN 分级、release_package/ 目录规范 |

## 输入

必备输入：

| 文件 | 产生者 |
|------|--------|
| 00_release_manifest.yaml | 生产 Agent / Release Package Builder |
| ontology_bundle_vN/ | 本体优化 Skill (09) |
| docs/ontology_guide.md | 人类可读解析 Skill (10) |
| docs/production_notes.md | 本体优化 Skill (09) / 生产 Agent |
| docs/evaluation_handoff.md | 评测数据输入生成 Skill (11) |
| _artifacts/artifact_manifest.yaml | 生产 Agent / Release Package Builder |
| _artifacts/sources/source_registry.json | 信息与数据搜索 Skill (01) |
| _artifacts/sources/source_quality_assessment.md | 信息与数据搜索 Skill (01) |
| _artifacts/material_graph/ | 材料图谱预处理 Skill (02)，可选但建议 |
| _artifacts/evidence_graph/ | 证据归一与校验 Skill (04)，可选但建议 |
| _artifacts/patches/ | 本体优化 Skill (09)，可选但建议 |
| _artifacts/reasoning_runs/ | 投研推理 Skill (14)，可选 |
| _compat/optimized_ontology_vN.json | 本体优化 Skill (09)，可选但建议 |

## 输出

```
release_package/
  00_release_manifest.yaml
  ontology_bundle_vN/
  docs/
    ontology_guide.md
    production_notes.md
    evaluation_handoff.md
    source_material_summary.md
  _compat/
  _artifacts/
```

`source_material_summary.md` 同时写入 `_artifacts/sources/source_material_summary.md` 作为审计归档。`production_notes.md` 只保留来源摘要的简版结论和指向 `source_material_summary.md` 的引用，不承载完整来源摘要。

可选输出：package_check_report.md（建议始终生成，7 章结构见 `./references/ReleasePackage组装校验要求.md` 第 7 节）

## 禁止事项

除核心规范定义的公共禁止事项外，本 Skill 额外禁止：

- 不修改 ontology_bundle_vN/ 或 optimized_ontology_vN.json
- 不输出 published_ontology_bundle_vN/、evaluation_result.json、release_decision.md
- 不输出任何发布或评测结论
- 不在 release_package/ 中包含中间产物（gap_items.json、replay_report.md 等）
