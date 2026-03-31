# utils/util_format.py
from datetime import datetime
from itertools import zip_longest
from typing import Any


# ======== format函数 ========
def format_repr(obj: Any, max_length: int) -> str:
    """
    将对象格式化为字符串，自动转义换行、截断超长文本。

    :param obj: 任意对象
    :param max_length: 显示的最大字符数（超出将被截断）
    :return: 格式化字符串
    """
    obj_str = str(obj).replace("\\", "\\\\").replace("\n", "\\n")
    if max_length <= 0 or len(obj_str) <= max_length:
        return obj_str

    # 截断逻辑（前 2/3 + ... + 后 1/3）
    segment_len = max(1, max_length // 3)

    first_part = obj_str[: segment_len * 2]
    last_part = obj_str[-segment_len:]

    return f"{first_part}...{last_part}"


def format_table(
    data: list,
    row_names: list[Any] | None = None,
    column_names: list[str] | None = None,
    index_header: str = "#",
    fill_value: str = "N/A",
    align: str = "left",
) -> str:
    """
    格式化表格数据为字符串(CelestialVault.TextTools中同名函数的简化版)。

    :param data: 二维列表，表格数据
    :param row_names: 行名列表（可选）
    :param column_names: 列名列表（可选）
    :param index_header: 行号列标题（默认 "#"）
    :param fill_value: 空值填充字符串（默认 "N/A"）
    :param align: 对齐方式（"left" 或 "right"，默认 "left"）
    :return: 格式化后的表格字符串
    """

    def _generate_excel_column_names(n: int, start_index: int = 0) -> list[str]:
        """
        生成 Excel 风格列名（A, B, ..., Z, AA, AB, ...）
        支持从指定起始索引开始生成。
        """
        names: list[str] = []
        for i in range(start_index, start_index + n):
            name = ""
            x = i
            while True:
                name = chr(ord("A") + (x % 26)) + name
                x = x // 26 - 1
                if x < 0:
                    break
            names.append(name)
        return names

    if not data:
        return "表格数据为空！"

    # 计算列数
    max_cols = max(map(len, data))

    # 生成列名
    if column_names is None:
        column_names = _generate_excel_column_names(max_cols)
    elif len(column_names) < max_cols:
        start = len(column_names)  # 从当前列名数量继续命名
        column_names.extend(
            _generate_excel_column_names(max_cols - len(column_names), start)
        )

    # 生成行名
    if row_names is None:
        row_names = list(range(len(data)))
    elif len(row_names) < len(data):
        row_names.extend([i for i in range(len(row_names), len(data))])

    # 添加行号列
    column_names = [index_header] + column_names
    num_columns = len(column_names)

    # 处理行号
    formatted_data: list[list[Any]] = []
    for i, row in enumerate(data):
        row_label = row_names[i] if row_names else i
        formatted_data.append([row_label] + list(row))

    # 统一填充数据行，确保所有行长度一致
    filled_rows = zip_longest(*formatted_data, fillvalue=fill_value)
    formatted_data = [list(row) for row in zip(*filled_rows)]  # 转置回来

    # 计算每列的最大宽度
    col_widths = [
        max(len(str(item)) for item in col)
        for col in zip(column_names, *formatted_data)
    ]

    # 选择对齐方式
    align_funcs = {
        "left": lambda text, width: f"{text:<{width}}",
        "right": lambda text, width: f"{text:>{width}}",
        "center": lambda text, width: f"{text:^{width}}",
    }
    align_func = align_funcs.get(align, align_funcs["left"])  # 默认左对齐

    # 生成表格
    separator = "+" + "+".join(["-" * (width + 2) for width in col_widths]) + "+"
    header = (
        "| "
        + " | ".join(
            [
                f"{align_func(name, col_widths[i])}"
                for i, name in enumerate(column_names)
            ]
        )
        + " |"
    )

    # 生成行
    rows_list = []
    for row in formatted_data:
        rows_list.append(
            "| "
            + " | ".join(
                [
                    f"{align_func(str(row[i]), col_widths[i])}"
                    for i in range(num_columns)
                ]
            )
            + " |"
        )
    rows = "\n".join(rows_list)

    # 拼接表格
    table = f"{separator}\n{header}\n{separator}\n{rows}\n{separator}"
    return table


def format_duration(seconds: int) -> str:
    """
    将秒数格式化为 HH:MM:SS 或 MM:SS（自动省略前导零）

    :param seconds: 秒数
    :return: 格式化后的时间字符串
    """
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_timestamp(timestamp: float) -> str:
    """
    将时间戳格式化为 YYYY-MM-DD HH:MM:SS

    :param timestamp: 时间戳（秒）
    :return: 格式化后的时间字符串
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def format_avg_time(elapsed: float, processed: int) -> str:
    """
    格式化平均时间（秒/任务或任务/秒）。

    :param elapsed: 总耗时（秒）
    :param processed: 已处理任务数
    :return: 格式化后的平均时间字符串
    """
    if elapsed and processed:
        avg_time = elapsed / processed
        if avg_time >= 1.0:
            # 显示 "X.XX s/it"
            avg_time_str = f"{avg_time:.2f}s/it"
        else:
            # 显示 "X.XX it/s"（取倒数）
            its_per_sec = processed / elapsed if elapsed else 0
            avg_time_str = f"{its_per_sec:.2f}it/s"
    else:
        avg_time_str = "N/A"

    return avg_time_str
