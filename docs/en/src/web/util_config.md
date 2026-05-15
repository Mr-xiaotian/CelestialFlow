# util_config

> 📅 Last Updated: 2026/04/22

Configuration file read/write utilities for the Web module.

## load_config

```python
def load_config(config_path: str) -> dict:
    """Load and validate frontend configuration from the specified path, returning a dictionary."""
```

Raises `FileNotFoundError` if the file does not exist.

## save_config

```python
def save_config(config: dict, config_path: str) -> bool:
    """Save frontend configuration to a JSON file, returning whether the operation succeeded."""
```
