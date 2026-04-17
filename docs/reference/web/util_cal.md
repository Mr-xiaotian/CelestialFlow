# util_cal

Web 模块的计算工具函数。

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """将毫秒刷新间隔换算为秒，并限制在 [1, 60] 范围内。"""
```

将前端传入的毫秒级刷新间隔转换为秒，并限制在合理范围内，防止过于频繁或过于稀疏的轮询。
