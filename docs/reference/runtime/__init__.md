# Runtime 模块

Runtime 模块提供了 CelestialFlow 的任务执行运行时环境，包括任务调度、队列管理、错误处理、性能监控等核心功能。它是任务实际执行的基础设施层。

## 模块概述

Runtime 模块负责管理任务执行的生命周期，从任务提交到结果返回的整个过程。它提供了多种执行模式（串行、并行、异步）、健壮的错误处理机制、性能监控和资源管理功能。

## 文件说明

### 核心运行时组件

1. **core_runner.py** (`TaskRunner`)
   - **作用**: 任务执行的核心运行器，支持多种执行模式
   - **执行模式**:
     - 串行执行: 顺序执行任务
     - 线程池: 并发执行 I/O 密集型任务
     - 进程池: 并发执行 CPU 密集型任务
     - 异步执行: 基于 asyncio 的异步任务
   - **关键功能**: 任务调度、工作线程管理、超时控制、资源清理

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **作用**: 任务输入/输出队列，实现节点间的数据传递
   - **队列类型**:
     - `TaskInQueue`: 任务输入队列，接收上游节点的输出
     - `TaskOutQueue`: 任务输出队列，发送结果给下游节点
   - **关键功能**: 线程安全、流量控制、背压处理、序列化支持

3. **core_envelope.py** (`TaskEnvelope`)
   - **作用**: 任务数据包装器，包含任务数据、元数据和执行上下文
   - **包含信息**: 任务ID、输入数据、执行参数、错误处理策略、优先级
   - **关键功能**: 数据封装、上下文传递、错误传播、优先级排序

### 监控和度量

4. **core_metrics.py** (`TaskMetrics`)
   - **作用**: 任务执行指标收集和监控
   - **收集指标**: 执行时间、成功率、错误率、队列长度、吞吐量
   - **关键功能**: 实时监控、性能分析、瓶颈检测、报警触发

5. **core_progress.py** (`TaskProgress`, `NullTaskProgress`)
   - **作用**: 任务进度报告和显示
   - **进度类型**: 确定性进度（已知总数）、不确定性进度（流式）
   - **关键功能**: 进度更新、进度条显示、ETA 估算、速度计算

### 工具和工具类

6. **util_errors.py** (`CelestialFlowError`, `ConfigurationError`, `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `LogLevelError`, `RemoteWorkerError`, `UnconsumedError`, `PickleError`)
   - **作用**: 错误处理框架，定义标准错误类型和处理策略
   - **错误类型**: 
     - `CelestialFlowError`: 所有自定义异常的基类
     - `ConfigurationError`: 配置错误（参数非法、组合不支持等）
     - `InvalidOptionError`: 配置项取值不合法
     - `ExecutionModeError`: 执行模式错误
     - `StageModeError`: Stage 模式错误
     - `LogLevelError`: 日志级别错误
     - `RemoteWorkerError`: 远程 Worker 错误
     - `UnconsumedError`: 未消费任务错误
     - `PickleError`: 序列化错误
   - **关键功能**: 错误分类、详细错误信息、参数验证、错误恢复

7. **util_factories.py**
   - **作用**: 运行时组件的工厂函数，简化对象创建
   - **工厂函数**:
     - `make_counter()`: 创建计数器（线程安全/进程安全）
     - `make_queue_backend()`: 根据执行模式创建队列后端
     - `make_task_in_queue()`: 创建任务输入队列
     - `make_task_out_queue()`: 创建任务输出队列
   - **关键功能**: 统一的对象创建接口、配置适配、依赖管理

8. **util_types.py**
   - **作用**: 运行时类型定义和数据结构
   - **包含类型**:
     - `TerminationSignal`: 任务队列终止的哨兵对象
     - `TerminationIdPool`: 终止信号 ID 池
     - `StageStatus`: Stage 状态枚举（IDLE, RUNNING, FINISHED, ERROR）
     - `STAGE_STYLE`: Stage 样式枚举
     - `NodeLabelStyle`: 节点标签样式（来自 CelestialTree）
   - **关键功能**: 类型定义、枚举管理、数据结构、类型安全

9. **util_tools.py**
   - **作用**: 运行时工具函数，提供通用功能
   - **关键函数**: `cleanup_mpqueue()`: 清理多进程队列，确保资源释放
   - **关键功能**: 资源管理、队列清理、内存释放、多进程安全

10. **util_hash.py**
    - **作用**: 对象哈希计算，用于任务去重和缓存
    - **关键函数**:
      - `make_hashable()`: 将对象转换为可哈希的形式
      - `object_to_str_hash()`: 计算对象的字符串哈希值
    - **关键功能**: 稳定哈希计算、对象序列化、任务去重、缓存键生成

11. **util_estimators.py**
    - **作用**: 执行时间估算和进度计算
    - **关键函数**:
      - `calc_elapsed()`: 计算已用时间
      - `calc_remaining()`: 计算剩余时间
      - `calc_global_remain_equal_pred()`: 计算全局剩余时间（等权重预测）
    - **关键功能**: 时间估算、进度预测、性能分析、ETA 计算

## 模块关联

### 内部关联
- `TaskRunner` 使用 `TaskInQueue` 和 `TaskOutQueue` 获取任务和发送结果
- `TaskEnvelope` 在队列中传递，包含完整的执行上下文
- `TaskMetrics` 和 `TaskProgress` 监控 `TaskRunner` 的执行状态
- 所有错误都通过 `CelestialFlowError` 及其子类统一处理

### 外部关联
- **与 Stage 模块**: `TaskRunner` 执行 `TaskExecutor` 和 `TaskStage`
- **与 Graph 模块**: 为 `TaskGraph` 提供执行引擎和通信机制
- **与 Persistence 模块**: 支持执行状态的持久化
- **与 Observability 模块**: 提供监控数据和性能指标

## 架构特点

### 多模式执行
- 支持四种执行模式，适应不同场景需求
- 自动选择最优执行策略
- 支持混合执行模式

### 健壮性设计
- 完整的错误处理链条
- 自动重试和故障转移
- 资源泄漏防护

### 可观测性
- 全面的指标收集
- 实时进度报告
- 详细的执行日志

### 可扩展性
- 插件式架构
- 自定义执行策略
- 可配置的队列实现

## 使用模式

### 基础使用
1. **创建运行器**: 根据任务类型选择合适的 `TaskRunner` 模式
2. **配置队列**: 设置输入/输出队列，建立数据流通道
3. **执行任务**: 提交任务到运行器，监控执行状态
4. **处理结果**: 从输出队列获取结果，处理错误

### 高级使用
1. **自定义运行器**: 继承 `TaskRunner` 实现特定执行逻辑
2. **混合模式**: 组合不同执行模式处理复杂工作流
3. **监控集成**: 集成外部监控系统，实现集中式监控

## 最佳实践

1. **I/O 密集型任务**: 使用线程池模式
2. **CPU 密集型任务**: 使用进程池模式
3. **异步任务**: 使用异步模式，提高并发性能
4. **关键任务**: 配置适当的重试策略和超时设置
5. **批量任务**: 使用批处理模式，提高吞吐量
6. **监控配置**: 为生产环境配置完整的监控和报警