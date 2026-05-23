# ~~UtilsDebug~~（已废弃）

> 📅 最后更新日期: 2026/05/24

## ⚠️ 废弃说明

该文档对应的源文件 `utils/util_debug.py` 已不存在（已从项目中移除），本文档仅保留历史参考价值。

---

## 历史描述（仅供参考）

原 `utils/util_debug.py` 提供调试辅助函数。

### 主要函数

- `find_unpickleable(obj)`：检测对象是否可被 pickle，失败时打印定位信息。

常用于排查对象不可序列化问题（例如需要跨进程传递数据或持久化时）。

---

> 如需类似调试功能，可参考 `celestialflow.runtime.util_hash.make_hashable` 或自行实现 pickling 检测。
