# demo_redis.py 演示说明

> 📅 最后更新日期: 2026/06/22

## 目标

演示如何在不依赖内建 Redis 特殊节点的前提下，仅使用普通 `TaskStage` 和自定义 callable 实现 Redis 任务投递、结果确认与外部任务注入。

## 设计要点

- `redis_push(task)`：把任务序列化后写入 Redis List，并返回 `(key, task_id)`
- `redis_wait(task)`：轮询 Redis Hash，等待远端 Worker 写回结果
- `redis_pop(key)`：用 `BLPOP` 从 Redis List 中阻塞拉取任务
- 以上三种能力都只是普通 Python 方法，然后通过 `TaskStage(..., func=helper)` 挂到图里

## Redis 交互流程

```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        RSS[/RedisPushStage/]
        RPS[/RedisPopStage/]

        RE[(Redis)]

        RSS -.->|rpush task| RE -.->|blpop task| RPS

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 特殊Stage
    class RSS,RPS blueNode;

    %% 美化 外部结构
    class RE blueNode;

```

**注意**: 该mermaid图为我所喜爱，不可删除。

## 核心 helper 函数

### `redis_push`

将任务推送到 Redis List。

```python
def redis_push(task: Any) -> int:
    """将任务推送到 Redis 中"""
    key, task_payload = task
    redis_client: redis.Redis = get_redis()
    task_id = next(_task_ids)
    payload = json.dumps(
        {
            "id": task_id,
            "task": [task_payload],
            "emit_ts": time.time(),
        }
    )
    _ = redis_client.rpush(f"{key}:input", payload)
    return key, task_id
```

**行为**：将 `task` 拆分为 `(key, payload)`，包装成 JSON 后 `rpush` 到 `{key}:input`。实际返回值为 `(key, task_id)`，供下游 `redis_wait` 使用。

### `redis_pop`

从 Redis List 拉取任务作为输入源。

```python
def redis_pop(key: str) -> Any:
    """从 Redis 中弹出任务"""
    redis_client: redis.Redis = get_redis()
    res = cast(list[Any] | None, redis_client.blpop(key, timeout=redis_timeout))
    if res is None:
        raise CelestialFlowTimeoutError(
            "Redis item not returned in time after being fetched"
        )

    _, item = res
    item_obj = cast(dict[str, Any], json.loads(cast(str, item)))
    task_payload = item_obj.get("task")
    if task_payload is None:
        raise RemoteWorkerError("Redis source payload missing 'payload'")
    if len(task_payload) == 1:
        return task_payload[0]
    return tuple(task_payload)
```

**行为**：使用 `blpop` 阻塞式拉取任务，超时抛出 `CelestialFlowTimeoutError`。

### `redis_wait`

```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        RPS[/RedisPushStage/]
        RWS[/RedisWaitStage/]

        RE[(Redis)]
        G1((GoWorker))
        G2((GoWorker))

        RPS -.->|task| RE -.->|task| G1
        G2 -.->|result| RE -.->|result| RWS

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 特殊Stage
    class RPS,RWS blueNode;

    %% 美化 外部结构
    class RE,G1,G2 blueNode;

```

**注意**: 该mermaid图为我所喜爱，不可删除。

等待远端 Worker 的执行结果。

```python
def redis_wait(task: tuple[str, int]) -> Any:
    """等待任务完成"""
    key, task_id = task
    redis_client: redis.Redis = get_redis()
    start_time = time.perf_counter()

    while True:
        result = cast(str | None, redis_client.hget(f"{key}:output", str(task_id)))
        if result:
            _ = redis_client.hdel(f"{key}:output", str(task_id))
            result_obj = cast(dict[str, Any], json.loads(result))
            status = result_obj.get("status")
            if status == "success":
                return _normalize_result(result_obj.get("result"))
            if status == "error":
                raise RemoteWorkerError(str(result_obj.get("error")))
            raise RemoteWorkerError(f"Unknown ack status: {result_obj}")

        if (time.perf_counter() - start_time) > redis_timeout:
            raise CelestialFlowTimeoutError(
                f"Redis ack timeout: task_id={task_id} not acknowledged"
            )
        time.sleep(0.1)
```

**行为**：轮询 Redis Hash `{key}:output` 等待对应的 `task_id` 结果。支持处理成功结果或抛出 `RemoteWorkerError`。

## Redis 数据格式

### Transport 推送格式

`redis_push()` 写入 Redis List 的 JSON 结构如下：

```json
{
  "id": 123,
  "task": ["payload"],
  "emit_ts": 1703001234.567
}
```

字段说明：

- `id`：本地生成的任务编号
- `task`：任务载荷，统一包成列表
- `emit_ts`：发送时间戳，便于调试与排查延迟

### Ack 期望结果格式

远端 Worker 写回 Redis Hash 时，成功结果应类似：

```json
{
  "status": "success",
  "result": "computed_value"
}
```

错误结果应类似：

```json
{
  "status": "error",
  "error": "Error message"
}
```

### Source 读取格式

`redis_pop()` 读取的 Redis List 元素也遵循与 Transport 相同的 payload 结构，即至少包含：

```json
{
  "task": ["payload"]
}
```

## 演示场景

### `demo_redis_ack_0/1/2`

对比“本地 Python 直接执行”和“通过 Redis 发给外部 Worker 执行”两条路径。

