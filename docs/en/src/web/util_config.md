# util_config

Configuration file read/write utilities for the Web module.

## load_config

```python
def load_config(config_path: str) -> dict:
    """Loads and validates the frontend configuration from the specified path, returning a dictionary."""
```

Raises `FileNotFoundError` if the file does not exist.

## save_config

```python
def save_config(config: dict, config_path: str) -> bool:
    """Saves the frontend configuration to a JSON file, returning whether the operation succeeded."""
```
