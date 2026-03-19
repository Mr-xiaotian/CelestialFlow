# UtilsDebug

`utils/debug.py` 提供调试辅助函数。

## 主要函数

- `find_unpickleable(obj)`：检测对象是否可被 pickle，失败时打印定位信息。

常用于排查 process 模式下对象不可序列化问题。
