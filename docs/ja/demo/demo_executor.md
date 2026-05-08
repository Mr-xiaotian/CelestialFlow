# demo_executor.py デモ説明

> 📅 最終更新日: 2026/05/08

## 目標

`TaskExecutor` の3つの実行モード（`serial`、`thread`、`async`）での独立実行能力をデモ。例外リトライ、進捗表示、タスク統計の完全なライフサイクルを紹介。

## デモ内容

| 関数 | モード | タスク | 特性 |
|------|--------|--------|------|
| `demo_fibonacci_serial` | serial | フィボナッチ計算 | シングルスレッド順次実行 |
| `demo_fibonacci_thread` | thread | フィボナッチ計算 | 6 スレッド並行 |
| `demo_fibonacci_async` | async | 非同期フィボナッチ | コルーチン並行 |

- **入力**: `range(25, 32) + [0, 27, None, 0, ""]`
- **例外設計**: `0`、`None`、`""` は `ValueError` をトリガーし、フレームワークが 1 回リトライ

## 主要設定

- `max_workers = 6`
- `max_retries = 1`
- `executor.add_observer(TaskProgress())` でプログレスバーを追加

## 実行方法

```bash
python demo/demo_executor.py
```

## 依存関係

- `celestialflow`（`TaskExecutor`、`TaskProgress`）
- `demo_utils`（`fibonacci`、`fibonacci_async`）
