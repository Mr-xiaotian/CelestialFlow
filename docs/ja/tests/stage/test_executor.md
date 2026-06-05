# TaskExecutor テスト (test_executor.py)

> 📅 最終更新日: 2026/06/05

## 目的

単独 executor の挙動、結果収集、リトライ、実行モード処理を検証します。

## 主要ポイント

- 完全なグラフ外での executor 利用に焦点を当てます。
- `TaskStage` 内部でも使われる契約を確認します。

## 実行方法

```bash
pytest tests/stage/test_executor.py -v
pytest tests/stage/test_executor.py -k "executor or retry" -v
```
