# util_config

> 📅 最后更新日期: 2026/05/23

Web 模块的配置文件读写工具，负责 `config.json` 的持久化管理。

## load_config

```python
def load_config(config_path: str) -> dict:
    """从指定路径加载并校验前端配置，返回字典。"""
```

- 若文件不存在，会尝试从默认模板初始化或直接报错。
- 提供基础的字段有效性校验。

## save_config

```python
def save_config(config: dict, config_path: str) -> bool:
    """将前端配置保存到 JSON 文件，返回是否成功。"""
```

- 使用线程锁保护，确保多并发下的文件写入安全。
