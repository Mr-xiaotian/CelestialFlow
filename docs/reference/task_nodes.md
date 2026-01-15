# TaskNodes

## TaskSplitter

```mermaid
flowchart LR
    subgraph TG[TaskSplitter]
        direction LR

        T1[Last Stage]
        T2[Next Stage]

        TS[[TaskSplitter]]

        T1 -->|1 task| TS
        TS -->|N task| T2

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 TaskStages
    class T1,T2 blueNode;

    %% 美化 特殊Stage
    class TS blueNode;

```

## TaskRouter


```mermaid
flowchart LR
    subgraph TG[TaskRouter]
        direction LR

        T1[Last Stage]
        T2[Next Stage 1]
        T3[Next Stage 2]

        TR{{TaskRouter}}

        T1 -->|2 task| TR
        TR -->|1 task| T2
        TR -->|1 task| T3

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 TaskStages
    class T1,T2,T3 blueNode;

    %% 美化 特殊Stage
    class TR blueNode;

```

## TaskRedis*系列节点

### TaskRedisSink & TaskRedisSource


```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        TRSI[/TaskRedisSink/]
        TRSO[/TaskRedisSource/]

        RE[(Redis)]

        TRSI -.-> RE -.->  TRSO

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 特殊Stage
    class TRSI,TRSO blueNode;

    %% 美化 外部结构
    class RE blueNode;

```

### TaskRedisAck


```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        TRSI[/TaskRedisSink/]
        TRA[/TaskRedisAck/]

        RE[(Redis)]
        G1((GoWorker))
        G2((GoWorker))

        TRSI -.->|task| RE -.->|task| G1
        G2 -.->|result| RE -.->|result| TRA

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 特殊Stage
    class TRSI,TRA blueNode;

    %% 美化 外部结构
    class RE,G1,G2 blueNode;

```

### 前期设置

1. 启动 Redis 服务
在运行`TaskRedis*`系节点时, 需要先启动 Redis 服务

2. 设置环境变量
然后在根目录下建立一个.env文件, 按以下格式填入:

```env
# .env
# Redis 服务地址
REDIS_HOST=127.0.0.1
# Redis 服务端口
REDIS_PORT=6379
# Redis 服务密码, 没有则留空
REDIS_PASSWORD=your_redis_password
```

3. 设置 TaskRedis*节点

然后直接通过读取.env中内容来设置 `TaskRedis*` 中 Redis 端口 节点名称与密码。

```python
import os
from dotenv import load_dotenv

load_dotenv()
redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")

# test_redis_ack_0
redis_sink = TaskRedisSink(key="testFibonacci:input", host=redis_host, password=redis_password)
redis_ack = TaskRedisAck(key="testFibonacci:output", host=redis_host, password=redis_password)

# test_redis_source_0
redis_sink = TaskRedisSink("test_redis", host=redis_host, password=redis_password)
redis_source = TaskRedisSource("test_redis", host=redis_host, password=redis_password)
```

## 下一步扩展方向
| 模块                     | 功能                                                        |
|--------------------------|-------------------------------------------------------------|
| 🔄 TaskRouter（分支控制）| 根据条件将任务路由到不同的 stage                            |
| 📦 TaskFanInr            | 将多个结果聚合后处理（fan-in）                              |
| 🔍 TaskTracer / Inspector| 给每个任务标记 trace_id、路径                               |

