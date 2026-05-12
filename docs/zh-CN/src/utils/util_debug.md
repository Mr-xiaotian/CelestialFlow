# UtilsDebug

> 📅 最后更新日期: 2026/05/09

`utils/util_debug.py` 提供调试辅助函数。

## 主要函数

- `find_unpickleable(obj)`：检测对象是否可被 pickle，失败时打印定位信息。

常用于排查对象不可序列化问题（例如需要跨进程传递数据或持久化时）。
