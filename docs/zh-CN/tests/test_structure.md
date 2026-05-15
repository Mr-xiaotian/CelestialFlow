# test_structure.py 测试说明

> 📅 最后更新日期: 2026/05/15

## 测试目标

验证 `TaskLoop` 和 `TaskWheel` 两种含环图结构的图分析能力，包括：
- DAG 检测（含环图应返回 `isDAG=False`）
- 层级计算（环内节点同层，center 节点单独一层）
- 源节点推导（`get_source_stages`）

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskLoop` | 2 | 环结构分析、环结构 source 推导 |
| `TestTaskWheel` | 2 | 轮结构分析（center + ring 层级）、轮结构 source 推导 |

### 关键用例详解

#### `test_loop_analysis`
- **目标**：验证 `TaskLoop`（s1 → s2 → s3 → s1）的图分析结果。
- **断言**：`isDAG` 为 `False`；所有节点在同一层级。

#### `test_loop_source_stages`
- **目标**：验证环结构的 `get_source_stages()` 返回环内某个代表节点。
- **断言**：返回 1 个 source，tag 属于环内节点。

#### `test_wheel_analysis`
- **目标**：验证 `TaskWheel`（center → {r1, r2, r3}，r1 → r2 → r3 → r1）的层级结构。
- **断言**：`isDAG` 为 `False`；center 在第 0 层，ring 节点在第 1 层。

#### `test_wheel_source_stages`
- **目标**：验证轮结构的 `get_source_stages()` 仅返回 center 节点。
- **断言**：返回 1 个 source，tag 等于 center 的 tag。

## 依赖

| 依赖 | 说明 |
|------|------|
| `celestialflow` | `TaskLoop`、`TaskWheel`、`TaskStage` |

## 运行方式

```bash
pytest tests/test_structure.py -v
```

## 性能参考

| 测试 | 耗时（Windows / i5） |
|------|---------------------|
| `TestTaskLoop` | ~2s |
| `TestTaskWheel` | ~2s |

## 相关文件

- `src/celestialflow/graph/core_structure.py`：`TaskLoop`、`TaskWheel` 实现
- `src/celestialflow/graph/util_analysis.py`：图分析工具函数
- `tests/test_graph.py`：`TaskGraph` 及其他结构子类测试
