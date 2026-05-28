# 克隆工具测试 (test_clone.py)

> 📅 最后更新日期: 2026/05/28

## 作用

验证 `celestialflow.utils.util_clone` 中的 `clone_executor`、`clone_stage`、`clone_graph` 三个克隆函数，确保深度复制后新对象与原对象属性一致且相互独立。

## 核心测试对象

- `clone_executor`: 复制 `TaskExecutor`，保留 `name`、`func`、`execution_mode`。
- `clone_stage`: 复制 `TaskStage`，保留 `name`、`func`、`execution_mode`、`stage_mode`。
- `clone_graph`: 复制 `TaskGraph`，保留完整的 DAG 结构（节点、边、schedule_mode），且节点间相互独立。

## 关键测试场景

### `clone_executor`
- 克隆后 `name` / `func` / `execution_mode` 与原对象相同
- 克隆返回的是不同对象（`is not` 检查）
- 修改克隆的 `execution_mode` 不影响原对象

### `clone_stage`
- 克隆后 `name` / `func` / `execution_mode` / `stage_mode` 与原对象相同
- 克隆返回的是不同对象
- 修改克隆的 `execution_mode` 不影响原 stage

### `clone_graph`
- 简单 DAG（A→B→C）：克隆后源节点、NetworkX 节点集合、边集合均一致
- `schedule_mode` 正确保留
- 克隆图中修改某节点的 `execution_mode` 不影响原图对应节点

## 运行方式

```bash
# 全部执行
pytest tests/utils/test_clone.py -v

# 仅运行 executor 克隆测试
pytest tests/utils/test_clone.py -k "executor" -v

# 仅运行 stage 克隆测试
pytest tests/utils/test_clone.py -k "stage" -v

# 仅运行 graph 克隆测试
pytest tests/utils/test_clone.py -k "graph" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestUtilClone` | ~0.1s |

## 重要细节

- 克隆图时通过 NetworkX 图验证节点和边的一致性，源节点访问同时触发 `_build_analysis`。
- `clone_graph` 测试构造了有向无环图 `A → B → C`，验证图结构完整性。

## 注意事项

- 克隆工具用于 `benchmark_graph` 内部复制图结构以实现不同模式组合的独立执行。
- 相关实现位于 `src/celestialflow/utils/util_clone.py`。
