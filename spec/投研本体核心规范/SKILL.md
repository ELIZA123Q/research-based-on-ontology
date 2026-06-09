---
name: touyan-bentiguifan-hexin
description: 投研本体公共核心规范，维护 ontology bundle 文件契约、概念层结构、对象 schema、关系 schema、动作与状态机 schema、bundle 级版本元数据、质量元数据和一致性校验规则。本 Skill 属于规范型 Skill，主要用于被其他任务型 Skill 引用、加载和校验，不直接面向用户生成研究输出。
metadata:
  short-description: 投研本体核心规范
---

# 投研本体核心规范

## 定位

本 Skill 是投研本体工程体系的公共规范层，负责维护 ontology bundle 文件契约、概念层结构、对象 schema、关系 schema、动作与状态机 schema、bundle 级版本元数据、质量元数据和一致性校验规则。

本 Skill 属于规范型 Skill，主要用于被其他任务型 Skill 引用、加载和校验，不直接面向用户生成研究输出。

它不做行业冷启动，不做材料抽取，不做本体优化，不做投研推理，也不输出投资结论、买卖建议、目标价、收益率预测或仓位建议。

本目录只描述公共 bundle 文件形态、概念层、对象、关系、动作、状态机、版本元数据、质量元数据、Temporal Evidence Layer、Patch Ledger 和 Inference Run 的公共契约，不描述跨任务编排关系。任务编排应由外部流程文档维护。

概念层用于定义研究范围、术语、边界、同义词和概念到业务对象的映射规则。核心规范只定义概念层结构，不写死任何行业的具体概念内容；半导体、光通信、硅光等概念实例应进入对应行业本体的 `concept_layer`。

业务结构图谱的可生成性由核心关系 schema 约束：图谱脚本只能消费显式关系，不能凭行业常识、对象排序或 `positionInChain` 补边。

Graphiti 式动态上下文图谱只作为证据和运行记录层的设计参考：EvidenceEpisode、EvidenceClaim、EvidenceFact、PatchRequest、PatchLedgerItem 和 InferenceRun 支撑来源追溯、有效期、失效、增量合并和推理运行审计，但不替代 Palantir 式本体主干。

## 规范文件

- `schemas/objects.yaml`：对象类型、字段、状态字段和治理层级。
- `schemas/concepts.yaml`：概念层结构、术语、边界、同义词和概念到业务对象的映射规则。
- `schemas/relations.yaml`：概念关系、业务关系、端点、方向、属性和信号角色约束。
- `schemas/actions.yaml`：动作类型、输入输出、状态流转、权限、审核、审计与状态机约束。
- `schemas/ontology_bundle.yaml`：bundle 级文件契约、版本字段、质量元数据、兼容字段和发布包约束。
- `references/01_投研本体核心说明.md`：业务主线和治理边界。
- `references/02_投研本体建模规格说明.md`：对象、关系、动作和状态机解释。
- `references/03_本体Bundle文件契约.md`：`base_ontology_bundle/`、`ontology_bundle_vN/`、`release_package/`、`_compat/` 和 `_artifacts/` 的公共文件契约。

## 使用规则

- 任务型目录可以保留本地 schema copy 以便单独安装，但本地 copy 必须声明 `core_schema_version`，并通过校验脚本确认其与本核心规范版本兼容。
- 任务型目录只应在 `SKILL.md` 中保留触发条件、边界、流程和输出契约；公共对象、关系、动作知识以本目录为准。
- 任务型目录读写本体时必须优先支持 `ontology_bundle_vN/` 或 `base_ontology_bundle/`，再兼容旧 JSON。
- 若公共 schema 或 bundle 契约变化，必须同步更新依赖目录的本地 copy、输出 schema、示例和校验脚本。

## 本地校验

```bash
python3 scripts/validate_core.py
```
