# util_config

> 📅 最終更新日: 2026/04/22

Web モジュールの設定ファイル読み書きユーティリティ。

## load_config

```python
def load_config(config_path: str) -> dict:
    """指定パスからフロントエンド設定を読み込み、検証して辞書を返す。"""
```

ファイルが存在しない場合、`FileNotFoundError` を送出します。

## save_config

```python
def save_config(config: dict, config_path: str) -> bool:
    """フロントエンド設定を JSON ファイルに保存し、成功したかどうかを返す。"""
```
