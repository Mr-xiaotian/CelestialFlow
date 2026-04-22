# util_config

Web モジュールの設定ファイル読み書きツールです。

## load_config

```python
def load_config(config_path: str) -> dict:
    """指定されたパスからフロントエンド設定を読み込み、検証して辞書を返します。"""
```

ファイルが存在しない場合、`FileNotFoundError` を送出します。

## save_config

```python
def save_config(config: dict, config_path: str) -> bool:
    """フロントエンド設定を JSON ファイルに保存し、操作が成功したかどうかを返します。"""
```
