# TaskManager

TaskManager 是一个用于管理和执行任务的灵活框架，支持串行、并行、异步及多进程的任务执行方式。它具有强大的重试机制、日志记录功能、进度管理，以及多种执行模式的兼容性。

## 特性
- **多种执行模式**：支持串行（serial）、线程池（thread）、进程池（process）以及异步（async）执行。
- **重试机制**：对于指定的异常类型任务，可以自动重试，支持指数退避策略。
- **日志记录**：使用 loguru 记录任务执行过程中的成功、失败、重试等情况。
- **进度管理**：支持通过 ProgressManager 动态显示任务进度。
- **任务结果管理**：任务的执行结果和错误信息被统一记录并可获取。
- **任务去重**：支持任务去重，防止重复任务的执行。
- **资源释放**：自动管理线程池和进程池资源的创建和关闭，防止资源泄漏。
- **可组成图结构**: 可以单独运行, 也可以组成为图结构, 实现任务的流操作。

## 快速上手

### 1. 初始化 TaskManager
首先，定义一个你想要并行执行的任务函数。任务函数接受的参数形式可以自由定义，稍后你需要在 TaskManager 中实现如何获取这些参数。

```python
def example_task(x, y):
    return x + y
```

然后，创建一个 TaskManager 实例，并指定你的任务函数、执行模式和其他配置参数：

```python
from celestialflow import TaskManager

# 创建TaskManager实例
task_manager = TaskManager(
    func=example_task,
    execution_mode='thread',    # 可选：serial, thread, process, async
    worker_limit=5,             # 最大并发限制
    max_retries=3,              # 最大重试次数
    max_info=50,                # 日志中单个信息的最大显示量
    unpack_task_args=True,      # 是否解包参数
    enable_success_cache=False, # 是否启用成功结果缓存
    enable_error_cache=False,   # 是否启用失败结果缓存
    enable_duplicate_check=True,# 是否启用重复检查
    progress_desc="Processing", # 进度条信息
    show_progress=True,         # 是否显示进度
)
```

### 2. 启动任务
准备好任务列表后，可以通过 start 方法启动任务执行：

```python
tasks = [(1, 2), (3, 4), (5, 6), (7, 8)]
task_manager.start(tasks)
```

TaskManager 将根据设定的执行模式并发或异步地执行任务，并自动处理任务的成功、失败和重试逻辑。

### 3. 获取任务结果
任务执行完成后，可以通过 get_success_dict 方法获取执行结果，或通过 get_error_dict 获取失败的任务及其对应的异常。

注意: 只有在`enable_success_cache=True || enable_error_cache=True`时才会记录结果信息， 否则 get_success_dict 和 get_error_dict 返回值为空。

```python
# 获取成功的结果
results = task_manager.get_success_dict()
print("Results:", results)

# 获取失败的任务及其异常
errors = task_manager.get_error_dict()
print("Errors:", errors)
```

## 主要参数和方法说明

### TaskManager 类
func: 任务执行函数，必须是可调用对象。
execution_mode: 执行模式，支持 'serial'、'thread'、'process' 和 'async'。
worker_limit: 最大并发任务数，适用于并发和异步执行模式, 一般<=50。
max_retries: 任务失败时的最大重试次数。
max_info: 日志中单个信息的最大显示量
unpack_task_args: 是否解包参数, 当输入参数多于一个时使用(但还有一种更方便的模式, 之后介绍)
enable_success_cache: 是否启用成功结果缓存, 将成功结果保存在 success_dict 中
enable_error_cache: 是否启用失败结果缓存, 将失败结果保存在 error_dict 中
enable_duplicate_check: 是否启用重复检查
show_progress: 是否显示任务进度条，默认不显示。
progress_desc: 进度条的描述文字，用于标识任务类型。

### 常用方法
start(task_list: List): 启动任务执行，task_list 是任务列表，每个任务的格式取决于你在 get_args 中如何定义。
start_async(task_list: List): 异步地执行任务。
get_success_dict() -> dict: 返回任务执行的结果字典，键是任务对象，值是任务结果。
get_error_dict() -> dict: 返回任务执行失败的字典，键是任务对象，值是异常信息。

### 自定义方法
你可以通过继承 TaskManager 并实现以下方法，来自定义任务处理的逻辑：

get_args(task): 从任务对象中提取执行函数的参数。根据任务对象的结构，自定义参数提取逻辑。
process_result(task, result): 处理任务的执行结果。可以对结果进行处理、格式化或存储。

process_result_dict(): 运行结束后执行, 可以统一处理所有结果。
handle_error_dict(): 运行结束后执行, 可以统一处理所有错误。

**示例**

以刚才的例子为蓝本, 我们可以通过定义 `get_args` `process_result` `process_result_dict` `handle_error_dict` 来获得更个性化的控制。

```python
from collections import defaultdict
from celestialflow import TaskManager

class ExampleTaskManager(TaskManager):
    def get_args(task):
        # 可以在 get_args 中对输入参数进行筛选, 或者预处理
        # 在组成 TaskGraph 时这一点尤其重要, 因为上游传递的任务未必是自己需要的形式
        num1, num2 = task
        if num1 < 0 or num2 < 0>:
            raise ValueError("num must large than 0.") 
        return num1, num2 # get_args返回的必须是一个可迭代对象, 默认为(task, )

    def process_result(task, result):
        # 可以在 process_result 中对函数结果进行处理
        # 同样在组成 TaskGraph 时非常重要
        num1, num2 = task
        return f"{num1} + {num2} = {result}"

    def process_result_dict():
        # 这个函数大多数情况下是不需要的, 但有时我们需要跟踪每一个任务的处理情况
        # 这里用的是默认实现
        return {**self.success_dict, **self.error_dict}

    def handle_error_dict(self):
        # 同样的, 这个函数大多数也用不到, 除非你想得到更系统的错误返回形式
        # 这里用的是默认实现
        error_groups = defaultdict(list)
        for task, error in self.error_dict.items():
            error_groups[error].append(task)

        return dict(error_groups)


def example_task(x, y):
    return x + y

example_task_manager = ExampleTaskManager(
    func=example_task,
    execution_mode='thread', 
    worker_limit=50,         
    unpack_task_args=False,     # 因为我们已经在 get_args 进行了解包, 这里选False
    enable_success_cache=True,  # 因为要运行 process_result_dict 和 handle_error_dict, 这里必须为True
    enable_error_cache=True,   
    progress_desc="Example Processing", 
    show_progress=True,         # 默认为False, 因为开启会影响性能, 具体可看experiments\benchmark_tqdm.py
)
```

## 日志
TaskManager 使用 loguru 进行日志记录，默认将日志保存到 logs/ 目录下。

## 进阶

### 自定义任务参数
见 自定义方法 一节。

### 重试机制
对于定义的 retry_exceptions，如 TimeoutError 或 ConnectionError，TaskManager 将自动重试这些任务。如果你有自定义的异常类型，可以通过设置 self.retry_exceptions 来扩展重试逻辑。
