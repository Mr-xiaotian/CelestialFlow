# Funnel 模块

> 📅 最后更新日期: 2026/05/09

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
- **与 Runtime 模块**: 使用 `TerminationSignal` 作为停止信号

## 使用示例

以下示例展示 `BaseInlet` 和 `BaseSpout` 的基本使用模式。

### BaseSpout + BaseInlet 协作

```python
from queue import Queue
from celestialflow.funnel import BaseSpout, BaseInlet

# 1. 自定义 Spout：将收到的记录打印到控制台
class PrintSpout(BaseSpout):
    def _handle_record(self, record):
        print(f"Spout 收到: {record}")

# 2. 创建 Spout 和 Inlet
spout = PrintSpout()
inlet = BaseInlet(spout.get_queue())

# 3. 启动后台监听线程
spout.start()

# 4. 通过 Inlet 发送记录
inlet._funnel("Hello, World!")
inlet._funnel({"key": "value"})
inlet._funnel(42)

# 5. 停止 Spout
spout.stop()
print("Spout 已停止")
```

### 使用 BaseSpout 的自定义钩子

```python
from queue import Queue
from celestialflow.funnel import BaseSpout

class FileSpout(BaseSpout):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename
        self.file = None

    def _before_start(self):
        print(f"打开文件: {self.filename}")

    def _handle_record(self, record):
        print(f"处理记录: {record}")

    def _after_stop(self):
        print(f"关闭文件: {self.filename}")

spout = FileSpout("records.log")
spout.start()
spout.get_queue().put("record1")
spout.get_queue().put("record2")
spout.stop()
```
