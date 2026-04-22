# util_config

Web 模块的配置文件读写工具。

## load_config

```python
def load_config(config_path: str) -> dict:
    """从指定路径加载并校验前端配置，返回字典。"""
```

若文件不存在，抛出 `FileNotFoundError`。

## save_config

```python
def save_config(config: dict, config_path: str) -> bool:
    """将前端配置保存到 JSON 文件，返回是否成功。"""
```
