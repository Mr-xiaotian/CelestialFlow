# demo_utils.py 演示工具说明

## 目标

为 `demo/` 目录下的演示脚本提供共享的测试函数和辅助类。与 `tests/test_utils.py` 内容基本一致，是演示代码的专用工具库。

## 内容分类

### 通用计算函数
- `fibonacci` / `fibonacci_async`：递归斐波那契（含异常边界）
- `no_op` / `sum_int` / `add_one` / `sqrt`：基础运算
- `square` / `add_offset` / `add_5` / `add_10` 等：含 1 秒 sleep 的模拟耗时任务
- `neuron_activation`：Sigmoid 激活函数（模拟 ML 推理）

### Sleep 变体
- `sleep_1` / `sleep_1_async`：纯延迟 1 秒

### 带 sleep 的运算（demo_structure 用）
- `operate_sleep` / `operate_sleep_A~E`：二元运算，延迟 1 秒
- `add_one_sleep`：含多条件异常边界（`n>30`、`n==0`、`n is None`）

### URL 处理函数（demo_stages 用）
- `generate_urls_sleep` / `log_urls_sleep` / `download_sleep` / `parse_sleep`
- `download_to_file`：真实 HTTP 下载到本地文件

### 特殊类
- `RouterWrapper`：`TaskRouter` 演示用的路由包装器

## 与 tests/test_utils.py 的关系

两个文件内容几乎完全相同。历史原因可能是演示代码从测试代码中分离出来时保留了副本。维护时建议保持两者同步，或考虑将公共工具提取到 `celestialflow/utils/` 下的独立模块。

## 可能出现的问题

1. **与 tests/test_utils.py 的重复**：修改一处时容易遗漏另一处，导致演示和单元测试的行为分化。
2. **Windows 路径硬编码**：`download_to_file` 中 `/tmp/` 路径替换为 `X:/Download/...`，在非 Windows 环境会失败。
3. **`requests` 网络依赖**：`download_to_file` 需要外网访问能力，在隔离网络环境不可用。

## 运行方式

此文件为共享模块，不直接运行：
```python
from demo_utils import fibonacci, sleep_1, RouterWrapper
```

## 依赖

- `requests`