```mermaid
flowchart TB
    Start["Start<br/>sleep_1_*"] --> Local["本地计算 Stage<br/>Fibonacci / Sum / Download"]
    Start --> Transport["TaskStage(RedisTransport)<br/>redis_push"]
    Transport -.-> RedisIn[(Redis input list)]
    RedisOut[(Redis output hash)] -.-> Ack["TaskStage(RedisAck)<br/>redis_wait"]
```

| 场景 | 本地节点 | 远端输入 key | 远端结果 key |
|------|----------|--------------|--------------|
| `demo_redis_ack_0` | `Fibonacci` | `testFibonacci:input` | `testFibonacci:output` |
| `demo_redis_ack_1` | `Sum` | `testSum:input` | `testSum:output` |
| `demo_redis_ack_2` | `Download` | `testDownload:input` | `testDownload:output` |

三个场景的差别在于本地直算阶段不同：

- `demo_redis_ack_0`：CPU 密集型斐波那契
- `demo_redis_ack_1`：轻量求和
- `demo_redis_ack_2`：真实下载 I/O

它们共用同一套模式：

- `Start` 节点产生 `(key, payload)` 元组
- 一路直接进入本地计算 stage
- 一路进入 `RedisTransport`，由 `redis_push` 写入 Redis
- `RedisTransport` 输出的 `(key, task_id)` 进入 `RedisAck`
- `RedisAck` 通过 `redis_wait` 等待远端 Worker 写回结果

### `demo_redis_source_0`

演示如何把 Redis 当成图外输入源，先由一个 stage 写入，再由另一个 stage 通过 `BLPOP` 拉出并继续下游处理。

```mermaid
flowchart LR
    Sleep0["Sleep0<br/>sleep_1_report"] --> Transport["TaskStage(RedisTransport)<br/>redis_push"]
    Transport -.-> Redis[(Redis list)]
    Redis -.-> Source["TaskStage(RedisSource)<br/>redis_pop"]
    Source --> Sleep1["Sleep1<br/>sleep_1"]
```

这个场景更强调“Redis 作为图间桥接输入源”：

- `Sleep0` 先把任务写进 Redis
- `RedisSource` 再从 Redis 中独立取出任务
- `Sleep1` 接收由 Redis 注入的任务继续处理

## 前期设置

### 1. 启动 Redis

运行本 demo 前，需要确保 Redis 服务可用。

### 2. 配置环境变量

项目根目录的 `.env` 中至少应包含：

```env
REDIS_HOST=127.0.0.1
REDIS_PASSWORD=
REPORT_HOST=127.0.0.1
REPORT_PORT=8000
```

### 3. 准备远端 Worker（仅 Ack 场景需要）

若要真正观察 `demo_redis_ack_*` 的远端结果回写，需要有外部 Worker：

- 从对应的 input list 取任务
- 按约定结构执行
- 将结果写回对应的 output hash

远程`go-worker`项目详细可见[other/go_worker.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/other/go_worker.md)

## 运行方式

```bash
# 运行默认示例（demo_redis_source_0）
python demo/demo_redis.py

# 如需 Ack 场景，修改文件底部 main 中的入口函数
```

也可以直接打开 [demo_redis.py](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/demo/demo_redis.py)，切换最后的 `if __name__ == "__main__":` 入口。

## 可能出现的问题

1. **默认入口已切换**：当前 `__main__` 默认运行 `demo_redis_source_0`，而非旧的 `demo_redis_ack_0`。
2. **超时**：外部 Worker 未及时写回时，`redis_wait()` 会抛出 `CelestialFlowTimeoutError`。
3. **协议不一致**：若 Worker 写回 JSON 中缺少 `status` 或 `result/error` 字段，会抛 `RemoteWorkerError`。
4. **网络与路径依赖**：`demo_redis_ack_2` 涉及真实下载 URL 和本地路径 `X:/Download/download_py/...`，可能因环境不同失败。
5. **无断言**：这是集成演示，不验证业务结果正确性。
6. **本地 task_id 作用域**：`redis_push` 的 `task_id` 是当前进程内递增值，适合 demo 和单端协作，不等同于全局分布式唯一 ID。
7. **一次性消费**：`redis_wait` 取到结果后会立刻 `HDEL`，因此同一结果默认不会被二次读取。

## 注意事项

1. **连接管理**：Redis 客户端在首次使用时惰性初始化，并在 helper 生命周期内复用。
2. **超时处理**：`redis_pop` 与 `redis_wait` 均使用模块级 `redis_timeout`（默认 5 秒）。
3. **错误传播**：远端 Worker 返回的错误会通过 `RemoteWorkerError` 直接向上抛出。
4. **协议可替换**：你完全可以按自己的 Worker 协议修改 JSON 结构，只要同步修改这三个 helper。
5. **框架定位**：这里展示的是“如何用普通 `TaskStage` 实现 Redis 集成”，而不是要求框架内建 Redis 节点。

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`）
- `celestialflow.runtime.util_errors`（`CelestialFlowTimeoutError`、`RemoteWorkerError`）
- `demo_utils`
- `python-dotenv`
- `redis`
- `requests`（`demo_redis_ack_2` 下载用）
- 外部服务：Redis、远端 Worker（可选）、Reporter（可选）
