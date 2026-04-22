# web/util_cal.py
def cal_interval(refresh_interval: int) -> float:
    """
    将毫秒刷新间隔换算为秒，并限制在 [1, 60] 范围内。

    :param refresh_interval: 刷新间隔（毫秒）
    :return: 限制在 [1, 60] 范围内的秒数
    """
    return max(1.0, min(float(refresh_interval) / 1000.0, 60.0))
