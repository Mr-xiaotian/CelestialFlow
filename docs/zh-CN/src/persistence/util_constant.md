# PersistenceConstant

> 📅 最后更新日期: 2026/05/24

`persistence/util_constant.py` 定义日志级别映射常量 `LEVEL_DICT`。

## 级别层级

日志级别按数值从低到高排列，形成严格的过滤层级：

```mermaid
flowchart TD
    subgraph Levels[日志级别层级 - 数值越大越优先]
        direction TB
        CRI["CRITICAL (60)"]
        ERR["ERROR (50)"]
        WAR["WARNING (40)"]
        INF["INFO (30)"]
        SUC["SUCCESS (20)"]
        DEB["DEBUG (10)"]
        TRA["TRACE (0)"]
    end

    CRI --> ERR
    ERR --> WAR
    WAR --> INF
    INF --> SUC
    SUC --> DEB
    DEB --> TRA

    style CRI fill:#b71c1c
    style ERR fill:#f44336
    style WAR fill:#ff9800
    style INF fill:#2196f3
    style SUC fill:#4caf50
    style DEB fill:#9e9e9e
    style TRA fill:#e0e0e0
```

该常量被 `LogInlet` 用于日志过滤与级别比较。当 `LogInlet` 的 `log_level` 设为某一级别时，所有级别数值低于该级别的日志均被丢弃。
