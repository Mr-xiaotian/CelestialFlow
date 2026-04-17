# Funnel 模块

Funnel 模块提供了 CelestialFlow 的队列通信基础设施，是 Persistence 模块中 `LogSpout`/`LogInlet` 和 `FailSpout`/`FailInlet` 的底层基类。

## 模块概述

Funnel 模块采用 Spout/Inlet（出口/入口）模式，实现多进程安全的异步队列通信。Inlet 负责将记录写入队列，Spout 在后台线程中从队列读取并处理记录。

## 文件说明

### 核心组件

1. **core_spout.py** (`BaseSpout`)
   - **作用**: 所有出口类的基类，提供后台线程监听和队列消费功能
   - **关键功能**: 后台线程监听、优雅启停、多进程安全队列

2. **core_inlet.py** (`BaseInlet`)
   - **作用**: 所有入口类的基类，提供队列写入功能
   - **关键功能**: 队列写入封装

## 继承关系

```
BaseSpout (funnel/core_spout.py)
├── LogSpout (persistence/core_log.py)
├── FailSpout (persistence/core_fail.py)
└── SuccessSpout (persistence/core_success.py)

BaseInlet (funnel/core_inlet.py)
├── LogInlet (persistence/core_log.py)
└── FailInlet (persistence/core_fail.py)
```

## 模块关联

### 外部关联
- **与 Persistence 模块**: `LogSpout`/`LogInlet`、`FailSpout`/`FailInlet`、`SuccessSpout` 均继承自本模块基类
- **与 Runtime 模块**: 使用 `TerminationSignal` 作为停止信号，使用 `cleanup_mpqueue` 清理队列
