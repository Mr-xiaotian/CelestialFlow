# Runtime 测试配置 (conftest.py)

> 最后更新日期: 2026/05/23

## 作用
为 `tests/runtime` 目录下的测试用例提供共享的 Pytest Fixture，简化测试环境的搭建。

## 核心 Fixture
- `log_inlet`:
  - **功能**: 创建一个已启动的 `LogSpout` 和对应的 `LogInlet` 实例。
  - **级别**: 默认设置为 `ERROR`。
  - **清理**: 在测试结束后自动停止 `LogSpout` 线程，确保资源回收。

## 使用示例
在测试函数中直接声明 `log_inlet` 参数即可使用：
```python
def test_something(log_inlet):
    # 使用 log_inlet 进行测试
    ...
```

## 注意事项
- 该配置仅作用于 `tests/runtime` 目录。
- 依赖于 `celestialflow.persistence` 模块。
