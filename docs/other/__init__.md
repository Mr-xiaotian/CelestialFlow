# Other 模块

## 概述

Other 模块包含 CelestialFlow 框架的扩展组件和外部集成，这些组件不属于核心框架但提供了重要的扩展功能。主要包括 CelestialTree 客户端和 Go Worker 两个组件，分别用于任务溯源追踪和跨语言任务执行。

## 文件详细说明

### 1. ctree_client.md - CelestialTree 客户端

**作用**: 集成 CelestialTree 事件溯源系统，实现任务全链路追踪和事件记录。

**核心功能**:
- **事件记录**: 自动记录任务生命周期中的关键事件（输入、成功、失败、重试、分裂、路由等）
- **数据血缘追踪**: 查询结果的数据来源和生成路径
- **错误根因定位**: 追踪错误任务的完整调用链
- **执行树可视化**: 生成任务执行的调用树结构

**关键特性**:
- 与 CelestialTree 服务集成，支持 HTTP 和 gRPC 通信
- 自动事件发射，无需手动埋点
- 提供简化的溯源查询接口
- 支持任务分裂、路由、重复检测等复杂场景

**使用模式**:
```python
# 配置 CelestialTree 客户端
graph.set_ctree(
    use_ctree=True,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778
)

# 查询溯源信息
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
error_trace = graph.get_error_trace(error_id=12345)
```

### 2. go_worker.md - Go Worker 任务消费者

**作用**: 轻量级、可并发扩展的基于 Redis 的任务消费者（Worker Pool），用于跨语言任务执行。

**核心功能**:
- **任务消费**: 从 Redis 队列中持续消费任务
- **并发执行**: 以可控的并发度执行任务
- **结果回写**: 将执行结果写回 Redis
- **跨语言支持**: 作为 TaskGraph 的 Go 语言执行节点

**架构特点**:
- **Worker Pool 模式**: 使用 goroutine 和 channel 实现并发控制
- **自动重连机制**: 支持 Redis 连接失败时的指数退避重试
- **可插拔设计**: Parser 和 Processor 可自定义扩展
- **通用任务结构**: 使用 JSON 格式的任务负载

**关键组件**:
- **TaskParser**: 解析任务负载，转换为 Processor 所需的格式
- **TaskProcessor**: 执行业务逻辑，返回计算结果
- **Worker Pool**: 管理并发执行和资源控制

**使用模式**:
```go
// 启动 Worker Pool
worker.StartWorkerPool(
    ctx,
    rdb,
    "testFibonacci:input",  // Redis 输入队列
    "testFibonacci:output", // Redis 输出哈希
    worker.ParseListTask,   // 任务解析器
    worker.Fibonacci,       // 任务处理器
    4,                      // 并发度
)
```

## 模块关联

### 与核心框架的关系

1. **CelestialTree 客户端**:
   - 与 `TaskGraph` 紧密集成，自动记录任务事件
   - 依赖 `observability` 模块的事件发射机制
   - 为 `web` 模块提供溯源数据支持

2. **Go Worker**:
   - 与 `runtime` 模块的 `TaskRedisTransport` 和 `TaskRedisAck` 节点配合
   - 通过 Redis 与 Python 端的 TaskGraph 通信
   - 可作为独立组件使用，不强制依赖核心框架

### 组件间协作

```
TaskGraph (Python) → Redis → Go Worker → Redis → TaskGraph (Python)
    ↓
CelestialTree Client → CelestialTree Service
```

1. **任务执行流程**:
   - TaskGraph 生成任务并写入 Redis
   - Go Worker 从 Redis 消费任务并执行
   - 执行结果写回 Redis，TaskGraph 读取结果
   - CelestialTree 客户端记录整个流程的事件

2. **数据流**:
   - 任务数据通过 Redis 在 Python 和 Go 之间传递
   - 事件数据通过 HTTP/gRPC 发送到 CelestialTree
   - 溯源查询通过客户端 API 从 CelestialTree 获取

## 架构特点

### 1. 松耦合设计
- 各组件可独立部署和使用
- 通过标准协议（Redis、HTTP）通信
- 无语言绑定，支持多语言扩展

### 2. 可观测性增强
- CelestialTree 提供细粒度的任务溯源
- 支持错误追踪和性能分析
- 与框架的监控指标互补

### 3. 性能优化
- Go Worker 提供高性能的任务执行
- 并发控制避免资源耗尽
- 自动重连保证系统稳定性

## 使用模式

### 1. 全链路追踪模式
```python
# 启用 CelestialTree 追踪
graph.set_ctree(use_ctree=True)

# 运行任务图
graph.start_graph(init_tasks)

# 查询任务溯源
trace = graph.get_stage_input_trace("ProcessingStage")
```

### 2. 跨语言执行模式
```python
# Python 端：定义 Redis 传输节点
redis_sink = TaskRedisTransport(key="tasks:input")
redis_ack = TaskRedisAck(key="tasks:output")

# Go 端：启动 Worker Pool 消费任务
# go_worker/main.go 中配置相同的 Redis key
```

### 3. 混合模式
同时使用 CelestialTree 追踪和 Go Worker 执行，获得完整的可观测性和高性能执行能力。

## 最佳实践

### 1. CelestialTree 配置
- 在生产环境部署独立的 CelestialTree 服务
- 根据任务量调整事件采样率
- 定期清理过期的事件数据

### 2. Go Worker 部署
- 根据任务类型选择合适的并发度
- 监控 Redis 连接状态和队列长度
- 实现自定义 Processor 处理特定业务逻辑

### 3. 错误处理
- 为 Go Worker 添加完善的错误日志
- 实现任务重试和死信队列机制
- 监控 CelestialTree 连接状态

### 4. 性能调优
- 调整 Redis 连接池大小
- 优化任务负载的序列化格式
- 根据硬件资源调整 Worker 并发数

## 扩展建议

### 1. 新增 Processor
在 `go_worker/worker/processors.go` 中添加新的 Processor 函数，支持更多类型的任务处理。

### 2. 自定义 Parser
实现自定义的 TaskParser，支持复杂任务格式的解析。

### 3. 监控集成
将 Go Worker 的指标集成到框架的监控系统中，实现统一的可观测性。

### 4. 多语言支持
参考 Go Worker 的模式，实现其他语言（如 Java、Rust）的 Worker 组件。

## 注意事项

1. **版本兼容性**: 确保 CelestialTree 客户端与服务器版本兼容
2. **网络延迟**: Redis 和 CelestialTree 的网络延迟会影响整体性能
3. **资源管理**: 合理配置 Worker 并发度，避免资源竞争
4. **数据一致性**: 注意 Redis 事务和原子操作的使用
5. **安全考虑**: 保护 Redis 和 CelestialTree 的访问凭证