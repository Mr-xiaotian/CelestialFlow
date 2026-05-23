# util_cal

> 📅 最后更新日期: 2026/05/23

Web 模块的计算工具函数。

## cal_interval

```python
def cal_interval(refresh_interval: int) -> float:
    """将毫秒刷新间隔换算为秒，并限制在 [1.0, 60.0] 范围内。"""
```

将前端传入的毫秒级刷新间隔转换为秒，并限制在合理范围内，防止轮询频率过高导致服务器压力过大或轮询频率过低导致数据延迟。
