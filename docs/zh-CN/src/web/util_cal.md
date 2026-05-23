# util_cal

> 📅 最后更新日期: 2026/05/23

Web 模块的计算工具函数。

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """将毫秒刷新间隔换算为秒，并限制在 [1.0, 60.0] 范围内。"""
```

将前端传入的毫秒级刷新间隔转换为秒，并限制在合理范围内，防止轮询频率过高导致服务器压力过大或轮询频率过低导致数据延迟。

## 使用示例

### 日历/时间计算函数的使用示例

```python
from celestialflow.web.util_cal import cal_interval

# 5000ms -> 5.0s（标准 5 秒刷新）
print(f"5000ms -> {cal_interval(5000)}s")    # 5.0

# 1000ms -> 1.0s（下限 1 秒）
print(f"1000ms -> {cal_interval(1000)}s")    # 1.0

# 500ms -> 1.0s（低于下限，被限制到 1.0）
print(f"500ms  -> {cal_interval(500)}s")     # 1.0

# 120000ms -> 60.0s（超过上限，被限制到 60.0）
print(f"120000ms -> {cal_interval(120000)}s") # 60.0

# 边界：正好等于上限
print(f"60000ms -> {cal_interval(60000)}s")   # 60.0

# 典型的 Web UI 刷新间隔配置
refresh_options_ms = [1000, 2000, 5000, 10000, 30000]
print("\n常见刷新间隔转换:")
for ms in refresh_options_ms:
    seconds = cal_interval(ms)
    print(f"  {ms:>6}ms -> {seconds:.1f}s")
# 输出：
#    1000ms -> 1.0s
#    2000ms -> 2.0s
#    5000ms -> 5.0s
#   10000ms -> 10.0s
#   30000ms -> 30.0s
```
