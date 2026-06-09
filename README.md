# 投研本体生产体系目录

本仓库包含投研本体的核心规范、建设型 Skill、评测与推理 Skill，以及新增的本体生产 Agent。

## 目录总览

```text
.
├── spec/
│   └── 投研本体核心规范/
├── skills/
│   ├── 01-信息与数据搜索/
│   ├── 02-材料图谱预处理/
│   ├── 03-冷启动/
│   ├── 04-证据归一与校验/
│   ├── 05-缺口发现/
│   ├── 06-历史案例生成/
│   ├── 07-历史回放校验/
│   ├── 08-生产任务合并/
│   ├── 09-本体优化/
│   ├── 10-人类可读解析/
│   ├── 11-评测数据输入生成/
│   ├── 12-Release组装校验/
│   ├── 13-本体评测/
│   └── 14-投研推理/
├── touyan-ontology-production-agent/
├── outputs/
├── demo_test/
├── scripts/
└── migration_map.md
```

## Agent

### `touyan-ontology-production-agent/`

投研本体生产线总调度 Agent，负责把冷启动、材料搜索、材料图谱预处理、证据归一、缺口发现、历史案例生成、历史回放、本体优化、人类可读解析和评测交接串成生产流程。

核心文件：

- `AGENT.md`：Agent 的目标、职责边界、输入输出和结束条件。
- `workflow.md`：新主题冷启动、已有本体优化、评测未通过修复等流程。
- `skill_registry.yaml`：Agent 可调用 Skill 的注册表。
- `io_contracts.md`：文件级输入输出契约。

最终交付：

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
    material_graph/
    evidence_graph/
    patches/
    reasoning_runs/
```

## Skill 分层

### 公共规范

- `spec/投研本体核心规范/`：公共 ontology bundle 文件契约、对象、关系、动作 schema、Temporal Evidence Layer、Patch Ledger、Inference Run 和核心建模规范。`source_registry.json` 单写原则在此定义。

### 生产 Skill（按管线顺序）

| 编号 | Skill | 注册名 | 职责 |
|------|-------|--------|------|
| 01 | `skills/01-信息与数据搜索/` | `source_search` | 统一搜索、登记、评估来源材料。`source_registry.json` 独占维护。 |
| 02 | `skills/02-材料图谱预处理/` | `material_graph_preprocessing` | Document→Chunk→Entity→Relationship 分层抽取，schema 三级降级约束。 |
| 03 | `skills/03-冷启动/` | `cold_start` | 研究主题 → `base_ontology_bundle/`。 |
| 04 | `skills/04-证据归一与校验/` | `evidence_episode_normalization` | 消费材料图谱 → Temporal Evidence Layer。 |
| 05 | `skills/05-缺口发现/` | `gap_discovery` | 本体 vs evidence claims 覆盖诊断（含原 6-2 的 adapter 逻辑）。 |
| 06 | `skills/06-历史案例生成/` | `historical_case_generation` | 搜索组装历史案例材料，t0 信息包防泄漏。 |
| 07 | `skills/07-历史回放校验/` | `historical_replay` | 历史案例回放校验传导链、阻断、误触发、漏触发。 |
| 08 | `skills/08-生产任务合并/` | `production_task_merge` | 合并去重多来源诊断，生成 bundle 路径化任务单。 |
| 09 | `skills/09-本体优化/` | `ontology_optimization` | 唯一输出 `ontology_bundle_vN/` 的建设型 Skill。 |
| 10 | `skills/10-人类可读解析/` | `readable_parser` | bundle → `docs/ontology_guide.md`。 |
| 11 | `skills/11-评测数据输入生成/` | `evaluation_input_generation` | 准备评测数据输入和交接说明。 |
| 12 | `skills/12-Release组装校验/` | `release_package_builder` | 组装校验 release_package，生成 `source_material_summary.md`（含原 6-5b 逻辑）。 |

### 独立 Skill（不在生产 Agent 管线中）

| 编号 | Skill | 用途 |
|------|-------|------|
| 13 | `skills/13-本体评测/` | 评测本体是否达到发布阈值 |
| 14 | `skills/14-投研推理/` | 基于本体 + evidence 执行链路推理 |

## 支撑说明

生产 Agent 的旧版跨 Skill 协作说明已放入 `touyan-ontology-production-agent/skill_collaboration.md`。

各支撑 Skill 的详细要求已放入各自目录的 `references/`，例如历史案例生成、人类可读解析和评测数据输入生成要求。

## 样例输出

- `outputs/`：历史运行或样例输出，用于查看半导体产业相关缺口发现、历史案例、历史回放和优化结果。

## 脚本

- `scripts/validate_all_skills.py`：读取 `skill_registry.yaml` 自动发现并校验所有已注册 Skill。
- `scripts/sync_core_copies.py`：同步核心规范副本。

## 命名说明

Skill 注册名（如 `source_search`、`gap_discovery`）保持稳定，是 Skill 的唯一身份标识。目录名表达管线顺序，可根据需要调整。`skill_registry.yaml` 为路径的唯一权威来源。旧目录到新目录的完整映射见 `migration_map.md`。
