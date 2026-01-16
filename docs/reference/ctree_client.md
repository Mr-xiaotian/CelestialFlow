# CelestialTreeClient

ctree_client 是[CelestialTree](https://github.com/Mr-xiaotian/CelestialTree)(简称: ctree)的py客户端, 在3.0.7引入, 并在3.0.9版本单独作为一个库而移出CelestialFlow。

CelestialTree 是一套高性能, 用于管理事件因果关系的系统框架, 在当前项目中 CelestialTree 用于跟踪任务及因其而诞生任务的完成情况, 例如在tests/test_nodes.py::test_splitter_1中, 我在节点`GenURLs`中注入一个任务, 注入事件(task.input)的id被记为 268, 同样在`GenURLs`中, 该任务被成功处理并诞生新任务, 该事件(task.success)id为278。随后新任务又在`GenURLs`的下游节点中得到处理, 如此往复。不难注意到, 一个正常结束的 TaskGraph 中, 事件树的叶子节点事件必为task.success, task.error, 以及之后会介绍的task.duplicate三种。

```
268 (task.input) @2026-01-13 07:30:44.042842 UTC
╘-->278 (task.success) @2026-01-13 07:30:52.974399 UTC
    ╞-->290 (task.split) @2026-01-13 07:30:53.031826 UTC
    │   ╞-->347 (task.error) @2026-01-13 07:31:08.043620 UTC
    │   ╘-->351 (task.error) @2026-01-13 07:31:10.040500 UTC
    ╞-->291 (task.split) @2026-01-13 07:30:53.035202 UTC
    │   ╞-->353 (task.error) @2026-01-13 07:31:11.044860 UTC
    │   ╘-->354 (task.error) @2026-01-13 07:31:12.040774 UTC
    ╞-->298 (task.success) @2026-01-13 07:30:57.983620 UTC
    ╞-->288 (task.split) @2026-01-13 07:30:53.026329 UTC
    │   ╞-->343 (task.error) @2026-01-13 07:31:07.033985 UTC
    │   ╘-->346 (task.error) @2026-01-13 07:31:08.043620 UTC
    ╘-->289 (task.split) @2026-01-13 07:30:53.029431 UTC
        ╞-->345 (task.error) @2026-01-13 07:31:08.027845 UTC
        ╘-->352 (task.success) @2026-01-13 07:31:10.041021 UTC
            ╘-->359 (task.success) @2026-01-13 07:31:16.056883 UTC
                ╞-->386 (task.success) @2026-01-13 07:31:22.066992 UTC
                ╞-->364 (task.split) @2026-01-13 07:31:16.059828 UTC
                │   ╞-->406 (task.error) @2026-01-13 07:31:32.090677 UTC
                │   ╘-->409 (task.error) @2026-01-13 07:31:33.099882 UTC
                ╞-->365 (task.split) @2026-01-13 07:31:16.062028 UTC
                │   ╞-->411 (task.error) @2026-01-13 07:31:34.103804 UTC
                │   ╘-->412 (task.success) @2026-01-13 07:31:35.092233 UTC
                │       ╘-->423 (task.success) @2026-01-13 07:31:40.102440 UTC
                │           ╞-->425 (task.split) @2026-01-13 07:31:40.105805 UTC
                │           │   ╞-->451 (task.error) @2026-01-13 07:31:48.151652 UTC
                │           │   ╘-->452 (task.error) @2026-01-13 07:31:49.110802 UTC
                │           ╞-->426 (task.split) @2026-01-13 07:31:40.107855 UTC
                │           │   ╞-->454 (task.error) @2026-01-13 07:31:50.134616 UTC
                │           │   ╘-->450 (task.error) @2026-01-13 07:31:48.150579 UTC
                │           ╞-->427 (task.split) @2026-01-13 07:31:40.109776 UTC
                │           │   ╞-->456 (task.error) @2026-01-13 07:31:51.119461 UTC
                │           │   ╘-->455 (task.error) @2026-01-13 07:31:50.134616 UTC
                │           ╘-->440 (task.success) @2026-01-13 07:31:45.106330 UTC
                ╘-->366 (task.split) @2026-01-13 07:31:16.064001 UTC
                    ╞-->410 (task.error) @2026-01-13 07:31:34.087984 UTC
                    ╘-->413 (task.error) @2026-01-13 07:31:35.108740 UTC
```
<p align="center"><em>一个任务的完整的事件树</em></p>

```
268
╘-->278
    ╞-->290
    │   ╞-->347
    │   ╘-->351
    ╞-->291
    │   ╞-->353
    │   ╘-->354
    ╞-->298
    ╞-->288
    │   ╞-->343
    │   ╘-->346
    ╘-->289
        ╞-->352
        │   ╘-->359
        │       ╞-->364
        │       │   ╞-->406
        │       │   ╘-->409
        │       ╞-->365
        │       │   ╞-->411
        │       │   ╘-->412
        │       │       ╘-->423
        │       │           ╞-->426
        │       │           │   ╞-->450
        │       │           │   ╘-->454
        │       │           ╞-->427
        │       │           │   ╞-->456
        │       │           │   ╘-->455
        │       │           ╞-->440
        │       │           ╘-->425
        │       │               ╞-->451
        │       │               ╘-->452
        │       ╞-->366
        │       │   ╞-->410
        │       │   ╘-->413
        │       ╘-->386
        ╘-->345
```
<p align="center"><em>只保留struct的事件树</em></p>

## 事件类型介绍

1. task.input
   
- "任务注入事件", 发生于 task_manager 的 put_task_queues/put_task_queues_async 方法, 或者 task_graph 的 put_stage_queue 方法中, 是唯一一种非框架内部的任务诞生方式。
- 无父事件。

2. task.success

- "任务成功事件", 表示某个任务被成功处理, 同时也代表一个新任务的诞生(如果没有后续节点, 新任务不会被处理)。
- 父事件可以为: task.input, task.success, task.retry, task.split, task.route。

3. task.error

- "任务失败事件", 表示某个任务被处理失败, 不会再有后续任务诞生。
- 父事件可以为: task.input, task.success, task.retry, task.split, task.route。

4. task.duplicate

- "任务重复事件", 表示某个任务被重复处理, 不会再有后续任务诞生。
- 父事件可以为: task.input, task.success, task.retry, task.split, task.route。

5. task.retry.{num}

- "任务重试事件", 表示某个任务被重新处理, 根据所在节点设置的retry_num, 可能会出现多次。
- 父事件可以为: task.input, task.success, task.retry, task.split, task.route。

6. task.split

- "任务分裂事件", 表示某个任务被分裂成多个任务, 同时也代表多个新任务的诞生。
- 父事件可以为: task.input, task.success, task.retry, task.split, task.route。

7. task.route

- "任务路由事件", 表示某个任务被路由到其他节点, 同时也代表一个新任务的诞生。
- 父事件可以为: task.input, task.success, task.retry, task.split, task.route。

## 一个"不存在"的id: task_id

在 task_graph 中, 每个任务被分配到一个唯一的 task_id, 如果当前启用了ctree_client的话, 那么这个task_id 也就是该任务创造事件的id, 比如如果该任务是从外界注入, 那么其 task_id 就是 task.input 事件的id。task.error与task.duplicate事件外的全部事件都可以作为任务的"创造事件"。

值得注意的是, 如果一个任务处理失败但还有retry机会的话, 那么其task_id会变为当前task.retry事件的id, 而不是其上有节点的task.input或者task.success等事件id; 当然, 如果retry进行了多次, 那么每次task_id都会改变。