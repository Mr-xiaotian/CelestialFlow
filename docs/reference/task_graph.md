# TaskGraph

TaskGraph 是一个用于组织和执行多阶段任务链的框架。每个阶段都是由 TaskExecutor 实例组成，任务链可以串行或并行执行。在任务链中，任务会依次通过每个阶段的处理，并最终返回结果。

## 特性

- **多阶段任务管理**：TaskGraph 将多个 TaskExecutor 实例连接起来，形成一个任务链，每个任务经过各个阶段的处理。
- **执行模式**：支持串行（serial）和多进程并行（process）执行方式。
- **任务结果追踪**：能够跟踪初始任务在整个任务链中的最终结果。
- **动态阶段管理**：可以动态添加、移除或修改任务链中的阶段。

## 依赖
TaskGraph 基于 TaskExecutor 构建，因此需要先安装 TaskExecutor 相关依赖：

```bash
pip install loguru
```

## 快速上手
### 1. 初始化 TaskGraph
首先，准备多个 TaskExecutor 实例，每个实例代表任务链中的一个阶段。然后，创建一个 TaskGraph 实例，将这些 TaskExecutor 实例作为参数传递给 TaskGraph。

```python
from task_executor import TaskExecutor, TaskGraph

# 定义几个简单的任务函数
def task_stage_1(x):
    return x + 1

def task_stage_2(x):
    return x * 2

# 创建 TaskExecutor 实例，代表不同的任务阶段
stage_1 = TaskExecutor(func=task_stage_1, execution_mode='serial')
stage_2 = TaskExecutor(func=task_stage_2, execution_mode='thread')

# 创建 TaskGraph 实例
task_graph = TaskGraph(stages=[stage_1, stage_2])
```

### 2. 启动任务链
准备好初始任务列表后，通过 start_graph 方法启动任务链执行。任务将依次通过每个阶段进行处理。

```python
# 定义初始任务
initial_tasks = [1, 2, 3, 4]

# 启动任务链（默认串行模式）
task_graph.start_graph(initial_tasks)
```

### 3. 获取最终结果
任务链执行完成后，可以通过 get_final_result_dict 方法获取每个初始任务的最终处理结果。

```python
# 获取任务链的最终结果
final_results = task_graph.get_final_result_dict()
print("Final Results:", final_results)
```

### 4. 并行执行任务链
如果任务链中的每个阶段需要并行处理任务，可以将 graph_mode 设置为 'process'，并启动任务链。这会使用多进程来并行处理任务链中的每个阶段，此时每个阶段的处理结果会立刻交给下一阶段进行处理。

```python
task_graph.set_graph_mode('process')
task_graph.start_graph(initial_tasks)
```

## 主要参数和方法说明
### TaskGraph 类
- **stages**: 一个包含 TaskStage 实例的列表，代表任务链的各个阶段。
- **graph_mode**: 任务链的执行模式，支持 'serial'（串行）和 'process'（并行）。默认为串行模式。

### 常用方法
- set_graph_mode(graph_mode: str): 设置任务链的执行模式，可以选择 'serial' 或 'process'。
- add_stage(stage: TaskStage): 动态添加一个新的任务阶段到任务链中。
- remove_stage(index: int): 移除任务链中指定索引的阶段。
- start_graph(tasks: List): 启动任务链，传入初始任务列表。根据 graph_mode 选择串行或并行方式执行任务链。
- run_graph_in_serial(tasks: List): 串行地执行任务链中的每个阶段。
- run_graph_in_process(tasks: List): 使用多进程并行地执行任务链中的每个阶段。
- get_final_result_dict() -> dict: 获取初始任务在整个任务链中最终处理的结果字典。

## TaskGraph 关键功能解释
### 串行模式（serial）

每个任务依次经过任务链的所有阶段，前一个阶段的输出作为下一个阶段的输入。

### 并行模式（process）

每个阶段在独立的进程中并行执行，使用多进程队列（MPQueue）在阶段间传递任务结果。任务在第一个阶段的结果会作为输入传递给下一个阶段，直到所有阶段完成。

## 任务链的工作流程
- 初始化任务队列：初始任务列表被放入第一个阶段的任务队列中。
- 阶段执行：每个阶段分别处理任务，串行或并行模式下，任务通过各个阶段的处理。
- 结果收集：每个阶段的结果会传递到下一个阶段，最终获取初始任务的最终处理结果。

## 示例
### 1. 串行任务链
```python
# 创建 TaskGraph 实例
task_graph = TaskGraph(stages=[stage_1, stage_2], graph_mode='serial')

# 定义初始任务
initial_tasks = [1, 2, 3, 4]

# 启动任务链
task_graph.start_graph(initial_tasks)

# 获取最终结果
final_results = task_graph.get_final_result_dict()
print("Final Results:", final_results)
```
### 2. 并行任务链
```python
# 创建 TaskGraph 实例
task_graph = TaskGraph(stages=[stage_1, stage_2], graph_mode='process')

# 定义初始任务
initial_tasks = [1, 2, 3, 4]

# 启动任务链（并行模式）
task_graph.start_graph(initial_tasks)

# 获取最终结果
final_results = task_graph.get_final_result_dict()
print("Final Results:", final_results)
```
