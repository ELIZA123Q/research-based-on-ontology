# 变更记录

## v1 (2026-06-08) — 冷启动

### 新增
- OBJ-001: 碳酸锂现货价格（macro_variable）
- OBJ-002: 磷酸铁锂正极材料企业毛利率（financial_metric）
- OBJ-003: 库存减值（accounting_event, triggered）
- OBJ-004: 长协锁价比例（business_parameter, modulates）
- CHAIN-001: 碳酸锂现货价→正极毛利率传导（4步）
- TRIG-001: 库存减值触发条件

### 保留
- 无（初始版本）

### 删除
- 无（初始版本）

### 降级
- 无

### 拒绝
- REJ-001: LFP/NCM 定量差异（证据不足）
