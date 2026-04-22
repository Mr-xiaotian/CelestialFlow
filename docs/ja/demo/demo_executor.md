# demo_executor.py デモ説明

> 📅 最終更新日: 2026/04/22

## 目的

`TaskExecutor` の3つの実行モード（`serial`、`thread`、`async`）における単独実行能力を実演します。例外リトライ、進捗表示、タスク統計の完全なライフサイクルを紹介し、フレームワーク入門の最初の体験として最適です。

## デモ内容

| 関数 | モード | タスク | 特徴 |
|------|--------|--------|------|
| `demo_fibonacci_serial` | serial | フィボナッチ計算 | シングルスレッド順次実行 |
| `demo_fibonacci_thread` | thread | フィボナッチ計算 | 6スレッド並行処理 |
| `demo_fibonacci_async` | async | 非同期フィボナッチ | コルーチン並行処理 |

- **入力**：`range(25, 32) + [0, 27, None, 0, ""]`
- **例外設計**：`0`、`None`、`""` は `ValueError` をトリガーし、フレームワークが自動的に1回リトライします

## 主要設定

- `max_workers = 6`
- `max_retries = 1`
- `show_progress = False`（デモ時の出力の混乱を避けるため tqdm を無効化）

## 発生しうる問題

1. **再帰の深さと実行時間**：`fibonacci(31)` は膨大な数の再帰呼び出しを伴い、serial モードでは10秒以上かかる場合があります。
2. **`asyncio` 環境**：`demo_fibonacci_async` は `asyncio.run()` を使用しており、Jupyter Notebook で直接実行するとエラーが発生します（Notebook には既にイベントループが存在するため）。
3. **アサーションなし**：このファイルは**デモスクリプト**であり、`assert` を含みません。実行成功はキャッチされない例外が発生しなかったことを意味するのみで、結果の正確性は検証されません。

## 実行方法

```bash
python demo/demo_executor.py
```

## 依存関係

- `celestialflow`（`TaskExecutor`）
- `demo_utils`（`fibonacci`、`fibonacci_async`）
